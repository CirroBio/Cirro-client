import json
import logging
import sys
import threading
import time
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Optional

import boto3
import jwt
import requests
from botocore.exceptions import ClientError
from cirro_api_client.cirro_auth import AuthMethod, RefreshableTokenAuth
from msal_extensions import FilePersistence
from msal_extensions.persistence import BasePersistence

from cirro.auth.base import AuthInfo
from cirro.auth.oauth_models import DeviceTokenResponse, OAuthTokenResponse
from cirro.config import Constants

logger = logging.getLogger()


def _build_token_persistence(location: str, fallback_to_plaintext=False):
    try:
        if sys.platform.startswith('win'):
            from msal_extensions import FilePersistenceWithDataProtection
            return FilePersistenceWithDataProtection(location)
        if sys.platform.startswith('darwin'):
            from msal_extensions import KeychainPersistence
            return KeychainPersistence(location, service_name='cirro-client')
        if sys.platform.startswith('linux'):
            from msal_extensions import LibsecretPersistence
            return LibsecretPersistence(location)
        raise RuntimeError(f"Unsupported platform: {sys.platform}")
    except Exception:
        if not fallback_to_plaintext:
            raise
        logger.debug("Encryption unavailable. Opting in to plain text.")
        return FilePersistence(location)


def _authenticate(client_id: str, auth_endpoint: str, auth_io: Optional[StringIO] = None):
    params = {'client_id': client_id}
    resp = requests.post(f'{auth_endpoint}/device-code', params=params)
    resp.raise_for_status()
    flow: DeviceTokenResponse = resp.json()
    if auth_io is None:
        print(flow['message'])
    else:
        auth_io.write(flow['message'])
    device_expiry = datetime.fromisoformat(flow['expiry'])

    params = {
        'client_id': client_id,
        'device_code': flow['device_code'],
        'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
    }

    auth_status = 'authorization_pending'
    while auth_status == 'authorization_pending':
        time.sleep(flow['interval'])
        if device_expiry < datetime.now().astimezone():
            raise RuntimeError('Authentication timed out')

        resp = requests.post(f'{auth_endpoint}/token', params=params)
        token_result: OAuthTokenResponse = resp.json()
        auth_status = token_result.get('message')
        logger.debug(auth_status)

        if 'access_token' in token_result:
            return token_result

    raise RuntimeError(f'error authenticating {auth_status}')


class DeviceCodeAuth(AuthInfo):
    """
    Authenticates to Cirro by asking
     the user to enter a verification code on the portal website

    :param enable_cache: Optionally enable cache to avoid re-authentication

    Implements the OAuth device code flow
    This is the preferred way to authenticate
    """
    def __init__(
        self,
        client_id: str,
        region: str,
        auth_endpoint: str,
        enable_cache=False,
        auth_io: Optional[StringIO] = None
    ):
        self.client_id = client_id
        self.region = region
        self._token_info: Optional[OAuthTokenResponse] = None
        self._persistence: Optional[BasePersistence] = None
        self._token_path = Path(Constants.home, f'{client_id}.token.dat').expanduser()

        if enable_cache:
            self._persistence = _build_token_persistence(str(self._token_path), fallback_to_plaintext=True)
            self._token_info = self._load_token_info()

        # Check saved token for change in endpoint
        if self._token_info and self._token_info.get('client_id') != client_id:
            logger.debug('Different client ID found, clearing saved token info')
            self._clear_token_info()

        # Check saved token for refresh token expiry
        if self._token_info and self._token_info.get('refresh_expires_in'):
            refresh_expiry_threshold = datetime.fromtimestamp(self._token_info.get('refresh_expires_in'))\
                                       - timedelta(hours=12)
            if refresh_expiry_threshold < datetime.now():
                logger.debug('Refresh token expiry is too soon, re-authenticating')
                self._clear_token_info()

        if not self._token_info:
            self._token_info = _authenticate(client_id=client_id, auth_endpoint=auth_endpoint, auth_io=auth_io)

        self._save_token_info()
        self._update_token_metadata()
        self._get_token_lock = threading.Lock()

    def get_auth_method(self) -> AuthMethod:
        return RefreshableTokenAuth(token_getter=lambda: self._get_token()['access_token'])

    def get_current_user(self) -> str:
        return self._username

    def _get_token(self):
        with self._get_token_lock:
            # Refresh access token using refresh token
            if datetime.now() > self.access_token_expiry:
                self._refresh_access_token()

        return self._token_info

    def _refresh_access_token(self):
        try:
            cognito = boto3.client('cognito-idp', region_name=self.region)
            resp = cognito.initiate_auth(
                ClientId=self.client_id,
                AuthFlow='REFRESH_TOKEN_AUTH',
                AuthParameters={
                    'REFRESH_TOKEN': self._token_info['refresh_token']
                }
            )
            logger.debug('Successfully refreshed token')
        except ClientError as err:
            logger.warning(err)
            self._clear_token_info()
            raise RuntimeError('Failed to refresh token, please reauthenticate')

        auth_result = resp['AuthenticationResult']
        self._token_info['access_token'] = auth_result['AccessToken']
        self._token_info['id_token'] = auth_result['IdToken']
        self._save_token_info()
        self._update_token_metadata()

    def _update_token_metadata(self):
        decoded_access_token = jwt.decode(self._token_info['access_token'],
                                          options={"verify_signature": False})
        self.access_token_expiry = datetime.fromtimestamp(decoded_access_token['exp'])
        self._username = decoded_access_token['username']

    def _load_token_info(self) -> Optional[OAuthTokenResponse]:
        if not self._persistence or not self._token_path.exists():
            return None

        token_info = json.loads(self._persistence.load())
        if 'access_token' not in token_info:
            return None

        return token_info

    def _save_token_info(self):
        if not self._persistence:
            return

        self._persistence.save(json.dumps(self._token_info))

    def _clear_token_info(self):
        if not self._persistence:
            return

        Path(self._persistence.get_location()).unlink(missing_ok=True)
        self._token_info = None

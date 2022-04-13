from typing import List

from gql import gql


def get_id_from_name(items, name_or_id) -> str:
    matched = next((p for p in items if p['id'] == name_or_id), None)
    if matched:
        return matched['id']
    return next(p for p in items if p['name'] == name_or_id)['id']


def filter_deleted(items: List) -> List:
    return list(filter(lambda item: not item.get('_deleted', False), items))


GET_FILE_ACCESS_TOKEN_QUERY = gql('''
  query GetFileAccessToken($input: GetFileAccessTokenInput!) {
    getFileAccessToken(input: $input) {
      AccessKeyId
      Expiration
      SecretAccessKey
      SessionToken
    }
  }
''')

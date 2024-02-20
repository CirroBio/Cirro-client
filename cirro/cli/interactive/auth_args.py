from typing import Tuple, Dict

from cirro.cli.interactive.utils import ask_yes_no, ask


def gather_auth_config() -> Tuple[str, Dict, bool]:
    auth_method_config = {
        'enable_cache': ask_yes_no("Would you like to save your login? (do not use this on shared devices)")
    }

    enable_additional_checksum = ask(
        "select",
        "Upload / download validation type (note: SHA-256 requires additional local compute)",
        choices=["MD5", "SHA-256"]
    ) == "SHA-256"

    return 'ClientAuth', auth_method_config, enable_additional_checksum

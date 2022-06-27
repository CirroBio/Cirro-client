from pubweb.cli.interactive.auth_args import gather_login
from pubweb.cli.interactive.download_args import gather_download_arguments, gather_download_arguments_dataset
from pubweb.cli.interactive.upload_args import gather_upload_arguments
from pubweb.cli.interactive.list_dataset_args import gather_list_arguments

__all__ = [
    'gather_login',
    'gather_download_arguments',
    'gather_download_arguments_dataset',
    'gather_upload_arguments',
    'gather_list_arguments'
]

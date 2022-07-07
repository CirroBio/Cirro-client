import sys
from pathlib import Path
from typing import List

from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.validation import Validator, ValidationError

from pubweb.cli.interactive.common_args import ask_project, ask_use_third_party_tool, ask_process
from pubweb.cli.interactive.utils import ask
from pubweb.cli.models import UploadArguments
from pubweb.file_utils import get_directory_stats
from pubweb.models.process import Process
from pubweb.models.project import Project


class DataDirectoryValidator(Validator):
    def validate(self, document):
        is_a_directory = Path(document.text).is_dir()
        if not is_a_directory or len(document.text.strip()) == 0:
            raise ValidationError(
                message='Please enter a valid directory',
                cursor_position=len(document.text)
            )


def gather_upload_arguments(input_params: UploadArguments, projects: List[Project], processes: List[Process]):
    input_params['project'] = ask_project(projects, input_params.get('project'))

    input_params['data_directory'] = ask('path',
                                         'Enter the full path of the data directory',
                                         validate=DataDirectoryValidator,
                                         default=input_params.get('data_directory'),
                                         complete_style=CompleteStyle.READLINE_LIKE,
                                         only_directories=True
    )

    stats = get_directory_stats(input_params['data_directory'])
    confirm_msg = f'Please confirm that you wish to upload {stats["numberOfFiles"]} files ({stats["sizeFriendly"]})'
    if not ask('confirm', confirm_msg):
        sys.exit(1)

    input_params['process'] = ask_process(processes, input_params.get('process'))

    data_directory_name = Path(input_params['data_directory']).name
    default_name = input_params.get('name') or data_directory_name
    input_params['name'] = ask('text', 'What is the name of this dataset?',
                               required=True, default=default_name)
    input_params['description'] = ask('text', 'What is the name of this dataset?',
                                      default=input_params['description'])

    input_params['use_third_party_tool'] = ask_use_third_party_tool()
    return input_params

from pathlib import Path
from typing import Optional

from prompt_toolkit.shortcuts import CompleteStyle

from cirro.cli.interactive import utils


def ask_pipeline_root_directory(input_value: str) -> str:
    """
    Asks the user for the root directory of the pipeline definition.
    """
    root_dir_prompt = {
        'type': 'path',
        'name': 'pipeline_dir',
        'message': 'Enter the root directory for the pipeline definition',
        'validate': utils.DirectoryValidator,
        'default': input_value or '',
        'complete_style': CompleteStyle.READLINE_LIKE,
        'only_directories': True
    }

    answers = utils.prompt_wrapper(root_dir_prompt)
    return str(Path(answers['pipeline_dir']).expanduser())


def ask_pipeline_entrypoint() -> Optional[str]:
    """
    Asks the user for the entrypoint script of the pipeline.
    """
    entrypoint_prompt = {
        'type': 'input',
        'name': 'entrypoint',
        'message': 'Enter the entrypoint script (optional, WDL only)',
    }

    answers = utils.prompt_wrapper(entrypoint_prompt)
    return answers['entrypoint'].strip() if answers['entrypoint'] else None


def ask_output_directory(input_value: str) -> str:
    """
    Asks the user for the output directory to write pipeline configuration files.
    """
    output_dir_prompt = {
        'type': 'path',
        'name': 'output_dir',
        'message': 'Enter the output directory for the pipeline configuration files',
        'default': input_value or str(Path.cwd()),
        'complete_style': CompleteStyle.READLINE_LIKE,
        'only_directories': True
    }

    answers = utils.prompt_wrapper(output_dir_prompt)
    return str(Path(answers['output_dir']).expanduser())


def gather_create_pipeline_config_arguments(input_params):
    """
    Gathers input parameters for creating pipeline configuration files interactively.
    """
    input_params['pipeline_dir'] = ask_pipeline_root_directory(input_params.get('pipeline_dir'))
    input_params['entrypoint'] = ask_pipeline_entrypoint()
    input_params['output_dir'] = ask_output_directory(input_params.get('output_dir'))
    return input_params

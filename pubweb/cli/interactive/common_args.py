from typing import List

from pubweb.cli.interactive.utils import prompt_wrapper
from pubweb.api.models.project import Project


def ask_project(projects: List[Project], input_value: str) -> str:
    project_names = [project.name for project in projects]
    project_prompt = {
        'type': 'list',
        'name': 'project',
        'message': 'What project is this dataset associated with?',
        'choices': project_names,
        'default': input_value if input_value in project_names else None
    }
    answers = prompt_wrapper(project_prompt)
    return answers['project']


def ask_use_third_party_tool():
    answers = prompt_wrapper({
        'type': 'list',
        'message': 'How would you like to upload or download your data?',
        'name': 'use_tool',
        'choices': [
            "PubWeb CLI",
            "Third-party tool (using AWS credentials temporarily issued for download)"
        ]
    })

    return answers['use_tool'] != 'PubWeb CLI'

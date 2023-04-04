from typing import List

from cirro.api.models.project import Project
from cirro.cli.interactive.utils import prompt_wrapper


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

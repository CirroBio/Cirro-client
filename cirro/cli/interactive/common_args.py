from typing import List

from cirro_api_client.v1.models import Project

from cirro.cli.interactive.utils import ask


def ask_project(projects: List[Project], input_value: str) -> str:
    project_names = sorted([project.name for project in projects])
    if len(project_names) <= 10:
        return ask(
            'select',
            'What project is this dataset associated with?',
            choices=project_names,
            default=input_value if input_value in project_names else None
        )
    else:
        return ask(
            'autocomplete',
            'What project is this dataset associated with? (use TAB to display options)',
            choices=project_names,
            default=input_value if input_value in project_names else ''
        )

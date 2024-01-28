from typing import List

from cirro_api_client.v1.models import Project

from cirro.cli.interactive.common_args import ask_project
from cirro.cli.models import ListArguments


def gather_list_arguments(input_params: ListArguments, projects: List[Project]):

    # Get the project name
    project_name = ask_project(projects, input_params.get('project'))

    # Map the name back to a unique ID
    id_map = {
        project.name: project.id
        for project in projects
    }

    # Save the ID
    input_params['project'] = id_map[project_name]

    return input_params

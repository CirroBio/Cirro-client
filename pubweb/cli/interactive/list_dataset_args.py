from typing import List

from pubweb.cli.interactive.common_args import ask_project
from pubweb.cli.models import ListArguments
from pubweb.api.models.project import Project


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

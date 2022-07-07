from typing import Dict, List, Optional

from pubweb.cli.interactive.common_args import ask_project
from pubweb.cli.interactive.utils import ask
from pubweb.cli.models import ReferenceArguments
from pubweb.models.project import Project
from pubweb.models.reference import ReferenceType
from pubweb.utils import find_first


def ask_reference_type(reference_types: List[ReferenceType], input_value: Optional[str]) -> str:
    reference_choices = [
        ref.name
        for ref in reference_types
    ]
    default_value = None
    if input_value:
        if matched := find_first(reference_types,
                                 lambda x: x.directory == input_value or x.name == input_value):
            default_value = matched.name

    choice = ask('select',
                 'What type of reference?',
                 choices=reference_choices,
                 default=default_value)

    return find_first(reference_types,
                      lambda x: x.name == choice).id


def gather_reference_arguments(input_params: ReferenceArguments,
                               projects: List[Project],
                               reference_types: List[ReferenceType]) -> Dict:
    input_params['project'] = ask_project(projects, input_params.get('project'))
    input_params['reference_type'] = ask_reference_type(reference_types, input_params.get('reference_type'))
    input_params['name'] = ask('text',
                               'What is the name of this reference?',
                               default=input_params.get('name'))
    return input_params

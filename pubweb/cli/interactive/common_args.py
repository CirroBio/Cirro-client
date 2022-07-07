from typing import List

from pubweb.cli.interactive.utils import ask
from pubweb.models.process import Process
from pubweb.models.project import Project


def ask_process(processes: List[Process], input_value: str) -> str:
    process_names = [process.name for process in processes]
    answer = ask('select',
                 'What type of files?',
                 choices=process_names,
                 default=input_value if input_value in process_names else None)
    return answer


def ask_project(projects: List[Project], input_value: str) -> str:
    project_names = [project.name for project in projects]
    answer = ask('select',
                 'What project is this associated with?',
                 choices=project_names,
                 default=input_value if input_value in project_names else None)
    return answer


def ask_use_third_party_tool():
    answer = ask('select',
                 'How would you like to upload or download your data?',
                 choices=[
                     "PubWeb CLI",
                     "Third-party tool (using AWS credentials temporarily issued for download)"
                 ])

    return answer != 'PubWeb CLI'

from pubweb.cli.interactive.prompt_wrapper import prompt_wrapper


def ask_project(projects, input_value):
    project_names = [project["name"] for project in projects]
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

from PyInquirer import prompt


def ask_project(projects, input_value):
    project_prompt = {
        'type': 'list',
        'name': 'project',
        'message': 'What project is this dataset associated with?',
        'choices': [project["name"] for project in projects],
        'default': input_value or ''
    }
    answers = prompt(project_prompt)
    return answers['project']

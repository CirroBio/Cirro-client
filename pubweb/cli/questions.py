from questionary import prompt
from . import utils
from github import Github


def prompt_wrapper(questions):
    answers = prompt(questions)
    # Prompt catches KeyboardInterrupt and sends back an empty dictionary
    # We want to catch this exception
    if len(answers) == 0:
        raise KeyboardInterrupt()
    return answers


def get_output_directory():
    """Get the output directory, where to save the output
    process records"""

    answers = prompt_wrapper([
        {
            'type': 'input',
            'name': 'workingdir',
            'message': 'Directory to save the process records.',
            'default': '.'
        }
    ])
    return answers['workingdir']


def gather_repo_arguments():
    """Get the GitHub organization, repo, and version/tag
    Return the result as a dict"""

    # Get the organization
    org = prompt_organization_name()

    # Get the repository
    repo = prompt_repo_name(org)
    repo_version = prompt_repo_version(repo_name=f"{org}/{repo}")

    return {'org': org,
            'repo': repo,
            'repo_version': repo_version}


def gather_nf_process_arguments(nf_schema):
    """
    Given a nextflow schema, parse it and 
    run the user through prompts to determine which fields to expose
    """

    parsed_schema = utils.parse_nextflow_schema(nextflow_schema=nf_schema)
    workflow_params = prompt_param_fields_from_nf(parsed_schema=parsed_schema)
    process_desc = prompt_process_description()
    upstream_processes = prompt_upstream_process()

    return {
        "upstream": upstream_processes,
        "description": process_desc,
        "fields": workflow_params
    }


def gather_blank_process_arguments():
    """
    main -> Do you want to create a new parameter or group?
       * Parameter
       * Group
       * Nope I'm Done
    Done in a loop until someone is done
    """
    answers = []

    keep_asking = True
    while keep_asking:
        # then use that to ask the user which repo to look at
        condition_prompt = {
            'type': 'list',
            'name': 'conditional_step',
            'message': 'New parameter or parameter group?',
            'choices': ['Parameter', 'Group', "I'm Done"],
            'default': "Parameter"
        }
        condition = prompt_wrapper(condition_prompt)
        if condition['conditional_step'] == 'Group':
            print(f"'Group' chosen")
            answers.append(prompt_param_groups())
        elif condition['conditional_step'] == 'Parameter':
            print(f"Parameter chosen")
            answers.append(prompt_param_single())
        else:
            keep_asking = False
            print(f"I'm done")

    process_desc = prompt_process_description()
    upstream_processes = prompt_upstream_process()
    return {
        "upstream": upstream_processes,
        "description": process_desc,
        "fields": answers
    }


def prompt_organization_name():
    """Get the name of the organization to import (e.g. 'nf-core')"""

    # Prompt for the GitHub organization
    answers = prompt_wrapper([
        {
            'type': 'input',
            'name': 'org',
            'message': 'Which GitHub organization is the workflow located within?',
            'default': 'nf-core'
        }
    ])

    # If none was provided
    if len(answers["org"]) == 0:

        # Ask again
        print("The GitHub organization must be specified")
        return prompt_organization_name()

    else:
        return answers['org']


def prompt_repo_name(org):
    """Get the name of the workflow repository to import."""

    # get a list of repos
    g = Github()
    repo_list = [repo.name for repo in g.get_user(org).get_repos()]

    # then use that to ask the user which repo to look at
    repo_prompt = {
        'type': 'list',
        'name': 'repo',
        'message': 'Which repository contains the workflow of interest?',
        'choices': repo_list,
        'default': None
    }
    answers = prompt_wrapper(repo_prompt)
    return answers['repo']


def prompt_repo_version(repo_name):
    """Parse the local repository and ask the user which tag/version to use."""
    g = Github()

    # Get the repository object
    repo = g.get_repo(repo_name)

    # The version will be specified with either a branch or a release
    version_type = prompt_wrapper({
        'type': 'list',
        'name': 'version_type',
        'message': 'Should the workflow version be specified by branch or release tag?',
        'choices': ['branch', 'release'],
        'default': None
    })['version_type']

    # If the user decided to select the version type by branch
    if version_type == 'release':

        # Get the releases which are available
        version_list = [x for x in repo.get_releases()]
        pretty_version_list = [f"{x.tag_name} ({x.title})" for x in version_list]
        
        version_prompt = {
            'type': 'list',
            'name': 'version',
            'message': f"Which version of {repo_name} do you want to use?",
            'choices': pretty_version_list,
            'default': None
        }
        answers = prompt_wrapper(version_prompt)
        print(answers['version'])
        version = [x for x in version_list if f"{x.tag_name} ({x.title})" == answers['version']][0]
        return version.tag_name

    else:

        assert version_type == "branch"

        # Get the branches which are available
        selected_branch = prompt_wrapper({
            'type': 'list',
            'name': 'branch',
            'message': f"Which branch of {repo_name} do you want to use?",
            'choices': [branch.name for branch in repo.get_branches()],
            'default': None
        })['branch']

        return selected_branch


def prompt_param_fields_from_nf(parsed_schema):
    """Ask the user for any params which need to be provided"""
    to_return = []
    for question_group in parsed_schema['fields']:
        group_name = question_group['group_name']
        choices_map = {}
        for q in question_group['questions']:
            friendly_name = f"{q['name']}: {q['description']}"
            if q['required']:
                friendly_name = f"(REQUIRED) {friendly_name}"
            choices_map[friendly_name] = q['name']

        param_prompt = {
            'type': 'checkbox',
            'name': group_name,
            'message': f"Select '{group_name}' parameters to expose in PubWeb",
            'choices': [k for k, v in choices_map.items()],
            'default': None
        }
        group_choices = prompt_wrapper(param_prompt)

        # now filter out which parameters were chosen, and add them
        # back to the list to return

        group_choices_list = []
        for g in group_choices[group_name]:
            g_key = choices_map[g]
            for q in question_group['questions']:
                if q['name'] == g_key:
                    group_choices_list.append(q)
        if len(group_choices_list) > 0:
            to_return.append({
                    "group_name": group_name,
                    "short_group_name": utils.get_short_name(group_name),
                    "questions": group_choices_list
                })

    return to_return


def prompt_param_groups():
    """
    * Group -> name of the group (regex validator)
    * Create a new parameter?
      * Yes, create_parameter()
      * Nope I'm Done -> main()
    """
    answers = prompt_wrapper([
        {
            'type': 'input',
            'name': 'group_name',
            'message': "Group name?",
            'default': ''
        }
    ])
    group_name = answers['group_name']

    # now let's get the questions to ask
    keep_asking = True
    group_questions = []
    group_questions.append(prompt_param_single())
    while keep_asking:
        # then use that to ask the user which repo to look at
        condition_prompt = {
            'type': 'confirm',
            'name': 'more_group_q',
            'message': 'Do you want to add another parameter?',
            'default': True
        }
        more_qs = prompt_wrapper(condition_prompt)
        if more_qs['more_group_q']:
            print(f"More questions")
            group_questions.append(prompt_param_single())
        else:
            keep_asking = False
            print(f"No more questions")

    # Finally, return the whole object to the calling stack
    return {'group_name': group_name,
            'questions': group_questions}


def prompt_param_single():
    """
    Ask for the parameter's name, data type, description, and help text.
    Return everything as a dict
    """ 
    name_resp = prompt_wrapper([
        {
            'type': 'input',
            'name': 'name',
            'message': "What's the new parameter's name?",
            'default': ''
        }
    ])
    
    type_resp = prompt_wrapper({
            'type': 'list',
            'name': 'data_type',
            'message': 'What data type is this parameter?',
            'choices': ["String", 
                        "Boolean", 
                        "Integer", 
                        "Decimal/Float", 
                        "List",
                        "File / Sample Sheet",
                        "Reference Genome"],
            'default': "String"
        })

    # default value
    default_prompt = {
            'name': 'name',
            'message': "What's the new parameter's default?",
    }
    if type_resp['data_type'] in ('String', 'File / Sample Sheet'):
        default_prompt['type'] = 'input'
    elif type_resp['data_type'] == 'List':
        default_prompt['type'] = 'input'
        default_prompt['message'] = "What's the new parameter's default? List elements must be defined by a comma"
        default_prompt['validate'] = lambda x: utils.is_list(x) or f"{x} must be a valid list"
    elif type_resp['data_type'] == 'Boolean':
        default_prompt['type'] = 'confirm'
    elif type_resp['data_type'] == 'Integer':
        default_prompt['type'] = 'input'
        default_prompt['validate'] = lambda x: utils.is_int(x) or f"{x} must be a valid integer"
    elif type_resp['data_type'] == 'Decimal/Float':
        default_prompt['type'] = 'input'
        default_prompt['validate'] = lambda x: utils.is_float(x) or f"{x} must be a valid decimal/float"
    elif type_resp['data_type'] == 'Reference Genome':
        default_prompt['type'] = 'list'
        default_prompt['choices'] = utils.get_reference_genomes()

    default_resp = prompt_wrapper(default_prompt)
    default_value = default_resp['name']
    if type_resp['data_type'] == 'List':
        default_value = list(default_value.split(','))

    # required?
    required_resp = prompt_wrapper({
            'type': 'confirm',
            'name': 'required',
            'message': 'Is this a required parameter?',
            'default': False
        })

    # description and help text
    desc_resp = prompt_wrapper([
        {
            'type': 'input',
            'name': 'description',
            'message': "What's the new parameter's description?",
            'default': ''
        }
    ])

    help_resp = prompt_wrapper([
        {
            'type': 'input',
            'name': 'help',
            'message': "What's the help text for the new parameter?",
            'default': ''
        }
    ])

    return {'name': name_resp['name'],
            'description': desc_resp['description'],
            'help': help_resp['help'],
            'required': required_resp['required'],
            'data_type': type_resp['data_type'],
            'default': default_value
            }


def prompt_process_description():
    """Prompt the user to edit the title and description of the process."""
    title_resp = prompt_wrapper([
        {
            'type': 'input',
            'name': 'title',
            'message': "What's the name/title for this new process?",
            'default': ''
        }
    ])

    desc_resp = prompt_wrapper([
        {
            'type': 'input',
            'name': 'description',
            'message': "What's the description for this new process?",
            'default': ''
        }
    ])

    version_resp = prompt_wrapper([
        {
            'type': 'input',
            'name': 'version',
            'message': "What's the version number for this process?",
            'default': '1.0'
        }
    ])

    return {'name': title_resp['title'],
            'description': desc_resp['description'],
            'version': version_resp['version']
            }


def prompt_upstream_process():
    """Prompt the user to select any process(es) which this is downstream of.
    Use a 'checkbox' question format b/c there can be multiple upstream processes
    """

    process_list = utils.get_upstream_processes()
    
    upstream_prompt = prompt_wrapper({
        'type': 'checkbox',
        'name': 'version',
        'message': f"Does this process have an upstream/parent processes?",
        'choices': process_list,
        'default': None
    })

    return upstream_prompt['version']

import json
import os
import shutil
from . import utils

data_type_map = {
    "String": "string",
    "Boolean": "boolean",
    "Integer": "integer",
    "Decimal/Float": "number",
    "List": "string",
    "File / Sample Sheet": "string",
    "Reference Genome": "string"
}


def convert_question(question):
    to_return = {
        "type": data_type_map.get(question['data_type'], question['data_type']),
        "title": question['name'],
        "description": question['description'],
        "help_text": question.get('help')
    }
    if question['data_type'] == 'Reference Genome':
        to_return['enum'] = utils.get_reference_genomes()
        to_return.pop('default')
    elif question['data_type'] == 'File / Sample Sheet':
        to_return.pop('default')
        to_return['file'] = "*.*"
        to_return['pathType'] = 'dataset'
    elif question['data_type'] == 'List':
        to_return['enum'] = question.get('default')
        to_return.pop('default')
    else:
        to_return['default'] = question.get('default')

    return to_return


def convert_group_questions(group_questions):

    # Set up the basic field structure
    field_structure = {
        "title": group_questions['group_name'],
        "type": "object",
        "properties": {}
    }

    # Populate the questions recursively
    for group_q in group_questions['questions']:
        structure_to_add = {}
        if group_q.get('group_name') is not None:
            structure_name = group_q.get('short_group_name')
            structure_to_add = convert_group_questions(group_q)
        else:
            structure_name = group_q['name']
            structure_to_add = convert_question(group_q)
        field_structure['properties'][structure_name] = structure_to_add

    return field_structure


def generate_form_parameters(input_params):
    to_return = {}

    for field in input_params['process']['fields']:
        field_structure = {}
        if field.get('group_name') is not None:
            # not a group
            field_structure = convert_group_questions(field)
            #field_structure = snippets.get('group')
            #field_name = field['group_name']
            #field_structure['title'] = field_name
            #field_structure['properties'] = convert_group_questions(field, snippets)
            if field_structure.get('properties') is not None:
                to_return[field['short_group_name']] = field_structure
        else:
            field_structure = convert_question(field)
            field_name = field['name']
            to_return[field_name] = field_structure
    return to_return


def write_compute_config(input_params, output_dir):
    """Write the process-compute.config template which can be further modified by the user."""

    with open(os.path.join(output_dir, 'process-compute.config'), 'w') as handle:
        handle.write("""profiles {
    standard {
        process {
            executor = 'awsbatch'
            errorStrategy = 'retry'
            maxRetries = 2
        }
    }
}
""")


def write_dynamo(input_params, output_dir):
    """Write the process-dynamo.json"""

    print(input_params)

    # # Populate the information expected by dynamo for this process
    # dynamo = dict(
    #     id=,
    #     name=input_params['process']['description']['name'].replace(' ', '_')
    # )

    target_loc = os.path.join(output_dir, 'process-dynamo.json')

    raw_record = raw_record.replace('{REPO}', input_params['repo']['repo'])
    raw_record = raw_record.replace('{WORKFLOW}', utils.get_short_name(workflow_name))
    raw_record = raw_record.replace('{VERSION}', input_params['process']['description']['version'])
    record = json.loads(raw_record)

    record['code']['repository'] = input_params['repo']['repo']
    record['code']['script'] = input_params['repo']['repo_version']['title']
    record['code']['uri'] = input_params['repo']['repo_version']['url']
    record['code']['version'] = input_params['repo']['repo_version']['tag']
    record['name'] = input_params['process']['description']['name']
    record['desc'] = input_params['process']['description']['description']

    with open(target_loc, 'w') as f:
        f.write(json.dumps(record))


def write_form(input_params, output_dir):
    """Write the process-form.json."""

    target_loc = os.path.join(output_dir, 'process-form.json')

    # Set up the template record
    record = {
        "ui": {},
        "form": {
            "title": "",
            "type": "object",
            "required": [],
            "properties": {}
        }
    }

    # Find the list of required fields
    required_fields = []
    required_fields.extend([x['name'] for x in input_params['process']['fields'] if x.get('required', False)])

    for group_field in input_params['process']['fields']:
        if group_field.get('group_name') is not None:
            required_fields.extend([x for x in group_field['questions'] if x.get('required', False)])
    
    record['form']['title'] = input_params['process']['description']['name']
    record['form']['required'] = required_fields

    record['form']['properties'] = generate_form_parameters(input_params)

    with open(target_loc, 'w') as f:
        f.write(json.dumps(record))


def write_input(input_params, output_dir):
    """Write the process-input.json."""
    template_loc = os.path.join(working_dir, 'process-input.json')
    target_loc = os.path.join(output_dir, 'process-input.json')

    with open(template_loc, 'r') as f:
        record = json.loads(f.read())

    for field in input_params['process']['fields']:
        if field.get('group_name') is None:
            # it's a single question, work on it
            field_name = field['name']
            record[field_name] = record['PLACEHOLDER'].replace('PLACEHOLDER', utils.get_short_name(field_name))
        else:
            short_group_name = field['short_group_name']
            for group_field in field['questions']:
                full_name = f"{short_group_name}.{group_field['name']}"
                if group_field['data_type'] == 'Reference Genome':
                    record[group_field['name']] = record['GENOME_PLACEHOLDER'].replace('GENOME_PLACEHOLDER', full_name)
                else:
                    record[group_field['name']] = record['PLACEHOLDER'].replace('PLACEHOLDER', full_name)

    record.pop('PLACEHOLDER')
    record.pop('GENOME_PLACEHOLDER')
    with open(target_loc, 'w') as f:
        f.write(json.dumps(record))


def write_output(input_params, output_dir):
    """Write the process-output.json."""
    template_loc = os.path.join(working_dir, 'process-output.json')
    target_loc = os.path.join(output_dir, 'process-output.json')
    shutil.copy(template_loc, target_loc)


def write_process_config(input_params, output_dir):
    """Write out all of the process configuration assets."""
    write_compute_config(input_params, output_dir)
    write_dynamo(input_params, output_dir)
    write_form(input_params, output_dir)
    write_input(input_params, output_dir)
    write_output(input_params, output_dir)

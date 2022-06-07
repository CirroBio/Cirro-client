import os
import json
import requests
import tarfile


def get_upstream_processes():
    """Return a list of potential 'upstream' processes
    TO DO: Connect to a PubWeb API and get the list
    This stub returns a dummy list right now"""
    upstream_list = []

    # this is a placeholder, to be replaced by a future implementation
    upstream_list = ['foo', 'bar', 'PubWeb Ingestion']
    return upstream_list


def get_reference_genomes(mode='List'):
    """Return a list of supported reference genomes
    TO DO: Connect to a PubWeb API and get the list
    This stub returns a dummy list right now

    FYI, used by multiple methods
    """
    reference_genomes = []

    # this is a placeholder, to be replaced by a future implementation
    reference_genomes = ['HG38', 'yeast']
    return reference_genomes


def parse_release_info(release_url):
    r = requests.get(release_url)
    release_info = json.loads(r.content)
    print(f"Tarball is {release_info['tarball_url']}")
    return release_info['tarball_url']


def get_repo(repo_url):
    """Clone a local copy of the repository which will be imported/parsed."""
    file_name = os.path.basename(repo_url)
    print(f"Downloading {file_name}")
    
    r = requests.get(repo_url)
    with open(file_name, 'w+b') as f:
        f.write(r.content)
    return file_name


def get_nextflow_schema(repo_tarball):
    """If a nextflow_schema.json is present, parse it and prompt the user for any modifications."""
    with tarfile.open(repo_tarball, 'r') as archive:
        archive_list = archive.getmembers()
        nextflow_schema_list = [x for x in archive_list if x.name.find('nextflow_schema.json') >= 0]
        if len(nextflow_schema_list) > 0:
            nextflow_schema_file = nextflow_schema_list[0].name
            archive.extract(nextflow_schema_file, path='tmp')
            local_nf_schema_file = f"tmp/{nextflow_schema_file}"
            with open(local_nf_schema_file, 'r') as f:
                nf_schema = json.loads(f.read())
                return nf_schema
        else:
            print(f"No nextflow_schema.json file found, switching to DIY mode")
            return None


def parse_nf_schema_option_group(parse_group):
    """Parse a question/option group from nf_schema format to a simpler format"""
    required_inputs = parse_group.get('required', [])
    question_list = []
    
    for key, item in parse_group['properties'].items():
        to_add = {
            "name": key,
            "description": item['description'],
            "help": item.get('help_text'),
            "required": True if key in required_inputs else False,
            "data_type": item['type'],
            "default": item.get('default')
        }
        question_list.append(to_add)
    return {
        "group_name": parse_group['title'],
        "questions": question_list
    }


def parse_nextflow_schema(nextflow_schema):
    """Parse a nextflow schema and prompt the user for any modifications."""
    schema_description = nextflow_schema['description']

    fields = []
    for key, option_group in nextflow_schema['definitions'].items():
        parsed_group = parse_nf_schema_option_group(option_group)
        fields.append(parsed_group)

    return {
        "description": schema_description,
        "fields": fields
    }


def get_short_name(name):
    to_return = name.replace(' ', '_').replace('/', '_').lower()
    return to_return


def is_list(element) -> bool:
    try:
        list(element.split(','))
        return True
    except ValueError:
        return False


def is_int(element) -> bool:
    try:
        int(element)
        return True
    except ValueError:
        return False


def is_float(element) -> bool:
    try:
        float(element)
        return True
    except ValueError:
        return False

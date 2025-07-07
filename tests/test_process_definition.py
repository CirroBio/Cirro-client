from os import path
import json

import pytest
from referencing import Resource

from cirro.models import process

data_path = path.join(path.dirname(__file__), 'data')

def test_pipeline_definition_nextflow_simple():
    root_dir = path.join(data_path, 'workflows', 'nextflow', 'simple')
    pipeline = process.PipelineDefinition(root_dir)

    with open(path.join(root_dir, 'expected-form.json'), 'r') as f:
        expected_form_configuration = json.load(f)
        expected_parameter_schema = Resource.from_contents(expected_form_configuration['form'])
    
    with open(path.join(root_dir, 'expected-input.json'), 'r') as f:
        expected_input_configuration = json.load(f)
    
    assert pipeline.parameter_schema == expected_parameter_schema
    assert pipeline.form_configuration == expected_form_configuration
    assert pipeline.input_configuration == expected_input_configuration

def test_pipeline_definition_wdl_simple():
    root_dir = path.join(data_path, 'workflows', 'wdl', 'simple')
    pipeline = process.PipelineDefinition(root_dir)

    with open(path.join(root_dir, 'expected-form.json'), 'r') as f:
        expected_form_configuration = json.load(f)
        expected_parameter_schema = Resource.from_contents(expected_form_configuration['form'])
    
    with open(path.join(root_dir, 'expected-input.json'), 'r') as f:
        expected_input_configuration = json.load(f)
    
    assert pipeline.parameter_schema == expected_parameter_schema
    assert pipeline.form_configuration == expected_form_configuration
    assert pipeline.input_configuration == expected_input_configuration

def test_pipeline_definition_wdl_alt_entrypoint():
    root_dir = path.join(data_path, 'workflows', 'wdl', 'alt-entrypoint')
    pipeline = process.PipelineDefinition(root_dir, entrypoint='main-alt.wdl')

    with open(path.join(root_dir, 'expected-form.json'), 'r') as f:
        expected_form_configuration = json.load(f)
        expected_parameter_schema = Resource.from_contents(expected_form_configuration['form'])
    
    with open(path.join(root_dir, 'expected-input.json'), 'r') as f:
        expected_input_configuration = json.load(f)
    
    assert pipeline.parameter_schema == expected_parameter_schema
    assert pipeline.form_configuration == expected_form_configuration
    assert pipeline.input_configuration == expected_input_configuration

def test_get_input_params_simple():
    schema_path = path.join(data_path, 'jsonschemas', 'simple.json')
    with open(schema_path, 'r') as f:
        contents = json.load(f)
    
    schema = Resource.from_contents(contents)
    
    # Test with a simple property
    params = list(process.get_input_params('$', contents, schema))
    
    assert len(params) == 3
    assert params[0]['name'] == 'param_1'
    assert params[0]['type'] == 'string'
    assert params[0]['default'] is None
    assert params[0]['jsonPath'] == '$.param_1'

def test_get_input_params_nested():
    schema_path = path.join(data_path, 'jsonschemas', 'nested.json')
    with open(schema_path, 'r') as f:
        contents = json.load(f)
    
    schema = Resource.from_contents(contents)
    
    # Test with a nested property
    params = list(process.get_input_params('$', contents, schema))
    
    assert len(params) == 3
    assert params[0]['name'] == 'param_1'
    assert params[0]['type'] == 'string'
    assert params[0]['default'] is None
    assert params[0]['jsonPath'] == '$.section_1.param_1'

    assert params[1]['name'] == 'param_2'
    assert params[1]['type'] == 'integer'
    assert params[1]['default'] == 42
    assert params[1]['jsonPath'] == '$.param_2'


def test_get_input_params_references():
    schema_path = path.join(data_path, 'jsonschemas', 'references.json')
    with open(schema_path, 'r') as f:
        contents = json.load(f)
    
    schema = Resource.from_contents(contents)
    
    # Test with a property that has a reference
    params = list(process.get_input_params('$', contents, schema))
    
    assert len(params) == 3
    assert params[0]['name'] == 'param_1'
    assert params[0]['type'] == 'string'
    assert params[0]['default'] is None
    assert params[0]['jsonPath'] == '$.section_1.param_1'

    assert params[1]['name'] == 'param_2'
    assert params[1]['type'] == 'integer'
    assert params[1]['default'] == 42
    assert params[1]['jsonPath'] == '$.param_2'


def test_get_input_params_wdl_types():
    schema_path = path.join(data_path, 'jsonschemas', 'wdlType.json')
    with open(schema_path, 'r') as f:
        contents = json.load(f)
    
    schema = Resource.from_contents(contents)
    
    # Test with WDL types
    params = list(process.get_input_params('$', contents, schema))
    
    assert len(params) == 4
    assert params[0]['name'] == 'file_param'
    assert params[0]['type'] == 'string'
    assert params[0]['default'] is None
    assert params[0]['jsonPath'] == '$.inputs[*].dataPath'

    assert params[1]['name'] == 'directory_param'
    assert params[1]['type'] == 'string'
    assert params[1]['default'] is None
    assert params[1]['jsonPath'] == '$.inputs[*].dataPath'

    assert params[2]['name'] == 'file_param_optional'
    assert params[2]['type'] == 'string'
    assert params[2]['default'] is None
    assert params[2]['jsonPath'] == '$.inputs[*].dataPath'

    assert params[3]['name'] == 'directory_param_optional'
    assert params[3]['type'] == 'string'
    assert params[3]['default'] is None
    assert params[3]['jsonPath'] == '$.inputs[*].dataPath'
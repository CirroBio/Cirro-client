import os
from os import path
from functools import cached_property
import json
from typing import Any, Iterable, Optional
import logging

from referencing import Resource, Registry
import WDL


class PipelineDefinition:
    """
    Represents a pipeline definition with a name and a list of steps.
    """

    def __init__(self, root_dir: str, entrypoint: Optional[str] = None, logger: Optional[logging.Logger] = None):
        self.root_dir = path.expanduser(path.expandvars(root_dir))
        self.entrypoint = entrypoint

        if logger:
            self.logger = logger
        else:
            log_formatter = logging.Formatter(
                '%(asctime)s %(levelname)-8s [PipelineDefinition] %(message)s'
            )
            self.logger = logging.getLogger()
            self.logger.setLevel(logging.INFO)
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_formatter)
            self.logger.addHandler(console_handler)
    
    @cached_property
    def parameter_schema(self) -> Resource:
        """
        Returns the parameter schema for the pipeline.
        """
        workflow_files = os.walk(self.root_dir, topdown=True)
        for dirpath, dirnames, filenames in workflow_files:
            # look for a nextflow_schema.json file at the root of the workflow directory
            if 'nextflow_schema.json' in filenames:
                schema_path = path.join(dirpath, 'nextflow_schema.json')
                self.logger.info(f"Nextflow schema found at {schema_path}")
                with open(schema_path, 'r') as f:
                    contents = json.load(f)
                
                break
            elif any(f.endswith('.wdl') for f in filenames):
                # generate schema from WDL workflow
                wdl_file = None
                if self.entrypoint:
                    self.logger.info(f"Using entrypoint WDL file: {self.entrypoint}")
                    # if an entrypoint is specified, look for that specific WDL file
                    wdl_file = next((f for f in filenames if f.endswith(self.entrypoint)), None)
                    if not wdl_file:
                        raise FileNotFoundError(f"Entrypoint WDL file '{self.entrypoint}' not found in {dirpath}")
                else:
                    # otherwise, just take the first WDL file found
                    wdl_file = next(f for f in filenames if f.endswith('.wdl'))
                
                wdl_file = path.join(dirpath, wdl_file)
                doc = WDL.load(wdl_file)
                contents = get_wdl_json_schema(doc)
                break
            
        else:
            raise RuntimeError("Unrecognized workflow format. Please provide a valid Nextflow or WDL workflow.")
        
        _all_of = {}
        if contents.get('allOf'):
            # this is typically a root attribute in nextflow_schema.json files and a list of $ref
            # convert this to an object
            _all_of = {item["$ref"].split('/')[-1]: item for item in contents['allOf']}
            del contents['allOf']
        
        contents['properties'] = contents.get('properties', {}) | _all_of
        schema = Resource.from_contents(contents)

        return schema

    @property
    def form_configuration(self) -> dict[str, Any]:
        """
        Returns the form configuration for the pipeline.
        """
        return {
            "form": self.parameter_schema.contents,
            "ui": {}
        }
    
    @property
    def input_configuration(self) -> dict[str, str]:
        """
        Returns the input configuration for the pipeline.
        """
        schema = self.parameter_schema
        contents = schema.contents
        
        parameters = {
            p["name"]: p["jsonPath"] 
            for p in get_input_params('$.dataset.params', contents, schema)
        }
        return parameters

    def __repr__(self):
        return f"PipelineDefinition(name={self.root_dir})"


def get_input_params(property_path: str, definition: dict[str, Any], schema: Resource) -> Iterable[dict[str, Any]]:
    resolved = definition
    if '$ref' in definition:
        registry = schema @ Registry()
        resolver = registry.resolver()
    
        resolved = resolver.lookup(f"{schema.id()}{definition['$ref']}").contents
    
    if resolved.get('type') == 'object':
        # recursively get input params for nested objects
        for p, d in resolved.get('properties', {}).items():
            nested_path = f"{property_path}.{p}"
            yield from get_input_params(nested_path, d, schema)
    else:
        jsonPath = property_path
        if resolved.get('wdlType') and resolved['wdlType'].replace('?', '') in ('File', 'Directory'):
            # override the jsonPath to be '$.inputs[*].dataPath'
            jsonPath = "$.inputs[*].dataPath"

        yield {
            'name': property_path.split('.')[-1],
            'type': resolved.get('type', 'string'),
            'default': resolved.get('default', None),
            'jsonPath': jsonPath,
        }


def get_wdl_json_schema(doc: WDL.Document) -> dict[str, Any]:  # type: ignore
    """
    Generate a JSON schema from a WDL Document.
    """
    # strictly look for top level workflow inputs
    if not doc.workflow:
        raise ValueError("WDL Document does not contain a workflow.")

    if not doc.workflow.inputs:
        raise ValueError("WDL Document workflow does not contain inputs.")

    # only get declarations from top-level workflow inputs
    params = {
        child.name: {
            'obj': child, 
            'type': str(child.type), 
            'default': child.expr.literal.value if child.expr and child.expr.literal else None, 
            'optional': child.type.optional}
        for child in (doc.workflow.inputs or []) if isinstance(child, WDL.Decl)  # type: ignore
    }

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:cirro:wdl:schema",
        "type": "object",
        "properties": {},
        "required": []
    }

    type_map = {
        'String': 'string',
        'Int': 'integer',
        'Float': 'number',
        'Boolean': 'boolean',
        'File': 'string',  # File is typically a string path
        'Directory': 'string',  # Directory is typically a string path
        'Array[String]': 'array',
        'Array[Int]': 'array',
        'Array[Float]': 'array',
        'Array[Boolean]': 'array',
        'Array[File]': 'array',
        'Array[Directory]': 'array',
        
        # complex types
        'Pair': 'string',  # WDL Pair type, encode as JSON string
        'Map': 'string',  # WDL Map type, encode as JSON string
        'Struct': 'string',  # WDL Struct type, encode as JSON string

        # unsuported types
        # 'Object': 'object',  # WDL Object type (deprecated), not directly supported in JSON Schema
    }

    # convert params into JSON schema properties
    for name, param in params.items():
        if param['type'].replace('?', '') not in type_map:
            raise ValueError(f"Unsupported WDL type: {param['type']} for parameter {name}")
        
        schema['properties'][name] = {
            "type": type_map[param['type'].replace('?', '')],  # remove optional marker
            "wdlType": param['type'],
            "default": param['default'],
            "description": f"Parameter {name} of type {param['type']}"
        }
        # paramters that are required have default=None and optional=False
        if param['default'] is None and not param['optional']:
            schema['required'].append(name)

    return schema
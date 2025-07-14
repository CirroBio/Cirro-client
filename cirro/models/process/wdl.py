from typing import Any, Optional
import logging

import WDL


def get_wdl_json_schema(wdl_file: str, logger: Optional[logging.Logger] = None) -> dict[str, Any]:  # type: ignore
    """
    Generate a JSON schema for parameters from a WDL workflow.

    :param wdl_file: Path to the main WDL file.
    """
    # Load the WDL document
    doc = WDL.load(wdl_file)

    # strictly look for top level workflow inputs
    if not doc.workflow:
        msg = "WDL Document does not contain a workflow."
        if logger:
            logger.error(msg)
        raise ValueError(msg)

    if not doc.workflow.inputs:
        msg = "WDL Document workflow does not contain inputs."
        if logger:
            logger.error(msg)
        raise ValueError(msg)

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
            msg = f"Unsupported WDL type: {param['type']} for parameter {name}"
            if logger:
                logger.error(msg)
            raise ValueError(msg)

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

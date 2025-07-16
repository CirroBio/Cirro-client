import os
from os import path
import json
from typing import Any, Optional
import logging

from nf_core.pipelines.schema import PipelineSchema


def get_nextflow_json_schema(workflow_dir: str, logger: Optional[logging.Logger] = None) -> dict[str, Any]:
    """
    Get or generate a JSON schema for parameters from a Nextflow workflow.

    :param workflow_dir: Workflow definition directory.
    """

    workflow_files = os.walk(workflow_dir, topdown=True, followlinks=True)
    for dirpath, dirnames, filenames in workflow_files:
        if 'nextflow_schema.json' in filenames:
            # check if a nextflow_schema.json file exists at the root of the workflow directory
            schema_path = path.join(dirpath, 'nextflow_schema.json')
            if logger:
                logger.info(f"Nextflow schema found at {schema_path}")
            with open(schema_path, 'r') as f:
                contents = json.load(f)
            break
        else:
            # generate the parameter schema non-interactively
            ps = PipelineSchema()

            # since this is already filtered to a case where a nextflow_schema.json file is not found,
            # only use a subset of functionality from the build_schema method and use our logger if provided.
            try:
                ps.get_schema_path(workflow_dir, local_only=True)
            except AssertionError:
                # if the schema path is not found, we will generate it
                if logger:
                    logger.info("Nextflow schema path not found, generating schema from workflow files.")

            ps.get_wf_params()
            ps.make_skeleton_schema()
            ps.remove_schema_notfound_configs()
            ps.remove_schema_empty_definitions()
            ps.add_schema_found_configs()

            try:
                ps.validate_schema()
            except AssertionError as e:
                if logger:
                    logger.error(f"Nextflow schema creation failed: {e}")
                raise e

            contents = ps.schema
            break
    else:
        msg = "Nextflow schema not found or could not be generated."
        if logger:
            logger.error(msg)
        raise FileNotFoundError(msg)

    # ignore the 'allOf' attribute if it exists
    # merge 'definitions' or '$defs' attribute with 'properties'
    if contents.get('allOf'):
        del contents['allOf']

    contents['properties'] = (
        contents.get('properties', {})
        | contents.get('$defs', {})
        | contents.get('definitions', {})
    )

    return contents

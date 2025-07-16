import os
from os import path
from functools import cached_property
from typing import Any, Iterable, Optional
import logging
from enum import Enum

from referencing import Resource, Registry


CONFIG_APP_URL = "https://app.cirro.bio/tools/pipeline-configurator/"


class ConfigAppStatus(Enum):
    """
    Enum to represent the status of the config app recommendation.
    """
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"


class PipelineDefinition:
    """
    A pipeline definition on disk.
    """

    def __init__(self, root_dir: str, entrypoint: Optional[str] = None, logger: Optional[logging.Logger] = None):
        self.root_dir: str = path.expanduser(path.expandvars(root_dir))
        self.entrypoint: Optional[str] = entrypoint
        self.config_app_status: ConfigAppStatus = ConfigAppStatus.RECOMMENDED

        if logger:
            self.logger: logging.Logger = logger
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
            is_nextflow = (
                ('nextflow_schema.json' in filenames)
                or ('nextflow.config' in filenames)
            )
            if is_nextflow:
                # lazy load nextflow dependencies
                from cirro.models.process.nextflow import get_nextflow_json_schema
                contents = get_nextflow_json_schema(self.root_dir, self.logger)

                if 'nextflow_schema.json' in filenames:
                    self.config_app_status = ConfigAppStatus.OPTIONAL

                break
            elif any(f.endswith('.wdl') for f in filenames):  # is WDL
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

                # lazy load wdl dependencies
                from cirro.models.process.wdl import get_wdl_json_schema

                wdl_file = path.join(dirpath, wdl_file)
                contents = get_wdl_json_schema(wdl_file, self.logger)
                break

        else:
            raise RuntimeError("Unrecognized workflow format. Please provide a valid Nextflow or WDL workflow.")

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
        json_path = property_path
        param_is_path = (
            (resolved.get('wdlType') and resolved['wdlType'].replace('?', '') in ('File', 'Directory'))
            or (resolved.get('format') and resolved['format'] in ('file-path', 'directory-path'))
        )
        if param_is_path:
            # override the jsonPath to be '$.inputs[*].dataPath'
            json_path = "$.inputs[*].dataPath"

        yield {
            'name': property_path.split('.')[-1],
            'type': resolved.get('type', 'string'),
            'default': resolved.get('default', None),
            'jsonPath': json_path,
        }

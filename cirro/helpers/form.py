from cirro.sdk.exceptions import DataPortalAssetNotFound
import json
from pathlib import Path


class FormSchema:
    """Form schema object"""
    FORM_FP = ".cirro/form.json"

    def __init__(self):

        if Path(self.FORM_FP).exists():
            self._schema = self._load_schema()
        else:
            self._schema = self._empty_schema()

    def add_param(self, param_id, **param_schema):
        """Add a param to the schema."""

        # If the parameter already exists
        saved_param = self._schema['form']['properties'].get(param_id)
        if saved_param is not None:

            # If any of the values are different
            for kw, new_val in param_schema.items():
                old_val = saved_param.get(kw)
                # Warn the user
                if old_val != new_val:
                    msg = f"Warning - changing {kw} of '{saved_param}' from {old_val} to {new_val}"
                    print(msg)

        # Set up the parameter definition
        self._schema['form']['properties'][param_id] = param_schema

    def save(self):
        """Save the schema as JSON."""
        # If the parent directory doesn't exist
        if not Path(self.FORM_FP).parent.exists():
            # Create the parent directory
            Path(self.FORM_FP).parent.mkdir(parents=True, exist_ok=True)

        with open(self.FORM_FP, 'w') as handle:
            json.dump(self._schema, handle, indent=4)

    def _load_schema(self) -> dict:
        with open(self.FORM_FP, 'r') as handle:
            schema: dict = json.load(handle)

        if not isinstance(schema, dict):
            msg = f"Invalid schema: {self.FORM_FP} - requires dict"
            raise DataPortalAssetNotFound(msg)

        for kw in ['form', 'ui']:
            if schema.get(kw) is None:
                msg = f"Invalid schema: {self.FORM_FP} - missing {kw}"
                raise DataPortalAssetNotFound(msg)

            if not isinstance(schema[kw], dict):
                msg = f"Invalid schema: {self.FORM_FP} - {kw} should be dict"
                raise DataPortalAssetNotFound(msg)

        return schema

    def _empty_schema(self) -> dict:
        return dict(
            form=dict(
                type='object',
                properties=dict()
            ),
            ui=dict()
        )

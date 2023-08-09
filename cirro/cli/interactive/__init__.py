import os
from pathlib import Path
configure_workflow_app = (
    Path(os.path.dirname(__file__)) / "configure_workflow_app.py"
).resolve()

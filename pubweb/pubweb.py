from pubweb.auth import AuthInfo
from pubweb.clients import ApiClient
from pubweb.services import DatasetService, ProcessService, ProjectService
from pubweb.helpers import WorkflowConfig

class PubWeb:
    def __init__(self, auth_info: AuthInfo):
        self._api_client = ApiClient(auth_info)
        self._dataset_service = DatasetService(self._api_client)
        self._project_service = ProjectService(self._api_client)
        self._process_service = ProcessService(self._api_client)

    @property
    def dataset(self):
        return self._dataset_service

    @property
    def project(self):
        return self._project_service

    @property
    def process(self):
        return self._process_service

    def configure_workflow(self):
        """Configure a workflow to be run via PubWeb"""
        
        # Instantiate a workflow configuration object
        workflow = WorkflowConfig(self)

        # The configuration process will rely on a series of
        # interactive prompts to the user
        workflow.configure()

        # After being configured, the workflow will be serialized to
        # a handful of local file objects
        workflow.save_local()

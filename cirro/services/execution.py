from cirro_api_client.v1.api.execution import run_analysis, stop_analysis, get_project_summary, \
    get_tasks_for_execution, get_task_logs, get_execution_logs
from cirro_api_client.v1.api.processes import get_process_parameters
from cirro_api_client.v1.models import RunAnalysisRequest

from cirro.models.form_specification import ParameterSpecification
from cirro.services.base import BaseService


class ExecutionService(BaseService):
    def run_analysis(self, project_id: str, request: RunAnalysisRequest):
        """
        Run analysis
        """
        form_spec = get_process_parameters.sync(process_id=request.process_id, client=self._api_client)
        ParameterSpecification(form_spec).validate_params(request.params.to_dict() if request.params else {})

        return run_analysis.sync(project_id=project_id, body=request, client=self._api_client)

    def stop_analysis(self, project_id: str, dataset_id: str):
        """
        Terminates all analysis jobs related to this execution
        """
        return stop_analysis.sync(project_id=project_id, dataset_id=dataset_id, client=self._api_client)

    def get_project_summary(self, project_id: str):
        """
        Gets an overview of the executions currently running in the project, by job queue
        """
        return get_project_summary.sync(project_id=project_id, client=self._api_client).additional_properties

    def get_execution_logs(self, project_id: str, dataset_id: str):
        """
        Gets live logs from main execution task
        """
        resp = get_execution_logs.sync(project_id=project_id, dataset_id=dataset_id, client=self._api_client)
        return '\n'.join(e.message for e in resp.events)

    def get_tasks_for_execution(self, project_id: str, dataset_id: str):
        """
        Gets the tasks submitted by the workflow execution
        """
        return get_tasks_for_execution.sync(project_id=project_id, dataset_id=dataset_id, client=self._api_client)

    def get_task_logs(self, project_id: str, dataset_id: str, task_id: str):
        """
        Gets the log output from an individual task
        """
        resp = get_task_logs.sync(project_id=project_id, dataset_id=dataset_id,
                                  task_id=task_id, client=self._api_client)
        return '\n'.join(e.message for e in resp.events)

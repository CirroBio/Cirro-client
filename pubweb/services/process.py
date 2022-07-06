from typing import List

from pubweb.clients.utils import get_id_from_name, filter_deleted
from pubweb.models.file import FileAccessContext
from pubweb.models.form_specification import ParameterSpecification
from pubweb.models.process import Executor, Process, RunAnalysisCommand
from pubweb.models.s3_path import S3Path
from pubweb.services.file import FileEnabledService


class ProcessService(FileEnabledService):
    def list(self, process_type: Executor = None) -> List[Process]:
        """
        Gets a list of processes filtered by an optional process type
        :param process_type:
        :return:
        """
        query = '''
          query ListProcesses(
            $filter: ModelProcessFilterInput
            $limit: Int
            $nextToken: String
          ) {
            listProcesses(filter: $filter, limit: $limit, nextToken: $nextToken) {
              items {
                id
                name
                desc
                _deleted
              }
            }
          }
        '''
        item_filter = {}
        if process_type:
            item_filter['executor'] = {'eq': process_type.value}
        resp = self._api_client.query(query, variables={'filter': item_filter})['listProcesses']
        return filter_deleted(resp['items'])

    def get_process(self, process_id: str) -> Process:
        """
        Gets detail of the specified process
        """
        query = '''
          query GetProcess($id: ID!) {
            getProcess(id: $id) {
              id
              childProcessIds
              name
              desc
              executor
              documentationUrl
              code {
                repository
                uri
                script
                version
              }
              paramMapJson
              formJson
              fileRequirementsMessage
              fileMappingRules {
                glob
                min
                max
                description
                isSample
                sampleMatchingPattern
              }
            }
          }
        '''
        return self._api_client.query(query, variables={'id': process_id})['getProcess']

    def get_process_id(self, name_or_id: str) -> str:
        return get_id_from_name(self.list(), name_or_id)

    def run_analysis(self, run_analysis_command: RunAnalysisCommand) -> str:
        """
        Runs an analysis on a dataset, returns the ID of the new dataset
        """
        spec = self.get_parameter_spec(run_analysis_command.process_id)
        spec.validate_params(run_analysis_command.params)
        query = '''
          mutation RunAnalysis($input: RunAnalysisInput!) {
            runAnalysis(input: $input)
          }
        '''
        resp = self._api_client.query(query, variables={'input': run_analysis_command.to_json()})
        return resp['runAnalysis']

    def get_parameter_spec(self, process_id: str) -> ParameterSpecification:
        """
        Gets a specification used to describe the parameters used in the process
        """
        access_context = FileAccessContext.resources()
        process = self.get_process(process_id)
        path = S3Path(process['formJson'])
        if path.valid:
            form_spec_json = self._file_service.get_file(access_context, path.key)
        else:
            form_spec_json = process['formJson']
        return ParameterSpecification.from_json(form_spec_json)

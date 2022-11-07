from typing import List, Optional

from pubweb.api.clients.utils import filter_deleted
from pubweb.api.models.file import FileAccessContext
from pubweb.api.models.form_specification import ParameterSpecification
from pubweb.api.models.process import Executor, RunAnalysisCommand, Process
from pubweb.api.models.s3_path import S3Path
from pubweb.api.services.file import FileEnabledService


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
                _deleted
              }
            }
          }
        '''
        item_filter = {}
        if process_type:
            item_filter['executor'] = {'eq': process_type.value}
        resp = self._api_client.query(query, variables={'filter': item_filter})['listProcesses']
        not_deleted = filter_deleted(resp['items'])
        return [Process.from_record(p) for p in not_deleted]

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
              _deleted
            }
          }
        '''
        return Process.from_record(self._api_client.query(query, variables={'id': process_id})['getProcess'])

    def find_by_name(self, name: str) -> Optional[Process]:
        """
        Get a process by its display name
        """
        matched_process = next((p for p in self.list() if p.name == name), None)
        if not matched_process:
            return None

        return self.get_process(matched_process.id)

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
        path = S3Path(process.form_spec_json)
        if path.valid:
            form_spec_json = self._file_service.get_file_from_path(access_context, path.key)
        else:
            form_spec_json = process.form_spec_json
        return ParameterSpecification.from_json(form_spec_json)

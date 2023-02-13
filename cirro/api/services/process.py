from pathlib import Path
from typing import List, Optional

from cirro.api.models.file import FileAccessContext, CheckDataTypesInput
from cirro.api.models.form_specification import ParameterSpecification
from cirro.api.models.process import Executor, RunAnalysisCommand, Process
from cirro.api.models.s3_path import S3Path
from cirro.api.services.file import FileEnabledService


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
                  min
                  max
                  description
                  isSample
                  fileNamePatterns {
                    exampleName
                    description
                    sampleMatchingPattern
                  }
                }
              }
            }
          }
        '''
        item_filter = {}
        if process_type:
            item_filter['executor'] = {'eq': process_type.value}
        resp = self._api_client.query(query, variables={'filter': item_filter})['listProcesses']
        return [Process.from_record(p) for p in resp['items']]

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
                min
                max
                description
                isSample
                fileNamePatterns {
                  exampleName
                  description
                  sampleMatchingPattern
                }
              }
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
        access_context = FileAccessContext.resources(self._configuration.resources_bucket)
        process = self.get_process(process_id)
        path = S3Path(process.form_spec_json)
        if path.valid:
            form_spec_json = self._file_service.get_file_from_path(access_context, path.key)
        else:
            form_spec_json = process.form_spec_json
        return ParameterSpecification.from_json(form_spec_json)

    def check_dataset_files(self, files: List[str], process_id: str, directory: str):
        """
        Checks if the file mapping rules for a process are met by the list of files
        :param files: files to check
        :param process_id: ID for the process containing the file mapping rules
        :param directory: path to directory containing files
        """
        # Parse samplesheet file if present
        samplesheet = None
        samplesheet_file = Path(directory, 'samplesheet.csv')
        if samplesheet_file.exists():
            samplesheet = samplesheet_file.read_text()

        # Call cirro function
        data_types_input = CheckDataTypesInput(fileNames=files, processId=process_id, sampleSheet=samplesheet)
        query = '''
            query checkDataTypes($input: CheckDataTypesInput!) {
              checkDataTypes(input: $input) {
                files
                errorMsg
                allowedDataTypes {
                  description
                  errorMsg
                  allowedPatterns {
                    exampleName
                    description
                    sampleMatchingPattern
                  }
                }
              }
            }
        '''
        resp = self._api_client.query(query, variables={'input': data_types_input})
        reqs = resp['checkDataTypes']

        # These will be samplesheet errors or no files errors
        if reqs['errorMsg']:
            raise ValueError(reqs['errorMsg'])

        # These will be errors for missing files
        all_errors = [entry['errorMsg'] for entry in reqs['allowedDataTypes'] if entry['errorMsg'] is not None]
        patterns = [' or '.join([e['exampleName'] for e in entry['allowedPatterns']])
                    for entry in reqs['allowedDataTypes']]

        if len(all_errors) != 0:
            raise ValueError("Files do not meet dataset type requirements. The expected files are: \n" +
                             "\n".join(patterns))

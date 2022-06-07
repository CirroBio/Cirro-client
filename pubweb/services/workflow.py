from pubweb.services.base import BaseService
import pubweb

class WorkflowService(BaseService):

    def configure(self):
        """Main method for getting user input, parsing the repo, and creating process docs"""
        input_params = {}
        input_params['resources_bucket'] = 'z-pubweb' # name of the S3 bucket to save the records

        # First, get info about the repo and version
        input_params['repo'] = pubweb.cli.questions.gather_repo_arguments()

        # If we're not using a repo, then gather blank process arguments
        if input_params['repo']['org'] is None or len(input_params['repo']['org']) < 1:
            input_params['process'] = pubweb.cli.questions.gather_blank_process_arguments()
            input_params['repo']['repo_version'] = {
                                                    'title': '',
                                                    'url': '',
                                                    'tag': ''
                                                }
        else:
            tarball_url = pubweb.cli.utils.parse_release_info(release_url=input_params['repo']['repo_version']['url'])
            repo_tarball = pubweb.cli.utils.get_repo(repo_url=tarball_url)
            nf_schema = pubweb.cli.utils.get_nextflow_schema(repo_tarball=repo_tarball)
            if nf_schema:
                input_params['repo_schema'] = nf_schema
                # Third, get all of the process-related parameters, based on the nextflow schema
                input_params['process'] = pubweb.cli.questions.gather_nf_process_arguments(nf_schema=input_params['repo_schema'])
            else:
                # Third, get all of the process-related parameters, based just on user input
                input_params['process'] = pubweb.cli.questions.gather_blank_process_arguments()

        # Fourth, write out the process config files
        output_dir = pubweb.cli.questions.get_output_directory()
        working_dir = 'process/templates'
        pubweb.cli.records.write_process_config(input_params=input_params,
                                    output_dir=output_dir,
                                    working_dir=working_dir)

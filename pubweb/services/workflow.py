from pubweb.services.base import BaseService
import pubweb

class WorkflowService(BaseService):

    def configure(self):
        """Main method for getting user input, parsing the repo, and creating process docs"""

        # All of the parameters will be added to a single object
        input_params = {}

        # First, get info about the repo and version
        input_params['repo'] = pubweb.cli.questions.gather_repo_arguments()

        # Get the URL to download with the indicated version of the workflow
        tarball_url = pubweb.cli.utils.parse_release_info(release_url=input_params['repo']['url'])
        repo_tarball = pubweb.cli.utils.get_repo(repo_url=tarball_url)

        # Try to parse a nextflow_schema.json file, if present
        nf_schema = pubweb.cli.utils.get_nextflow_schema(repo_tarball=repo_tarball)

        # If a nextflow_schema.json is present
        if nf_schema:
            input_params['repo_schema'] = nf_schema
            # Third, get all of the process-related parameters, based on the nextflow schema
            input_params['process'] = pubweb.cli.questions.gather_nf_process_arguments(nf_schema=input_params['repo_schema'])
        else:
            # Third, get all of the process-related parameters, based just on user input
            input_params['process'] = pubweb.cli.questions.gather_blank_process_arguments()

        # Fourth, write out the process config files
        output_dir = pubweb.cli.questions.get_output_directory()

        # Write out all of the needed configuration files to output_dir
        pubweb.cli.records.write_process_config(
            input_params=input_params,
            output_dir=output_dir
        )

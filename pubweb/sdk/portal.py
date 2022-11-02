import fnmatch
import gzip
from io import BytesIO, StringIO
from typing import Union
import pandas as pd
from pubweb import PubWeb
from pubweb.file_utils import get_files_in_directory
from pubweb.models.form_specification import ParameterSpecification
from pubweb.models.project import Project
from pubweb.models.process import RunAnalysisCommand, Process
from pubweb.models.dataset import Dataset, CreateIngestDatasetInput
from pubweb.models.file import File
from pubweb.models.reference import Reference, ReferenceType
from pubweb.sdk.exceptions import DataPortalAssetNotFound, DataPortalInputError
from time import sleep


class DataPortalAsset:
    """Dummy class"""
    def __init__(self):
        pass


class DataPortalAssets(list):
    """Generic class of assets (projects, datasets, etc.) in the Data Portal."""

    # Overridden by child classes
    asset_name = 'asset'
    asset_class = DataPortalAsset

    def __init__(self, input_list):

        # Add all of the items from the input list
        self.extend(input_list)

    def __str__(self):
        return "\n\n".join([str(i) for i in self])

    def description(self):
        """Render a text summary of the assets."""

        return '\n\n---\n\n'.join([
            str(i)
            for i in self
        ])

    def get_by_name(self, name: str):
        """Return the item which matches with name attribute."""

        if name is None:
            raise DataPortalInputError(f"Must provide name to identify {self.asset_name}")

        # Get the items which have a matching name
        matching_queries = [i for i in self if i.name == name]

        # Error if no items are found
        msg = '\n'.join([f"No {self.asset_name} found with name '{name}'.", self.description()])
        if len(matching_queries) == 0:
            raise DataPortalAssetNotFound(msg)

        # Error if multiple projects are found
        msg = f"Multiple {self.asset_name} items found with name '{name}', use ID instead.\n{self.description()}"
        if len(matching_queries) > 1:
            raise DataPortalAssetNotFound(msg)

        return matching_queries[0]

    def get_by_id(self, id: str):

        if id is None:
            raise DataPortalInputError(f"Must provide id to identify {self.asset_name}")

        # Get the items which have a matching ID
        matching_queries = [i for i in self if i.id == id]

        # Error if no items are found
        msg = '\n'.join([f"No {self.asset_name} found with id '{id}'.", self.description()])
        if len(matching_queries) == 0:
            raise DataPortalAssetNotFound(msg)

        return matching_queries[0]

    def filter_by_pattern(self, pattern: str) -> 'DataPortalAssets':
        """Filter the items to just those whose name attribute matches the pattern."""

        # Get a list of the names to search against
        all_names = [i.name for i in self]

        # Filter the names by the pattern
        filtered_names = fnmatch.filter(all_names, pattern)

        # Filter the list to only include those items
        return self.__class__(
            [
                i
                for i in self
                if i.name in filtered_names
            ]
        )


class DataPortalFile:
    """
    Datasets are made up of a collection of File objects in the Data Portal
    """

    def __init__(self, file: File, client: PubWeb):

        # Note that the 'name' and 'id' attributes are set to the relative path
        # The purpose of this is to support the DataPortalAssets class functions
        self.name = file.relative_path
        self.id = file.relative_path
        self.absolute_path = file.absolute_path
        self.abs_path = file.absolute_path

        # Inherit all of the other attributes
        self.relative_path = file.relative_path
        self.size = file.size
        self.access_context = file.access_context
        self.client = client

        # Attach the file object
        self.file = file

    def __str__(self):
        return f"{self.relative_path} ({self.size} bytes)"

    def get(self) -> str:
        """Internal method to call client.file.get_file"""

        return self.client.file.get_file(self.file)

    def read_csv(self, compression='infer', encoding='utf-8', **kwargs):
        """
        Parse the file as a Pandas DataFrame.

        The default field separator is a comma (for CSV), use sep='\\t' for TSV.

        File compression is inferred from the extension, but can be set
        explicitly with the compression= flag.

        All other keyword arguments are passed to pandas.read_csv
        https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
        """

        if compression == 'infer':
            # If the file appears to be compressed
            if self.relative_path.endswith('.gz'):
                compression = dict(method='gzip')
            elif self.relative_path.endswith('.bz2'):
                compression = dict(method='bz2')
            elif self.relative_path.endswith('.xz'):
                compression = dict(method='zstd')
            elif self.relative_path.endswith('.zst'):
                compression = dict(method='zstd')
            else:
                compression = None

        if compression is not None:
            handle = BytesIO(self.get())
        else:
            handle = StringIO(self.get().decode(encoding))

        df = pd.read_csv(
            handle,
            compression=compression,
            encoding=encoding,
            **kwargs
        )
        handle.close()
        return df

    def readlines(self, encoding='utf-8', compression=None):
        """Read the file contents as a list of lines."""

        return self.read(
            encoding=encoding,
            compression=compression
        ).splitlines()

    def read(self, encoding='utf-8', compression=None) -> str:
        """Read the file contents as text."""

        # Get the raw file contents
        cont = self.get()

        # If the file is uncompressed
        if compression is None:
            return cont.decode(encoding)
        # If the file is compressed
        else:

            # Only gzip-compression is supported currently
            if not compression == "gzip":
                raise DataPortalInputError("compression may be 'gzip' or None")

            with gzip.open(
                BytesIO(
                    cont
                ),
                'rt',
                encoding=encoding
            ) as handle:
                return handle.read()

    def download(self, download_location: str = None):
        """Download the file to a local directory."""

        if download_location is None:
            raise DataPortalInputError("Must provide download location")

        self.client.file.download_files(
            self.file.access_context,
            download_location,
            [self.relative_path]
        )


class DataPortalFiles(DataPortalAssets):
    asset_name = "file"
    asset_class = DataPortalFile

    def download(self, download_location: str = None) -> None:
        """Download the collection of files to a local directory."""

        for f in self:
            f.download(download_location)


class DataPortalProcess:
    """Helper functions for interacting with analysis processes."""

    def __init__(self, process: Process, client: PubWeb):

        self.id = process.id
        self.name = process.name
        self.description = process.description
        self.child_process_ids = process.child_process_ids
        self.executor = process.executor
        self.documentation_url = process.documentation_url
        self.code = process.code
        self.form_spec_json = process.form_spec_json
        self.sample_sheet_path = process.sample_sheet_path
        self.file_requirements_message = process.file_requirements_message
        self.file_mapping_rules = process.file_mapping_rules
        self.client = client

    def __str__(self):
        return '\n'.join([
            f"{i.title()}: {self.__getattribute__(i)}"
            for i in ['name', 'id', 'description']
        ])

    def get_parameter_spec(self) -> ParameterSpecification:
        """
        Gets a specification used to describe the parameters used in the process
        """
        return self.client.process.get_parameter_spec(self.id)


class DataPortalProcesses(DataPortalAssets):
    asset_name = "process"
    asset_class = DataPortalProcess


class DataPortalDataset:
    """
    Datasets in the Data Portal are collections of files which have
    either been uploaded directly, or which have been output by
    an analysis pipeline or notebook.
    """

    def __init__(self, dataset: Dataset, client: PubWeb):
        self.id = dataset.id
        self.name = dataset.name
        self.description = dataset.description
        self.process_id = dataset.process_id
        self.project_id = dataset.project_id
        self.status = dataset.status
        self.source_dataset_ids = dataset.source_dataset_ids
        self.info = dataset.info
        self.params = dataset.params
        self.created_at = dataset.created_at
        self.client = client

    def __str__(self):
        return '\n'.join([
            f"{i.title()}: {self.__getattribute__(i)}"
            for i in ['name', 'id', 'description', 'status']
        ])

    def list_files(self) -> DataPortalFiles:
        """Return the list of files which make up the dataset."""

        return DataPortalFiles(
            [
                DataPortalFile(
                    f,
                    client=self.client
                )
                for f in self.client.dataset.get_dataset_files(
                    project_id=self.project_id,
                    dataset_id=self.id
                )
            ]
        )

    def download_files(self, download_location: str = None) -> None:
        """Download all of the files from the dataset to a local directory."""

        # Alias for internal method
        self.list_files().download(download_location)

    def run_analysis(
        self,
        name: str = None,
        description: str = "",
        process: Union[DataPortalProcess, str] = None,
        params={},
        notifications_emails=[]
    ) -> str:
        """
        Runs an analysis on a dataset, returns the ID of the new dataset.
        The process can be provided as either a DataPortalProcess object,
        or a string which corresponds to the name or ID of the process.
        """

        if name is None:
            raise DataPortalInputError("Must specify 'name' for run_analysis")
        if process is None:
            raise DataPortalInputError("Must specify 'process' for run_analysis")

        # If the process is a string, try to parse it as a process name or ID
        if isinstance(process, str):

            # Make a Portal object
            portal = DataPortal(self.client)

            # Try to parse it as a name
            try:
                process = portal.get_process_by_name(process)
            except DataPortalAssetNotFound:
                pass

            # If that didn't work
            if isinstance(process, str):

                # Try to parse it as an ID
                try:
                    process = portal.get_process_by_id(process)
                except DataPortalAssetNotFound:

                    # Raise an error indicating that the process couldn't be parsed
                    raise DataPortalInputError(f"Could not parse process name or id: '{process}'")

        return self.client.process.run_analysis(
            RunAnalysisCommand(
                name=name,
                description=description,
                process_id=process.id,
                parent_dataset_id=self.id,
                project_id=self.project_id,
                params=params,
                notifications_emails=notifications_emails
            )
        )


class DataPortalDatasets(DataPortalAssets):
    asset_name = "dataset"
    asset_class = DataPortalDataset


class DataPortalReference:
    """
    Reference data is organized by project, categorized by type.
    """

    def __init__(self, ref: Reference):
        self.name = ref.name
        self.access_context = ref.access_context
        self.relative_path = ref.relative_path
        self.absolute_path = f'{self.access_context.domain}/{self.relative_path.strip("/")}'

    def __str__(self):
        return self.name


class DataPortalReferences(DataPortalAssets):
    asset_name = "reference"
    asset_class = DataPortalReference


class DataPortalReferenceType:
    """
    Reference data is organized by project, categorized by type.
    """

    def __init__(self, ref_type: ReferenceType):
        self.name = ref_type.name
        self.description = ref_type.description
        self.directory = ref_type.directory
        self.validation = ref_type.validation

    def __str__(self):
        return '\n'.join([
            f"{i.title()}: {self.__getattribute__(i)}"
            for i in ['name', 'description']
        ])


class DataPortalReferenceTypes(DataPortalAssets):
    asset_name = "reference type"
    asset_class = DataPortalReferenceType


class DataPortalProject:
    """
    Projects in the Data Portal contain collections of Datasets.
    Users are granted permissions at the project-level, allowing them
    to view and/or modify all of the datasets in that collection.
    """

    def __init__(self, proj: Project, client: PubWeb):
        """Initialize the Project from the base PubWeb model."""

        self.id = proj.id
        self.name = proj.name
        self.description = proj.description
        self.client = client

    def __str__(self):
        """Control how the Project is rendered as a string."""

        return '\n'.join([
            f"{i.title()}: {self.__getattribute__(i)}"
            for i in ['name', 'id', 'description']
        ])

    def list_datasets(self) -> DataPortalDatasets:
        """List all of the datasets available in the project."""

        return DataPortalDatasets(
            [
                DataPortalDataset(d, self.client)
                for d in self.client.dataset.find_by_project(self.id)
            ]
        )

    def get_dataset_by_name(self, name: str = None) -> DataPortalDataset:
        """Return the dataset with the specified name."""

        return self.list_datasets().get_by_name(name)

    def get_dataset_by_id(self, id: str = None) -> DataPortalDataset:
        """Return the dataset with the specified id."""

        return self.list_datasets().get_by_id(id)

    def list_references(self, reference_type: str = None) -> DataPortalReferences:
        """
        List the references available in a project.
        Optionally filter to references of a particular type (identified by name)
        """

        # Get the complete list of references which are available
        references = DataPortalReferenceTypes(
            [
                DataPortalReferenceType(ref)
                for ref in self.client.common.get_references_types()
            ]
        )

        # If a particular name was specified
        if reference_type is not None:
            references = references.filter_by_pattern(reference_type)
            if len(references) == 0:
                msg = f"Could not find any reference types with the name {reference_type}"
                raise DataPortalAssetNotFound(msg)

        return DataPortalReferences(
            [
                DataPortalReference(ref)
                for reference_type in references
                for ref in self.client.project.get_references(
                    self.id,
                    reference_type.directory
                )
            ]
        )

    def get_reference_by_name(self, name: str = None, reftype: str = None) -> DataPortalReference:
        """Return the reference of a particular type with the specified name."""

        if name is None:
            raise DataPortalInputError("Must specify the reference name")

        return self.list_references(reftype).get_by_name(name)

    def upload_dataset(
        self,
        name: str = None,
        description='',
        process: DataPortalProcess = None,
        upload_folder: str = None,
        files: list = None
    ):
        """
        Upload a set of files to the Data Portal, creating a new dataset.
        """

        if name is None:
            raise DataPortalInputError("Must provide name for new dataset")
        if process is None:
            raise DataPortalInputError("Must provide the process which is used for ingest")
        if upload_folder is None:
            raise DataPortalInputError("Must provide upload_folder -- folder containing files to upload")

        # If no files were provided
        if files is None:

            # Get the list of files in the upload folder
            files = get_files_in_directory(upload_folder)

        # Create the ingest process request
        dataset_create_request = CreateIngestDatasetInput(
            project_id=self.id,
            process_id=process.id,
            name=name,
            description=description,
            files=files
        )

        # Get the response
        create_response = self.client.dataset.create(dataset_create_request)

        # Upload the files
        self.client.dataset.upload_files(
            project_id=self.id,
            dataset_id=create_response['datasetId'],
            directory=upload_folder,
            files=dataset_create_request.files
        )

        # Return the dataset which was created, which might take a second to update
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                return self.get_dataset_by_id(create_response['datasetId'])
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise e
                else:
                    sleep(1)


class DataPortalProjects(DataPortalAssets):
    asset_name = "project"
    asset_class = DataPortalProject


class DataPortal:
    """
    Helper functions for exploring the projects, datasets, samples, and files
    available in the PubWeb Data Portal.
    """

    def __init__(self, client: PubWeb = None):
        """Set up the DataPortal object, establishing a connection with the PubWeb Data Portal."""

        # If the user provided their own client to get information from PubWeb
        if client is not None:

            # Attach it
            self.client = client

        # If the user did not provide their own client
        else:

            # Set up a client
            self.client = PubWeb()

    def list_projects(self) -> DataPortalProjects:
        """List all of the projects available in the Data Portal."""

        return DataPortalProjects(
            [
                DataPortalProject(proj, self.client)
                for proj in self.client.project.list()
            ]
        )

    def get_project_by_name(self, name: str = None) -> DataPortalProject:
        """Return the project with the specified name."""

        return self.list_projects().get_by_name(name)

    def get_project_by_id(self, id: str = None) -> DataPortalProject:
        """Return the project with the specified id."""

        return self.list_projects().get_by_id(id)

    def list_processes(self, ingest=False) -> DataPortalProcesses:
        """
        List all of the processes available in the Data Portal.
        By default, only list non-ingest processes (those which can be run on existing datasets).
        To list the processes which can be used to upload datasets, use ingest = True.
        """

        return DataPortalProcesses(
            [
                DataPortalProcess(p, self.client)
                for p in self.client.process.list()
                if (p.executor.name == "INGEST") == ingest
            ]
        )

    def get_process_by_name(self, name: str, ingest=False) -> DataPortalProcess:
        """Return the process with the specified name."""

        return self.list_processes(ingest=ingest).get_by_name(name)

    def get_process_by_id(self, id: str, ingest=False) -> DataPortalProcess:
        """Return the process with the specified id."""

        return self.list_processes(ingest=ingest).get_by_id(id)

    def list_reference_types(self):
        """Return the list of all available reference types."""

        return DataPortalReferenceTypes(
            [
                DataPortalReferenceType(ref)
                for ref in self.client.common.get_references_types()
            ]
        )

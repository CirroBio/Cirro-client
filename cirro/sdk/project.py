from time import sleep
from typing import Union

from cirro.api.clients.portal import DataPortalClient
from cirro.api.models.dataset import CreateIngestDatasetInput
from cirro.api.models.project import Project
from cirro.file_utils import get_files_in_directory
from cirro.sdk.asset import DataPortalAssets, DataPortalAsset
from cirro.sdk.dataset import DataPortalDataset, DataPortalDatasets
from cirro.sdk.exceptions import DataPortalAssetNotFound, DataPortalInputError
from cirro.sdk.helpers import parse_process_name_or_id
from cirro.sdk.process import DataPortalProcess
from cirro.sdk.reference import DataPortalReference, DataPortalReferences
from cirro.sdk.reference_type import DataPortalReferenceType, DataPortalReferenceTypes


class DataPortalProject(DataPortalAsset):
    """
    Projects in the Data Portal contain collections of Datasets.
    Users are granted permissions at the project-level, allowing them
    to view and/or modify all of the datasets in that collection.
    """
    name = None

    def __init__(self, proj: Project, client: DataPortalClient):
        """Initialize the Project from the base Cirro model."""

        self.id = proj.id
        self.name = proj.name
        self.description = proj.description
        self._client = client

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
                DataPortalDataset(d, self._client)
                for d in self._client.dataset.find_by_project(self.id)
            ]
        )

    def get_dataset_by_name(self, name: str = None) -> DataPortalDataset:
        """Return the dataset with the specified name."""

        dataset = next(iter(self._client.dataset.find_by_project(self.id, name=name)), None)
        if dataset is None:
            raise DataPortalAssetNotFound(f'Dataset with name {name} not found')
        return DataPortalDataset(dataset, self._client)

    def get_dataset_by_id(self, _id: str = None) -> DataPortalDataset:
        """Return the dataset with the specified id."""

        dataset = self._client.dataset.get_from_id(_id=_id)
        if dataset is None:
            raise DataPortalAssetNotFound(f'Dataset with ID {_id} not found')
        return DataPortalDataset(dataset, self._client)

    def list_references(self, reference_type: str = None) -> DataPortalReferences:
        """
        List the references available in a project.
        Optionally filter to references of a particular type (identified by name)
        """

        # Get the complete list of references which are available
        references = DataPortalReferenceTypes(
            [
                DataPortalReferenceType(ref)
                for ref in self._client.common.get_references_types()
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
                for ref in self._client.project.get_references(
                    self.id,
                    reference_type.directory
                )
            ]
        )

    def get_reference_by_name(self, name: str = None, ref_type: str = None) -> DataPortalReference:
        """Return the reference of a particular type with the specified name."""

        if name is None:
            raise DataPortalInputError("Must specify the reference name")

        return self.list_references(ref_type).get_by_name(name)

    def upload_dataset(
        self,
        name: str = None,
        description='',
        process: Union[DataPortalProcess, str] = None,
        upload_folder: str = None,
        files: list = None
    ):
        """
        Upload a set of files to the Data Portal, creating a new dataset.

        If the files parameter is not provided, it will upload all files in the upload folder
        """

        if name is None:
            raise DataPortalInputError("Must provide name for new dataset")
        if process is None:
            raise DataPortalInputError("Must provide the process which is used for ingest")
        if upload_folder is None:
            raise DataPortalInputError("Must provide upload_folder -- folder containing files to upload")

        # Parse the process provided by the user
        process = parse_process_name_or_id(process, self._client)

        # If no files were provided
        if files is None:

            # Get the list of files in the upload folder
            files = get_files_in_directory(upload_folder)

        # Make sure that the files match the expected pattern
        self._client.process.check_dataset_files(files, process.id, upload_folder)

        # Create the ingest process request
        dataset_create_request = CreateIngestDatasetInput(
            project_id=self.id,
            process_id=process.id,
            name=name,
            description=description,
            files=files
        )

        # Get the response
        create_response = self._client.dataset.create(dataset_create_request)

        # Upload the files
        self._client.dataset.upload_files(
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
            except DataPortalAssetNotFound as e:
                if attempt == max_attempts - 1:
                    raise e
                else:
                    sleep(2)


class DataPortalProjects(DataPortalAssets[DataPortalProject]):
    asset_name = "project"

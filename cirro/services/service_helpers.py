from typing import List

from cirro_api_client.v1.models import ShareType

from cirro import CirroApi
from cirro.models.dataset import DatasetWithShare


def list_all_datasets(project_id: str, client: CirroApi) -> List[DatasetWithShare]:
    """
    List all datasets for a given project, including those shared with the project

    Args:
        project_id (str): ID of the Project
        client (cirro.CirroApi): Cirro API client

    Returns:
        List of datasets
    """
    datasets = client.datasets.list(project_id=project_id)
    datasets = [DatasetWithShare.from_dataset(d, share=None) for d in datasets]
    # Pull datasets from subscribed shares
    subscribed_shares = client.shares.list(project_id=project_id, share_type=ShareType.SUBSCRIBER)
    for share in subscribed_shares:
        datasets_in_share = client.datasets.list_shared(project_id, share.id)
        datasets_in_share = [DatasetWithShare.from_dataset(d, share=share) for d in datasets_in_share]
        datasets += datasets_in_share
    return datasets

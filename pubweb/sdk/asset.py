import fnmatch
from pubweb.sdk.exceptions import DataPortalAssetNotFound, DataPortalInputError


class DataPortalAsset:
    """Base class used for all Data Portal Assets"""
    def __init__(self):
        pass


class DataPortalAssets(list):
    """
    Generic class with helper functions for any group of assets (projects, datasets, etc.) in the Data Portal.
    """

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
        """Return the item which matches by id attribute."""

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

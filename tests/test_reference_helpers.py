import unittest

from cirro_api_client.v1.models import ReferenceType

from cirro.helpers.references import generate_reference_file_path_map

test_reference_type = ReferenceType.from_dict(
    {
        "name": "CRISPR sgRNA Library",
        "description": "",
        "directory": "crispr_libraries",
        "validation": [
            {
                "fileType": "csv",
                "saveAs": "library.csv",
                "glob": "*lib*"
            },
            {
                "fileType": "csv",
                "saveAs": "controls.txt",
                "glob": "*cont*"
            }
        ]
    },
)


class ReferenceHelperTest(unittest.TestCase):
    def test_generate_reference_file_map(self):
        name = "TestLibrary"
        file_map = generate_reference_file_path_map(
            files=["/tmp/library-test.csv"],
            name=name,
            ref_type=test_reference_type
        )

        expected_file_map = {
            "/tmp/library-test.csv": f"crispr_libraries/{name}/library.csv"
        }
        self.assertEqual(file_map, expected_file_map)

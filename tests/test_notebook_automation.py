from pathlib import Path
import unittest
import os


def read(fp):
    return Path(fp).read_text()


class IntegrationTestNotebookAutomation(unittest.TestCase):
    def test_form_setup(self):

        # Run the notebook as it would be run in interactive mode
        os.system("pip3 install nbconvert ipykernel")
        os.system("jupyter nbconvert --to notebook --execute example_notebook_form/example_notebook.ipynb --inplace")

        # Get the output provided by the user in the notebook itself
        self.assertEqual(
            read("example_notebook_form/final_story.txt"),
            read("example_notebook_form/expected_final_story_1.txt")
        )

        # Now run the notebook with the flag pointing to values provided by the non-interactive input form
        os.system("PW_NOTEBOOK_DATA=pw-notebook-data.json jupyter nbconvert --to notebook --execute example_notebook_form/example_notebook.ipynb --inplace")

        # Get the output driven by the parameter values from the pw-notebook-data.json file
        self.assertEqual(
            read("example_notebook_form/final_story.txt"),
            read("example_notebook_form/expected_final_story_2.txt")
        )


if __name__ == '__main__':
    unittest.main()

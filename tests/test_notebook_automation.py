import json
from pathlib import Path
import unittest
import os


def read(fp):
    return Path(fp).read_text()


def cleanup(fp):
    f = Path(fp)
    if f.exists():
        os.remove(fp)


class IntegrationTestNotebookAutomation(unittest.TestCase):
    def test_form_setup(self):

        # Run the notebook as it would be run in interactive mode
        os.system("pip3 install nbconvert ipykernel")
        run_notebook = "jupyter nbconvert --to notebook --execute example_notebook_form/example_notebook.ipynb --inplace" # noqa
        os.system(run_notebook)

        # Make sure that the output was produced
        final_story = "example_notebook_form/final_story.txt"
        self.assertTrue(Path(final_story).exists())

        # Make sure that the form JSON was produced
        form_json = "example_notebook_form/.cirro/form.json"
        self.assertTrue(Path(form_json).exists())

        # Make sure that the story matches what was defined in the notebook
        self.assertEqual(
            read(final_story),
            read("example_notebook_form/expected_final_story_1.txt")
        )
        cleanup(final_story)

        # Now add data which would have been provided by the user
        params_fp = "example_notebook_form/.cirro/params.json"
        with open(params_fp, "w") as handle:
            json.dump(
                dict(
                    person="Kenji",
                    food="hot dogs",
                    emotion="mustard"
                ),
                handle
            )

        # Now run the notebook again
        os.system(run_notebook)

        # Make sure that the story matches what was defined in the params file
        self.assertEqual(
            read(final_story),
            read("example_notebook_form/expected_final_story_2.txt")
        )

        cleanup(final_story)
        cleanup(params_fp)


if __name__ == '__main__':
    unittest.main()

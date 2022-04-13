from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

entry_points = {
    'console_scripts': [
        'pubweb-cli = pubweb.cli.cli:main'
    ]
}

install_requires = [
    "click>=8.0,<8.1",
    "boto3>=1.20,<1.30",
    "questionary==1.10.0",
    "gql[requests]==3.0.0",
    "requests==2.27.1",
    "pycognito==2022.1.0",
    "tqdm==4.62.3"
]

setup(
    name='pubweb',
    version='0.1.1',
    author='Fred Hutch',
    author_email='viz@fredhutch.org',
    description='CLI tool for interacting with the PubWeb platform',
    packages=find_packages(),
    install_requires=install_requires,
    url='https://github.com/FredHutch/PubWeb-client',
    entry_points=entry_points,
    # long_description=long_description
)

from pathlib import Path

from setuptools import setup, find_packages

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

entry_points = {
    'console_scripts': [
        'cirro-cli = cirro.cli.cli:main'
    ]
}

install_requires = [
    "click>=8.1.3",
    "boto3==1.*",
    "botocore==1.*",
    "questionary>=1.10.0",
    "gql[requests]>=3.4.0",
    "requests>=2.28.1",
    "requests_aws4auth>=1.1.2",
    "pycognito>=2022.8.0",
    "tqdm>=4.62.3",
    "pandas>=1.5.0",
    "pygithub>=1.56",
    "jsonschema>=4.6.1",
    "s3fs==0.4.*",
    "fsspec==2022.*",
    "pyjwt==2.4.0",
    "msal-extensions==1.0.0"
]

setup(
    name='cirro',
    version='0.6.2',
    author='Fred Hutch',
    license='MIT',
    author_email='cirro@fredhutch.org',
    description='CLI tool for interacting with the Cirro platform',
    packages=find_packages(include=['cirro*']),
    install_requires=install_requires,
    url='https://github.com/FredHutch/Cirro-client',
    entry_points=entry_points,
    long_description=long_description,
    long_description_content_type="text/markdown"
)

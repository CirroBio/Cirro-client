from pathlib import Path

from setuptools import setup, find_packages

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

entry_points = {
    'console_scripts': [
        'pubweb-cli = pubweb.cli.cli:main'
    ]
}

install_requires = [
    "click>=8.1.3",
    "boto3>=1.24",
    "questionary==1.10.0",
    "gql[requests]==3.4.0",
    "requests==2.28.1",
    "requests_aws4auth==1.1.2",
    "pycognito==2022.8.0",
    "tqdm==4.62.3",
    "pandas>=1.4.0,<1.5.0",
    "pygithub>=1.55",
    "jsonschema==4.6.1"
]

install_analysis_requires = [
    "s3fs==2022.8.2"
]

install_all_requires = install_requires + install_analysis_requires

setup(
    name='pubweb',
    version='0.3.8',
    author='Fred Hutch',
    license='MIT',
    author_email='viz@fredhutch.org',
    description='CLI tool for interacting with the PubWeb platform',
    packages=find_packages(include=['pubweb*']),
    install_requires=install_requires,
    extras_require={
        "all": install_all_requires,
        "analysis": install_analysis_requires
    },
    url='https://github.com/FredHutch/PubWeb-client',
    entry_points=entry_points,
    long_description=long_description
)

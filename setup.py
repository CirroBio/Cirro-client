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
    "click>=8.0,<8.1",
    "boto3>=1.20,<1.30",
    "questionary==1.10.0",
    "gql[requests]==3.0.0",
    "requests==2.27.1",
    "requests_aws4auth==1.1.2",
    "pycognito==2022.1.0",
    "tqdm==4.62.3",
    "pygithub>=1.55",
    "jsonschema==4.6.1"
]

install_analysis_requires = [
    "pandas>=1.4.0,<1.5.0",
    "s3fs==2022.5.0"
]

install_all_requires = install_requires + install_analysis_requires

setup(
    name='pubweb',
    version='0.2.2',
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
    # long_description=long_description
)

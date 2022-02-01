from setuptools import setup, find_packages

entry_points = {
    'console_scripts': [
        'pubweb-cli = pubweb.cli.cli:main'
    ]
}

interactive_requires = [
    "questionary==1.10.0"
]

install_requires = [
    "click>=8.0,<8.1",
    "boto3>=1.20,<1.30",
    "gql[requests]==3.0.0",
    "requests==2.27.1",
    "pycognito==2022.1.0",
    "tqdm==4.62.3"
]

setup(
    name='pubweb',
    version='0.0.1',
    author='Fred Hutch',
    author_email='viz@fredhutch.org',
    description='CLI tool for interacting with the PubWeb platform',
    packages=find_packages(),
    install_requires=install_requires+interactive_requires,
    extras_require={
        "no_interactive": install_requires
    },
    url='https://github.com/FredHutch/PubWeb-client',
    entry_points=entry_points
)

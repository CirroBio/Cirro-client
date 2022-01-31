from setuptools import setup, find_packages

entry_points = {
    'console_scripts': [
        'pubweb-cli = pubweb.cli.cli:main'
    ]
}

install_requires = [

]

setup(
    name='pubweb',
    version='0.0.1',
    author='Fred Hutch',
    author_email='viz@fredhutch.org',
    description='CLI tool for interacting with the PubWeb platform',
    packages=find_packages(),
    install_requires=install_requires,
    url='https://github.com/FredHutch/PubWeb-cli',
    entry_points=entry_points
)

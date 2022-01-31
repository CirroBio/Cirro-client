import click

from pubweb import run_ingest
from pubweb.cli.controller import run_download


@click.group(help="PubWeb CLI - Tool for interacting with datasets")
def run():
    pass


@run.command(help='Download dataset files', no_args_is_help=True)
@click.option('--project',
              help='Name or ID of the project')
@click.option('--dataset',
              help='ID of the dataset')
@click.option('--data-directory',
              help='Directory to store the files')
@click.option('--interactive',
              help='Gather arguments interactively',
              is_flag=True, default=False)
def download(**kwargs):
    run_download(kwargs, interactive=kwargs.get('interactive'))


@run.command(help='Upload and create dataset', no_args_is_help=True)
@click.option('--data-directory',
              help='Directory you wish to upload')
@click.option('--project',
              help='Name or ID of the project')
@click.option('--process',
              help='Name or ID of the ingest process')
@click.option('--name',
              help='Name of the dataset')
@click.option('--description',
              help='Description of the dataset (optional)',
              default='')
@click.option('--interactive',
              help='Gather arguments interactively',
              is_flag=True, default=False)
def upload(**kwargs):
    run_ingest(kwargs, interactive=kwargs.get('interactive'))


if __name__ == '__main__':
    run()

import click

from pubweb.cli import run_ingest, run_download, run_configure, run_list_datasets, run_configure_workflow


def check_required_args(args):
    if args.get('interactive'):
        return
    if any(value is None for value in args.values()):
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit()


@click.group(help="PubWeb CLI - Tool for interacting with datasets")
@click.version_option()
def run():
    pass  # Print out help text, nothing to do


@run.command(help='List datasets', no_args_is_help=True)
@click.option('--project',
              help='Name or ID of the project')
@click.option('-i', '--interactive',
              help='Gather arguments interactively',
              is_flag=True, default=False)
def list_datasets(**kwargs):
    check_required_args(kwargs)
    run_list_datasets(kwargs, interactive=kwargs.get('interactive'))


@run.command(help='Download dataset files', no_args_is_help=True)
@click.option('--project',
              help='Name or ID of the project')
@click.option('--dataset',
              help='ID of the dataset')
@click.option('--data-directory',
              help='Directory to store the files')
@click.option('-i', '--interactive',
              help='Gather arguments interactively',
              is_flag=True, default=False)
def download(**kwargs):
    check_required_args(kwargs)
    run_download(kwargs, interactive=kwargs.get('interactive'))


@run.command(help='Upload and create a dataset', no_args_is_help=True)
@click.option('--name',
              help='Name of the dataset')
@click.option('--description',
              help='Description of the dataset (optional)',
              default='')
@click.option('--project',
              help='Name or ID of the project')
@click.option('--process',
              help='Name or ID of the ingest process')
@click.option('--data-directory',
              help='Directory you wish to upload')
@click.option('-i', '--interactive',
              help='Gather arguments interactively',
              is_flag=True, default=False)
@click.option('--use-third-party-tool',
              help='Use third party tool for upload (Generate manifest and one-time upload authentication token)',
              is_flag=True, default=False)
def upload(**kwargs):
    check_required_args(kwargs)
    run_ingest(kwargs, interactive=kwargs.get('interactive'))


@run.command(help='Configure a workflow to run in the Data Portal')
def configure_workflow():
    run_configure_workflow()


@run.command(help='Configure authentication')
def configure():
    run_configure()


def main():
    try:
        run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

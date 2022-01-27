import click

from pubweb import run_ingest


@click.group()
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
@click.pass_context
def run(ctx, **kwargs):
    is_interactive = ctx.invoked_subcommand == 'interactive'
    run_ingest(kwargs, interactive=is_interactive)


@run.command(help='Gather dataset details interactively')
def interactive():
    pass


if __name__ == '__main__':
    run()

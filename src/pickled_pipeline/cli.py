import click
from .cache import Cache


@click.group()
def cli():
    """CLI for managing pickled_pipeline cache."""
    pass


@cli.command()
@click.argument("checkpoint_name")
@click.option(
    "--cache-dir",
    default="pipeline_cache",
    help="Cache directory path.",
)
def truncate(checkpoint_name, cache_dir):
    """Truncate cache from a specific checkpoint."""
    cache = Cache(cache_dir=cache_dir)
    if cache.truncate_cache(checkpoint_name):
        click.echo(f"Cache truncated from checkpoint '{checkpoint_name}'.")


@cli.command()
@click.option(
    "--cache-dir",
    default="pipeline_cache",
    help="Cache directory path.",
)
def clear(cache_dir):
    """Clear the entire cache."""
    cache = Cache(cache_dir=cache_dir)
    cache.clear_cache()
    click.echo("Entire cache has been cleared.")


@cli.command("list")
@click.option(
    "--cache-dir",
    default="pipeline_cache",
    help="Cache directory path.",
)
def list_checkpoints(cache_dir):
    """List all checkpoints in the cache."""
    cache = Cache(cache_dir=cache_dir)
    checkpoints = cache.list_checkpoints()
    if checkpoints:
        click.echo("Checkpoints in cache:")
        for checkpoint in checkpoints:
            click.echo(f"- {checkpoint}")
    else:
        click.echo("No checkpoints found in cache.")

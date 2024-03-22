import click
import logging
import signal

import Pyro4

from plugins.metrics import MetricsPlugin
from plugins.nas import PathManagementMixin
from plugins.sensitive import SecretsPlugin
from plugins.workflows import WorkflowsPlugin
from store import AbstractKVStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('remote_proxies')


class EnhancedKVStore(AbstractKVStore, MetricsPlugin, SecretsPlugin, WorkflowsPlugin, PathManagementMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        SecretsPlugin.__init__(self, *args, **kwargs)
        MetricsPlugin.__init__(self, *args, **kwargs)
        WorkflowsPlugin.__init__(self, *args, **kwargs)
        PathManagementMixin.__init__(self, *args, **kwargs)


@click.group()
def cli():
    """Command line interface for managing the KV Store."""
    pass


@cli.command()  # Marks the function as a command within the CLI group
@click.option('--host', default="localhost", help='Host for the KV Store server.')
@click.option('--port', default=6666, type=int, help='Port for the KV Store server.')
@click.option('--use-backup', is_flag=True, help='Load the key-value store from the most recent backup on startup.')
def start_server(host, port, use_backup):
    """Starts the KV Store server."""
    storage = EnhancedKVStore(
        collect_metrics=True,
        backup_dir="test_backups",
        metrics_interval=5,
        use_backup=use_backup
    )
    storage.start_tasks()

    daemon = Pyro4.Daemon(host=host, port=port)
    uri = daemon.register(storage, objectId="key_value_store")
    logger.info(f"Service started. Object uri = {uri}")

    def signal_handler(sig, frame):
        logger.info('Signal received, shutting down...')
        storage.shutdown()
        daemon.shutdown()
        logger.info("Server has been shut down.")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        daemon.requestLoop()
    finally:
        daemon.close()


@cli.command(name="update-config")
@click.option('--host', default="localhost", help='Host for the KV Store server.')
@click.option('--port', default=6666, help='Port for the KV Store server.')
@click.option('--backup-dir', type=str, help="New backup directory path.")
@click.option('--metrics-interval', type=int, help="New metrics collection interval in seconds.")
@click.option('--status-ttl', type=int, help="New status TTL.")
@click.option('--cleanup-frequency', type=int, help="New cleanup frequency in seconds.")
def update_config(host, port, backup_dir, metrics_interval, status_ttl, cleanup_frequency):
    """Updates the KV Store server's configuration."""
    with Pyro4.Proxy(f"PYRO:key_value_store@{host}:{port}") as proxy:
        proxy.update_configuration(
            backup_dir=backup_dir,
            metrics_interval=metrics_interval,
            status_ttl=status_ttl,
            cleanup_frequency=cleanup_frequency
        )
    logger.info("Configuration update sent to server.")


@cli.command(name="show-config")
@click.option('--host', default="localhost", help='Host for the KV Store server.')
@click.option('--port', default=6666, type=int, help='Port for the KV Store server.')
def show_config(host, port):
    """Displays the current KV Store server's configuration."""
    with Pyro4.Proxy(f"PYRO:key_value_store@{host}:{port}") as proxy:
        config = proxy.get_configuration()
        for key, value in config.items():
            click.echo(f"{key}: {value}")


@cli.command(name="shutdown")
@click.option('--host', default="localhost", help='Host for the KV Store server.')
@click.option('--port', default=6666, type=int, help='Port for the KV Store server.')
@click.option('--task-name', default=None, type=str,
              help='Name of the task to shut down. Leave empty to shut down all tasks.')
def shutdown_task(host, port, task_name):
    """Shuts down a specific task or all tasks in the KV Store server."""
    with Pyro4.Proxy(f"PYRO:key_value_store@{host}:{port}") as proxy:
        if task_name:
            proxy.shutdown(task_name=task_name)
            logger.info(f"Shutdown signal sent to task: {task_name}")
        else:
            proxy.shutdown()
            logger.info("Shutdown signal sent to all tasks.")


@cli.command(name="start-task")
@click.option('--host', default="localhost", help='Host for the KV Store server.')
@click.option('--port', default=6666, type=int, help='Port for the KV Store server.')
@click.option('--task-name', default=None, type=str, help='Name of the task to start. Leave empty to start all tasks.')
def start_task(host, port, task_name):
    """Starts a specific task or all tasks in the KV Store server."""
    with Pyro4.Proxy(f"PYRO:key_value_store@{host}:{port}") as proxy:
        if task_name:
            proxy.start_tasks(task_name=task_name)
            logger.info(f"Start signal sent to task: {task_name}")
        else:
            proxy.start_tasks()  # No task name provided, start all tasks
            logger.info("Start signal sent to all tasks.")


@cli.command(name="create-store")
@click.option('--host', default="localhost", help='Host for the KV Store server.')
@click.option('--port', default=6666, help='Port for the KV Store server.')
@click.argument('store_name')
def create_store(host, port, store_name):
    """Creates a new store."""
    with Pyro4.Proxy(f"PYRO:key_value_store@{host}:{port}") as proxy:
        result = proxy.create_store(store_name)
        if result:
            click.echo(f"Store '{store_name}' created successfully.")
        else:
            click.echo(f"Store '{store_name}' already exists or could not be created.")


@cli.command(name="delete-store")
@click.option('--host', default="localhost", help='Host for the KV Store server.')
@click.option('--port', default=6666, help='Port for the KV Store server.')
@click.argument('store_name')
def delete_store(host, port, store_name):
    """Deletes a store."""
    with Pyro4.Proxy(f"PYRO:key_value_store@{host}:{port}") as proxy:
        result = proxy.delete_store(store_name)
        if result:
            click.echo(f"Store '{store_name}' deleted successfully.")
        else:
            click.echo(f"Store '{store_name}' does not exist.")


@cli.command(name="list-stores")
@click.option('--host', default="localhost", help='Host for the KV Store server.')
@click.option('--port', default=6666, help='Port for the KV Store server.')
def list_stores(host, port):
    """Lists all stores."""
    with Pyro4.Proxy(f"PYRO:key_value_store@{host}:{port}") as proxy:
        stores = proxy.list_stores()
        click.echo("Stores:")
        for store in stores:
            click.echo(f"- {store}")


@cli.command(name="add-internal-key")
@click.argument('key')
@click.argument('value')
@click.option('--ttl', default=None, type=int, help='Time to live for the key.')
@click.option('--readonly', is_flag=True, help='Set the key as read-only.')
@click.option('--host', default="localhost", help='Host for the KV Store server.')
@click.option('--port', default=6666, type=int, help='Port for the KV Store server.')
def add_internal_key(key, value, ttl, readonly, host, port):
    """Adds a key to the internal store."""
    with Pyro4.Proxy(f"PYRO:key_value_store@{host}:{port}") as proxy:
        proxy.add_internal_key(key, value, ttl, readonly)
        click.echo(f"Key '{key}' added to the internal store.")


@cli.command(name="delete-internal-key")
@click.argument('key')
@click.option('--host', default="localhost", help='Host for the KV Store server.')
@click.option('--port', default=6666, type=int, help='Port for the KV Store server.')
def delete_internal_key(key, host, port):
    """Deletes a key from the internal store."""
    with Pyro4.Proxy(f"PYRO:key_value_store@{host}:{port}") as proxy:
        proxy.delete_internal_key(key)
        click.echo(f"Key '{key}' deleted from the internal store.")


@cli.command(name="edit-internal-key")
@click.argument('key')
@click.option('--value', default=None, type=str, help='New value for the key.')
@click.option('--ttl', default=None, type=int, help='New time to live for the key.')
@click.option('--readonly', type=bool, help='Set the key as read-only.')
@click.option('--host', default="localhost", help='Host for the KV Store server.')
@click.option('--port', default=6666, type=int, help='Port for the KV Store server.')
def edit_internal_key(key, value, ttl, readonly, host, port):
    """Edits an existing key within the internal store."""
    with Pyro4.Proxy(f"PYRO:key_value_store@{host}:{port}") as proxy:
        proxy.edit_internal_key(key, value, ttl, readonly)
        click.echo(f"Key '{key}' has been updated in the internal store.")


@cli.command(name="get-internal-key")
@click.argument('key')
@click.option('--host', default="localhost", help='Host for the KV Store server.')
@click.option('--port', default=6666, type=int, help='Port for the KV Store server.')
def get_internal_key(key, host, port):
    """Retrieves the value of a key from the internal store."""
    with Pyro4.Proxy(f"PYRO:key_value_store@{host}:{port}") as proxy:
        value = proxy.get_internal_key(key)
        click.echo(f"Value of '{key}': {value}")


@cli.command(name="get-all-internal-keys")
@click.option('--host', default="localhost", help='Host for the KV Store server.')
@click.option('--port', default=6666, type=int, help='Port for the KV Store server.')
def get_all_internal_keys(host, port):
    """Retrieves all keys and their values from the internal store."""
    with Pyro4.Proxy(f"PYRO:key_value_store@{host}:{port}") as proxy:
        keys_values = proxy.get_all_internal_keys()
        click.echo("Internal keys and their values:")
        for key, value in keys_values.items():
            click.echo(f"{key}: {value}")


@cli.command(name="list-pipelines")
@click.option('--host', default="localhost", help='Host for the KV Store server.')
@click.option('--port', default=6666, type=int, help='Port for the KV Store server.')
def list_pipelines(host, port):
    """Lists all pipelines."""
    with Pyro4.Proxy(f"PYRO:key_value_store@{host}:{port}") as proxy:
        pipelines = proxy.list_pipelines()
        click.echo("Pipelines:")
        for pipeline in pipelines:
            click.echo(f"- {pipeline}")


@cli.command(name="get-pipeline")
@click.argument('pipeline_id')
@click.option('--host', default="localhost", help='Host for the KV Store server.')
@click.option('--port', default=6666, type=int, help='Port for the KV Store server.')
def get_pipeline(pipeline_id, host, port):
    """Retrieves a specific pipeline by its ID."""
    with Pyro4.Proxy(f"PYRO:key_value_store@{host}:{port}") as proxy:
        pipeline = proxy.get_pipeline(pipeline_id)
        if pipeline:
            click.echo(f"Pipeline '{pipeline_id}': {pipeline}")
        else:
            click.echo(f"Pipeline '{pipeline_id}' not found.")


@cli.command(name="add-update-path")
@click.argument('label')
@click.argument('env')
@click.argument('system')
@click.argument('path')
@click.option('--host', default="localhost", help='Host for the KV Store server.')
@click.option('--port', default=6666, type=int, help='Port for the KV Store server.')
def add_update_path(host, port, label, env, system, path):
    """Adds or updates a path for a given label, environment, and system."""
    with Pyro4.Proxy(f"PYRO:key_value_store@{host}:{port}") as proxy:
        proxy.add_or_update_path(label, env, system, path)
        click.echo(f"Path for '{label}' in {env}/{system} updated to: {path}")


@cli.command(name="get-path")
@click.argument('label')
@click.argument('env')
@click.argument('system')
@click.option('--host', default="localhost", help='Host for the KV Store server.')
@click.option('--port', default=6666, type=int, help='Port for the KV Store server.')
def get_path(host, port, label, env, system):
    """Retrieves a specific path for a given label, environment, and system."""
    with Pyro4.Proxy(f"PYRO:key_value_store@{host}:{port}") as proxy:
        path = proxy.get_path(label, env, system)
        if path:
            click.echo(f"Path for '{label}' in {env}/{system}: {path}")
        else:
            click.echo(f"No path found for '{label}' in {env}/{system}")


@cli.command(name="update-paths-object")
@click.argument('label')
@click.argument('new_paths', type=click.File('r'))
@click.option('--host', default="localhost", help='Host for the KV Store server.')
@click.option('--port', default=6666, type=int, help='Port for the KV Store server.')
def update_paths_object(host, port, label, new_paths):
    """Updates the entire paths object for a given label."""
    paths = click.format_filename(new_paths)
    with Pyro4.Proxy(f"PYRO:key_value_store@{host}:{port}") as proxy:
        proxy.update_paths_object(label, paths)
        click.echo(f"Paths object for '{label}' updated.")


@cli.command(name="get-all-paths")
@click.option('--host', default="localhost", help='Host for the KV Store server.')
@click.option('--port', default=6666, type=int, help='Port for the KV Store server.')
def get_all_paths(host, port):
    """Retrieves all paths."""
    with Pyro4.Proxy(f"PYRO:key_value_store@{host}:{port}") as proxy:
        paths = proxy.get_all_paths()
        click.echo("All paths:")
        for label, env_paths in paths.items():
            click.echo(f"{label}:")
            for env, system_paths in env_paths.items():
                for system, path in system_paths.items():
                    click.echo(f"  {env}/{system}: {path}")


if __name__ == "__main__":
    cli()

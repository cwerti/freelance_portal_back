import os
import pathlib
import sys

import mako.template
import sqlalchemy.schema
from alembic import context, util
from alembic.operations.ops import MigrationScript
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import engine_from_config, pool

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
# without this flag, raises internal " KeyError: 'formatters'" error via CI run
if os.environ.get("TEST_RUN_ENVIRON", "LOCAL") != "CI":
    # Interpret the config file for Python logging.
    # This line sets up loggers basically.
    # fileConfig(config.config_file_name)
    pass

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "app/"))
from models.core import Base

target_metadata = Base.metadata

IGNORE_TABLES = ["alembic_version", "smev_connector.messages", "relevant_search"]
IGNORE_SCHEMAS = ["relevant_search"]


def include_object(object: sqlalchemy.schema.Table | sqlalchemy.schema.Column, name, type_, reflected, compare_to):
    """
    Should you include this table or not?
    """
    # excludes with matched schema name, not only table itself
    if isinstance(object, sqlalchemy.schema.Table):
        if object.fullname in IGNORE_TABLES or object.schema in IGNORE_SCHEMAS:
            return False
    elif object.table in IGNORE_TABLES:
        return False

    if type_ == "table" and (name in IGNORE_TABLES or object.info.get("skip_autogenerate", False)):
        return False

    elif type_ == "column" and object.info.get("skip_autogenerate", False):
        return False

    return True


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_version_path(script: ScriptDirectory, revid: str, message: str) -> str:
    """
    Get path for the creating revision version.

    It is a snippet from alembic package, cause alembic does not have separate function for generating the path
    """
    head = "head"

    with script._catch_revision_errors(
        multiple_heads=(
            "Multiple heads are present; please specify the head "
            "revision on which the new revision should be based, "
            "or perform a merge."
        )
    ):
        heads = script.revision_map.get_revisions(head)

    if len(set(heads)) != len(heads):
        raise util.CommandError("Duplicate head revisions specified")

    if len(script._version_locations) > 1:
        for head in heads:
            if head is not None:
                version_path = os.path.dirname(head.path)
                break
        else:
            raise util.CommandError("Multiple version locations present, " "please specify --version-path")
    else:
        version_path = script.versions

    norm_path = os.path.normpath(os.path.abspath(version_path))
    for vers_path in script._version_locations:
        if os.path.normpath(vers_path) == norm_path:
            break
    else:
        raise util.CommandError("Path %s is not represented in current " "version locations" % version_path)

    if script.version_locations:
        script._ensure_directory(version_path)

    create_date = script._generate_create_date()
    path = script._rev_path(version_path, revid, message, create_date)

    return path


def data_migration(context: MigrationContext, revision, directives: list[MigrationScript]):
    """
    Generate data migration script from template if `data_migration` flag is specified.

    Data migration file is generated from /versions/data_versions/data_script.py.mako file
    which is default for creating migration containing data only changes
    """
    SUBDIRECTORY_NAME = "./data_versions"
    DATA_SCRIPT_NAME = "data_script.py.mako"

    args = context.environment_context.get_x_argument(as_dictionary=True)
    if args.get("data_migration"):
        directive = directives[0]
        script: ScriptDirectory = context.script

        migration_path = pathlib.Path(get_version_path(script, directive.rev_id, directive.message))
        data_versions_dir = migration_path.parent / SUBDIRECTORY_NAME
        data_migration_path = data_versions_dir / f"data_{migration_path.name}"
        # на этого лог опирается admin-cli
        print(f"Generating {data_migration_path} done")

        create_date = script._generate_create_date()

        data_script_template_path = data_versions_dir / DATA_SCRIPT_NAME
        with open(data_script_template_path) as data_script_file:
            data_script_template = mako.template.Template(data_script_file.read())
            built_data_script = data_script_template.render(
                message=directive.message, create_date=create_date, revision=revision
            )
            with open(data_migration_path, "w") as result_file:
                result_file.write(built_data_script)
    else:
        print(
            "data migration is not created. if you want to create separate data migration,"
            ' please specify "-x data_migration=True" option'
        )


def run_migrations_offline():
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        process_revision_directives=data_migration,
        include_object=include_object,
        version_table_schema="public",
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            process_revision_directives=data_migration,
            version_table_schema="public",
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

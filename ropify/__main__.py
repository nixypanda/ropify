from pathlib import Path
from typing import Callable

import click
from click.decorators import FC
from rope.base.fscommands import FileSystemCommands
from rope.base.libutils import path_to_resource
from rope.base.project import Project
from rope.base.pynames import ImportedModule
from rope.base.resources import File, Folder
from rope.refactor.move import MoveModule, create_move


@click.group()
def cli() -> None:
    pass


def project_option() -> Callable[[FC], FC]:
    return click.option(
        "--project",
        type=click.Path(exists=True, file_okay=False, path_type=Path),
        default=Path.cwd(),
        help="The project to work on.",
    )


def ropefolder_option() -> Callable[[FC], FC]:
    return click.option(
        "--ropefolder",
        type=click.STRING,
        help="The location of the rope folder relative to the project root.",
    )


def _create_rope_project(project: Path, ropefolder: str | None) -> Project:
    # Git fscommands complain when files are untracked, so we use the default instead
    if ropefolder is not None:
        return Project(project, fscommands=FileSystemCommands(), ropefolder=ropefolder)
    else:
        return Project(project, fscommands=FileSystemCommands())


@cli.command()
@click.argument("resource", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("destination", type=click.Path(exists=True, file_okay=False, path_type=Path))
@project_option()
@ropefolder_option()
def move_module(resource: Path, destination: Path, project: Path, ropefolder: str | None) -> None:
    """
    Move a module to another package.

    \b
    RESOURCE: The path to the module file.
    DESTINATION: The path to the destination folder.
    """

    rope_project = _create_rope_project(project, ropefolder)
    m_source = path_to_resource(rope_project, resource)
    m_dest = path_to_resource(rope_project, destination)
    assert isinstance(m_source, File) and isinstance(m_dest, Folder)

    move = create_move(rope_project, m_source)
    assert isinstance(move, MoveModule)
    click.echo(f"Moving definition of `{move.old_name}`")
    click.echo(f"Definition is currently at: {m_source.path}")

    changes = move.get_changes(m_dest)
    rope_project.do(changes)
    click.echo(f"Module `{m_source.path}` moved to: {m_dest.path}")


@cli.command()
@click.argument("resource", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("offset", type=click.IntRange(min=0))
@click.argument("destination", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@project_option()
@ropefolder_option()
def move_symbol_offset(
    resource: Path, offset: int, destination: Path, project: Path, ropefolder: str | None
) -> None:
    """
    Move the definition of a global symbol to another file.

    \b
    RESOURCE: The path to the file containing the symbol to move.
    OFFSET: The byte offset of the symbol within the file.
    """
    move_with_offset(resource, destination, offset, project, ropefolder)


def move_with_offset(
    source: Path, destination: Path, offset: int, project: Path, ropefolder: str | None
) -> None:
    rope_project = _create_rope_project(project, ropefolder)

    f_source = path_to_resource(rope_project, source)
    f_dest = path_to_resource(rope_project, destination)
    assert isinstance(f_source, File) and isinstance(f_dest, File)
    move = create_move(rope_project, f_source, offset)

    symbol_name = move.old_name
    click.echo(f"Moving definition of `{symbol_name}`")

    if isinstance(move.old_pyname, ImportedModule):
        click.echo("ERROR: Cannot move modules, use `ropify move-module` instead.")
        exit(1)

    symbol_def_source = move.old_pyname.get_definition_location()[0].get_resource()
    click.echo(f"Definition is currently at: {symbol_def_source.path}")

    changes = move.get_changes(f_dest)
    rope_project.do(changes)
    click.echo(f"Definition of `{symbol_name}` moved to: {f_dest.path}")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()

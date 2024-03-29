from os import popen
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
from rope.refactor.occurrences import Finder, Occurrence
from rope.refactor.rename import Rename


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
@click.argument("source_file_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("dest_folder_path", type=click.Path(exists=True, file_okay=False, path_type=Path))
@project_option()
@ropefolder_option()
def move_module(
    source_file_path: Path, dest_folder_path: Path, project: Path, ropefolder: str | None
) -> None:
    """
    Move a module.

    \b
    SOURCE_FILE_PATH: The path to the module file.
    DEST_FOLDER_PATH: The destination folder path.
    """
    rope_project = _create_rope_project(project, ropefolder)
    source_file = path_to_resource(rope_project, source_file_path)
    dest_folder = path_to_resource(rope_project, dest_folder_path)
    assert isinstance(source_file, File) and isinstance(dest_folder, Folder)

    move = create_move(rope_project, source_file)
    assert isinstance(move, MoveModule)
    click.echo(f"Moving definition of `{move.old_name}`")
    click.echo(f"Definition is currently at: {source_file.path}")

    changes = move.get_changes(dest_folder)
    rope_project.do(changes)
    click.echo(f"Module `{source_file.path}` moved to: {dest_folder.path}")


@cli.command()
@click.argument("module_file_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("new_name", type=click.STRING)
@project_option()
@ropefolder_option()
def rename_module(
    module_file_path: Path, new_name: str, project: Path, ropefolder: str | None
) -> None:
    """
    Rename a module.

    \b
    MODULE_FILE_PATH: The path to the module file.
    NEW_NAME: The new name of the module.
    """
    rope_project = _create_rope_project(project, ropefolder)
    source_module = path_to_resource(rope_project, module_file_path)
    changes = Rename(rope_project, source_module).get_changes(new_name)
    rope_project.do(changes)


@cli.command()
@click.argument("symbol_s_filepath", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("offset", type=click.IntRange(min=0))
@click.argument(
    "destination_file_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@project_option()
@ropefolder_option()
def move_symbol_by_offset(
    symbol_s_filepath: Path,
    offset: int,
    destination_file_path: Path,
    project: Path,
    ropefolder: str | None,
) -> None:
    """
    Move the definition of a global symbol to another file.

    \b
    RESOURCE: The path to the file containing the symbol to move.
    OFFSET: The byte offset of the symbol within the file.
    """
    rope_project = _create_rope_project(project, ropefolder)

    source_file = path_to_resource(rope_project, symbol_s_filepath)
    dest_file = path_to_resource(rope_project, destination_file_path)
    assert isinstance(source_file, File) and isinstance(dest_file, File)
    move_with_offset(source_file, dest_file, offset, rope_project)


def find_definition_in_resource(name: str, resource: File, project: Project) -> Occurrence:
    finder = Finder(project, name)
    return next(
        occ
        for occ in finder.find_occurrences(resource=resource)
        if occ.is_defined() or occ.is_written()
    )


@cli.command()
@click.argument("symbol_s_filepath", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("name", type=click.STRING)
@click.argument(
    "destination_file_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@project_option()
@ropefolder_option()
def move_symbol_by_name(
    symbol_s_filepath: Path,
    name: str,
    destination_file_path: Path,
    project: Path,
    ropefolder: str | None,
) -> None:
    """
    Move the definition of a global symbol to another file.

    \b
    RESOURCE: The path to the file containing the symbol to move.
    OFFSET: The byte offset of the symbol within the file.
    """
    rope_project = _create_rope_project(project, ropefolder)

    source_file = path_to_resource(rope_project, symbol_s_filepath)
    dest_file = path_to_resource(rope_project, destination_file_path)
    assert isinstance(source_file, File) and isinstance(dest_file, File)

    definition_occurrence = find_definition_in_resource(name, source_file, rope_project)
    move_with_offset(source_file, dest_file, definition_occurrence.offset, rope_project)


def move_with_offset(source: File, destination: File, offset: int, rope_project: Project) -> None:
    # f_source = path_to_resource(rope_project, source)
    # f_dest = path_to_resource(rope_project, destination)
    # assert isinstance(f_source, File) and isinstance(f_dest, File)
    move = create_move(rope_project, source, offset)

    symbol_name = move.old_name
    click.echo(f"Moving definition of `{symbol_name}`")

    if isinstance(move.old_pyname, ImportedModule):
        click.echo("ERROR: Cannot move modules, use `ropify move-module` instead.")
        exit(1)

    symbol_def_source = move.old_pyname.get_definition_location()[0].get_resource()
    click.echo(f"Definition is currently at: {symbol_def_source.path}")

    changes = move.get_changes(destination)
    rope_project.do(changes)
    click.echo(f"Definition of `{symbol_name}` moved to: {destination.path}")


@cli.command()
@click.argument("module", type=click.STRING)
@click.argument("symbol", type=click.STRING)
def fixup_imports(module: str, symbol: str):
    pattern = f"{module}.{symbol}"
    matches = popen(f"rg --files-with-matches {pattern}").read().splitlines()

    for match in matches:
        prepend_from_import_to_file(match, f"from {module} import {symbol}")
        replace_fully_qualified_name_with_symbol(match, pattern, symbol)


def prepend_from_import_to_file(filename, string):
    with open(filename) as file:
        lines = file.readlines()

    lines.insert(0, string + "\n")

    with open(filename, "w") as file:
        file.writelines(lines)


def replace_fully_qualified_name_with_symbol(filename, old_string, new_string):
    with open(filename) as file:
        filedata = file.read()

    new_filedata = filedata.replace(old_string, new_string)

    with open(filename, "w") as file:
        file.write(new_filedata)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()

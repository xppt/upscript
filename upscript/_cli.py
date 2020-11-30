import argparse
import os
import sys
import venv
from typing import Optional, List

from upscript._state import write_state
from upscript._scripts import refresh_entry_points
from upscript._update import refresh_packages, UpdateError
from upscript._utils import normalize_package_name, echo

venv_subdir = '.files'
default_index = 'https://pypi.org/simple'


def cli_main(args_list: Optional[List[str]] = None) -> None:
    if args_list is None:
        args_list = sys.argv[1:]

    if len(args_list) < 1 or args_list[0] != 'fetch':
        echo('Usage: upscript fetch <name> <destination-dir> [--index-url <index-url>]')
        sys.exit(10)

    args_list = args_list[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument('name')
    parser.add_argument('destination')
    parser.add_argument('--index-url', default=default_index)
    args = parser.parse_args(args_list)

    fetch(args.name, args.destination, args.index_url)


def fetch(name: str, destination: str, index_url: str = default_index) -> None:
    venv_dir = os.path.join(destination, venv_subdir)

    package = normalize_package_name(name)
    if package is None:
        echo('invalid package name', name)
        sys.exit(11)

    venv_builder = venv.EnvBuilder(with_pip=True)
    venv_builder.create(venv_dir)

    write_state({
        'version': 1,
        'index_url': index_url,
        'client_packages': [{'name': package}],
        'entry_points': [],
        'index_hashes': {},
    }, venv_dir)

    try:
        refresh_packages(venv_dir)
    except UpdateError as e:
        echo('unable to install:', *e.args)
        sys.exit(12)

    refresh_entry_points(destination, venv_dir)

import distutils.sysconfig
import os
from configparser import RawConfigParser
from typing import Sequence, Tuple

import distlib.database
import distlib.scripts

from upscript._state import read_state, write_state
from upscript._utils import venv_rel_bin, echo


def refresh_entry_points(ep_dir: str, venv_path: str) -> None:
    state = read_state(venv_path)
    packages = state['client_packages']

    new_eps = [
        {
            'package': package['name'],
            'name': ep_name,
            'callable': ep_callable,
        }
        for package in packages
        for ep_name, ep_callable in get_package_entry_points(package['name'], venv_path)
    ]

    for old_ep_name in new_eps:
        write_distrib_entry_point(old_ep_name['name'], ep_dir, venv_path)

    _cleanup_old_entry_points(ep_dir, new_eps, state['entry_points'])

    state['entry_points'] = new_eps
    write_state(state, venv_path)


def get_package_entry_points(package: str, prefix: str) -> Sequence[Tuple[str, str]]:
    libs_path = distutils.sysconfig.get_python_lib(prefix=prefix)

    distrib = distlib.database.DistributionPath([libs_path]).get_distribution(package)
    assert distrib is not None, 'package is not installed'

    entry_points_config = os.path.join(distrib.path, f'entry_points.txt')

    if not os.path.exists(entry_points_config):
        return []

    parser = RawConfigParser()
    parser.read(entry_points_config)
    if not parser.has_section('console_scripts'):
        return []

    return [
        (key, parser.get('console_scripts', key))
        for key in parser.options('console_scripts')
    ]


def write_distrib_entry_point(name: str, ep_dir: str, venv_path: str):
    maker = distlib.scripts.ScriptMaker(
        source_dir=None,
        target_dir=ep_dir,
    )
    maker.variants = {''}
    maker.executable = os.path.join(
        venv_path, venv_rel_bin(),
        'python' + distutils.sysconfig.get_config_var('EXE'),
    )
    maker.make(f'{name} = upscript._internal_api:client_entry_point')


def _cleanup_old_entry_points(ep_dir, new_eps, old_eps):
    old_ep_names = (ep['name'] for ep in old_eps)
    new_ep_names = {ep['name'] for ep in new_eps}
    for old_ep_name in old_ep_names:
        if old_ep_name in new_ep_names:
            continue

        path = os.path.join(ep_dir, old_ep_name + distutils.sysconfig.get_config_var('EXE'))

        try:
            os.unlink(path)
        except OSError:
            echo('warning: unable to unlink', path)

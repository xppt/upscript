import importlib
import os
import sys
from typing import Any

from upscript._utils import echo
from upscript._state import read_state
from upscript._scripts import refresh_entry_points
from upscript._update import refresh_packages, UpdateError


def client_entry_point() -> Any:
    venv_dir = sys.prefix

    entry_point_name, _ = os.path.splitext(os.path.basename(sys.argv[0]))

    if os.getenv('UPSCRIPT_AUTO_UPDATE', '1') == '1':
        _check_updates(venv_dir)

    state = read_state(venv_dir)
    entry_point = next(
        (ep for ep in state['entry_points'] if ep['name'] == entry_point_name),
        None
    )
    if entry_point is None:
        echo('unable to find entry point', entry_point_name)
        sys.exit(11)

    module_name, callable_name = entry_point['callable'].split(':', 1)
    module = importlib.import_module(module_name)

    return getattr(module, callable_name)()


def _check_updates(venv_dir: str) -> None:
    try:
        refresh_packages_result = refresh_packages(venv_dir)
        if refresh_packages_result.updated_client or refresh_packages_result.updated_self:
            refresh_entry_points(os.path.join(venv_dir, '..'), venv_dir)
    except UpdateError as e:
        echo('warning: update failed:', *e.args)

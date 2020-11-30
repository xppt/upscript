import sys
from functools import partial
from typing import Optional, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    import subprocess

echo = partial(print, file=sys.stderr)


def normalize_package_name(name: str) -> Optional[str]:
    import re

    # see pep503
    result = re.sub(r'[-_.]+', '-', name).lower()

    if re.search(r'[^-a-z0-9]', result) is not None:
        return None

    return result


def venv_rel_bin() -> str:
    # see `venv.EnvBuilder.ensure_directories`
    if sys.platform == 'win32':
        bin_path = 'Scripts'
    else:
        bin_path = 'bin'

    return bin_path


def run_python_text_mode(args: Sequence[str], **kwargs) -> 'subprocess.CompletedProcess':
    import subprocess
    import os

    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    return subprocess.run(
        args, env=env, encoding=env['PYTHONIOENCODING'], **kwargs,
    )

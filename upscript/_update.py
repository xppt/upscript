import hashlib
import os
import subprocess
import textwrap
from typing import NamedTuple, Optional
from urllib.parse import quote, urljoin
from urllib.request import urlopen

from upscript._state import State, read_state, write_state
from upscript._utils import venv_rel_bin, echo, run_python_text_mode


class RefreshPackagesResult(NamedTuple):
    updated_self: bool
    updated_client: bool


class UpdateError(Exception):
    pass


def refresh_packages(venv_dir: str) -> RefreshPackagesResult:
    """
    :raises UpdateError
    """

    state = read_state(venv_dir)

    updated_self = updated_client = False

    updated_self = update_package_maybe(
        venv_dir, state, 'upscript',
        source=os.getenv('UPSCRIPT_SELF_INSTALL_SOURCE'),
    )

    for package in state['client_packages']:
        if update_package_maybe(venv_dir, state, package['name']):
            updated_client = True

    write_state(state, venv_dir)

    return RefreshPackagesResult(updated_self, updated_client)


def update_package_maybe(
        venv_dir: str, state: State, package: str, source: Optional[str] = None,
) -> bool:

    index_url = state['index_url']
    index_hash = None

    if source is None:
        index_hash = get_index_hash(package, index_url)
        if index_hash == state['index_hashes'].get(package):
            return False

    result = do_update_package(venv_dir, package, index_url, source)

    if index_hash is not None:
        state['index_hashes'][package] = index_hash

    return result


def get_index_hash(package: str, index_url: str) -> str:
    package_url = urljoin(index_url, f'{quote(package)}/')

    timeout = float(os.getenv('UPSCRIPT_UPDATE_TIMEOUT', '15'))

    try:
        with urlopen(package_url, timeout=timeout) as package_resp:
            assert package_resp.status == 200
            body = package_resp.read()
    except Exception as e:
        raise UpdateError(f'unable to fetch {package} from {index_url}') from e

    body_hash = hashlib.sha1(body).hexdigest()
    return body_hash


def do_update_package(
        venv_dir: str, package: str, index_url: str, source: Optional[str] = None,
) -> bool:

    import distutils.sysconfig
    import distlib.database

    if source is None:
        source = package

    libs_path = distutils.sysconfig.get_python_lib(prefix=venv_dir)

    distrib_before = distlib.database.DistributionPath([libs_path]).get_distribution(package)
    version_before = distrib_before.version if distrib_before is not None else None

    pip_args = ('install', '--upgrade', '--index-url', index_url, '--', source)

    try:
        run_python_text_mode(
            (os.path.join(venv_dir, venv_rel_bin(), 'python'), '-Im', 'pip') + pip_args,
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        echo(e)
        if e.stdout:
            echo('\nstdout:')
            echo(textwrap.indent(e.stdout, '\t'))
        if e.stderr:
            echo('\nstderr:')
            echo(textwrap.indent(e.stderr, '\t'))
        raise UpdateError(f'unable to install {package}') from e

    distrib_after = distlib.database.DistributionPath([libs_path]).get_distribution(package)
    assert distrib_after is not None

    return distrib_after.version != version_before

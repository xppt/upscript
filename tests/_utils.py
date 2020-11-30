import os
import subprocess
import sys
import wsgiref.simple_server
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from types import SimpleNamespace
from typing import Mapping, Optional, List

import pypiserver


@contextmanager
def run_index_server(packages_dir: str):
    ctxt = wsgiref.simple_server.make_server(
        host='127.0.0.1',
        port=0,
        app=_make_index_server(packages_dir),
    )
    with ctxt as server:
        result = SimpleNamespace(server_port=server.server_port)

        thread = Thread(target=server.serve_forever)
        thread.start()

        try:
            yield result
        finally:
            server.shutdown()
            thread.join()


@contextmanager
def prepare_distribution_source(
        files: Mapping[str, str],
        distrib_name: str, version: str, packages: List[str],
        setup_kwargs: Optional[dict] = None,
) -> None:

    with TemporaryDirectory() as temp_dir:
        for filename, body in files.items():
            path = Path(temp_dir) / filename
            path.absolute().parent.mkdir(parents=True, exist_ok=True)
            with open(str(path), 'w', encoding='utf-8') as file:
                file.write(body)

        if setup_kwargs is None:
            setup_kwargs = {}

        kwargs = {
            'name': distrib_name,
            'version': version,
            'packages': packages,
            **setup_kwargs,
        }

        setup_py_path = os.path.join(temp_dir, 'setup.py')
        with open(setup_py_path, 'w', encoding='utf-8') as file:
            file.write((
                f'from setuptools import setup\n'
                f'setup(**{kwargs!r})\n'
            ))

        yield temp_dir


def build_wheel(source_dir: str, destination_dir: str) -> None:
    subprocess.run(
        (
            sys.executable, '-Im', 'pip', 'wheel',
            '-w', destination_dir,
            source_dir,
        ),
        check=True,
    )


def _make_index_server(packages_dir: str):
    # noinspection PyTypeChecker
    return pypiserver.app(
        root=[packages_dir],
    )

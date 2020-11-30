import os
import subprocess
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from tests._utils import run_index_server, prepare_distribution_source, build_wheel
from upscript._cli import cli_main

SOURCE_ROOT = str(Path(__file__).absolute().parent.parent)


class UpscriptTestCase(TestCase):
    def setUp(self) -> None:
        self._context = ExitStack()
        self.addCleanup(self._context.close)

        self._dist_dir = self._context.enter_context(TemporaryDirectory())

        index_server = self._context.enter_context(run_index_server(self._dist_dir))
        self._index_url = f'http://localhost:{index_server.server_port}/simple/'

    def test_upscript(self):
        build_wheel(SOURCE_ROOT, self._dist_dir)
        self._build_test_wheel('1.0')

        with TemporaryDirectory() as temp_dir:
            install_dir = os.path.join(temp_dir, 'install')

            cli_main([
                'fetch',
                '--index-url', self._index_url,
                'upscript-test-package', install_dir,
            ])

            result = subprocess.run(
                (os.path.join(install_dir, 'script')),
                check=True, stdout=subprocess.PIPE,
            )
            self.assertEqual(result.stdout.decode('ascii').strip(), '1.0')

            self._build_test_wheel('2.0')

            result = subprocess.run(
                (os.path.join(install_dir, 'script')),
                check=True, stdout=subprocess.PIPE,
            )
            self.assertEqual(result.stdout.decode('ascii').strip(), '2.0')

    def _build_test_wheel(self, version: str) -> None:
        with prepare_distribution_source(
            files={'package/__init__.py': f'def main(): print({version!r})'},
            distrib_name='upscript-test-package',
            version=version,
            packages=['package'],
            setup_kwargs={
                'entry_points': {
                    'console_scripts': ['script=package:main'],
                },
            },
        ) as wheel_source_dir:
            build_wheel(wheel_source_dir, self._dist_dir)

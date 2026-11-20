"""The build patch must validate both inputs before writing any file."""
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as N
import unittest
from unittest.mock import patch
from test_offset_recovery import installer


class InstallerTests(unittest.TestCase):
    def run_install(self, bad_flow=False, bad_controller=False):
        with TemporaryDirectory() as temp:
            package = Path(temp) / 'music_assistant'
            controller = package / 'controllers/player_queues/controller.py'
            controller.parent.mkdir(parents=True)
            flow = package / 'controllers/streams/audio.py'
            flow.parent.mkdir(parents=True)
            source = 'class Controller:\n' + installer.ANCHOR + '\n    def play_index(self):\n        pass\n'
            flow_source = 'def stream():\n' + installer.FLOW_ANCHOR + '\n'
            controller.write_text(source)
            flow.write_text(flow_source)
            with patch.object(installer.importlib.util, 'find_spec', return_value=N(origin=str(package / '__init__.py'))), patch.object(installer, 'EXPECTED_SOURCE_SHA256', 'bad' if bad_controller else hashlib.sha256(source.encode()).hexdigest()), patch.object(installer, 'FLOW_SOURCE_SHA256', 'bad' if bad_flow else hashlib.sha256(flow_source.encode()).hexdigest()):
                if bad_flow or bad_controller:
                    with self.assertRaises(RuntimeError):
                        installer.main()
                    self.assertEqual(controller.read_text(), source)
                    self.assertEqual(flow.read_text(), flow_source)
                    self.assertFalse(controller.with_name('alexa_recovery_timeline.py').exists())
                else:
                    installer.main()
                    self.assertIn('recover_alexa_flow', controller.read_text())
                    self.assertIn('remember_flow', flow.read_text())
                    self.assertTrue(controller.with_name('alexa_recovery_timeline.py').exists())

    def test_both_valid_inputs_install_hook_and_helper(self):
        self.run_install()

    def test_bad_flow_hash_writes_nothing(self):
        self.run_install(bad_flow=True)

    def test_bad_controller_hash_writes_nothing(self):
        self.run_install(bad_controller=True)

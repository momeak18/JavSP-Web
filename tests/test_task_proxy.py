import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from javsp_web import tasks


class TaskProxyTest(unittest.TestCase):
    def test_task_preserves_preset_proxy_unless_nonempty_override(self):
        for override in (None, '', 'http://override.example:7890'):
            for preset_proxy in (None, 'socks5://preset.example:1080'):
                with self.subTest(override=override, preset_proxy=preset_proxy), tempfile.TemporaryDirectory() as directory:
                    config = {'network': {'proxy_server': preset_proxy}}
                    with patch.dict(os.environ, {}, clear=True), patch.object(tasks, 'DATA_DIR', Path(directory)), patch.object(tasks, '_preset_config_data', return_value=(config, {'name': 'test'})):
                        if override is not None:
                            os.environ['JAVSP_PROXY_SERVER'] = override
                        path, _ = tasks._build_task_config('test', '/video/115av', 'test')
                        actual = yaml.safe_load(path.read_text())
                    self.assertEqual(actual['network']['proxy_server'], override or preset_proxy)
                    self.assertTrue(actual['summarizer']['copy_files'])


if __name__ == '__main__':
    unittest.main()

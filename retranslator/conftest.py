import pytest
import json
import os

from xprocess import ProcessStarter


base_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def retranslator_server(xprocess):
    class Starter(ProcessStarter):
        pattern = "Serving"
        args = ['python', os.path.join(base_dir, "main.py")]
    xprocess.ensure("retranslator_server", Starter)

    return True


@pytest.fixture
def base_config():
    with open(os.path.join(base_dir, "config.cfg"), 'r') as json_file:
        config = json.loads(json_file.read())
    return config

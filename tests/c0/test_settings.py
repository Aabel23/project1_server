from pathlib import Path

import pytest

from server.config.settings import load_settings


EXAMPLE = Path(__file__).resolve().parents[2] / "server.example.toml"


def test_template_and_defaults(tmp_path):
    config = load_settings(EXAMPLE)
    assert config["db"] == {"path": "var/flexmix.db", "timeout": 10}
    assert config["protocol"]["poll_seconds"] == 25
    minimal = tmp_path / "minimal.toml"
    minimal.write_text(
        '[db]\npath="test.db"\n[net]\ncert_file="cert"\nkey_file="key"\n'
        'ca_file="ca"\nhostname="localhost"\n[fm1]\naudience="test"\n',
        encoding="utf-8",
    )
    assert load_settings(minimal)["net"]["agent_threads"] == 18


@pytest.mark.parametrize("old,new", [
    ('path = "var/flexmix.db"', ''),
    ('hostname = "flexmix.local"', 'hostname = ""'),
    ('hostname = "flexmix.local"', 'hostname = "example.com:443"'),
    ('hostname = "flexmix.local"', 'hostname = "example.com/path"'),
    ('path = "var/flexmix.db"', 'path = ":memory:"'),
    ('audience = "flexmix-dev"', 'audience = "../other"'),
    ('admin_port = 443', 'admin_port = 8443'),
    ('agent_port = 8443', 'agent_port = 65536'),
    ('agent_threads = 18', 'agent_threads = true'),
    ('timeout = 60', 'timeout = 0'),
    ('poll_seconds = 25', 'poll_seconds = 26'),
    ('timeout = 60', 'timeout = 25'),
    ('ledger_days = 30', 'ledger_days = -1'),
    ('hostname = "flexmix.local"', 'hostname = "x"\nextra = 2'),
    ('[db]', '[dbb]'),
])
def test_invalid_config_fails(tmp_path, old, new):
    path = tmp_path / "invalid.toml"
    path.write_text(EXAMPLE.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")
    with pytest.raises(ValueError):
        load_settings(path)


@pytest.mark.parametrize("hostname", ["192.168.1.10", "::1", "flexmix.local", "localhost"])
def test_valid_network_hostnames(tmp_path, hostname):
    path = tmp_path / "hostname.toml"
    path.write_text(EXAMPLE.read_text(encoding="utf-8").replace("flexmix.local", hostname), encoding="utf-8")
    assert load_settings(path)["net"]["hostname"] == hostname

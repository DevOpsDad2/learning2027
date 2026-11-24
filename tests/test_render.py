"""Basic checks that the sample data renders cleanly.

Run from the repo root:  python -m unittest -v
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import render  # noqa: E402


class FilterTests(unittest.TestCase):
    def test_ipv4_address(self):
        self.assertEqual(render.ipv4_address("10.0.12.1/30"), "10.0.12.1")

    def test_ipv4_netmask(self):
        self.assertEqual(render.ipv4_netmask("10.0.12.1/30"), "255.255.255.252")
        self.assertEqual(render.ipv4_netmask("1.1.1.1/32"), "255.255.255.255")


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.env = render.build_env()
        self.global_vars = render.load_yaml(render.DATA_DIR / "global.yaml")
        self.global_vars["admin_secret"] = "test-secret"

    def render(self, host):
        host_vars = render.load_host(render.DATA_DIR / "hosts" / f"{host}.yaml", self.global_vars)
        return render.render_host(self.env, host_vars)

    def test_every_host_renders(self):
        for host_file in sorted((render.DATA_DIR / "hosts").glob("*.yaml")):
            with self.subTest(host=host_file.stem):
                config = self.render(host_file.stem)
                self.assertTrue(config.rstrip().endswith("end"))

    def test_r1_interface_and_ospf(self):
        config = self.render("r1")
        self.assertIn("hostname R1", config)
        self.assertIn(" ip address 10.0.12.1 255.255.255.252", config)
        self.assertIn(" ip ospf 1 area 0", config)
        self.assertIn(" router-id 1.1.1.1", config)

    def test_mgmt_interface_not_in_ospf(self):
        config = self.render("r1")
        mgmt_block = config.split("interface GigabitEthernet0/0")[1].split("!")[0]
        self.assertNotIn("ip ospf", mgmt_block)

    def test_r2_passive_interface(self):
        self.assertIn(" passive-interface GigabitEthernet0/2", self.render("r2"))

    def test_sw1_vlans_and_shutdown(self):
        config = self.render("sw1")
        self.assertIn("vlan 10\n name USERS", config)
        self.assertIn(" switchport access vlan 99", config)
        spare = config.split("interface GigabitEthernet0/3")[1].split("!")[0]
        self.assertIn(" shutdown", spare)
        self.assertNotIn("no shutdown", spare)

    def test_bad_ip_is_rejected(self):
        bad = {"hostname": "X", "role": "router", "interfaces": [{"name": "Gi0/1", "ipv4": "10.0.0.300/24"}]}
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir) / "bad.yaml"
            tmp.write_text(render.yaml.safe_dump(bad))
            with self.assertRaises(ValueError):
                render.load_host(tmp, self.global_vars)


if __name__ == "__main__":
    unittest.main()

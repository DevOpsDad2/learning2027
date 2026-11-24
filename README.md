# learning2027

Python and network automation.

A hands-on project for learning to manage Cisco network configs as code:
the network is described in **YAML**, configs are generated from **Jinja2 templates**
by a small **Python** script, and the result is loaded onto a lab running in
CML, GNS3 or EVE-NG.

```
data/global.yaml ─┐
                  ├─► scripts/render.py ─► templates/ios/<role>.j2 ─► output/<host>.cfg ─► lab
data/hosts/*.yaml ┘
```

## Layout

| Path | What it is |
|------|------------|
| `lab/README.md` | The lab topology (2 routers, 1 switch) and how to build it |
| `data/global.yaml` | Settings every device shares: domain, DNS, NTP, syslog, banner |
| `data/hosts/*.yaml` | One file per device: interfaces, OSPF, VLANs |
| `templates/ios/_base.j2` | Common IOS config included by every role |
| `templates/ios/router.j2` | Router config: interfaces + OSPF |
| `templates/ios/switch.j2` | Switch config: VLANs, access ports, mgmt SVI |
| `scripts/render.py` | Merges the YAML, renders templates, writes `output/` |
| `tests/` | Checks that the sample data renders correctly |

## Quick start

```bash
git clone https://github.com/DevOpsDad2/learning2027.git
cd learning2027
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m unittest -v                # 8 tests should pass
python scripts/render.py --host r1 --stdout
```

Then follow [`lab/README.md`](lab/README.md) to build the lab and load the configs.

`output/` is git-ignored because rendered configs contain the admin secret.
Set it with `export LAB_ADMIN_SECRET=...` before rendering; without it you get `CHANGE_ME`.

## Exercises

Try these in order. Each one is a change to YAML, a template, or both, followed by
`python scripts/render.py` and `python -m unittest`.

1. **Change data, not templates.** Change the banner, add a second NTP server. Re-render and diff.
2. **Add a device.** Create `data/hosts/r3.yaml` with a link to R2 and a Loopback 3.3.3.3/32.
   Add the link to R2's YAML too. No template changes should be needed.
3. **Add a feature.** Add an optional `snmp` section to `global.yaml` and render it in `_base.j2`
   only when it exists (`{% if snmp is defined %}`).
4. **Add a trunk.** Make SW1 Gi0/1 a trunk (`mode: trunk`) and give R2 subinterfaces.
   The switch template already handles `trunk`; the router template needs work.
5. **Write a test** in `tests/test_render.py` for whatever you added.
6. **Push configs with Python.** Install `netmiko` and write `scripts/deploy.py` to send
   `output/<host>.cfg` to a device over SSH. Check the current Netmiko docs for the API.

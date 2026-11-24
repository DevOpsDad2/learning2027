# Lab: 2 routers + 1 switch

A small Cisco IOS topology that works the same in **Cisco CML**, **GNS3** or **EVE-NG**.
The sample YAML in `data/hosts/` describes exactly this lab.

```
                 MGMT network 10.99.0.0/24  (Gi0/0 on every device)
        ┌──────────────────────┬──────────────────────┬──────────────────┐
        │ .11                  │ .12                  │ .21 (Vlan99)     │
   ┌────┴────┐  10.0.12.0/30  ┌┴────────┐            ┌┴────────┐
   │   R1    │ Gi0/1 ── Gi0/1 │   R2    │ Gi0/2 ──── │  SW1    │ Gi0/2 ── host (VLAN 10)
   │ Lo0     │  .1       .2   │ Lo0     │ 10.10.10.1 │ Gi0/1   │
   │ 1.1.1.1 │                │ 2.2.2.2 │   /24      │ VLAN 10 │
   └─────────┘                └─────────┘            └─────────┘
        └────────── OSPF area 0 (R1 ↔ R2) ───────────┘
```

| Device | Node type (verify in your platform) | Mgmt IP       | Other links |
|--------|-------------------------------------|---------------|-------------|
| R1     | IOSv router                         | 10.99.0.11/24 | Gi0/1 → R2 Gi0/1 |
| R2     | IOSv router                         | 10.99.0.12/24 | Gi0/1 → R1 Gi0/1, Gi0/2 → SW1 Gi0/1 |
| SW1    | IOSvL2 switch                       | 10.99.0.21/24 | Gi0/1 → R2 Gi0/2, Gi0/2 → test host |

## Build it

1. **Add the nodes.** CML ships IOSv and IOSvL2 node types. GNS3 and EVE-NG need you to supply
   the Cisco images yourself; image names and versions vary, so check your platform's docs.
2. **Wire the data links** as shown in the table.
3. **Wire management.** Connect every Gi0/0 to one unmanaged switch, then connect that switch to
   your platform's bridge to the host (CML: External Connector; GNS3: Cloud or NAT node;
   EVE-NG: a Cloud network). Your laptop needs to reach 10.99.0.0/24.
   - If your bridge network uses a different subnet, change the `ipv4` on each Gi0/0 / `mgmt`
     and the `dns_servers` / `ntp_servers` / `syslog_servers` / `gateway` values in `data/`.
     10.99.0.1 is assumed to be your host/gateway on that network.
4. **Optional:** add a small Linux node on SW1 Gi0/2 with 10.10.10.10/24, gateway 10.10.10.1.

## Load the configs

1. On your laptop, from the repo root:
   ```bash
   export LAB_ADMIN_SECRET='pick-a-lab-password'
   python scripts/render.py
   ```
2. Open each device's **console** and generate SSH keys first. IOS rejects `ip ssh version 2`
   until an RSA key exists:
   ```
   enable
   configure terminal
   hostname R1
   ip domain-name lab.local
   crypto key generate rsa modulus 2048
   ```
3. Paste the matching `output/<host>.cfg` into configuration mode, then `end` and
   `write memory`.

## Check it worked

```
R1# show ip ospf neighbor          ! R2 (2.2.2.2) should be FULL
R1# show ip route ospf             ! 2.2.2.2/32 and 10.10.10.0/24 learned from R2
R1# ping 2.2.2.2 source Loopback0
SW1# show vlan brief               ! Gi0/1 and Gi0/2 in VLAN 10
```
And from your laptop: `ssh admin@10.99.0.11`.

Exact command output and some syntax differ between IOS versions. If a line is rejected,
check `?` help on the device and adjust the template.

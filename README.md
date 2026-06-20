# tuned-cachyos-profiles

CachyOS-specific TuneD profiles for AMD laptops running `amd-pstate-epp`, packaged for Fedora via COPR.

Six profiles covering every AC/battery × PPD state combination, with tuning correct for AMD hardware. Full profile documentation and design rationale lives in the [AUR repo](https://github.com/SCFUCHS87/tuned-cachyos).

---

## Installation

```bash
sudo dnf copr enable scfuchs87/tuned-cachyos-profiles
sudo dnf install tuned-cachyos-profiles
sudo systemctl enable --now tuned tuned-ppd
```

TuneD picks up the active PPD state automatically. No manual profile switching needed if you use KDE PowerDevil.

---

## Profile map

The package writes `/etc/tuned/ppd.conf` on install to wire up KDE PowerDevil → PPD → TuneD. KDE PowerDevil defaults to **performance on AC** and **power-saver on battery**.

| PPD state   | On AC                            | On battery                          |
|-------------|----------------------------------|-------------------------------------|
| performance | `throughput-performance-cachyos` | `balanced-cachyos`                  |
| balanced    | `laptop-ac-balanced-cachyos`     | `battery-balanced-cachyos`          |
| power-saver | `laptop-ac-powersaver-cachyos`   | `laptop-battery-powersaver-cachyos` |

| Profile                             | EPP                 | Governor    | Swappiness | Use case                    |
|-------------------------------------|---------------------|-------------|------------|-----------------------------|
| `throughput-performance-cachyos`    | `performance`       | `performance` | 10       | Gaming, compute, no limits  |
| `laptop-ac-balanced-cachyos`        | `balance_performance` | `powersave` | 30       | AC balanced, snappy + efficient |
| `laptop-ac-powersaver-cachyos`      | `balance_power`     | `powersave` | 40         | AC powersaver, cool and quiet |
| `balanced-cachyos`                  | `balance_performance` | `powersave` | 30       | Performance on battery      |
| `battery-balanced-cachyos`          | `balance_power`     | `powersave` | 50         | Balanced on battery         |
| `laptop-battery-powersaver-cachyos` | `power`             | `powersave` | 60         | Max battery life            |

---

## ppd.conf lifecycle

- **Fresh install:** any existing `ppd.conf` not managed by this package is backed up to `/etc/tuned/ppd.conf.tuned-cachyos.bak` before being replaced with the CachyOS mapping.
- **Upgrade:** existing `ppd.conf` content is preserved. Managed files stay in place, and non-managed files are left untouched.
- **Removal:** the backup is restored if it exists; if no backup and the file is ours, it is removed.

---

## Customizing profiles

Profile files are installed as `%config(noreplace)`. If you edit a profile at `/etc/tuned/profiles/<name>/tuned.conf`, RPM upgrades will deliver the new version as `.rpmnew` rather than overwriting your changes.

VM tuning values (`vm.swappiness`, `vm.vfs_cache_pressure`) were calibrated on 64 GB RAM. On systems with 8–16 GB, consider raising swappiness in the battery profiles by editing the `[sysctl]` section.

---

## Verifying settings took effect

```bash
tuned-adm active
cat /sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference | sort -u
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u
cat /sys/devices/system/cpu/cpufreq/boost
sysctl vm.swappiness
```

---

## Requirements

- `tuned` and `tuned-ppd` (pulled in automatically as dependencies)
- AMD CPU with `amd-pstate-epp` driver (`/sys/devices/system/cpu/amd_pstate/status` should read `active`)
- KDE / PowerDevil for automatic profile switching (optional — profiles work standalone)

---

## License

MIT

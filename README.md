# tuned-cachyos-profiles

CachyOS-specific TuneD profiles for AMD laptops running `amd-pstate-epp`, packaged for Fedora/COPR.

> For Arch/AUR packaging, see [tuned-cachyos](https://github.com/SCFUCHS87/tuned-cachyos).

Most users interact with Power Profiles Daemon (PPD) through KDE's power settings and stop there — three states, no scripting, no per-AC-vs-battery differentiation. This package replaces that with six TuneD profiles that cover every combination of AC/battery and PPD state, with tuning that is actually correct for AMD hardware.

---

## Installation

### COPR

```bash
sudo dnf copr enable scfuchs87/tuned-cachyos-profiles
sudo dnf install tuned-cachyos-profiles
```

### Enable TuneD

```bash
sudo systemctl enable --now tuned tuned-ppd
```

TuneD will pick up the active PPD state automatically. No manual profile switching needed if you use KDE PowerDevil.

---

## Why TuneD instead of PPD alone

PPD gives you three generic states. TuneD gives you:

- Separate profiles for AC and battery at each power level (six total vs three)
- `energy_performance_preference=` written correctly for `amd-pstate-epp` — most AMD configs out there still use `energy_perf_bias=`, which is an Intel MSR setting and does nothing on AMD
- `governor=powersave` explicitly set — `schedutil` is not available on `amd-pstate-epp` and silently no-ops
- PCI, USB, and audio runtime power management via a script that PPD never touches
- VM memory tuning (swappiness, dirty bytes, VFS cache pressure) scaled per power state
- Full KDE PowerDevil compatibility — KDE still controls everything through its power settings, TuneD just does the actual work underneath via `ppd.conf`

---

## Profile map

TuneD integrates with PPD via `/etc/tuned/ppd.conf`. KDE PowerDevil switches PPD states (performance / balanced / power-saver), and TuneD maps those to the right profile based on whether you are on AC or battery. This package writes the CachyOS mapping into `ppd.conf` on install. Any pre-existing non-CachyOS `ppd.conf` is backed up to `/etc/tuned/ppd.conf.tuned-cachyos.bak` before being replaced. On upgrade, a CachyOS-managed `ppd.conf` is preserved; non-managed files are left untouched.

| PPD state   | On AC                          | On battery                          |
|---|---|---|
| performance | `throughput-performance-cachyos` | `balanced-cachyos`                |
| balanced    | `laptop-ac-balanced-cachyos`   | `battery-balanced-cachyos`          |
| power-saver | `laptop-ac-powersaver-cachyos` | `laptop-battery-powersaver-cachyos` |

KDE PowerDevil defaults to **performance on AC** and **power-saver on battery**, so in daily use you will mostly be hitting `throughput-performance-cachyos` when plugged in and `laptop-battery-powersaver-cachyos` on battery.

### Profile details

| Profile | EPP | Governor | Swappiness | Use case |
|---|---|---|---|---|
| `throughput-performance-cachyos` | `performance` | `performance` | 10 | Gaming, compute, no limits |
| `laptop-ac-balanced-cachyos` | `balance_performance` | `powersave` | 30 | AC balanced, snappy + efficient |
| `laptop-ac-powersaver-cachyos` | `balance_power` | `powersave` | 40 | AC powersaver, cool and quiet |
| `balanced-cachyos` | `balance_performance` | `powersave` | 30 | Performance on battery |
| `battery-balanced-cachyos` | `balance_power` | `powersave` | 50 | Balanced on battery |
| `laptop-battery-powersaver-cachyos` | `power` | `powersave` | 60 | Max battery life |

---

## AMD-specific design decisions

**`boost=1` in every profile, including powersavers.** On AMD Ryzen APUs the CPU and iGPU share a power budget. Disabling turbo causes the iGPU to grab the headroom the CPU gave up, which creates resource contention and can cause hangs. The race-to-sleep principle applies: a short turbo burst that finishes quickly uses less total energy than a throttled CPU that runs longer. Note: TuneD's CPU plugin uses `boost=` — the key `turbo=` is not recognized and is silently ignored.

**`energy_performance_preference=` not `energy_perf_bias=`.** The `energy_perf_bias` key in TuneD writes to an Intel MSR. On systems running `amd-pstate-epp` it is silently ignored. These profiles use the correct AMD key and set values that map cleanly to each profile's role.

**`governor=powersave` not `schedutil`.** On `amd-pstate-epp`, the available governors are `powersave` and `performance` only. `schedutil` does not exist in this context and generates warnings on every profile switch without taking effect. All efficiency profiles use `powersave` (which lets the EPP hint guide the hardware), and only `throughput-performance-cachyos` uses `performance`.

---

## RAM note

The VM tuning values in these profiles — `vm.swappiness`, `vm.vfs_cache_pressure` — were calibrated on a system with **64 GB of RAM**. On systems with 8–16 GB you may want to adjust these values upward, particularly for the battery profiles.

To override for your system, edit the `[sysctl]` section of whichever profile you use most at `/etc/tuned/profiles/<profile-name>/tuned.conf`. Files marked `%config(noreplace)` in the RPM will be preserved as `.rpmnew` on upgrades rather than overwriting your edits.

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

- `tuned` and `tuned-ppd` (installed automatically as dependencies)
- AMD CPU with `amd-pstate-epp` driver (`/sys/devices/system/cpu/amd_pstate/status` should read `active`)
- KDE / PowerDevil for automatic profile switching (optional — profiles work standalone too)

---

## License

MIT

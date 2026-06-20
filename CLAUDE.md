# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

An RPM package (`tuned-cachyos-profiles`) that installs custom TuneD profiles for CachyOS on Fedora/COPR. The profiles live under `etc/tuned/profiles/` and are deployed to `/etc/tuned/profiles/` on the target system. This is the RPM counterpart to the AUR package at https://github.com/SCFUCHS87/tuned-cachyos — profile content is identical, only the packaging layer differs.

## Build & install

```bash
# Build RPM locally (requires rpm-build and rpmdevtools)
rpmdev-setuptree
cp tuned-cachyos-profiles.spec ~/rpmbuild/SPECS/
spectool -g -R tuned-cachyos-profiles.spec   # download sources
rpmbuild -ba tuned-cachyos-profiles.spec

# Or build directly with mock for a clean environment
mock -r fedora-42-x86_64 tuned-cachyos-profiles.spec
```

Manual apply without packaging (for quick testing):
```bash
sudo cp -r etc/tuned/profiles/* /etc/tuned/profiles/
sudo sh -c '. ./install-ppd.sh'   # see scripts/install-ppd.sh if available

sudo tuned-adm profile <profile-name>
tuned-adm active
```

Verify CPU settings took effect:
```bash
cat /sys/devices/system/cpu/cpufreq/boost
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u
cat /sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference | sort -u
```

## RPM spec gotchas

- **Shell variables in `%install`**: use `$var`, not `%{var}`. RPM expands `%{...}` as macros before the shell runs — `%{profile}` in a loop would be treated as an undefined macro, not the shell variable.
- **`%autosetup -n tuned-cachyos-rpm-%{version}`**: GitHub archives extract to `<repo-name>-<version>/`, not `<package-name>-<version>/`. The `-n` flag tells RPM the actual directory name after extraction.
- **`%{_sysconfdir}` in scriptlets**: macros ARE expanded in `%post`/`%preun` before the shell runs, so `ppd_conf=%{_sysconfdir}/tuned/ppd.conf` correctly becomes `/etc/tuned/ppd.conf` at install time.
- **`%dir` entries**: RPM requires explicit ownership of every directory the package creates. Missing `%dir` entries cause build warnings and leave orphaned directories on removal.

## Package structure

- `tuned-cachyos-profiles.spec` — RPM spec file; the single source of truth for packaging
- `etc/tuned/profiles/<name>/tuned.conf` — profile config files, installed as `%config(noreplace)`
- `scripts/pci-pm.sh` — fanned out to every profile's `scripts/` dir at install time by the spec
- `LICENSE`, `README.md` — installed as `%license` and `%doc`

## Profile architecture

Each profile is a single `tuned.conf` that `include=`s an upstream TuneD base profile, then overrides specific sections (`[cpu]`, `[vm]`, `[sysctl]`).

Profiles are wired to KDE PowerDevil via `/etc/tuned/ppd.conf`, which maps PPD states to TuneD profiles separately for AC and battery. `tuned-ppd` owns that file, so this package does not ship it as a payload file. Instead, the `%post` scriptlet writes the mapping on install. The file is stamped with `# managed by tuned-cachyos-profiles` so the scriptlet can distinguish it from a foreign config; foreign files are backed up once to `/etc/tuned/ppd.conf.tuned-cachyos.bak` before being replaced. On upgrade, a managed `ppd.conf` is preserved; non-managed files are left untouched. On removal (`%preun` with `$1 -eq 0`), the backup is restored and deleted; if no backup exists and `ppd.conf` is ours, it is removed.

| PPD state | On AC | On battery |
|---|---|---|
| `performance` | `throughput-performance-cachyos` | `balanced-cachyos` |
| `balanced` | `laptop-ac-balanced-cachyos` | `battery-balanced-cachyos` |
| `power-saver` | `laptop-ac-powersaver-cachyos` | `laptop-battery-powersaver-cachyos` |

KDE PowerDevil defaults: AC → `performance`, Battery → `power-saver`.

| Profile | Role | EPP |
|---|---|---|
| `throughput-performance-cachyos` | Gaming/compute, no limits | `performance` |
| `laptop-ac-balanced-cachyos` | AC balanced, snappy + efficient | `balance_performance` |
| `laptop-ac-powersaver-cachyos` | AC powersaver, cool & quiet | `balance_power` |
| `balanced-cachyos` | Performance on battery | `balance_performance` |
| `battery-balanced-cachyos` | Balanced on battery | `balance_power` |
| `laptop-battery-powersaver-cachyos` | Max battery life | `power` |

## Scripts

`scripts/pci-pm.sh` sets PCI/USB runtime PM on profile start and restores `on` on stop. The spec installs it to every profile's `scripts/` subdirectory. The `[audio] timeout=` plugin in each `tuned.conf` handles `snd_hda_intel` separately — pci-pm.sh does not touch it.

## What to update when you change things

**Changing a profile's tuning values (`tuned.conf`):**
- Update the profile file under `etc/tuned/profiles/<name>/tuned.conf`
- Update the profile details table in `README.md` if EPP, governor, or swappiness changed
- Update the profile table in `CLAUDE.md` if the role or EPP changed

**Adding or removing a profile:**
- Add/remove the profile directory under `etc/tuned/profiles/`
- Add/remove it from the `%files` section in `tuned-cachyos-profiles.spec` (both the `%config(noreplace)` tuned.conf line and the scripts line)
- Update the `%post` and `%preun` ppd.conf content if the profile is part of the PPD mapping
- Update PPD mapping tables in `README.md` and `CLAUDE.md`
- Bump the `Version:` in the spec and add a `%changelog` entry
- Update `AGENTS.md` if the structure description changes
- Mirror the change in the AUR repo (https://github.com/SCFUCHS87/tuned-cachyos)

**Changing the PPD mappings:**
- Update the `cat > "$ppd_conf"` block inside `%post` in the spec
- Update the PPD mapping tables in `README.md` and `CLAUDE.md`

**Bumping the package version:**
- Update `Version:` in `tuned-cachyos-profiles.spec`
- Add a `%changelog` entry at the top of the changelog section
- Tag the release in git: `git tag v<version>`

**Changing `scripts/pci-pm.sh`:**
- Update the Scripts section in `CLAUDE.md` if behavior changes
- Mirror the change in the AUR repo

**Changing the `%post`/`%preun` scriptlets:**
- Update the ppd.conf lifecycle description in `CLAUDE.md` and `README.md`
- Mirror equivalent logic in the AUR repo's `.install` file

## Key design decisions

- **`boost=1` is intentional even in power-saving profiles.** On AMD Ryzen APUs, disabling turbo causes hangs and crashes when the iGPU and CPU compete for the shared power budget. The "race to sleep" principle means short bursts are more efficient than throttled-and-hung states. Note: the TuneD CPU plugin option is `boost=` (not `turbo=` — that is silently ignored).
- **Driver is `amd-pstate-epp`** (confirmed on Ryzen 5 7535HS). Only `powersave` and `performance` governors are available — `schedutil` is not valid and will warn/no-op. Use `governor=powersave` for all efficiency profiles, `governor=performance` only for `throughput-performance-cachyos`. The primary power control is `energy_performance_preference=` (not `energy_perf_bias=`, which is Intel-only).
- **`%config(noreplace)`** on all `tuned.conf` files means user edits are preserved as `.rpmnew` on upgrades, equivalent to `backup=()` in pacman.
- **ppd.conf is not a package payload.** `tuned-ppd` owns it. The `%post` scriptlet manages it using a sentinel comment to avoid clobbering user or foreign configs.

## Relationship to AUR repo

Profile content (`etc/tuned/profiles/`, `scripts/`) is kept in sync with https://github.com/SCFUCHS87/tuned-cachyos. When fixing a bug in a profile, update both repos. The packaging layer (spec vs PKGBUILD/.install) differs but the logic should be equivalent.

## .gitignore note

`/etc/` is in `.gitignore` but the profile files under `etc/tuned/profiles/` are tracked — they are the package payload. Do not remove them from tracking.

# Repository Guidelines

## Project Structure & Module Organization

This repository packages CachyOS-specific TuneD profiles for Fedora/COPR as `tuned-cachyos-profiles`. The single packaging entry point is `tuned-cachyos-profiles.spec`. Profile sources live in `etc/tuned/profiles/<profile-name>/tuned.conf` and are installed to `/etc/tuned/profiles/`. The root-level `scripts/pci-pm.sh` is installed to every profile's `scripts/` subdirectory by the spec's `%install` section.

PPD mapping lives in `/etc/tuned/ppd.conf`, which is owned by the `tuned-ppd` package. This package does not ship it as a payload file — instead, the `%post` scriptlet writes the CachyOS mapping into it on install. The file is stamped with `# managed by tuned-cachyos-profiles` so the scriptlet can distinguish it from a foreign config (foreign files get backed up to `ppd.conf.tuned-cachyos.bak` first). On upgrade, managed `ppd.conf` files are preserved and non-managed files are left untouched. On removal (`%preun`, `$1 -eq 0`), the backup is restored and deleted; if no backup exists and the file is ours, it is removed.

This repo is the RPM counterpart to the AUR repo at https://github.com/SCFUCHS87/tuned-cachyos. Profile content is identical — only the packaging layer differs. Keep them in sync when fixing profile bugs.

## Build, Test, and Development Commands

- `rpmbuild -ba tuned-cachyos-profiles.spec`: build source and binary RPMs (requires `rpm-build`, `rpmdevtools`).
- `mock -r fedora-42-x86_64 tuned-cachyos-profiles.spec`: clean-room build via mock.
- `spectool -g -R tuned-cachyos-profiles.spec`: download sources declared in the spec.
- `tuned-adm active`: verify the active TuneD profile on a target system.
- `tuned-adm verify`: compare live settings with the active profile.
- `cat /sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference | sort -u`: confirm AMD EPP settings took effect.

For quick manual testing, copy profile files to `/etc/tuned/profiles/` and apply one with `sudo tuned-adm profile <profile-name>`.

## Coding Style & Naming Conventions

Use shell-compatible POSIX sh style in `%post`/`%preun` scriptlets: quoted variables, explicit paths, no bashisms. Keep profile names lowercase and hyphenated, ending in `-cachyos`. TuneD configuration should remain simple INI-style sections (`[cpu]`, `[vm]`, `[sysctl]`). Use `boost=1`, not `turbo=1`, for TuneD CPU boost control.

## Change Checklist

Always keep these files in sync — stale docs or metadata are a common failure mode.

| What changed | Also update |
|---|---|
| Profile tuning values (`tuned.conf`) | `README.md` profile details table if EPP/governor/swappiness changed; mirror in AUR repo |
| Profile added or removed | `%files` in spec (tuned.conf + scripts line), `%post`/`%preun` ppd.conf block if in PPD map, PPD tables in `README.md` and `CLAUDE.md`, bump `Version:`, add `%changelog` entry |
| PPD mappings in `%post` | PPD mapping tables in `README.md` and `CLAUDE.md` |
| `Version:` bump | Add `%changelog` entry at top of changelog; tag release with `git tag v<version>` |
| `scripts/pci-pm.sh` behavior | Scripts section in `CLAUDE.md`; mirror in AUR repo |
| `%post`/`%preun` scriptlet behavior | ppd.conf lifecycle description in `CLAUDE.md` and `README.md`; mirror logic in AUR repo `.install` file |
| `CLAUDE.md` workflow or architecture | Mirror relevant changes in `AGENTS.md` and vice versa |

## Testing Guidelines

There is no automated test suite. Validate by building with `rpmbuild -ba` or `mock`, installing the RPM, switching profiles with `tuned-adm`, and checking CPU governor, boost, EPP, and sysctl values. For ppd.conf behavior, verify that: a fresh install writes the file with the sentinel; a non-managed existing file is backed up before being replaced; an upgrade leaves a managed file untouched; removal restores the backup and deletes it, or removes the file if no backup exists.

## Commit & Pull Request Guidelines

Use short imperative summaries. Keep commits focused: profile behavior, spec/packaging, scripts, or docs. Mention any hardware assumptions (AMD `amd-pstate-epp`). When bumping the version, always include the `%changelog` entry in the same commit.

## Agent-Specific Instructions

Keep `AGENTS.md` and `CLAUDE.md` aligned when workflow, architecture, or validation guidance changes. Do not remove tracked `etc/` profile files — `.gitignore` excludes `/etc/` but these files are already tracked as the package payload.

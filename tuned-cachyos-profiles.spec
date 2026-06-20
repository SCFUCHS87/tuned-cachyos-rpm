Name:           tuned-cachyos-profiles
Version:        1.0.0
Release:        2%{?dist}
Summary:        CachyOS-flavored TuneD profiles for AMD laptops

License:        MIT
URL:            https://github.com/SCFUCHS87/tuned-cachyos-rpm
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildArch:      noarch

Requires:       tuned
Requires:       tuned-ppd

%description
CachyOS-specific TuneD profiles for AMD laptops running amd-pstate-epp.

Provides six profiles covering every AC/battery and PPD state combination,
with tuning correct for AMD hardware: proper energy_performance_preference
keys, boost=1 in every profile to prevent iGPU/CPU power budget conflicts,
and PCI/USB runtime PM via a helper script.

KDE PowerDevil integration is configured automatically via /etc/tuned/ppd.conf.

%prep
# GitHub archives extract to <repo-name>-<version>/, not <package-name>-<version>/
%autosetup -n tuned-cachyos-rpm-%{version}

%build
# Nothing to build — noarch config files only

%install
install -d %{buildroot}%{_sysconfdir}/tuned/profiles

for profile_dir in etc/tuned/profiles/*/; do
    profile=$(basename "$profile_dir")
    install -d %{buildroot}%{_sysconfdir}/tuned/profiles/$profile
    install -d %{buildroot}%{_sysconfdir}/tuned/profiles/$profile/scripts
    install -m644 "$profile_dir/tuned.conf" \
        %{buildroot}%{_sysconfdir}/tuned/profiles/$profile/tuned.conf

    # Per-profile scripts/
    if [ -d "$profile_dir/scripts" ]; then
        for f in "$profile_dir/scripts/"*; do
            install -m755 "$f" \
                %{buildroot}%{_sysconfdir}/tuned/profiles/$profile/scripts/
        done
    fi

    # Fan out root scripts/ to every profile
    install -m755 scripts/pci-pm.sh \
        %{buildroot}%{_sysconfdir}/tuned/profiles/$profile/scripts/pci-pm.sh
done

%post
ppd_conf=%{_sysconfdir}/tuned/ppd.conf
backup_conf=%{_sysconfdir}/tuned/ppd.conf.tuned-cachyos.bak

if [ "$1" -eq 1 ]; then
    # Back up any ppd.conf that is not ours before overwriting on fresh install
    if [ -e "$ppd_conf" ] && ! grep -q 'managed by tuned-cachyos-profiles' "$ppd_conf"; then
        cp -a "$ppd_conf" "$backup_conf"
    fi

    # Write our ppd.conf only if it does not already have our sentinel
    if ! grep -q 'managed by tuned-cachyos-profiles' "$ppd_conf" 2>/dev/null; then
        install -d %{_sysconfdir}/tuned
        cat > "$ppd_conf" << 'EOF'
# managed by tuned-cachyos-profiles
[main]
default=balanced
battery_detection=true
sysfs_acpi_monitor=false

[profiles]
# PPD state = TuneD profile (on AC)
power-saver=laptop-ac-powersaver-cachyos
balanced=laptop-ac-balanced-cachyos
performance=throughput-performance-cachyos

[battery]
# PPD state = TuneD profile (on battery)
power-saver=laptop-battery-powersaver-cachyos
balanced=battery-balanced-cachyos
performance=balanced-cachyos
EOF
        echo "tuned-cachyos-profiles: KDE PowerDevil / PPD mapping written to $ppd_conf"
    else
        echo "tuned-cachyos-profiles: existing managed PPD mapping preserved at $ppd_conf"
    fi
else
    echo "tuned-cachyos-profiles: existing PPD mapping preserved on upgrade"
fi

echo "Enable TuneD if not already running: sudo systemctl enable --now tuned tuned-ppd"

%preun
if [ $1 -eq 0 ]; then
    ppd_conf=%{_sysconfdir}/tuned/ppd.conf
    backup_conf=%{_sysconfdir}/tuned/ppd.conf.tuned-cachyos.bak

    if [ -e "$backup_conf" ]; then
        if [ ! -e "$ppd_conf" ] || grep -q 'managed by tuned-cachyos-profiles' "$ppd_conf"; then
            cp -a "$backup_conf" "$ppd_conf"
            rm -f "$backup_conf"
        fi
    elif [ -e "$ppd_conf" ] && grep -q 'managed by tuned-cachyos-profiles' "$ppd_conf"; then
        rm -f "$ppd_conf"
    fi
fi

%files
%license LICENSE
%doc README.md
%dir %{_sysconfdir}/tuned/profiles/balanced-cachyos
%dir %{_sysconfdir}/tuned/profiles/balanced-cachyos/scripts
%dir %{_sysconfdir}/tuned/profiles/battery-balanced-cachyos
%dir %{_sysconfdir}/tuned/profiles/battery-balanced-cachyos/scripts
%dir %{_sysconfdir}/tuned/profiles/laptop-ac-balanced-cachyos
%dir %{_sysconfdir}/tuned/profiles/laptop-ac-balanced-cachyos/scripts
%dir %{_sysconfdir}/tuned/profiles/laptop-ac-powersaver-cachyos
%dir %{_sysconfdir}/tuned/profiles/laptop-ac-powersaver-cachyos/scripts
%dir %{_sysconfdir}/tuned/profiles/laptop-battery-powersaver-cachyos
%dir %{_sysconfdir}/tuned/profiles/laptop-battery-powersaver-cachyos/scripts
%dir %{_sysconfdir}/tuned/profiles/throughput-performance-cachyos
%dir %{_sysconfdir}/tuned/profiles/throughput-performance-cachyos/scripts
%config(noreplace) %{_sysconfdir}/tuned/profiles/balanced-cachyos/tuned.conf
%config(noreplace) %{_sysconfdir}/tuned/profiles/battery-balanced-cachyos/tuned.conf
%config(noreplace) %{_sysconfdir}/tuned/profiles/laptop-ac-balanced-cachyos/tuned.conf
%config(noreplace) %{_sysconfdir}/tuned/profiles/laptop-ac-powersaver-cachyos/tuned.conf
%config(noreplace) %{_sysconfdir}/tuned/profiles/laptop-battery-powersaver-cachyos/tuned.conf
%config(noreplace) %{_sysconfdir}/tuned/profiles/throughput-performance-cachyos/tuned.conf
%{_sysconfdir}/tuned/profiles/balanced-cachyos/scripts/pci-pm.sh
%{_sysconfdir}/tuned/profiles/battery-balanced-cachyos/scripts/pci-pm.sh
%{_sysconfdir}/tuned/profiles/laptop-ac-balanced-cachyos/scripts/pci-pm.sh
%{_sysconfdir}/tuned/profiles/laptop-ac-powersaver-cachyos/scripts/pci-pm.sh
%{_sysconfdir}/tuned/profiles/laptop-battery-powersaver-cachyos/scripts/pci-pm.sh
%{_sysconfdir}/tuned/profiles/throughput-performance-cachyos/scripts/pci-pm.sh

%changelog
* Sat Jun 20 2026 Steven Fuchs <stevencfuchs@icloud.com> - 1.0.0-2
- Preserve existing /etc/tuned/ppd.conf mappings on package upgrades
- Remove stale manual install-ppd.sh documentation reference

* Sat Jun 20 2026 Steven Fuchs <stevencfuchs@icloud.com> - 1.0.0-1
- Initial RPM release
- Six TuneD profiles covering all AC/battery PPD state combinations
- boost=1 in every profile to prevent AMD iGPU/CPU power budget conflicts
- PCI/USB runtime PM via pci-pm.sh
- KDE PowerDevil PPD mapping configured via /etc/tuned/ppd.conf

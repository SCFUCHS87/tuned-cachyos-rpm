#!/usr/bin/env bash
# PCI runtime PM and USB autosuspend via direct sysfs writes.
# [audio] timeout= in tuned.conf handles snd_hda_intel power_save.
case "$1" in
  start)
    for f in /sys/bus/pci/devices/*/power/control; do
      echo auto > "$f" 2>/dev/null
    done
    for f in /sys/bus/usb/devices/*/power/control; do
      echo auto > "$f" 2>/dev/null
    done
    ;;
  stop)
    for f in /sys/bus/pci/devices/*/power/control; do
      echo on > "$f" 2>/dev/null
    done
    for f in /sys/bus/usb/devices/*/power/control; do
      echo on > "$f" 2>/dev/null
    done
    ;;
esac

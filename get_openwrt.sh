#!/bin/sh

echo "Creating tftp_root directory"
mkdir -p tftp_root
cd tftp_root
echo "Downloading OpenWRT Barrier Breaker squashfs root image"
wget "http://downloads.openwrt.org/barrier_breaker/14.07/atheros/generic/openwrt-atheros-root.squashfs" &&
echo "Downloading OpenWRT Barrier Breaker vmlinux image" &&
wget "http://downloads.openwrt.org/barrier_breaker/14.07/atheros/generic/openwrt-atheros-vmlinux.gz" &&
echo "Download complete"

#!/bin/sh

echo "Creating tftp_root directory"
mkdir -p tftp_root
cd tftp_root
echo "Downloading OpenWRT Attitude Adjustment squashfs root image"
wget "http://downloads.openwrt.org/barrier_breaker/14.07/atheros/generic/openwrt-atheros-root.squashfs" &&
echo "Downloading OpenWRT Attitude Adjustment vmlinux image" &&
wget "http://downloads.openwrt.org/barrier_breaker/14.07/atheros/generic/openwrt-atheros-vmlinux.gz" &&
echo "Download complete"

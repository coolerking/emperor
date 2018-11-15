#!/bin/sh
# run with sudo
echo "** sixaxis config phase 01 **"
echo ""
echo "install apt packages and modify group setting"
echo "and reboot"
apt install -y bluetooth libbluetooth3 libusb-dev
systemctl enable bluetooth.service
usermod -G bluetooth -a pi
reboot
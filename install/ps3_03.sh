#!/bin/sh
# run as pi user
echo "** sixaxis config phase 03 **"
echo ""
echo "you have to connect sixaxis with usb cable"
echo ""
echo "download and run sudo sixaxis"
wget http://www.pabr.org/sixlinux/sixpair.c
gcc -o sixpair sixpair.c -lusb
sudo sixaxis
echo ""
echo "and run as follows:"
echo "bluetooth"
echo "agent on"
echo "devices"
echo "trust <MAC ADDRESS>"
echo "default-agent"
echo "quit"
echo ""
echo "after bluetooth config, unplug usb cable and push ps3 logo button"
echo "you can check connection to run ls /dev/input/js0"
echo ""
echo "you can also check sixaxis connection to run hexdump /dev/input/js0"
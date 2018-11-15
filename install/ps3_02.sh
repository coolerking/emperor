#!/bin/sh
# run as pi user
echo "** sixaxis config phase 02 **"
echo ""
echo "install sixaxis controller package"
git clone https://github.com/autorope/donkeypart_ps3_controller.git
cd donkeypart_ps3_controller
pip install -e .
echo ""
echo "next, edit manage.py"
echo "from donkeypart_ps3_controller.part import JoystickController"
echo ""
echo "after edit manage.py, please run sudo shutdown -h now"
echo "and connect sixaxis with usb cable"
echo ""

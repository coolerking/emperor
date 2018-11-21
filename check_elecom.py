#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import array
import time
import struct
from fcntl import ioctl

axis_states = {}            # 方向状態辞書{方向名:状態}:init()にて書き込まれる
button_states = {}          # ボタン状態辞書{ボタン名,状態}:init()にて書き込まれる
axis_map = []               # 方向マップ[方向名]:init()にて書き込まれる
button_map = []             # ボタンマップ[ボタン名]:init()にて書き込まれる
jsdev = None                # ジョイスティックキャラクタデバイス ファイルオブジェクト
dev_fn = '/dev/input/js0'   # ジョイスティックキャラクタデバイス パス

axis_names = {
    0x00 : 'left_stick_horz',
    0x01 : 'left_stick_vert',
    0x02 : 'right_stic_vert',
    0x03 : 'right_stick_horz',
    0x04 : 'dpad_horz',
    0x05 : 'dpad_vert',
}

button_names = {
    0x130 : '1',
    0x131 : '2',
    0x132 : '3',
    0x133 : '4',
    0x134 : '5',
    0x135 : '6',
    0x136 : '7',
    0x137 : '8',
    0x138 : '9?',
    0x139 : '10?',
    0x13a : '11',
    0x13b : '12',
}

def init():
    print('Opening %s...' % dev_fn)
    with open(dev_fn, 'rb') as jsdev:

        # Get the device name.
        buf = array.array('B', [0] * 64)
        ioctl(jsdev, 0x80006a13 + (0x10000 * len(buf)), buf) # JSIOCGNAME(len)
        js_name = buf.tobytes().decode('utf-8')
        print('Device name: %s' % js_name)

        # Get number of axes and buttons.
        buf = array.array('B', [0])
        ioctl(jsdev, 0x80016a11, buf) # JSIOCGAXES
        num_axes = buf[0]
        print('num_axes: ', num_axes)

        buf = array.array('B', [0])
        ioctl(jsdev, 0x80016a12, buf) # JSIOCGBUTTONS
        num_buttons = buf[0]
        print('num_buttons: ', num_buttons)

        # Get the axis map.
        buf = array.array('B', [0] * 0x40)
        ioctl(jsdev, 0x80406a32, buf) # JSIOCGAXMAP

        print('***** axis_name list')
        for axis in buf[:num_axes]:
            axis_name = axis_names.get(axis, 'unknown(0x%02x)' % axis)
            axis_map.append(axis_name)
            axis_states[axis_name] = 0.0
            print(' ', axis_name)
            print('    = 0x%02x' % axis)

        # Get the button map.
        buf = array.array('H', [0] * 200)
        ioctl(jsdev, 0x80406a34, buf) # JSIOCGBTNMAP

        print('***** button_name list')
        for btn in buf[:num_buttons]:
            btn_name = button_names.get(btn, 'unknown(0x%03x)' % btn)
            button_map.append(btn_name)
            button_states[btn_name] = 0
            print(' ', btn_name)
            print('    = 0x%03x' % btn)

        EVENT_FORMAT = "llHHI"; # long, long, unsigned short, unsigned short, unsigned int
        EVENT_SIZE = struct.calcsize(EVENT_FORMAT)

        event = jsdev.read(EVENT_SIZE)
        while event:
            #(tv_sec, tv_usec, type, code, value) = struct.unpack(EVENT_FORMAT, event)
            print(struct.unpack(EVENT_FORMAT, event))
            event = jsdev.read(EVENT_SIZE)

if __name__ == '__main__':
    init()
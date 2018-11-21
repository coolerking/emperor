# -*- coding: utf-8 -*-
"""
Logicool製ジョイスティック F710 を使用するためのpartクラス。
donkeypart_ps3_controller パッケージのクラスを基底クラスとして使用するため、
先にインストールしておく必要がある。

git clone https://github.com/autorope/donkeypart_ps3_controller.git
cd donkeypart_ps3_controller
pip install -e .

"""
import struct
from donkeypart_ps3_controller.part import Joystick, JoystickController

class F710_Joystick(Joystick):

    def __init__(self, *args, **kwargs):
        super(F710_Joystick, self).__init__(*args, **kwargs)

        self.axis_names = {
            0:  'left_stick_horz',
            1:  'left_stick_vert',
            2:  'LT_pressure',
            3:  'right_stick_horz',
            4:  'right_stick_vert',
            5:  'RT_pressure',
            6:  'dpad_horz',
            7:  'dpad_vert',
        }

        self.button_names = {
            0: 'A',     # cross
            1: 'B',     # circle
            2: 'X',     # square
            3: 'Y',     # triangle
            4: 'LB',    # L1
            5: 'RB',    # R1
            6: 'BACK',  # select
            7: 'START', # start
        }
    
    def init(self):
        '''
        初期化処理
        親クラスの同一メソッドを実行後、以下のインスタンス変数を書き換える。
        * num_axes, num_buttons
        * axis_map, button_map
        * axis_states, button_states

        引数
            なし
        戻り値
            なし 
        '''
        super(F710_Joystick, self).init()

        self.num_axes = len(self.axis_names)
        self.axis_map = self.axis_names.values()
        self.axis_states = {}
        for axis_name in self.axis_map:
            self.axis_states[axis_name] = 0.0
        
        self.num_buttons = len(self.button_names)
        self.button_map = self.button_names.values()
        self.button_states = {}
        for btn_name in self.button_map:
            self.button_states[btn_name] = 0

    def poll(self):
        button = None
        button_state = None
        axis = None
        axis_val = None

        if self.jsdev is None:
            return button, button_state, axis, axis_val

        # Main event loop
        evbuf = self.jsdev.read(8)

        if evbuf:
            _, value, typev, number = struct.unpack('IhBB', evbuf)

            if typev & 0x80:
                # ignore initialization event
                return button, button_state, axis, axis_val

            if typev == 1:
                button = self.button_map[number]
                # print(tval(_), value, typev, number, button, 'pressed')
                if button:
                    self.button_states[button] = value
                    button_state = value

            if typev == 2:
                axis = self.axis_map[number]
                if axis:
                    fvalue = value / 32767.0
                    self.axis_states[axis] = fvalue
                    axis_val = fvalue

        return button, button_state, axis, axis_val

    def _test_poll(self):
        evbuf = self.jsdev.read(8)
        if evbuf:
            _, value, typev, number = struct.unpack('IhBB', evbuf)
            if typev == 1:
                if number < self.num_buttons:
                    button_name = self.button_names[number]
                    print('[B] ', button_name, ' pressed value= ', value)
                else:
                    print('[B] out of range number=', number)
            elif typev == 2:
                if number < self.num_axes:
                    axis_name = self.axis_names[number]
                    print('[A] ', axis_name, ' pressed value= ', value)
                else:
                    print('[A] out of range number=', number)
            else:
                print('[W] warning: typev=', typev, ', number=', number)

class F710_JoystickController(JoystickController):
    '''
    A Controller object helps create a new controller object and mapping
    '''

    def __init__(self, *args, **kwargs):
        super(F710_JoystickController, self).__init__(*args, **kwargs)

    def init_js(self):
        '''
        F710_Joystickオブジェクトを生成、初期化する。

        引数
            なし
        戻り値
            なし
        '''
        try:
            self.js = F710_Joystick(self.dev_fn)
            self.js.init()
        except FileNotFoundError:
            print(self.dev_fn, "not found.")
            self.js = None

        return self.js is not None

    def init_trigger_maps(self):
        '''
        F710上の各ボタンに機能を割り当てるマッピング情報を
        初期化する。

        引数
            なし
        戻り値
            なし
        '''
        self.button_down_trigger_map = {
            'BACK': self.toggle_mode,
            'B': self.toggle_manual_recording,
            'Y': self.erase_last_N_records,
            'A': self.emergency_stop,
            'START': self.toggle_constant_throttle,
            "RB": self.chaos_monkey_on_right,
            "LB": self.chaos_monkey_on_left,
        }

        self.button_up_trigger_map = {
            "RB": self.chaos_monkey_off,
            "LB": self.chaos_monkey_off,
        }

        self.axis_trigger_map = {
            'left_stick_horz': self.set_steering,
            'right_stick_vert': self.set_throttle,
            'LT_pressure': self.increase_max_throttle,
            'RT_pressure': self.decrease_max_throttle,
        }

    def _test_poll(self):
        while True:
            self.js._test_poll()

def main():
    ctr = F710_JoystickController(
                 throttle_scale=0.25,
                 steering_scale=1.0,
                 auto_record_on_throttle=True)
    ctr.init_js()
    ctr._test_poll()

if __name__ == '__main__':
    main()
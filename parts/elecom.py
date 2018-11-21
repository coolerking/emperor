# -*- coding: utf-8 -*-
"""
ELECOM製ジョイスティック JC-U3912T を使用するためのpartクラス。
donkeypart_ps3_controller パッケージのクラスを基底クラスとして使用するため、
先にインストールしておく必要がある。

git clone https://github.com/autorope/donkeypart_ps3_controller.git
cd donkeypart_ps3_controller
pip install -e .

"""
import struct
from donkeypart_ps3_controller.part import Joystick, JoystickController

class JC_U3912T_Joystick(Joystick):

    def __init__(self, *args, **kwargs):
        super(JC_U3912T_Joystick, self).__init__(*args, **kwargs)

        self.axis_names = {
            0:  'left_stick_horz',
            1:  'left_stick_vert',
            2:  'right_stick_vert',
            3:  'right_stick_horz',
            4:  'dpad_horz',
            5:  'dpad_vert'
        }

        self.button_names = {
            0: '1',   # square
            1: '2',   # triangle
            2: '3',   # cross
            3: '4',   # circle
            4: '5',   # L1
            5: '6',   # R1
            6: '7',   # L2
            7: '8',   # R2
            10: '11', # select
            11: '12'  # start
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
        super(JC_U3912T_Joystick, self).init()

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

    def getJsdev(self):
        return self.jsdev

class JC_U3912T_JoystickController(JoystickController):
    '''
    A Controller object helps create a new controller object and mapping
    '''

    def __init__(self, *args, **kwargs):
        super(JC_U3912T_JoystickController, self).__init__(*args, **kwargs)

    def init_js(self):
        '''
        JC_U3912T_Joystickオブジェクトを生成、初期化する。

        引数
            なし
        戻り値
            なし
        '''
        try:
            self.js = JC_U3912T_Joystick(self.dev_fn)
            self.js.init()
        except FileNotFoundError:
            print(self.dev_fn, "not found.")
            self.js = None

        return self.js is not None

    def init_trigger_maps(self):
        '''
        JC-U3912T上の各ボタンに機能を割り当てるマッピング情報を
        初期化する。

        引数
            なし
        戻り値
            なし
        '''
        self.button_down_trigger_map = {
            '11': self.toggle_mode,
            '4': self.toggle_manual_recording,
            '2': self.erase_last_N_records,
            '3': self.emergency_stop,
            '7': self.increase_max_throttle,
            '8': self.decrease_max_throttle,
            '12': self.toggle_constant_throttle,
            "6": self.chaos_monkey_on_right,
            "5": self.chaos_monkey_on_left,
        }

        self.button_up_trigger_map = {
            "6": self.chaos_monkey_off,
            "5": self.chaos_monkey_off,
        }

        self.axis_trigger_map = {
            'left_stick_horz': self.set_steering,
            'right_stick_vert': self.set_throttle,
        }
    def getJsdev(self):
        return self.js.getJsdev()


def main():
    ctr = JC_U3912T_JoystickController(
                 throttle_scale=0.25,
                 steering_scale=1.0,
                 auto_record_on_throttle=True)

    evbuf = ctr.js.getJsdev().read(8)
    while evbuf:
        _, value, typev, number = struct.unpack('IhBB', evbuf)
        if typev == 1:
            button_name = ctr.js.button_names[number]
            print('[B] ', button_name, ' pressed value= ', value)
            axis_name = ctr.js.axis_names[number]
            print('[A] ', axis_name, ' pressed value= ', value)
        else:
            print('[W] warning: typev=', typev, ', number=', number)
        evbuf = ctr.js.getJsdev().read(8)

if __name__ == '__main__':
    main()
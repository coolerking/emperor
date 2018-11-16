# -*- coding: utf-8 -*-
"""
controller_logicool.py

Logicool F710 Wireless Joystick 用コントローラクラス

本コードは https://github.com/mituhiromatuura/donkey よりダウンロード
したもの(MITライセンス)に、日本語コメントを追記しています。
"""
import array
import time
import struct


#from donkeycar.parts.web_controller.web import LocalWebController

class Joystick():
    """
    キャラクタデバイス /dev/input が有効となっている物理ジョイスティック
    へのインターフェイスとなる。
    """
    access_url = None # Web コントローラとの一貫性のために定義

    def __init__(self, dev_fn='/dev/input/js0'):
        """
        コンストラクタ

        引数：
          dev_fn        キャラクタデバイスへのパス
        """
        # 軸状態辞書{軸名:状態}:init()にて書き込まれる
        self.axis_states = {}
        # ボタン状態辞書{ボタン名,状態}:init()にて書き込まれる
        self.button_states = {}
        # 軸マップ[軸名]:init()にて書き込まれる
        self.axis_map = []
        # ボタンマップ[ボタン名]:init()にて書き込まれる
        self.button_map = []
        # ジョイスティックキャラクタデバイス ファイルオブジェクト
        self.jsdev = None
        # ジョイスティックキャラクタデバイス パス
        self.dev_fn = dev_fn

        # これらの定数は linux/input.h から借用
        # キャラクタデバイス上のコードと軸名の辞書(F710固有)
        self.axis_names = {
            0x00 : 'x',
            0x01 : 'y',
            0x02 : 'z',
            0x03 : 'rx',
            0x04 : 'ry',
            0x05 : 'rz',
            0x06 : 'trottle',
            0x07 : 'rudder',
            0x08 : 'wheel',
            0x09 : 'gas',
            0x0a : 'brake',
            0x10 : 'hat0x',
            0x11 : 'hat0y',
            0x12 : 'hat1x',
            0x13 : 'hat1y',
            0x14 : 'hat2x',
            0x15 : 'hat2y',
            0x16 : 'hat3x',
            0x17 : 'hat3y',
            0x18 : 'pressure',
            0x19 : 'distance',
            0x1a : 'tilt_x',
            0x1b : 'tilt_y',
            0x1c : 'tool_width',
            0x20 : 'volume',
            0x28 : 'misc',
        }
        # キャラクタデバイス上のコードとボタン名の辞書(F710固有)
        self.button_names = {
            0x120 : 'trigger',
            0x121 : 'thumb',
            0x122 : 'thumb2',
            0x123 : 'top',
            0x124 : 'top2',
            0x125 : 'pinkie',
            0x126 : 'base',
            0x127 : 'base2',
            0x128 : 'base3',
            0x129 : 'base4',
            0x12a : 'base5',
            0x12b : 'base6',

            #PS3 Dualshock2 固有
            0x12c : "triangle",
            0x12d : "circle",
            0x12e : "cross",
            0x12f : 'square',

            0x130 : 'a',
            0x131 : 'b',
            0x132 : 'c',
            0x133 : 'x',
            0x134 : 'y',
            0x135 : 'z',
            0x136 : 'tl',
            0x137 : 'tr',
            0x138 : 'tl2',
            0x139 : 'tr2',
            0x13a : 'select',
            0x13b : 'start',
            0x13c : 'mode',
            0x13d : 'thumbl',
            0x13e : 'thumbr',

            0x220 : 'dpad_up',
            0x221 : 'dpad_down',
            0x222 : 'dpad_left',
            0x223 : 'dpad_right',

            # XBox 360 controller ではこれらのコードを使用
            # F710はXBox互換
            0x2c0 : 'dpad_left',
            0x2c1 : 'dpad_right',
            0x2c2 : 'dpad_up',
            0x2c3 : 'dpad_down',
        }


    def init(self):
        """
        /dev/input/js0 への接続をセットアップし、ボタンのマッピングを行う
        初期処理関数

        引数
          N/A
        戻り値
        　真偽値    常に真を返却
        """
        # 以下のパッケージはUNIX/Linuxにしかないため
        # Windows 上で開くとエラー表示されることがある
        from fcntl import ioctl

        # ジョイスティックキャラクタデバイスのオープン
        print('Opening %s...' % self.dev_fn)
        self.jsdev = open(self.dev_fn, 'rb')

        # デバイス名の取得
        buf = array.array('B', [0] * 64)
        # キャラクタデバイスからデバイス名を取得しbufへ書き込む
        ioctl(self.jsdev, 0x80006a13 + (0x10000 * len(buf)), buf) # JSIOCGNAME(len)
        # バイト配列化後、UTF-8に変換し、デバイス名とする
        self.js_name = buf.tobytes().decode('utf-8')
        print('Device name: %s' % self.js_name)

        # 軸やボタンの番号を取得
        buf = array.array('B', [0]) # unsigned charを初期値[0]で配列化
        # キャラクタデバイスから、軸数を取得しbufへ書き込む
        ioctl(self.jsdev, 0x80016a11, buf) # JSIOCGAXES
        # 最初のバイト値を軸数とする
        self.num_axes = buf[0]

        buf = array.array('B', [0]) # unsigned charを初期値[0]で配列化
        # キャラクタデバイスから、ボタン数を取得しbufへ書き込む
        ioctl(self.jsdev, 0x80016a12, buf) # JSIOCGBUTTONS
        self.num_buttons = buf[0]

        # 軸マップの取得
        buf = array.array('B', [0] * 0x40) # unsigned charを初期値 [0] * 0x40 で配列化
        # キャラクタデバイスから軸名連結データを取得しbufへ書き込む
        ioctl(self.jsdev, 0x80406a32, buf) # JSIOCGAXMAP

        # bufの先頭から軸数分のバイト配列を切り出し、1バイトづつ axisに格納するループ
        for axis in buf[:self.num_axes]:
            # コンストラクタにて定義した辞書axis_namesをもとに軸名を取得する
            # 存在しない場合は'unknown(0x%02x)' % axis形式の文字列で代替
            axis_name = self.axis_names.get(axis, 'unknown(0x%02x)' % axis)
            # コンストラクタで空定義していた軸マップ(軸名の配列)に軸名を追加
            self.axis_map.append(axis_name)
            # コンストラクタで空定義していた軸状態辞書(軸名の配列)に初期値の状態0.0をセット
            self.axis_states[axis_name] = 0.0

        # ボタンマップの取得
        buf = array.array('H', [0] * 200) # unsigned charを初期値 [0] * 200 で配列化
        ioctl(self.jsdev, 0x80406a34, buf) # JSIOCGBTNMAP

        # bufの先頭からボタン数分のバイト配列を切り出し、1バイトづつbtnに格納するループ
        for btn in buf[:self.num_buttons]:
            # コンストラクタにて定義した辞書button_namesをもとにボタン名を取得する
            # 存在しない場合は'unknown(0x%03x)' % axis形式の文字列で代替
            btn_name = self.button_names.get(btn, 'unknown(0x%03x)' % btn)
            # コンストラクタで空定義していたボタンマップ(ボタン名の配列)にボタン名を追加
            self.button_map.append(btn_name)
            # コンストラクタで空定義していたボタン状態辞書(ボタン名の配列)に初期値の状態0をセット
            self.button_states[btn_name] = 0

        # すべて終了したら、真値を返却
        return True


    def show_map(self):
        """
        ジョイスティック上のすべてのボタンリストおよび軸リストを表示します。
        """
        print ('%d axes found: %s' % (self.num_axes, ', '.join(self.axis_map)))
        print ('%d buttons found: %s' % (self.num_buttons, ', '.join(self.button_map)))


    def poll(self):
        """
        ジョイスティックの状態を照会し、押されたボタン、もしあれば移動した軸、
        もしあれば移動したボタンを返します。 
        button_stateの値は、変更なしの場合None、押下された場合 1 、
        押していたボタンを話した場合 0 となります。
        axis_val の値は -1 から +1 までの float となります。
        ボタンと軸は、関数 init の軸マップにより決定する文字列ラベルとなります。

        戻り値
          button        ボタン名
          button_state  ボタンの状態(None:変化なし, 1:押下, 0:押下状態からリリース)
          axis          軸名
          axsis_val     軸値(-1.0～1.0)
        """
        # 戻り値用変数の定義
        button = None
        button_state = None
        axis = None
        axis_val = None

        # メインイベント ループ
        # キャラクタデバイスから8バイト読み込む
        evbuf = self.jsdev.read(8)

        # キャラクタデバイスから8バイト読み込めた場合
        if evbuf:
            # evbufに格納されたバイト配列を書式文字列'IhBB'に従ってそれぞれ
            # unsigned int tval, short value, unsigned char typev, unsigned char number
            # にパックされたバイナリとして解釈された多胎を格納する
            # なお先頭の tval は使用しない
            tval, value, typev, number = struct.unpack('IhBB', evbuf)

            ＃初期化イベントの場合
            if typev & 0x80:
                # 無視
                return button, button_state, axis, axis_val

            # ボタンイベントの場合
            if typev & 0x01:
                # ボタン名にする、ない場合None
                button = self.button_map[number]
                # 存在するボタン名の場合
                if button:
                    # ボタン状態をキャラクタデバイスから取得した値に変更
                    self.button_states[button] = value
                    button_state = value

            # 軸イベントの場合
            if typev & 0x02:
                # 軸名にする、ない場合None
                axis = self.axis_map[number]
                # 存在する軸名の場合
                if axis:
                    # 軸状態をキャラクタデバイスから取得した値を
                    # -1.0から1.0の範囲内のfloat値にして変更
                    fvalue = value / 32767.0
                    self.axis_states[axis] = fvalue
                    axis_val = fvalue

        # 戻り値を返却
        return button, button_state, axis, axis_val


class JoystickController(object):
    """
    Logcool F710 ジョイスティックのPartクラス（Thredベース）
    ローカルの物理デバイス(キャラクタデバイス)入力データへのアクセスを
    利用するために用意された。
    インスタンス変数群はジョイスティックで操作可能な値をすべて格納しており

    """

    def __init__(self, poll_delay=0.0,
                 max_throttle=1.0,
                 steering_axis='x',
                 throttle_axis='ry',
                 steering_scale=1.0,
                 throttle_scale=-1.0,
                 pan_l_axis='z',
                 pan_r_axis='rz',
                 dev_fn='/dev/input/js0',
                 auto_record_on_throttle=True):
        """
        コンストラクタ。

        引数
            poll_delay                  ポーリングの間隔(デフォルト:0.0)
            max_throttle                最大スロットル値(デフォルト:1.0)
            steering_axis               ステアリング軸名(デフォルト:'x')
            steering_scale              ステアリング値(デフォルト:1.0)
            throttle_scale              スロットル値(デフォルト:-1.0)
            pan_l_axis                  
            pan_r_axis
            dev_fn
            auto_record_on_throttle
        """

        self.angle = 0.0
        self.throttle = 0.0
        self.mode = 'user'
        self.poll_delay = poll_delay
        self.running = True
        self.max_throttle = max_throttle
        self.steering_axis = steering_axis
        self.throttle_axis = throttle_axis
        self.steering_scale = steering_scale
        self.throttle_scale = throttle_scale
        self.pan_l = -1.0
        self.pan_r = -1.0
        self.pan_l_axis = pan_l_axis
        self.pan_r_axis = pan_r_axis
        self.pan = 0.0
        self.tilt = 0.0
        self.recording = False
        self.constant_throttle = False
        self.auto_record_on_throttle = auto_record_on_throttle
        self.dev_fn = dev_fn
        self.js = None

        # このPartクラスはThread動作前提の実装のため、
        # Parts フレームワークはファイル fn が更新されたら
        # 新しいスレッドを開始すると想定して動作します。
        # それを使用して、jsイベントのポーリングのために2つのスレッドを
        # 発生させるようにしました。

    def on_throttle_changes(self):
        """
        turn on recording when non zero throttle in the user mode.
        """

        #　スロットルオン時に記録フラグが真の場合
        if self.auto_record_on_throttle:
            # 記録フラグを更新する。
            # スロットルがオンであり、かつモードが'user'の場合のみ真値にする。
            self.recording = (self.throttle != 0.0 and self.mode == 'user')

    def init_js(self):
        """
        ジョイスティックの初期化を行う。

        引数
            なし
        戻り値
            真偽値  正常に初期化を完了したらTrue、例外発生時はFalseを返却
        """
        try:
            # ジョイスティックインスタンスを生成
            self.js = Joystick(self.dev_fn)
            # ジョイスティックインスタンスを初期化
            self.js.init()
        # キャラクタデバイスが存在しない場合
        except FileNotFoundError:
            print(self.dev_fn, "not found.")
            self.js = None
        # 正常に初期化を完了したらTrue、例外発生時はFalseを返却
        return self.js is not None


    def update(self):
        """
        poll a joystick for input events

        button map name => PS3 button => function
        * top2 = PS3 dpad up => increase throttle scale
        * base = PS3 dpad down => decrease throttle scale
        * base2 = PS3 dpad left => increase steering scale
        * pinkie = PS3 dpad right => decrease steering scale
        * trigger = PS3 select => switch modes
        * top = PS3 start => toggle constant throttle
        * base5 = PS3 left trigger 1
        * base3 = PS3 left trigger 2
        * base6 = PS3 right trigger 1
        * base4 = PS3 right trigger 2
        * thumb2 = PS3 right thumb
        * thumb = PS3 left thumb
        * circle = PS3 circrle => toggle recording
        * triangle = PS3 triangle => increase max throttle
        * cross = PS3 cross => decrease max throttle
        """

        # ジョイスティックがオンラインになるまで待機するループ。
        # ループ実行可否値および初期化完了を問い合わせ、
        # 両方真値になるまで5秒間隔で繰り返す。
        while self.running and not self.init_js():
            time.sleep(5)

        while self.running:
            button, button_state, axis, axis_val = self.js.poll()

            if axis == self.steering_axis:
                self.angle = self.steering_scale * axis_val
                print("angle", self.angle)

            if axis == self.throttle_axis:
                #this value is often reversed, with positive value when pulling down
                self.throttle = (self.throttle_scale * axis_val * self.max_throttle)
                print("throttle", self.throttle)
                self.on_throttle_changes()

            if axis == self.pan_l_axis:
                self.pan_l = axis_val
                print("pan_l", self.pan_l)
                self.pan = ((self.pan_l + 1) - (self.pan_r + 1)) / 2
                print("pan", self.pan)

            if axis == self.pan_r_axis:
                self.pan_r = axis_val
                print("pan_r", self.pan_r)
                self.pan = ((self.pan_l + 1) - (self.pan_r + 1)) / 2
                print("pan", self.pan)

            if button == 'tl' and button_state == 1:
                self.tilt = round(min(1.0, self.tilt + 0.1), 2)
                print('tilt:', self.tilt)

            if button == 'tr' and button_state == 1:
                self.tilt = round(max(-1.0, self.tilt - 0.1), 2)
                print('tilt:', self.tilt)

            if button == 'select' and button_state == 1:
                """
                switch modes from:
                user: human controlled steer and throttle
                local_angle: ai steering, human throttle
                local: ai steering, ai throttle
                """
                if self.mode == 'user':
                    self.mode = 'local_angle'
                elif self.mode == 'local_angle':
                    self.mode = 'local'
                else:
                    self.mode = 'user'
                print('new mode:', self.mode)

            if button == 'b' and button_state == 1:
                """
                toggle recording on/off
                """
                if self.auto_record_on_throttle:
                    self.recording = False
                    print('auto record on throttle is disabled.')
                    self.auto_record_on_throttle = False
                else:
                    self.recording = False
                    print('auto record on throttle is enabled.')
                    self.auto_record_on_throttle = True

                print('recording:', self.recording)

            if button == 'y' and button_state == 1:
                """
                increase max throttle setting
                """
                self.max_throttle = round(min(1.0, self.max_throttle + 0.01), 2)
                if self.constant_throttle:
                    self.throttle = self.max_throttle
                    self.on_throttle_changes()

                print('max_throttle:', self.max_throttle)

            if button == 'a' and button_state == 1:
                """
                decrease max throttle setting
                """
                self.max_throttle = round(max(0.0, self.max_throttle - 0.01), 2)
                if self.constant_throttle:
                    self.throttle = self.max_throttle
                    self.on_throttle_changes()

                print('max_throttle:', self.max_throttle)

            if axis == 'hat0y' and axis_val == 1:
                """
                increase throttle scale
                """
                self.throttle_scale = round(min(0.0, self.throttle_scale + 0.05), 2)
                print('throttle_scale:', self.throttle_scale)

            if axis == 'hat0y' and axis_val == -1:
                """
                decrease throttle scale
                """
                self.throttle_scale = round(max(-1.0, self.throttle_scale - 0.05), 2)
                print('throttle_scale:', self.throttle_scale)

            if axis == 'hat0x' and axis_val == 1:
                """
                increase steering scale
                """
                self.steering_scale = round(min(1.0, self.steering_scale + 0.05), 2)
                print('steering_scale:', self.steering_scale)

            if axis == 'hat0x' and axis_val == -1:
                """
                decrease steering scale
                """
                self.steering_scale = round(max(0.0, self.steering_scale - 0.05), 2)
                print('steering_scale:', self.steering_scale)

            if button == 'start' and button_state == 1:
                """
                toggle constant throttle
                """
                if self.constant_throttle:
                    self.constant_throttle = False
                    self.throttle = 0
                    self.on_throttle_changes()
                else:
                    self.constant_throttle = True
                    self.throttle = self.max_throttle
                    self.on_throttle_changes()
                print('constant_throttle:', self.constant_throttle)

            time.sleep(self.poll_delay)

    def run_threaded(self, img_arr=None):
        self.img_arr = img_arr
        return self.angle, self.throttle, self.mode, self.recording, self.pan, self.tilt

    def run(self, img_arr=None):
        raise Exception("We expect for this part to be run with the threaded=True argument.")
        return False

    def shutdown(self):
        self.running = False
        time.sleep(0.5)


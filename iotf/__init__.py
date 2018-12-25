# -*- coding: utf-8 -*-
"""
スロットル、アングル値をMQTTブローカへPublishするPubTelemetryクラスと
AIのかわりにMQTTブローカからスロット、アングル値を受け取るSubPilotクラスを提供する。
なお本ファイル上のクラスはすべて IBM Watson IoT Platform をMQTTブローカとして使用しており、
ibmiotf パッケージをインストールする必要がある。

pip install ibmiotf
"""

import os
import json
import numpy as np
import donkeycar as dk
import logging
#import datetime
from ibmiotf import MessageCodec, Message, InvalidEventException
import ibmiotf.device
import ibmiotf.application
import pytz
from datetime import datetime

class LogBase:
    """
    ログ出力ユーティリティメソッドを備えた基底クラス。
    """
    def __init__(self, debug=False):
        """
        デバッグフラグをインスタンス変数へ格納する。

        引数
            debug   デバッグフラグ
        戻り値
            なし
        """
        self.debug = debug
    
    def log(self, msg):
        """
        debugレベルのログを出力する。

        引数
            msg メッセージ文字列
        戻り値
            なし
        """
        if self.debug:
            print(msg)


class IoTFPubBase(LogBase):
    """
    IBM Watson IoT Platform をMQTTブローカとして使用するPublisher基底クラス。
    """
    def __init__(self, dev_conf_path, debug=False):
        """
        設定ファイルからデバイス情報を読み込み、MQTTブローカへ接続する。

        引数
            dev_conf_path   デバイス設定ファイルのパス
            debug           デバッグフラグ
        戻り値
            なし
        """
        super().__init__(debug)
        self.log('[__init__] start dev_conf_path={}, msgFormat'.format(dev_conf_path))

        try:
            dev_options = ibmiotf.device.ParseConfigFile(dev_conf_path)
            self.log('[__init__] dev config loaded options=' + str(dev_options))
            self.client = ibmiotf.device.Client(dev_options)
            self.log('[__init__] new client')
            self.client.setMessageEncoderModule('image', ImageCodec)
            self.log('[__init__] add image codec')
        except ibmiotf.ConnectionException  as e:
            self.log('[__init__] config load failed ' + dev_conf_path)
            raise e

        self.client.connect()
        self.log('[__init__] connect client')

    def publishImageEvent(self, event='status', msg_bin=None, qos=0):
        """
        テキストデータをイベントステータスでpublishする。
        引数 msg_text は、本メソッド内部で UTF-8 にエンコードしてpublishされる。

        引数
            event       イベント名
            msg_text    データ（文字列型）
            qos         QoSレベル
        戻り値
            なし
        """
        self.log('[publishImageEvent] start event={}, msg_bin={}, qos={}'.format(
            event, str(msg_bin), str(qos)))
        self.publishEvent(event=event, data=msg_bin, msgFormat='image', qos=qos)

    def publishJsonEvent(self, event='status', msg_dict={}, qos=0):
        """
        JSON型式データをイベントステータスでpublishする。
        JSON は、Watson IoT Platform の標準形式である。
        組み込みの Watson IoT Platform ダッシュボードを使用する予定の場合は、
        メッセージ・ペイロード・フォーマットが整形式 JSON テキストに準拠していること
        を確認すること。

        引数
            event       イベント名
            msg_dict    データ（辞書型）
            qos         QoSレベル
        戻り値
            なし
        """
        self.log('[publishJsonEvent] start event={}, msg_dict={}, qos={}'.format(
            event, str(msg_dict), str(qos)))
        self.publishEvent(event=event, data=msg_dict, msgFormat='json', qos=qos)
    
    def publishEvent(self, event, data, msgFormat, qos):
        """
        イベントステータスでpublishする。
        Watson IoT Platform のペイロードの最大サイズは、131072 バイトであり、これを超えた
        場合は拒否される。

        引数
            event       イベント名
            data        データ
            msgFormat   データフォーマット（json/image）
            qos         QoSレベル
        戻り値
            なし
        """
        self.log('[publishEvent] event={}, megFormat={}, len(data)={}, qos={}'.format(
            event, msgFormat, str(len(data)), str(qos)))
        self.client.publishEvent(event=event, msgFormat=msgFormat, data=data, qos=qos)
        self.log('[publishJson] published')
    
    def disconnect(self):
        self.client.disconnect()
        self.log('[disconnect] disconnected client')


class IoTFSubBase(LogBase):
    """
    IBM Watson IoT Platform をMQTTブローカとして使用するSubscriber基底クラス。
    """
    def __init__(self, dev_conf_path, app_conf_path, msgFormat='json', debug=False):
        """
        設定ファイルからアプリケーションを読み込み、MQTTブローカへ接続する。
        デバイス設定ファイルは、購読元デバイス情報を入手するために読み込んでいる。

        引数
            dev_conf_path   デバイス設定ファイルのパス
            app_conf_path   アプリケーション設定ファイルのパス
            msgFormat       メッセージフォーマット(json/text/bin)
            debug           デバッグフラグ
        戻り値
            なし
        """
        super().__init__(debug)
        self.log('[__init__] start dev_conf_path={}, app_conf_path={}'.format(
            dev_conf_path, app_conf_path))
        self.msgFormat = msgFormat
        self.log('[__init__] msgFormat=' + msgFormat)

        try:
            # 送信元情報の入手
            dev_options = ibmiotf.device.ParseConfigFile(dev_conf_path)
            self.log('[__init__] dev config loaded options=' + str(dev_options))
            self.dev_type = dev_options['type']
            self.dev_id = dev_options['id']
            self.log('[__init__] dev_type={}, dev_id={}'.format(self.dev_type, self.dev_id))

            app_options = ibmiotf.application.ParseConfigFile(app_conf_path)
            self.log('[__init__] app config loaded options=' + str(app_options))
            self.client = ibmiotf.application.Client(app_options)
            self.log('[__init__] new client')
            if msgFormat == 'image':
                self.client.setMessageEncoderModule('image', ImageCodec)
                self.log('[__init__] add image codec')
        except ibmiotf.ConnectionException  as e:
            self.log('[__init__] config load failed ' + app_conf_path)
            raise e
        
        self.client.connect()
        self.log('[__init__] connect client')

    def subscribe(self, event=None, on_subscribe=None):
        if on_subscribe is None:
            self.client.deviceEventCallback = self._on_subscribe
        else:
            self.client.deviceEventCallback = on_subscribe
        self.log('[subscribe] set on_subscribe')
        if event is None:
            self.client.subscribeToDeviceEvents(
                deviceType=self.dev_type, deviceId=self.dev_id)
            self.log('[subscribe] subscribe dev_type={}, dev_id={}'.format(
                self.dev_type, self.dev_id))
        else:
            self.client.subscribeToDeviceEvents(
                deviceType=self.dev_type, deviceId=self.dev_id, event=event, msgFormat=self.msgFormat)
            self.log('[subscribe] subscribe dev_type={}, dev_id={}, event={}, format={}'.format(
                self.dev_type, self.dev_id, event, self.msgFormat))

    def _on_subscribe(self, event):
      str = "[on_subscribe] %s event '%s' received from device [%s]: %s"
      self.log(str % (event.format, event.event, event.device, json.dumps(event.data)))

    def disconnect(self):
        self.client.disconnect()
        self.log('[disconnect] disconnected client')

class PubTelemetry(IoTFPubBase):
    """
    テレメトリデータを送信する。
    """
    def __init__(self, dev_conf_path, pub_count=1000, debug=False):
        """
        ログ出力準備を行い、設定ファイルを読み込みMQTTクライアントの接続を確立する。

        引数
            dev_conf_path   設定ファイルへのパス
            pub_count       publishが実行される間隔
            debug           デバッグフラグ
        戻り値
            なし
        """
        super().__init__(dev_conf_path, debug)
        self.throttle = 1.0
        self.angle = 1.0
        self.delta = 0.005
        self.count = 0
        self.pub_count = abs(pub_count)
        self.log('[__init__] end')

    def run(self, image_array, user_mode, user_angle, user_throttle, pilot_angle, pilot_throttle):
        """
        スロットル値、アングル値を含むJSONデータをMQTTブローカへ送信する。
        引数
            image_array         カメラ画像イメージデータ(np.ndarray)
            user_mode           運転モード(user,local_angle,local)
            user_angle          手動操作によるアングル値
            user_throttle       手動操作によるスロットル値
            pilot_angle         自動運転アングル値
            pilot_throttle      自動運転スロットル値
        戻り値
            なし
        """
        # pub_count数に達したら実行
        self.count = self.count + 1
        if self.count <= self.pub_count:
            #self.log('[run] ignnore data, very often sending')
            return
        else:
            self.count = 0
        
        angle, throttle = self.getAction(user_mode, user_angle, user_throttle, pilot_angle, pilot_throttle)
        if self.isInDelta(user_mode, user_angle, user_throttle, pilot_angle, pilot_throttle):
            self.log('[run] ignnore data, delta is small th:[{}, {}] an[{}, {}]'.format(
                str(throttle), str(self.throttle), str(angle), str(self.angle)))

        msg_dict = {
            "user_mode":        user_mode,
            "user_angle":       user_angle,
            "user_throttle":    user_throttle,
            "pilot_angle":      pilot_angle,
            "pilot_throttle":   pilot_throttle,
            "angle":            angle,
            "throttle":         throttle,
            "timestamp":        str(datetime.now())
        }


        #self.log('[run] image_arrat type: ' + type(image_array))
        self.publishImageEvent(msg_bin=image_array)
        self.publishJsonEvent(msg_dict=msg_dict)
        self.angle = angle
        self.throttle = throttle
        self.log('[run] published telemetry data')

    def getAction(self, user_mode, user_angle, user_throttle, pilot_angle, pilot_throttle):
        """
        ユーザモードから実際にDonkey Carが採用したアングル値、スロットル値を返却する。

        引数
            user_mode           運転モード(user,local_angle,local)
            user_angle          手動操作によるアングル値
            user_throttle       手動操作によるスロットル値
            pilot_angle         自動運転アングル値
            pilot_throttle      自動運転スロットル値
        戻り値
            angle               実際に採用したアングル値
            throttle            実際に採用したスロットル値
        """
        # 運転モードから実際に使用されたアングル、スロットル値を判断
        if user_mode == 'user':
            return user_angle, user_throttle
        elif user_mode == 'local_angle':
            return user_angle, pilot_throttle
        else:
            return pilot_angle, pilot_throttle

    def isInDelta(self, user_mode, user_angle, user_throttle, pilot_angle, pilot_throttle):
        """
        アングル、スロットル値が前に送信した値とほとんど変わらないかどうかを判定する。

        引数
            user_mode           運転モード(user,local_angle,local)
            user_angle          手動操作によるアングル値
            user_throttle       手動操作によるスロットル値
            pilot_angle         自動運転アングル値
            pilot_throttle      自動運転スロットル値
        戻り値
            eval                しきい値範囲内：真、しきい値範囲外：偽
        """
        # 運転モードから実際に使用されたアングル、スロットル値を判断
        angle, throttle = self.getAction(user_mode, user_angle, user_throttle, 
        pilot_angle, pilot_throttle)

        # アングル、スロットル値が前に送信した値とほとんど変わらないかどうか
        isInDelta_throttle = abs(abs(throttle) - abs(self.throttle)) < self.delta
        isInDelta_angle =  abs(abs(angle) - abs(self.angle)) < self.delta
        return isInDelta_throttle and isInDelta_angle
            
    
    def shutdown(self):
        self.disconnect()
        self.log('[shutdown] disconnect client')

class ImageCodec(MessageCodec):
    """
    フォーマット形式'image'に対応するCodecクラス。
    
      deviceCli.setMessageCodec("image", ImageCodec)
    """
    
    @staticmethod
    def encode(data=None, timestamp=None):
        """
        data を送信可能なデータに変換する。
        data がnp.ndarray型の場合はtobytes()を返却する。

        引数
            data        送信データ
            timestamp   タイムスタンプ
        戻り値
            data        送信データ        
        """
        if type(data) is np.ndarray:
          return dk.util.img.arr_to_binary(data)
        return data
    
    @staticmethod
    def decode(message):
        """
        文字列をnp.ndarray型式に戻し型を(120, 160, 3)に戻す。

        引数
            message     受信メッセージ
        戻り値
            Messageオブジェクト
        """
        try:
            data = message.payload.decode('utf-8')
            data = np.fromstring(data, dtype=np.uint8)
            data = np.reshape(data, (120, 160, 3))
        except ValueError as e:
            raise InvalidEventException("Unable to parse image.  payload=\"%s\" error=%s" % (message.payload, str(e)))
        
        timestamp = datetime.now(pytz.timezone('UTC'))
        
        # TODO: Flatten JSON, covert into array of key/value pairs
        return Message(data, timestamp)

class SubPilot(IoTFSubBase):
    """
    外部オートパイロットから次のスロットル値、アングル値を取得する。
    """
    def __init__(self, dev_conf_path, app_conf_path, debug=False):
        """
        MQTT通信の準備を行い、インスタンス変数を初期化する。

        引数
            dev_conf_path   デバイス側設定ファイル
            app_conf_path   アプリケーション側設定ファイル
            debug           デバッグモード
        戻り値
            なし
        """
        super().__init__(dev_conf_path, app_conf_path, debug)
        self.throttle = 0.0
        self.angle = 0.0
        self.timestamp = datetime.now().isoformat()
        self.log('[__init__] end')

    def on_subscribe(self, event):
        """
        イベントデータ受信したとき、受領したスロットル値、アングル値を
        インスタンス変数へ格納する。

        引数
            event       イベントデータ
        戻り値
            なし
        """
        self.log('[on_subscribe] call at ' + event.timestamp.isoformat())
        self.log('[on_subscribe] event.data=' + json.dumps(event.data))
        self.throttle = float(event.data['throttle'])
        self.angle = float(event.data['angle'])
        self.timestamp = str(event.data['timestamp'])
    
    def run(self):
        """
        インスタンス変数として格納されているスロットル値、アングル値を返却する。

        引数
            なし
        戻り値
            throttle    スロットル値
            angle       アングル値
            timestamp   タイムスタンプ文字列
        """
        self.log('[run] return throttle={}, angle={}, timestamp={}'.format(
            str(self.throttle), str(self.angle), str(self.timestamp)))
        return self.throttle, self.angle, self.timestamp
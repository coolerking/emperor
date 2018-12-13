# -*- coding: utf-8 -*-
"""
スロットル、アングル値をMQTTブローカへPublishするPubTelemetryクラスと
AIのかわりにMQTTブローカからスロット、アングル値を受け取るSubPilotクラスを提供する。
なお本ファイル上のクラスはすべて IBM Watson IoT Platform をMQTTブローカとして使用しており、
ibmiotf パッケージをインストールする必要がある。

pip install ibmiotf
"""

import json
import logging
import datetime
import ibmiotf.device
import ibmiotf.application

class LogBase:
    """
    ログ出力ユーティリティメソッドを備えた基底クラス。
    """
    def __init__(self, logger=None):
        if logger is None:
            self.logger = logging.getLogger('LogBase')
            self.logger.setLevel(10)
            self.logger.addHandler(logging.StreamHandler())
        else:
            self.logger = logger

    def info(self, msg):
        """
        infoレベルのログを出力する。

        引数
            msg メッセージ文字列
        戻り値
            なし
        """
        self.logger.info(msg)
    
    def debug(self, msg):
        """
        debugレベルのログを出力する。

        引数
            msg メッセージ文字列
        戻り値
            なし
        """
        self.logger.debug(msg)


class IoTFPubBase(LogBase):
    """
    IBM Watson IoT Platform をMQTTブローカとして使用するPublisher基底クラス。
    """
    def __init__(self, dev_conf_path, logger):
        """
        設定ファイルからデバイス情報を読み込み、MQTTブローカへ接続する。

        引数
            dev_conf_path   デバイス設定ファイルのパス
            logger          ロガーオブジェクト
        戻り値
            なし
        """
        super().__init__(self.logger)
        self.debug('[__init__] start dev_conf_path={}'.format(dev_conf_path))

        try:
            dev_options = ibmiotf.device.ParseConfigFile(dev_conf_path)
            self.debug('[__init__] dev config loaded options=' + str(dev_options))
            self.client = ibmiotf.device.Client(dev_options)
            self.debug('[__init__] new client')
        except ibmiotf.ConnectionException  as e:
            self.debug('[__init__] config load failed ' + dev_conf_path)
            raise e

        self.client.connect()
        self.debug('[__init__] connect client')


    def publish(self, event='status', msg_dict={}, qos=0):
        self.debug('[publish] start event={}, msg_dict={}, qos={}'.format(
            event, str(msg_dict), str(qos)))
        self.client.publishEvent(event=event, msgFormat='json', data=msg_dict, qos=0)
        self.debug('[publish] published')
    
    def disconnect(self):
        self.client.disconnect()
        self.debug('[disconnect] disconnected client')


class IoTFSubBase(LogBase):
    """
    IBM Watson IoT Platform をMQTTブローカとして使用するSubscriber基底クラス。
    """
    def __init__(self, dev_conf_path, app_conf_path, logger):
        """
        設定ファイルからアプリケーションを読み込み、MQTTブローカへ接続する。
        デバイス設定ファイルは、購読元デバイス情報を入手するために読み込んでいる。

        引数
            dev_conf_path   デバイス設定ファイルのパス
            app_conf_path   アプリケーション設定ファイルのパス
            logger          ロガーオブジェクト
        戻り値
            なし
        """
        super().__init__(logger)
        self.debug('[__init__] start dev_conf_path={}, app_conf_path={}'.format(
            dev_conf_path, app_conf_path))

        try:
            # 送信元情報の入手
            dev_options = ibmiotf.device.ParseConfigFile(dev_conf_path)
            self.debug('[__init__] dev config loaded options=' + str(dev_options))
            self.dev_type = dev_options['type']
            self.dev_id = dev_options['id']
            self.debug('[__init__] dev_type={}, dev_id={}'.format(self.dev_type, self.dev_id))

            app_options = ibmiotf.application.ParseConfigFile(app_conf_path)
            self.debug('[__init__] app config loaded options=' + str(app_options))
            self.client = ibmiotf.application.Client(app_options)
            self.debug('[__init__] new client')
        except ibmiotf.ConnectionException  as e:
            self.debug('[__init__] config load failed ' + app_conf_path)
            raise e
        
        self.client.connect()
        self.debug('[__init__] connect client')

    def subscribe(self, event=None, on_subscribe=None):
        if on_subscribe is None:
            self.client.deviceEventCallback = self._on_subscribe
        else:
            self.client.deviceEventCallback = on_subscribe
        self.debug('[subscribe] set on_subscribe')
        if event is None:
            self.client.subscribeToDeviceEvents(
                deviceType=self.dev_type, deviceId=self.dev_id)
            self.debug('[subscribe] subscribe dev_type={}, dev_id={}'.format(
                self.dev_type, self.dev_id))
        else:
            self.client.subscribeToDeviceEvents(
                deviceType=self.dev_type, deviceId=self.dev_id, event=event, msgFormat='json')
            self.debug('[subscribe] subscribe dev_type={}, dev_id={}, event={}, format=json'.format(
                self.dev_type, self.dev_id, event))

    def _on_subscribe(self, event):
      str = "[on_subscribe] %s event '%s' received from device [%s]: %s"
      self.debug(str % (event.format, event.event, event.device, json.dumps(event.data)))

    def disconnect(self):
        self.client.disconnect()
        self.debug('[disconnect] disconnected client')

class PubTelemetry(IoTFPubBase):
    def __init__(self, dev_conf_path, logger=None):
        if logger is None:
            logger = logging.getLogger('PubTelemetry')
            logger.setLevel(10)
            logger.addHandler(logging.StreamHandler())
        super().__init__(dev_conf_path, logger)
        self.debug('[__init__] end')

    def run(self, throttle=0.0, angle=0.0):
        """
        スロットル値、アングル値を含むJSONデータをMQTTブローカへ送信する。
        引数
            throttle    スロットル値
            angle       アングル値
        戻り値
            なし
        """
        msg_dict = {
            "throttle": throttle,
            "angle": angle,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.publish(msg_dict=msg_dict)
        self.debug('[run] publish :' + json.dumps(msg_dict))
    
    def shutdown(self):
        self.disconnect()
        self.debug('[shutdown] disconnect client')

class SubPilot(IoTFSubBase):
    def __init__(self, dev_conf_path, app_conf_path, logger=None):
        if logger is None:
            logger = logging.getLogger('SubPilot')
            logger.setLevel(10)
            logger.addHandler(logging.StreamHandler())
        super().__init__(dev_conf_path, app_conf_path, logger)
        self.throttle = 0.0
        self.angle = 0.0
        self.timestamp = datetime.datetime.now().isoformat()
        self.debug('[__init__] end')

    def on_subscribe(self, event):
        self.debug('[on_subscribe] call at ' + event.timestamp.isoformat())
        self.debug('[on_subscribe] event.data=' + json.dumps(event.data))
        self.throttle = float(event.data['throttle'])
        self.angle = float(event.data['angle'])
        self.timestamp = str(event.data['timestamp'])
    
    def run(self):
        self.debug('[run] return throttle={}, angle={}, timestamp={}'.format(
            str(self.throttle), str(self.angle), str(self.timestamp)))
        return self.throttle, self.angle, self.timestamp
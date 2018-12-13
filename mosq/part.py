# -*- coding: utf-8 -*-
"""
スロットル、アングル値をMQTTブローカへPublishするPubTelemetryクラスと
AIのかわりにMQTTブローカからスロット、アングル値を受け取るSubPilotクラスを提供する。
なお本ファイル上のクラスはすべて eclipse-mosquitto をMQTTブローカとして使用しており、
paho-mqtt パッケージをインストールする必要がある。

pip install paho-mqtt
"""

import os
import json
import yaml
import logging
import datetime
import paho.mqtt.client as mqtt

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

class ConfigBase(LogBase):
    """
    ログ基底クラスに設定ファイルを読み込みインスタンス変数へ格納する機能を
    デコレートした基底クラス。
    """
    def __init__(self, conf_path, logger=None):
        """
        設定ファイルを読み込み、インスタンス変数へ格納する。
        引数
            conf_path   設定ファイルのパス
            logger      ロガーオブジェクト
        戻り値
            なし
        """
        if logger is None:
            logger = logging.getLogger('Config')
            logger.setLevel(10)
            logger.addHandler(logging.StreamHandler())
        super().__init__(logger)

        conf_path = os.path.expanduser(conf_path)
        if not os.path.exists(conf_path):
            raise Exception('[__init__] conf_path={} is not exists'.format(conf_path))
        if not os.path.isfile(conf_path):
            raise Exception('[__init__] conf_path={} is not a file'.format(conf_path))

        with open(conf_path, 'r') as f:
            conf = yaml.load(f)
        self.debug('[__init__] read conf : ' + str(conf))

        broker_conf = conf['broker']

        self.host = broker_conf['host']
        if self.host is None:
            self.host = '127.0.0.1'
        self.port = broker_conf['port']
        if self.port is None:
            self.port = 1883
        else:
            self.port = int(self.port)
        
        pub_conf = conf['publisher']
        self.pub_topic = pub_conf['topic']

        sub_conf = conf['subscriber']
        self.sub_topic = sub_conf['topic']

        self.debug('[__init__] host=' + self.host)
        self.debug('[__init__] port=' + str(self.port))
        self.debug('[__init__] pub_topic=' + self.pub_topic)
        self.debug('[__init__] sub_topic=' + self.sub_topic)

class MosqPubBase(ConfigBase):
    """
    eclipse-mosquitto を MQTT ブローカとして使用する Publisher 基底クラス。
    """
    def __init__(self, conf_path, logger=None):
        """
        設定ファイルからデバイス情報を読み込み、MQTTブローカへ接続する。

        引数
            conf_path   デバイス設定ファイルのパス
            logger          ロガーオブジェクト
        戻り値
            なし
        """
        if logger is None:
            logger = logging.getLogger('MosqPubBase')
            logger.setLevel(10)
            logger.addHandler(logging.StreamHandler())
        super().__init__(conf_path, logger)
        self.debug('[__init__] start dev_conf_path={}'.format(conf_path))

        self.client = mqtt.Client(protocol=mqtt.MQTTv311)

        self.debug("[__init__] new client")

        self.client.connect(self.host, port=self.port, keepalive=60)
        self.debug("[__init__] connect client host:" + self.host + ', port:' + str(self.port))


    def publish(self, msg_dict={}):
        """
        引数msg_dictで与えられた辞書をJSONデータ化してpublish処理を実行する。

        引数
            msg_dict    送信メッセージ（辞書）
        戻り値
            なし
        """
        self.debug('[publish] start msg_dict={}'.format(json.dumps(msg_dict)))
        self.client.publish(self.pub_topic, json.dumps(msg_dict))
        self.debug('[publish] published topic:' + self.pub_topic)
    
    def disconnect(self):
        """
        接続を解除する。

        引数
            なし
        戻り値
            なし
        """
        self.client.disconnect()
        self.debug('[disconnect] disconnected client')


class MosqSubBase(ConfigBase):
    """
    eclipse-mosquitto をMQTTブローカとして使用するSubscriber基底クラス。
    """
    def __init__(self, conf_path, on_message=None, logger=None):
        """
        設定ファイルからデバイス情報を読み込み、MQTTブローカへ接続する。

        引数
            conf_path   デバイス設定ファイルのパス
            on_message  メッセージ受信時コールバック関数
            logger      ロガーオブジェクト
        戻り値
            なし
        """
        if logger is None:
            logger = logging.getLogger('MosqPubBase')
            logger.setLevel(10)
            logger.addHandler(logging.StreamHandler())
        super().__init__(conf_path, logger)
        self.debug('[__init__] start dev_conf_path={}'.format(conf_path))

        self.client = mqtt.Client(protocol=mqtt.MQTTv311)

        self.debug("[__init__] new client")

        self.client.on_connect = self.on_connect
        self.debug('[__init__] set default on_connect')
        if on_message is None:
            self.client.on_message = self._on_message
            self.debug('[__init__] set default on_message')
        else:
            self.client.on_message = on_message
            self.debug('[__init__] set on_message')

        self.client.connect(self.host, port=self.port, keepalive=60)
        self.debug("[__init__] connect client host:" + self.host + ', port:' + str(self.port))
    
    def on_connect(self, client, userdata, flags, respons_code):
        """
        接続時コールバック関数、この中でトピックの購読を開始している。

        引数
            client          MQTTクライアントオブジェクト
            userdata        ユーザデータ
            flags           フラグ
            response_code   返却コード
        戻り値
            なし
        """
        self.debug('[on_connect] status {0}'.format(respons_code))
        self.client.subscribe(self.sub_topic)
        self.debug('[on_connect] subscribe topic=' + self.sub_topic)
    
    def _on_message(self, client, userdata, message):
        """
        デフォルトのメッセージ受信時コールバック関数、実装なし。

        引数
            client          MQTTクライアントオブジェクト
            userdata        ユーザデータ
            message         受診メッセージ
        戻り値
            なし
        """
        self.debug('[_on_message] no operation ' + message.topic + ' ' + str(message.payload))

    def disconnect(self):
        """
        クライアント接続を解除する。

        引数   
            なし
        戻り値
            なし
        """
        self.client.disconnect()
        self.debug('[disconnect] disconnected client')

class PubTelemetry(MosqPubBase):
    """
    スロットル、アングル値をMQTTブローカへPublishするPubTelemetryクラス。
    """
    def __init__(self, conf_path, logger=None):
        """
        設定ファイルを読み込み、MQTTクライアントを生成、接続する。

        引数
            config_path     設定ファイルのパス
            logger          ロガーオブジェクト
        戻り値
            なし
        """
        if logger is None:
            logger = logging.getLogger('PubTelemetry')
            logger.setLevel(10)
            logger.addHandler(logging.StreamHandler())
        super().__init__(conf_path, logger)
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
        """
        MQTTクライアント接続を解除する。

        引数
            なし
        戻り値
            なし
        """
        self.disconnect()
        self.debug('[shutdown] disconnect client')

class SubPilot(MosqSubBase):
    """
    AIのかわりにMQTTブローカからスロット、アングル値を受け取るSubPilotクラス
    """
    def __init__(self, conf_path, logger=None):
        """
        設定ファイルを読み込み、MQTTクライアントを生成、接続する。

        引数
            config_path     設定ファイルのパス
            logger          ロガーオブジェクト
        戻り値
            なし
        """
        if logger is None:
            logger = logging.getLogger('SubPilot')
            logger.setLevel(10)
            logger.addHandler(logging.StreamHandler())
        super().__init__(conf_path, self.on_message, logger)
        self.throttle = 0.0
        self.angle = 0.0
        self.timestamp = datetime.datetime.now().isoformat()
        self.debug('[__init__] end')

    def on_message(self, client, userdata, message):
        """
        デフォルトのメッセージ受信時コールバック関数。
        取得したスロットル値、アングル値をインスタンス変数へ格納する。

        引数
            client          MQTTクライアントオブジェクト
            userdata        ユーザデータ
            message         受診メッセージ
        戻り値
            なし
        """
        self.debug('[on_message] start ' + message.topic + ' ' + str(message.payload))
        data = message.payload
        self.debug('[on_message] message.payload is ' + type(data))
        self.throttle = float(data['throttle'])
        self.angle = float(data['angle'])
        self.timestamp = str(data['timestamp'])
    
    def run(self):
        """
        最新のスロットル値、アングル値を返却する。

        引数
            なし
        戻り値
            throttle    スロットル値
            angle       アングル値
        """
        self.debug('[run] return throttle={}, angle={}, timestamp={}'.format(
            str(self.throttle), str(self.angle), str(self.timestamp)))
        return self.throttle, self.angle #, self.timestamp
    
    def shutdown(self):
        """
        MQTTクライアント接続を解除する。

        引数
            なし
        戻り値
            なし
        """
        self.disconnect()
        self.debug('[shutdown] disconnect client')
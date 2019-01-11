# -*- coding: utf-8 -*-
"""
ibmiotfパッケージ用カスタムコーデックモジュール。
donkeycarのvehicleフレームワークで取り扱う、画像イメージデータ(np.ndarray型-uint8、(120,160,3))
をIBM Watson IoT Platform へ送受信する際にibmiotfパッケージから使用される。
"""
from datetime import datetime
import pytz
import base64
import numpy as np
from ibmiotf import Message
import donkeycar as dk

from logging import getLogger
logger = getLogger(__name__)

class ImageCodec:
    @staticmethod
    def encode(data=None, timestamp=None):
        '''
        np.ndarray形式の場合はdonkeycar.util.imgを使ってバイナリへ変換する。
        文字列型の場合は、encode()後、base64でdecodeしてバイナリへ変換する。
        その他はそのまま送信する。

        引数
            date        送信データ
            timestamp   時刻（使用されない）
        戻り値
            実際に送信される送信データ
        '''
        if type(data) is np.ndarray:
            logger.debug('encode: data is np.ndarray')
            return dk.util.img.arr_to_binary(data)
        if type(data) is str:
            logger.debug('encode: data is str')
            return base64.b64decode(data.encode())
        logger.debug('encode: data is {}'.format(str(type(data))))
        return data

    @staticmethod
    def decode(message):
        '''
        message.payloadに格納された受信データをbase64にエンコードした文字列として
        Messageオブジェクトへ格納、返却する。

        引数
            message     受信データ
        戻り値
            ibmiotfパッケージとして取扱可能なMessageオブジェクト
        '''
        data = message.payload
        if type(data) is bytes:
            logger.debug('decode: data is bytes')
            data = base64.b64encode(message.payload).decode('utf-8')
        timestamp = datetime.now(pytz.timezone('UTC'))
    
        return Message(data, timestamp)

    @staticmethod
    def encode_to_arr(data=None, timestamp=None):
        '''
        data をnd.array型式(120,160,3)型のuint8配列に変換する。
    
        引数
            data        送信データ
            timestamp   時刻（使用しない）
        戻り値
            ibmiotfパッケージとして取扱可能なMessageオブジェクト
        '''
        if type(data) is str:
            logger.debug('encode_to_arr: data is str')
            data = base64.b64decode(data.encode())
        if type(data) is bytes:
            logger.debug('encode_to_arr: data is bytes')
            data = dk.util.img.binary_to_img(data)
            data = dk.util.img.img_to_arr(data)
        logger.debug('encode_to_arr: data is converted to {}'.format(str(type(data))))
        return data

    @staticmethod
    def get_now_str():
        '''
        現在時刻文字列を取得する。

        引数
            なし
        戻り値
            現在時刻文字列
        '''
        return str(datetime.now(pytz.timezone('UTC')))

# -*- coding: utf-8 -*-
"""
tubclean 実行後のtubデータを再度番号を振り直すユーティリティプログラム。
以下の手順で実行する。
1. cd ~/mycar
2. python manage.py drive [--js] を実行し、運転データをtubディレクトリへ保管
3. mv data data_old
5. python tubarrange.py
6. cd data
7. floyd login && floyd data init user_name/data_prj_name
8. floyd data upload
9. floyd.xml を編集し floyd run --task train
10. mypilotをダウンロードし、~/mycar/models/mypilot としてコピー
11. python manage.py drive --model models/mypilot [--js] を実行して自動運転開始


Usage:
    tubarrange.py [--tub=<tub1,tub2,..tubn>]  [--data=<>dada_dir] [--debug]

Options:
    --tub TUBPATHS   tubファイルが格納されているディレクトリへのパスを指定する。
    --data DATADIR   整理後データが格納されるディレクトリ。
    --debug          デバッグモード。
"""
import os
import json
import shutil
import docopt
#import donkeycar as dk

class Arranger:
    """
    donkey tubclean 直後のtubデータを再整理するユーティリティクラス。
    """
    # デフォルトディレクトリ
    DEFAULT_TUB_DIR = 'tub'
    DEFAULT_DATA_DIR = 'data'
    # tubデータ関連の定数
    JSON_PREFIX = 'record_' # JSONファイル接頭文字列
    JSON_SUFFIX = '.json' # JSONファイル接尾文字列
    META_JSON_FILE = 'meta.json' # metaデータJSONファイル
    JPG_SUFFIX = '_cam-image_array_.jpg' # イメージファイル接尾文字列
    JSONKEY_IMAGE = 'cam/image_array' # イメージファイル名を値に持つキー

    def __init__(self, tub_dir, debug=False):
        """
        tubディレクトリを評価し、問題がなければ、tubデータ情報をインスタンス変数へ展開する。

        引数
            tub_dir   tubディレクトリへのパス
            debug     デバッグモード
        """
        self.debug = debug
        self.tub_dir = self.eval_tub_dir(tub_dir)
        self.init()

    def eval_tub_dir(self, tub_dir):
        """
        引数tub_dirが指すディレクトリが存在するかどうかを評価する。

        引数
            tub_dir   tubディレクトリへのパス
        戻り値
            tub_dir   tubディレクトリへのパス
        例外
            Exception 存在しないもしくはファイルだった場合
        """
        # デフォルト設定
        if tub_dir is None:
            base_dir = os.path.dirname(os.path.realpath(__file__))
            tub_dir = os.path.join(base_dir, self.DEFAULT_TUB_DIR)
        # 指定ありの場合は、絶対パス化
        else:
            tub_dir = os.path.expanduser(tub_dir)
        
        if self.debug:
            print('use tub_dir = ' + tub_dir)
        
        # 評価
        if not os.path.exists(tub_dir):
            raise Exception(tub_dir + ' is not exists')
        elif not os.path.isdir(tub_dir):
            raise Exception (tub_dir + ' is not a directory')
        
        return tub_dir
    
    def eval_data_dir(self, data_dir):
        """
        引数data_dirが指すディレクトリが存在するかどうかを評価する。

        引数
            data_dir  dataディレクトリへのパス
        戻り値
            data_dir  dataディレクトリへのパス
        例外
            Exception ファイルだった場合
        """
        # デフォルト設定
        if data_dir is None:
            base_dir = os.path.dirname(os.path.realpath(__file__))
            data_dir = os.path.join(base_dir, self.DEFAULT_DATA_DIR)
        # 指定ありの場合は、絶対パス化
        else:
            data_dir = os.path.expanduser(data_dir)
        
        if self.debug:
            print('use data_dir = ' + data_dir)
        
        # 評価
        if os.path.isfile(data_dir):
            raise Exception(data_dir + ' is a file')
        elif not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            if self.debug:
                print('create dir: ' + data_dir)
            #raise Exception (data_dir + ' is not a directory')
        
        files = os.listdir(data_dir)
        if len(files) > 0:
            raise Exception(data_dir + ' has ' + str(len(files)) + ' file(s)')
        
        return data_dir
    
    def init(self):
        """
        インスタンス変数を初期化する。
        tubディレクトリ内のファイルを確認し、連番をキーとした辞書をそれぞれ作成する。

        引数
            なし
        戻り値
            なし
        例外
            Exception tubデータとして不整合がある場合
        """
        # tub内のjson/jpgファイル名の取得
        files = os.listdir(self.tub_dir)
        # JSONファイル辞書 {インデックス, ファイル名（非フルパス）}
        self.json_dict = {}
        # JPGファイル辞書 {インデックス, ファイル名（非フルパス）}
        self.jpg_dict = {}
        is_meta_json = False
        for f in files:
            path = os.path.join(self.tub_dir, f)
            if os.path.isfile(path):
                if f.endswith(self.JSON_SUFFIX) and self.JSON_PREFIX in f:
                    index =int(f[f.rindex(self.JSON_PREFIX) + len(self.JSON_PREFIX):f.rindex(self.JSON_SUFFIX)])
                    self.json_dict[index] = f
                elif f.endswith(self.JPG_SUFFIX):
                    index =int(f[:f.rindex(self.JPG_SUFFIX)])
                    self.jpg_dict[index] = f
                elif f == self.META_JSON_FILE:
                    is_meta_json = True
                else:
                    if self.debug:
                        print('ignore file: ', path)

        # 評価
        if not is_meta_json:
            raise Exception('no ' + self.META_JSON_FILE)
        json_indexes = sorted(list(self.json_dict.keys()))
        jpg_indexes = sorted(list(self.jpg_dict.keys()))
        if json_indexes != jpg_indexes:
            if self.debug:
                for json_index in json_indexes:
                   if json_index not in jpg_indexes:
                        print('no match json index: ', json_index)
                for jpg_index in jpg_indexes:
                    if jpg_index not in json_indexes:
                        print('no match jpg index: ', jpg_index)
            # 例外を発生
            raise Exception(self.tub_dir + ' is not valid files')
        elif self.debug:
            print(self.tub_dir + ' has normal tub data')

    def execute(self, data_dir):
        """
        tub側データを再整列してdata側へコピーする。

        引数
            data_dir   data側ディレクトリのパス
        戻り値
            なし
        例外
            
        """
        self.data_dir = self.eval_data_dir(data_dir)
        indexes = list(self.json_dict.keys()) # tub側連番リスト

        cnt = 0 # data側の連番
        max_index = max(indexes) # tub側連番最大値
        for index in range(max_index + 1): # 0～tub側連番最大値までのループ
            json_file = self.json_dict.get(index) # indexに該当するJSONファイル名
            jpg_file = self.jpg_dict.get(index) # indexに該当するイメージファイル名
            if json_file is None or jpg_file is None: # 少なくともどちらかのファイル名がみつからなかった場合
                if self.debug:
                    if json_file:
                        print('ignore json file index=', index)
                    if jpg_file:
                        print('ignore jpg file index=', index)
                continue # 無視

            # コピー元、コピー先各ファイルのフルパス
            src_json_path = os.path.join(self.tub_dir, json_file)
            src_jpg_path = os.path.join(self.tub_dir, jpg_file)
            dest_json_path = os.path.join(self.data_dir, json_file.replace(str(index), str(cnt)))
            dest_jpg_path = os.path.join(self.data_dir, jpg_file.replace(str(index), str(cnt)))

            # イメージファイルのコピー
            shutil.copy2(src_jpg_path, dest_jpg_path)
            if self.debug:
                print('src:[' + src_jpg_path +  "] dest:[" + dest_jpg_path  + ']')
            
            # JSONファイルのコピー
            self.copy_tub_json_file(src_json_path, index, dest_json_path, cnt)
            if self.debug:
                print('src:[' + src_json_path + "] dest:[" + dest_json_path + ']')
            # data側連番を加算
            cnt += 1

        # meta.json のコピー
        src_meta_json_path = os.path.join(self.tub_dir, self.META_JSON_FILE)
        dest_meta_json_path = os.path.join(self.data_dir, self.META_JSON_FILE)
        if not os.path.exists(src_meta_json_path):
            raise Exception('no meta json file: ', src_meta_json_path)

        if self.debug:
            print('src:[' + src_meta_json_path +  "] dest:[" + dest_meta_json_path  + ']')
        else:
            shutil.copy2(src_meta_json_path, dest_meta_json_path)

        print('Done. last_index=', (cnt-1))


    def copy_tub_json_file(self, src_path, org_index, dest_path, dest_index):
        """
        JSONファイル(tubデータ)をコピーする。
        連番が異なる場合は、JSON要素内のイメージファイル名を更新する。

        引数
            src_path      元となるJSONファイルのフルパス
            src_index     元となるJSONファイルの連番
            dest_path     コピー先のJSONファイルのフルパス
            dest_index    コピー先のJSONファイルの連番
        戻り値
            なし
        例外
            Exception     元となるJSONファイルにイメージファイル要素が存在しない場合
        """
        # 連番が同じ場合はコピーのみ実行
        if org_index == dest_index:
            shutil.copy2(src_path, dest_path)
            if self.debug:
                print('copy from ' + src_path + ' to ' + dest_path)
            return
        with open(src_path, 'r') as fr:
            json_data = json.load(fr)
            dest_file = json_data.get(self.JSONKEY_IMAGE)
            if dest_file is None:
                raise Exception('no cam/image_array in json: ' + src_path)
            new_image_file = dest_file.replace(str(org_index), str(dest_index))
            with open(dest_path, 'w') as fw:
                json_data[self.JSONKEY_IMAGE] = new_image_file
                json.dump(json_data, fw)
                if self.debug:
                    print('write {} to {}', json.dumps(json_data), dest_path)


# 本ファイル自体が実行された場合
if __name__ == '__main__':
    # 引数情報の収集
    args = docopt.docopt(__doc__)

    # 再整理ユーティリティの初期化
    arranger = Arranger(args['--tub'], debug=args['--debug'])
    # dataディレクトリの確定
    arranger.execute(args['--data'])
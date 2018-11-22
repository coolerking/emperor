# emperor

WORRIORベースのDonkey Car独自アプリのディレクトリをリポジトリ化したものです。

![emperor号](./docs/assets/emperor2.jpg)

## インストール

1. emperor 上のRaspberry Piにターミナル接続します。

2. 以下のコマンドを実行して、python donkeycar パッケージのバージョンが2.5.8であることを確認します。
   ```bash
   python -c "import donkeycar as dk; print(dk.__version__)"
   ```

3. 以下のコマンドを実行して、リポジトリをRaspberry Pi上に展開します。
   ```bash
   git clone https://github.com/coolerking/emperor.git
   ```

### Logicool F710 ジョイスティックを使用する

1. Raspberry Piをシャットダウン
2. Logicool F710コントローラ同梱のUSBドングルをRaspberry Piにセット
3. Raspberry Piを起動
4. ターミナル接続し、ログイン
5. F710本体正面のLogicoolボタンを押す（電源ON）
6. 以下のコマンドを実行し、F710が接続されていることを確認する
   ```bash
   ls /dev/input/js0
   hexdump /dev/input/js0
   ```
   hexdumpを実行後、F710を適当に操作すると、ヘキサダンプが表示されれば、正常。Ctrl+Cで終了する。
7. `~/mycar/manage.py` を次のように編集する
   ```python
        # F710用ジョイスティックコントローラを使用
        from parts.logicool import F710_JoystickController
        ctr = F710_JoystickController(
        # PS4 Dualshock4 ジョイスティックコントローラを使用
        #from donkeypart_ps3_controller.part import PS4JoystickController
        #ctr = PS4JoystickController(
        # ELECOM JC-U3912T ジョイスティックコントローラを使用
        #from parts.elecom import JC_U3912T_JoystickController
        #ctr = JC_U3912T_JoystickController(
   ```

### ELECOM JC-U3917T ジョイスティックを使用する

1. Raspberry Piをシャットダウン
2. ELECOM JC-U3912T コントローラ同梱のUSBドングルをRaspberry Piにセット
3. Raspberry Piを起動
4. ターミナル接続し、ログイン
5. JC-U3912T本体下部の電源スイッチを入れ、本体のボタンを適当に数回操作する
6. 以下のコマンドを実行し、F710が接続されていることを確認する
   ```bash
   ls /dev/input/js0
   hexdump /dev/input/js0
   ```
   hexdumpを実行後、F710を適当に操作すると、ヘキサダンプが表示されれば、正常。Ctrl+Cで終了する。
7. `~/mycar/manage.py` を次のように編集する
   ```python
        # F710用ジョイスティックコントローラを使用
        from parts.logicool import F710_JoystickController
        ctr = F710_JoystickController(
        # PS4 Dualshock4 ジョイスティックコントローラを使用
        #from donkeypart_ps3_controller.part import PS4JoystickController
        #ctr = PS4JoystickController(
        # ELECOM JC-U3912T ジョイスティックコントローラを使用
        #from parts.elecom import JC_U3912T_JoystickController
        #ctr = JC_U3912T_JoystickController(
   ```

### SONY Dualshock4 PS4 ジョイスティックを使用する

donkeypart_ps3_controller パッケージと [別売りUSBドングル](https://amzn.to/2QYbVhe) を使って接続します。

1. Raspberry Piをシャットダウン
2. Dualshock4 USBドングル( [別売](https://amzn.to/2QYbVhe) )をRaspberry Piにセット
3. Raspberry Piを起動
4. ターミナル接続し、ログイン
5. Dualshock4 USBドングルを刺した方向に３秒以上押し込み、青LEDの点滅を早くする
5. Dualshock4のSHAREボタンとPSロゴボタンを同時に3秒以上押す
   ドングルのLEDが青点灯状態になると成功。
6. 以下のコマンドを実行し、Dualshock4コントローラが接続されていることを確認する
   ```bash
   ls /dev/input/js0
   hexdump /dev/input/js0
   ```
   hexdumpを実行後、Dualshock4コントローラを適当に操作すると、ヘキサダンプが表示されれば、正常。Ctrl+Cで終了する。
7. `~/mycar/manage.py` を次のように編集する
   ```python
        # F710用ジョイスティックコントローラを使用
        #from parts.logicool import F710_JoystickController
        #ctr = F710_JoystickController(
        # PS4 Dualshock4 ジョイスティックコントローラを使用
        from donkeypart_ps3_controller.part import PS4JoystickController
        ctr = PS4JoystickController(
        # ELECOM JC-U3912T ジョイスティックコントローラを使用
        #from parts.elecom import JC_U3912T_JoystickController
        #ctr = JC_U3912T_JoystickController(
   ```

## 実行

1. キャリブレーション

   スロットル、ステアリングの調整を以下のコマンドで行い、取得した値を `config.py` に書き込みます。


   * スロットル(Ch0)
     ```bash
     donkey calibrate --channel 0
     ```

   * ステアリング(Ch1)
     ```bash
     donkey calibrate --channel 1
     ```

2. 手動運転(データ収集)

   以下の手順で手動運転を行い、学習データ(tubデータ)を `data` ディレクトリに収集します。

   * 携帯もしくはWeb画面から操作
      ```bash
      cd emperor
      python manage.py drive
      ```

   * ジョイスティックから操作
      ```bash
      cd emperor
      python manage.py drive --js
      ```

3. トレーニング

   トレーニングは Raspberry Pi上ではなく、PC等で実行します。
   `emperor/data` ディレクトリをトレーニングを実行するノードへコピーし、`python manage.py --tub <tubデータディレクトリ> --model models/mypylot` を実行します。

   > トレーニングを実行するノードのdonkeycar パッケージのバージョンも 2.5.8 を使用してください。

   上記コマンドを実行すると、`mypilot`が新たに作成されるので、これを Raspberry Pi 側の `emperor/models` ディレクトリにコピーします。

4. 自動運転

   以下の手順で自動運転を実行します。
   ```bash
   git clone https://github.com/autorope/donkeypart_ps3_controller.git
   cd donkeypart_ps3_controller
   pip install -e .
   cd ..
   cd emperor
   python manage.py drive --model models/mypilot
   ```



## 利用OSS

* GitHub [autorope/donkeycar](https://github.com/autorope/donkeycar) v2.5.8
  Donkey Car の基本機能OSS、MITライセンス準拠です。2.5.1から2.5.8へ更新した際にpartsのリポジトリは分割されました。

* GitHub [autorope/donkeypart_ps3_controller](https://github.com/autorope/donkeypart_ps3_controller)
  PS3やPS4を使用しない場合でもF710やJC-U3912Tの各コントローラが基底クラスとして使用しています。

## ライセンス

本リポジトリの上記OSSで生成、コピーしたコード以外のすべてのコードはMITライセンス準拠とします。

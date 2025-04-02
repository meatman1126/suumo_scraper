# SUUMO 賃貸物件情報スクレイパー

このツールは、SUUMO の賃貸物件情報をスクレイピングし、Google Spreadsheet に出力する Python スクリプトです。

## 機能

- SUUMO の賃貸物件情報をスクレイピング
- カスタマイズ可能な検索条件（JSON ファイルで管理）
- Google Spreadsheet への自動出力
- 新着物件の自動ハイライト表示
- 新着物件のメール通知
- ヘッドレスモードでの実行
- 定期実行機能（午前 6 時と午後 6 時）

## プロジェクト構造

```
suumo/
├── src/
│   ├── scraper/
│   │   ├── suumo_scraper.py    # メインスクレイパー
│   │   └── property_parser.py  # 物件情報パーサー
│   ├── sheets/
│   │   └── sheets_manager.py   # Google Sheets操作
│   └── utils/
│       ├── driver_manager.py   # Selenium WebDriver管理
│       ├── config_loader.py    # 設定ファイル読み込み
│       └── notification_service.py  # メール通知
├── params.json            # 検索パラメータ設定
├── requirements.txt           # 依存パッケージ
└── .env                      # 環境変数
```

## 必要条件

- Python 3.8 以上
- Chrome ブラウザ
- Google Cloud Platform アカウント
- Google Sheets API の有効化
- SMTP サーバー（メール通知用）

## セットアップ

1. 必要なパッケージのインストール:

```bash
pip install -r requirements.txt
```

2. Google Cloud Platform の設定:

   - Google Cloud Console で新しいプロジェクトを作成
   - Google Sheets API を有効化
   - 認証情報を作成し OAuth クライアントを追加し認証情報を、`client_secret.json`としてダウンロード
   - ダウンロードした`client_secret.json`をプロジェクトのルートディレクトリに配置

3. 環境変数の設定:

   - `.env`ファイルを作成し、以下の変数を設定:
     ```
     SPREADSHEET_ID=your_spreadsheet_id
     SMTP_SERVER=your_smtp_server
     SMTP_PORT=587
     SMTP_USERNAME=your_email
     SMTP_PASSWORD=your_password
     NOTIFICATION_EMAIL=notification_recipient
     ```

4. 検索パラメータの設定:
   - `config/params.json`を編集し、必要な検索条件を設定
   - 利用可能なパラメータは`params.json`または`params_sample.txt`を参照
   - suumo の Web サイトで実際に検索して実使用されているパラメータを使用することも可能
     参考：https://suumo.jp/chintai/kanto/

## 使用方法

1. 通常実行:

```bash
python suumo_scraper.py
```

2. 定期実行モード（午前 6 時と午後 6 時に実行）:

```bash
python suumo_scraper.py --schedule
```

3. バックグラウンド実行:

```bash
# バックグラウンドで実行（ログは suumo_scraper.log に出力）
nohup python suumo_scraper.py --schedule > suumo_scraper.log 2>&1 &

# プロセスの確認
ps aux | grep suumo_scraper.py

# プロセスの停止
pkill -f suumo_scraper.py

# ログの確認
tail -f suumo_scraper.log
```

## 出力情報

スクレイピングした物件情報には以下の項目が含まれます：

- 物件名
- 所在地
- アクセス
- 築年数
- 賃料
- 管理費
- 敷金
- 礼金
- 間取り
- 専有面積
- 物件 URL
- メイン画像 URL
- 画像一覧 URL

## 注意事項

- SUUMO のウェブサイト構造が変更された場合、スクレイピングが正常に動作しない可能性があります
- 過度なアクセスは避けてください
- Google Sheets API の利用制限に注意してください
- メール通知機能を使用する場合は、SMTP サーバーの設定を適切に行ってください


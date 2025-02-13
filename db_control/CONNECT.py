import os
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

# データベース接続情報
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')  # 元のパスワードを保持
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

# DATABASE_URLを環境変数から取得
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("DATABASE_URL が環境変数に設定されていません。")

# データベース接続に必要な基本情報のチェック
if not DB_USER or not DB_PASSWORD or not DB_HOST or not DB_PORT or not DB_NAME:
    raise ValueError(
        "環境変数が不足しています。 .env ファイルを確認してください。"
    )

# データベース接続設定
db_config = {
    "host": DB_HOST,
    "user": DB_USER,
    "password": DB_PASSWORD,
    "database": DB_NAME,
    "port": int(DB_PORT),
    "ssl_ca": os.getenv("SSL_CA_CERT").replace('\\n', '\n')
}

print("DB設定:", {
    "host": DB_HOST,
    "user": DB_USER,
    "database": DB_NAME,
    "port": DB_PORT
})

# SSL証明書の確認を追加
ssl_cert = os.getenv("SSL_CA_CERT")
print("SSL証明書の長さ:", len(ssl_cert) if ssl_cert else "証明書なし")
print("SSL証明書の先頭:", ssl_cert[:50] if ssl_cert else "証明書なし") 
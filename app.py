from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import mysql.connector
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from db_control.CONNECT import db_config  # 追加

# FastAPI のインスタンス作成
app = FastAPI()

# CORSの設定（Next.jsからのリクエストを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # すべてのオリジンを許可 (開発時のみ推奨)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

# Pydanticモデル
class Product(BaseModel):
    prd_code: str
    name: str
    price: int

class Transaction(BaseModel):
    emp_cd: str
    store_cd: str
    pos_no: str
    product_code: str
    quantity: int

# レスポンスモデルの定義
class ProductResponse(BaseModel):
    product_code: str | None = None
    product_name: str | None = None
    product_price: int | None = None

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/products/{product_code}", response_model=ProductResponse)
async def get_product(product_code: str):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                CODE as product_code,
                NAME as product_name,
                PRICE as product_price
            FROM m_product_sake_shm
            WHERE CODE = %s
            LIMIT 1
        """, (product_code,))
        
        product = cursor.fetchone()
        
        # 商品が見つからない場合
        if not product:
            return ProductResponse()
        
        # 商品が見つかった場合
        return ProductResponse(
            product_code=str(product["product_code"]),
            product_name=str(product["product_name"]).strip(),  # ここで 余分な空白を削除
            product_price=int(product["product_price"])
        )

        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.post("/transactions")
async def create_transaction(transaction: Transaction):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # 商品の存在確認
        cursor.execute(
            "SELECT PRICE FROM m_product_sake_shm WHERE CODE = %s",
            (transaction.product_code,)
        )
        product = cursor.fetchone()
        if not product:
            raise HTTPException(status_code=404, detail="商品が見つかりません")

        # 取引データの作成
        total_amount = product[0] * transaction.quantity
        current_time = datetime.now()

        # 取引テーブルに登録
        cursor.execute("""
            INSERT INTO 取引 (DATETIME, EMP_CD, STORE_CD, POS_NO, TOTAL_AMT)
            VALUES (%s, %s, %s, %s, %s)
        """, (current_time, transaction.emp_cd, transaction.store_cd, 
              transaction.pos_no, total_amount))
        
        trd_id = cursor.lastrowid

        # 取引明細テーブルに登録
        cursor.execute("""
            INSERT INTO 取引明細 (TRD_ID, PRD_CODE, PRD_NAME, PRD_PRICE)
            SELECT %s, CODE, NAME, PRICE
            FROM m_product_sake_shm
            WHERE CODE = %s
        """, (trd_id, transaction.product_code))

        conn.commit()
        return {"message": "取引が正常に登録されました", "transaction_id": trd_id}

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.get("/test-db")
async def test_db():
    try:
        print("接続開始...")  # デバッグ用
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")  # 簡単なクエリを実行
        result = cursor.fetchone()
        
        # SSL情報を安全に取得
        ssl_info = "SSL使用中" if db_config.get("ssl_ca") else "SSL未使用"
        
        return {
            "message": "Database connection successful",
            "test_query": result[0] if result else None,
            "ssl": ssl_info,
            "config": {  # 接続設定を表示（パスワードは除く）
                "host": db_config["host"],
                "user": db_config["user"],
                "database": db_config["database"],
                "port": db_config["port"]
            }
        }
    except Exception as e:
        print(f"エラー発生: {str(e)}")  # デバッグ用
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "error_details": getattr(e, 'msg', str(e))
        }
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()



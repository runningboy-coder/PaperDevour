# database.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_database():
    # 這裡導入模型是為了確保它們在創建表之前被 SQLAlchemy 知道
    from models import Keyword, Author, Article, Analysis
    db.create_all()
    print("Database tables created.")


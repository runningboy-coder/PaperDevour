# models.py
from database import db
from datetime import datetime
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    api_key = db.Column(db.String(255), nullable=True) # 每个使用者储存自己的 API Key

    # User 模型反向关联其他模型
    keywords = db.relationship('Keyword', backref='user', lazy=True, cascade="all, delete-orphan")
    articles = db.relationship('Article', backref='user', lazy=True, cascade="all, delete-orphan")


# 多對多關係的關聯表
article_author_association = db.Table('article_author_association',
    db.Column('article_id', db.Integer, db.ForeignKey('article.id'), primary_key=True),
    db.Column('author_id', db.Integer, db.ForeignKey('author.id'), primary_key=True)
)

class Keyword(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(100), unique=True, nullable=False)

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    articles = db.relationship('Article', secondary=article_author_association, back_populates='authors')

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(500), nullable=False)
    published = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    pdf_url = db.Column(db.String(255))
    original_summary = db.Column(db.Text)
    local_path = db.Column(db.String(255))
    image_paths = db.Column(db.JSON, default=list)  # 存储图片路径的列表
    authors = db.relationship('Author', secondary=article_author_association, back_populates='articles')
    analyses = db.relationship('Analysis', backref='article', lazy=True, cascade="all, delete-orphan")
    qna_history = db.relationship('QnaHistory', backref='article', lazy=True, cascade="all, delete-orphan")
    is_favorited = db.Column(db.Boolean, default=False, nullable=False)

    
class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    analysis_type = db.Column(db.String(50), nullable=False)  # 'summary' or 'detailed'
    content = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# *** 新增模型 ***: 用於存儲問答記錄
class QnaHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)


# models.py (最终完整版 - 已恢复 Setting)

from database import db
from datetime import datetime
from flask_login import UserMixin

# 多对多关系的关联表
article_author_association = db.Table('article_author_association',
    db.Column('article_id', db.Integer, db.ForeignKey('article.id'), primary_key=True),
    db.Column('author_id', db.Integer, db.ForeignKey('author.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    api_key = db.Column(db.String(255), nullable=True) # 储存每个用户自己的 API Key

    # 使用 back_populates 明确声明关系
    keywords = db.relationship('Keyword', back_populates='user', lazy=True, cascade="all, delete-orphan")
    articles = db.relationship('Article', back_populates='user', lazy=True, cascade="all, delete-orphan")

class Keyword(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # 在关系的另一端也使用 back_populates 明确声明
    user = db.relationship('User', back_populates='keywords')

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
    image_paths = db.Column(db.JSON, default=list)
    is_favorited = db.Column(db.Boolean, default=False, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # 为 Article 和 User 的关系进行明确声明
    user = db.relationship('User', back_populates='articles')
    
    authors = db.relationship('Author', secondary=article_author_association, back_populates='articles')
    analyses = db.relationship('Analysis', backref='article', lazy=True, cascade="all, delete-orphan")
    qna_history = db.relationship('QnaHistory', backref='article', lazy=True, cascade="all, delete-orphan")

class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    analysis_type = db.Column(db.String(50), nullable=False)
    content = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class QnaHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# *** 恢复 Setting 模型，用于全局应用设定 ***
class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)
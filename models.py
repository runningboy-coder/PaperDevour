# models.py
from database import db
from datetime import datetime

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
    authors = db.relationship('Author', secondary=article_author_association, back_populates='articles')
    analyses = db.relationship('Analysis', backref='article', lazy=True, cascade="all, delete-orphan")

class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    analysis_type = db.Column(db.String(50), nullable=False)  # 'summary' or 'detailed'
    content = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
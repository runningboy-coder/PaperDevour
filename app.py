# app.py - 主應用入口
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from database import db, init_database
from models import Keyword, Author, Article, Analysis
import services
import scheduler

# --- Flask 應用設置 ---
app = Flask(__name__, static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///research_assistant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化資料庫和 CORS
db.init_app(app)
CORS(app)

# --- API 路由 ---

# 獲取所有文章，包含簡易分析
@app.route('/api/articles')
def get_articles():
    articles = Article.query.order_by(Article.published.desc()).all()
    results = []
    for article in articles:
        # 只獲取簡易分析用於列表展示
        simple_analysis = Analysis.query.filter_by(article_id=article.id, analysis_type='summary').first()
        results.append({
            'id': article.id,
            'title': article.title,
            'published': article.published.strftime('%Y-%m-%d'),
            'authors': [author.name for author in article.authors],
            'summary_analysis': simple_analysis.content if simple_analysis else None
        })
    return jsonify(results)

# 獲取單篇文章的詳細信息和所有分析
@app.route('/api/articles/<int:article_id>')
def get_article_details(article_id):
    article = Article.query.get_or_404(article_id)
    summary = Analysis.query.filter_by(article_id=article.id, analysis_type='summary').first()
    detailed = Analysis.query.filter_by(article_id=article.id, analysis_type='detailed').first()
    
    return jsonify({
        'id': article.id,
        'title': article.title,
        'published': article.published.strftime('%Y-%m-%d'),
        'authors': [author.name for author in article.authors],
        'pdf_url': article.pdf_url,
        'original_summary': article.original_summary,
        'summary_analysis': summary.content if summary else None,
        'detailed_analysis': detailed.content if detailed else None,
    })

# 對文章進行提問
@app.route('/api/articles/<int:article_id>/ask', methods=['POST'])
def ask_question(article_id):
    article = Article.query.get_or_404(article_id)
    question = request.json.get('question')
    if not question:
        return jsonify({'error': 'Question is required'}), 400
    
    # 結合原文摘要和詳細分析作為上下文
    detailed_analysis = Analysis.query.filter_by(article_id=article.id, analysis_type='detailed').first()
    context = f"Original Abstract: {article.original_summary}\n\nDetailed Analysis: {detailed_analysis.content if detailed_analysis else ''}"
    
    answer = services.AnalysisService.ask_question_with_context(question, context)
    return jsonify({'answer': answer})


# 關鍵字管理
@app.route('/api/keywords', methods=['GET', 'POST'])
def manage_keywords():
    if request.method == 'POST':
        keyword_text = request.json.get('keyword')
        if keyword_text and not Keyword.query.filter_by(keyword=keyword_text).first():
            new_keyword = Keyword(keyword=keyword_text)
            db.session.add(new_keyword)
            db.session.commit()
    
    keywords = Keyword.query.all()
    return jsonify([k.keyword for k in keywords])

@app.route('/api/keywords/<string:keyword_text>', methods=['DELETE'])
def delete_keyword(keyword_text):
    keyword = Keyword.query.filter_by(keyword=keyword_text).first()
    if keyword:
        db.session.delete(keyword)
        db.session.commit()
    return jsonify({'success': True})

# 作者管理 (與關鍵字類似)
# ... 可以在此處添加作者管理的 API ...

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    # *** 已修正 ***: 在啟動應用前，確保資料庫和表已創建
    with app.app_context():
        init_database()

    # 啟動定時任務
    scheduler.start_scheduler(app)
    
    # 首次啟動時，運行一次任務
    with app.app_context():
        services.run_fetch_and_process_job()
    
    app.run(host='0.0.0.0', port=5006)
# app.py - 主应用入口
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from database import db, init_database
from models import Keyword, Author, Article, Analysis
import services
import scheduler

# --- Flask 应用设置 ---
app = Flask(__name__, static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///research_assistant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化资料库和 CORS
db.init_app(app)
CORS(app)

# --- API 路由 ---

# 获取所有文章，包含简易分析
@app.route('/api/articles')
def get_articles():
    articles = Article.query.order_by(Article.published.desc()).all()
    results = []
    for article in articles:
        # 只获取简易分析用于列表展示
        simple_analysis = Analysis.query.filter_by(article_id=article.id, analysis_type='summary').first()
        results.append({
            'id': article.id,
            'title': article.title,
            'published': article.published.strftime('%Y-%m-%d'),
            'authors': [author.name for author in article.authors],
            'summary_analysis': simple_analysis.content if simple_analysis else None
        })
    return jsonify(results)

# 获取单篇文章的详细信息和所有分析
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

# 对文章进行提问
@app.route('/api/articles/<int:article_id>/ask', methods=['POST'])
def ask_question(article_id):
    article = Article.query.get_or_404(article_id)
    question = request.json.get('question')
    if not question:
        return jsonify({'error': 'Question is required'}), 400
    
    detailed_analysis = Analysis.query.filter_by(article_id=article.id, analysis_type='detailed').first()
    context = f"Original Abstract: {article.original_summary}\n\nDetailed Analysis: {detailed_analysis.content if detailed_analysis else ''}"
    
    answer = services.AnalysisService.ask_question_with_context(question, context)
    return jsonify({'answer': answer})

# *** 新增功能 ***: 手动触发根据已存关键字抓取
@app.route('/api/articles/fetch', methods=['POST'])
def fetch_new_articles():
    services.run_fetch_and_process_job()
    return jsonify({'status': 'success', 'message': 'New articles fetch job started.'})

# *** 新增功能 ***: 根据特定关键字即时搜索
@app.route('/api/articles/search', methods=['GET'])
def search_articles():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
    
    search_results = services.ArxivService.search_raw(query)
    return jsonify(search_results)

# *** 新增功能 ***: 批量导入并分析选中的文章
@app.route('/api/articles/batch-import', methods=['POST'])
def batch_import_articles():
    entry_ids = request.json.get('entry_ids')
    if not entry_ids:
        return jsonify({'error': 'entry_ids list is required'}), 400
    
    services.batch_import_and_process(entry_ids)
    return jsonify({'status': 'success', 'message': 'Batch import job started.'})


# 关键字管理
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


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    with app.app_context():
        init_database()

    scheduler.start_scheduler(app)
    
    # 首次启动时不再自动运行，等待用户手动触发
    # with app.app_context():
    #     services.run_fetch_and_process_job()
    
    app.run(host='0.0.0.0', port=5006)
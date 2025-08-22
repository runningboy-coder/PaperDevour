# app.py
import os
from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database import db, init_database
from models import User, Keyword, Author, Article, Analysis, QnaHistory
import services
import scheduler

# --- Flask 应用设置 ---
app = Flask(__name__, static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///research_assistant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)

db.init_app(app)
CORS(app, supports_credentials=True)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Auth API ---
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'User registered successfully.'}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password_hash, password):
        login_user(user)
        return jsonify({'status': 'success', 'username': user.username})
    return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/api/auth/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'status': 'success'})

@app.route('/api/auth/status')
def status():
    if current_user.is_authenticated:
        return jsonify({'isLoggedIn': True, 'username': current_user.username})
    return jsonify({'isLoggedIn': False})

# --- User Settings API ---
@app.route('/api/user/settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    if request.method == 'POST':
        data = request.json
        current_user.api_key = data.get('api_key')
        db.session.commit()
        return jsonify({'status': 'success'})
    
    # 全局设定与使用者设定合并
    # 暂时只返回使用者自己的 api_key
    return jsonify({
        'api_key': current_user.api_key or ''
    })

# --- Core API (所有查询都已修改) ---

@app.route('/api/articles/latest')
@login_required
def get_latest_articles():
    articles = Article.query.filter_by(user_id=current_user.id).order_by(Article.published.desc()).all()
    results = []
    for article in articles:
        results.append({
            'id': article.id,
            'title': article.title,
            'authors': [author.name for author in article.authors],
            'is_favorited': article.is_favorited
        })
    return jsonify(results)

@app.route('/api/articles/favorites')
@login_required
def get_favorite_articles():
    articles = Article.query.filter_by(user_id=current_user.id, is_favorited=True).order_by(Article.published.desc()).all()
    results = []
    for article in articles:
         results.append({
            'id': article.id,
            'title': article.title,
            'authors': [author.name for author in article.authors],
            'is_favorited': article.is_favorited
        })
    return jsonify(results)

@app.route('/api/articles/<int:article_id>')
@login_required
def get_article_details(article_id):
    article = Article.query.filter_by(id=article_id, user_id=current_user.id).first_or_404()
    summary = Analysis.query.filter_by(article_id=article.id, analysis_type='summary').first()
    detailed = Analysis.query.filter_by(article_id=article.id, analysis_type='detailed').first()
    qna_history = QnaHistory.query.filter_by(article_id=article.id).order_by(QnaHistory.created_at).all()
    
    return jsonify({
        'id': article.id,
        'title': article.title,
        'published': article.published.strftime('%Y-%m-%d'),
        'authors': [author.name for author in article.authors],
        'pdf_url': article.pdf_url,
        'original_summary': article.original_summary,
        'summary_analysis': summary.content if summary else None,
        'detailed_analysis': detailed.content if detailed else None,
        'qna_history': [{'question': q.question, 'answer': q.answer} for q in qna_history],
        'is_favorited': article.is_favorited,
        'image_paths': article.image_paths
    })

@app.route('/api/articles/<int:article_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite_status(article_id):
    article = Article.query.filter_by(id=article_id, user_id=current_user.id).first_or_404()
    article.is_favorited = not article.is_favorited
    db.session.commit()
    return jsonify({'status': 'success', 'is_favorited': article.is_favorited})

@app.route('/api/articles/<int:article_id>/ask', methods=['POST'])
@login_required
def ask_question(article_id):
    article = Article.query.filter_by(id=article_id, user_id=current_user.id).first_or_404()
    question = request.json.get('question')
    if not question:
        return jsonify({'error': 'Question is required'}), 400
    
    # 注意：这里需要一个机制来设定和使用使用者的 API Key
    # 暂时我们先假设 services 模块可以获取到它
    # services.set_api_key(current_user.api_key)
    answer = "Q&A feature to be implemented with user API key" # Placeholder
    
    new_qna = QnaHistory(article_id=article.id, question=question, answer=answer)
    db.session.add(new_qna)
    db.session.commit()
    return jsonify({'answer': answer})

@app.route('/api/articles/<int:article_id>', methods=['DELETE'])
@login_required
def delete_article(article_id):
    article = Article.query.filter_by(id=article_id, user_id=current_user.id).first_or_404()
    db.session.delete(article)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Article deleted.'})

@app.route('/api/articles/search', methods=['GET'])
@login_required
def search_articles():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
    search_results = services.ArxivService.search_raw(query)
    return jsonify(search_results)

@app.route('/api/articles/batch-import', methods=['POST'])
@login_required
def batch_import_articles():
    entry_ids = request.json.get('entry_ids')
    if not entry_ids:
        return jsonify({'error': 'entry_ids list is required'}), 400
    
    # services.batch_import_and_process(entry_ids, user_id=current_user.id) # 需要改造 service
    return jsonify({'status': 'success', 'message': 'Batch import job started.'})

# *** 核心修正：补全缺失的 /api/articles/fetch 路由 ***
@app.route('/api/articles/fetch', methods=['POST'])
@login_required
def fetch_new_articles():
    user = User.query.get(current_user.id)
    services.fetch_and_process_for_user(user)
    return jsonify({'status': 'success', 'message': 'New articles fetch job started.'})


@app.route('/api/keywords', methods=['GET', 'POST'])
@login_required
def manage_keywords():
    if request.method == 'POST':
        keyword_text = request.json.get('keyword')
        if keyword_text and not Keyword.query.filter_by(keyword=keyword_text, user_id=current_user.id).first():
            new_keyword = Keyword(keyword=keyword_text, user_id=current_user.id)
            db.session.add(new_keyword)
            db.session.commit()
    
    keywords = Keyword.query.filter_by(user_id=current_user.id).all()
    return jsonify([k.keyword for k in keywords])

@app.route('/api/keywords/<string:keyword_text>', methods=['DELETE'])
@login_required
def delete_keyword(keyword_text):
    keyword = Keyword.query.filter_by(keyword=keyword_text, user_id=current_user.id).first()
    if keyword:
        db.session.delete(keyword)
        db.session.commit()
    return jsonify({'success': True})

# --- Main Routes ---
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/media/<path:subpath>')
def serve_media(subpath):
    return send_from_directory(services.SAVE_PATH, subpath)
@app.route('/api/articles/<int:article_id>/export/bibtex')
@login_required
def export_bibtex(article_id):
    article = Article.query.filter_by(id=article_id, user_id=current_user.id).first_or_404()

    # 为 BibTeX 格式化作者
    authors = " and ".join([author.name for author in article.authors])
    year = article.published.year
    # 提取 ID 作为 BibTeX 的 key
    bibtex_key = article.entry_id.split('/')[-1]

    # 创建 BibTeX 条目字串
    bibtex_entry = f"""@article{{{bibtex_key},
  author  = {{{authors}}},
  title   = {{{article.title}}},
  journal = {{arXiv preprint arXiv:{bibtex_key}}},
  year    = {{{year}}}
}}"""

    # 返回一个响应，触发浏览器下载 .bib 文件
    return Response(
        bibtex_entry,
        mimetype="application/x-bibtex",
        headers={"Content-disposition":
                 f"attachment; filename={bibtex_key}.bib"}
    )

if __name__ == '__main__':
    with app.app_context():
        init_database()
    # scheduler.start_scheduler(app) # 暂时注释掉定时任务
    app.run(host='0.0.0.0', port=5006, debug=True)
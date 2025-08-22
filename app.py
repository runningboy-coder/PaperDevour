# app.py - 主應用入口
import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database import db, init_database
from models import User,Keyword, Author, Article, Analysis, QnaHistory, Setting # *** 1. 匯入 Setting ***
import services
import scheduler

# --- Flask 應用設置 ---
app = Flask(__name__, static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///research_assistant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24) # 用于 session 加密

db.init_app(app)
CORS(app, supports_credentials=True)
bcrypt=Bcrypt(app)


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

@app.route('/api/user/settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    if request.method == 'POST':
        data = request.json
        current_user.api_key = data.get('api_key')
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'api_key': current_user.api_key})


# --- API 路由 ---

# @app.route('/api/settings', methods=['GET', 'POST'])
# @login_required
# def manage_settings():
#     if request.method == 'POST':
#         settings_data = request.json
#         for key, value in settings_data.items():
#             setting = Setting.query.filter_by(key=key).first()
#             if setting:
#                 setting.value = str(value)
#             else:
#                 setting = Setting(key=key, value=str(value))
#                 db.session.add(setting)
#         db.session.commit()
    
#     settings = Setting.query.all()
#     return jsonify({s.key: s.value for s in settings})


# *** 3. 將 /api/articles 重命名為 /api/articles/latest 並增加 is_favorited ***
@app.route('/api/articles/latest')
@login_required
def get_latest_articles():
    articles = Article.query.filter_by(user_id=current_user.id).order_by(Article.published.desc()).all()
    results = []
    for article in articles:
        simple_analysis = Analysis.query.filter_by(article_id=article.id, analysis_type='summary').first()
        results.append({
            'id': article.id,
            'title': article.title,
            'published': article.published.strftime('%Y-%m-%d'),
            'authors': [author.name for author in article.authors],
            'summary_analysis': simple_analysis.content if simple_analysis else None,
            'is_favorited': article.is_favorited # <-- 新增
        })
    return jsonify(results)

# *** 4. 新增 /api/articles/favorites 路由 ***
@app.route('/api/articles/favorites')
@login_required
def get_favorite_articles():
    articles = Article.query.filter_by(user_id=current_user.id, is_favorited=True).order_by(Article.published.desc()).all()
    results = []
    for article in articles:
        simple_analysis = Analysis.query.filter_by(article_id=article.id, analysis_type='summary').first()
        results.append({
            'id': article.id,
            'title': article.title,
            'published': article.published.strftime('%Y-%m-%d'),
            'authors': [author.name for author in article.authors],
            'summary_analysis': simple_analysis.content if simple_analysis else None,
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
        'is_favorited': article.is_favorited # <-- 新增
    })

# *** 5. 新增收藏/取消收藏的路由 ***
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
    
    detailed_analysis = Analysis.query.filter_by(article_id=article.id, analysis_type='detailed').first()
    context = f"Original Abstract: {article.original_summary}\n\nDetailed Analysis: {detailed_analysis.content if detailed_analysis else ''}"
    
    answer = services.AnalysisService.ask_question_with_context(question, context)

    # 保存問答記錄到資料庫
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

@app.route('/api/articles/<int:article_id>/regenerate', methods=['POST'])
@login_required
def regenerate_analysis(article_id):
    article = Article.query.filter_by(id=article_id, user_id=current_user.id).first_or_404()
    services.regenerate_analysis_for_article(article)
    return jsonify({'status': 'success', 'message': 'Analysis regeneration started.'})

@app.route('/api/articles/fetch', methods=['POST'])
@login_required
def fetch_new_articles():
    services.run_fetch_and_process_job()
    return jsonify({'status': 'success', 'message': 'New articles fetch job started.'})

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
    
    services.batch_import_and_process(entry_ids)
    return jsonify({'status': 'success', 'message': 'Batch import job started.'})

@app.route('/api/keywords', methods=['GET', 'POST'])
@login_required
def manage_keywords():
    if request.method == 'POST':
        keyword_text = request.json.get('keyword')
        if keyword_text and not Keyword.query.filter_by(keyword=keyword_text).first():
            new_keyword = Keyword(keyword=keyword_text)
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

# *** 新增路由 ***: 用於提供媒體檔案 (圖片)
@app.route('/media/<path:subpath>')
@login_required
def serve_media(subpath):
    # 從 services 配置中獲取儲存路徑
    return send_from_directory(services.SAVE_PATH, subpath)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')



if __name__ == '__main__':
    with app.app_context():
        init_database()
    scheduler.start_scheduler(app)
    app.run(host='0.0.0.0', port=5006)
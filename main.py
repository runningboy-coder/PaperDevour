# main.py
# 需要先安裝依賴: pip install Flask APScheduler arxiv requests
import os
import json
import logging
import time
import re
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import arxiv
import requests
from datetime import datetime
from openai import OpenAI

# --- 配置區域 ---
# ==============================================================================
# 1. 指定您的雲端硬碟或本地文件夾路徑
#    Windows 示例: "C:/Users/YourUser/Nextcloud/ResearchPapers"
#    macOS/Linux 示例: "/Users/YourUser/Nextcloud/ResearchPapers"
#    確保這個文件夾是存在的！
DEEP_SEEK_API_KEY = "sk-260dfedfa436468083d26113526f8acb"

SAVE_PATH = "/Volumes/马学龙/arxiv_paper" 

# 2. 定義你的研究領域關鍵詞
RESEARCH_KEYWORDS = "Ising machine, QUBO, HUBO, quantum annealing, Graph Neural Network, GNN, Reinforcement Learning, RL, Transformer, Large Language Model, LLM, AI, artificial intelligence, machine learning, deep learning, neural network, quantum computing, quantum information" 

# 3. 定義獲取文章的數量
MAX_RESULTS = 3 # 為了測試方便，先設置為3

# 4. 定義你希望大模型如何總結文章
#    我們現在要求結構化輸出，以便後續處理
SUMMARY_PROMPT = """
Please analyze the following academic paper abstract and provide a structured summary in JSON format. 
The JSON object should contain these keys:
- "simplified_summary_zh": A summary in simple Chinese, about 300 characters, highlighting key contributions.
- "keywords_en": An array of 3 to 5 most relevant English keywords.
- "innovation_rating": A rating from 1 to 5 (integer) on the potential novelty of the work, with 5 being highly innovative.

Here is the abstract:
"""

# 5. 儲存總結結果的索引文件
OUTPUT_JSON_FILE = 'summaries.json'
# ==============================================================================


# --- Flask 應用設置 ---
app = Flask(__name__, static_folder='static')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
CORS(app)

# --- 核心功能函數 ---


def get_structured_llm_summary(text_to_summarize):
    """調用 DeepSeek API 來獲取結構化的總結 (使用 OpenAI 庫)"""
    logging.info("Calling DeepSeek API via OpenAI library for structured summarization...")
    
    try:
        # *** 已更新 ***: 使用 OpenAI 客戶端來調用 DeepSeek API
        # 關鍵在於設定 base_url 指向 DeepSeek 的服務器
        client = OpenAI(
            api_key=DEEP_SEEK_API_KEY,
            base_url="https://api.deepseek.com/v1"
        )

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": SUMMARY_PROMPT + text_to_summarize}
            ],
            response_format={"type": "json_object"}
        )
        
        json_text = response.choices[0].message.content
        logging.info("Successfully received summary from DeepSeek API.")
        return json.loads(json_text)

    except Exception as e:
        logging.error(f"An error occurred while calling DeepSeek API via OpenAI library: {e}")
        
    # 如果失敗，返回一個預設的錯誤結構
    return {
        "simplified_summary_zh": "無法生成摘要。",
        "keywords_en": [],
        "innovation_rating": 0
    }

def sanitize_filename(name):
    """清理文件名，移除無效字符"""
    return re.sub(r'[\\/*?:"<>|]', "", name)

def fetch_and_process_papers():
    """獲取、總結、下載並保存最新的學術文章"""
    with app.app_context():
        logging.info("Starting scheduled job: fetch_and_process_papers")
        
        if not os.path.isdir(SAVE_PATH) or "path/to" in SAVE_PATH:
            logging.error(f"Save path '{SAVE_PATH}' is not a valid directory. Please configure it first.")
            return

        try:
            search = arxiv.Search(
                query=RESEARCH_KEYWORDS,
                max_results=MAX_RESULTS,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            
            client = arxiv.Client()
            results = list(client.results(search))
            if not results:
                logging.info("No new papers found for the given keywords.")
                return

            all_papers_metadata = []
            for paper in results:
                logging.info(f"Processing paper: {paper.title}")

                date_str = paper.published.strftime('%Y-%m-%d')
                sanitized_title = sanitize_filename(paper.title)[:80]
                paper_folder_name = f"{date_str} - {sanitized_title}"
                paper_folder_path = os.path.join(SAVE_PATH, paper_folder_name)
                os.makedirs(paper_folder_path, exist_ok=True)

                pdf_filename = f"{sanitized_title}.pdf"
                pdf_path = os.path.join(paper_folder_path, pdf_filename)
                if not os.path.exists(pdf_path):
                    paper.download_pdf(dirpath=paper_folder_path, filename=pdf_filename)
                    logging.info(f"Downloaded PDF to {pdf_path}")
                else:
                    logging.info(f"PDF already exists at {pdf_path}")

                structured_summary = get_structured_llm_summary(paper.summary)

                metadata = {
                    'title': paper.title,
                    'authors': [author.name for author in paper.authors],
                    'published': date_str,
                    'id': paper.entry_id,
                    'pdf_url': paper.pdf_url,
                    'original_summary': paper.summary,
                    'ai_analysis': structured_summary,
                    'local_path': paper_folder_path 
                }
                all_papers_metadata.append(metadata)

                analysis_filename = "analysis_summary.json"
                analysis_path = os.path.join(paper_folder_path, analysis_filename)
                with open(analysis_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=4)
                logging.info(f"Saved analysis to {analysis_path}")

            with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_papers_metadata, f, ensure_ascii=False, indent=4)
            logging.info(f"Successfully updated UI index file {OUTPUT_JSON_FILE}")

        except Exception as e:
            logging.error(f"An error occurred in fetch_and_process_papers: {e}", exc_info=True)

# --- API 路由與定時任務 ---
@app.route('/api/summaries')
def get_summaries():
    if not os.path.exists(OUTPUT_JSON_FILE):
        return jsonify([])
    with open(OUTPUT_JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return jsonify(data)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(fetch_and_process_papers, 'cron', day_of_week='mon-fri', hour=7, minute=30)
scheduler.start()

if __name__ == '__main__':
    fetch_and_process_papers()
    app.run(host='0.0.0.0', port=5006)

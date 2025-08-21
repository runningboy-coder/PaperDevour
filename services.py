# services.py
import os
import re
import arxiv
import json
import shutil # *** 新增匯入 ***
from datetime import datetime
from openai import OpenAI
from models import db, Keyword, Author, Article, Analysis
from dotenv import load_dotenv
import tarfile

# 加载 .env 文件中的环境变量
load_dotenv()

# --- 配置 ---
# 从环境变量中读取 API Key，如果找不到则为空字符串
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
SAVE_PATH = "path/to/your/folder"
MAX_RESULTS = 5
SEARCH_MAX_RESULTS = 20 # 搜索时返回更多结果供选择

# --- Prompt 设计 ---
SUMMARY_PROMPT = """
Please analyze the following academic paper abstract and provide a structured summary in JSON format.
The JSON object must contain these keys:
- "simplified_summary_zh": A summary in simple Chinese, about 300 characters.
- "keywords_en": An array of 3 to 5 most relevant English keywords.
- "innovation_rating": A rating from 1 to 5 (integer) on the potential novelty.
Abstract:
"""

DETAILED_PROMPT = """
Please provide a detailed analysis of the following academic paper abstract in JSON format in simple Chinese.
The JSON object must contain these keys:
- "background": A brief introduction to the research area and the problem it addresses.
- "methodology": A description of the methods or techniques used in the paper.
- "key_innovations": A bullet-point list (array of strings) of the core innovations or contributions.
- "potential_impact": A discussion on the potential impact or future implications of this research.
Abstract:
"""

QNA_PROMPT_TEMPLATE = """
Based on the following context, please answer the user's question. Be concise and helpful.
Context:
---
{context}
---
Question: {question}
Answer:
"""

class AnalysisService:
    # 检查 API Key 是否已配置
    if not DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY not found in .env file. Please configure it.")
    
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")

    @classmethod
    def _get_json_analysis(cls, prompt_template, abstract):
        try:
            response = cls.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                    {"role": "user", "content": prompt_template + abstract}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error calling LLM API: {e}")
            return None

    @classmethod
    def get_summary_analysis(cls, abstract):
        return cls._get_json_analysis(SUMMARY_PROMPT, abstract)

    @classmethod
    def get_detailed_analysis(cls, abstract):
        return cls._get_json_analysis(DETAILED_PROMPT, abstract)
    
    @classmethod
    def ask_question_with_context(cls, question, context):
        try:
            prompt = QNA_PROMPT_TEMPLATE.format(context=context, question=question)
            response = cls.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in Q&A call: {e}")
            return "抱歉，我无法处理您的问题。"

class ArxivService:
    @staticmethod
    def sanitize_filename(name):
        return re.sub(r'[\\/*?:"<>|]', "", name)

    @staticmethod
    def search_raw(query):
        """只搜索并返回原始结果，不存入数据库"""
        print(f"Searching arXiv with query: {query}")
        search = arxiv.Search(query=query, max_results=SEARCH_MAX_RESULTS, sort_by=arxiv.SortCriterion.Relevance)
        client = arxiv.Client()
        results = []
        for r in client.results(search):
            exists = Article.query.filter_by(entry_id=r.entry_id).first()
            results.append({
                "entry_id": r.entry_id,
                "title": r.title,
                "summary": r.summary,
                "authors": [a.name for a in r.authors],
                "published": r.published.strftime('%Y-%m-%d'),
                "pdf_url": r.pdf_url,
                "is_imported": exists is not None
            })
        return results

    @staticmethod
    def process_and_save_paper(paper):
        """处理单个 paper 对象并存入数据库，如果已存在则跳过"""
        if Article.query.filter_by(entry_id=paper.entry_id).first():
            print(f"Skipping existing article: {paper.title}")
            return None

        # 创建或获取作者
        authors_in_db = []
        for author_name in [a.name for a in paper.authors]:
            author = Author.query.filter_by(name=author_name).first()
            if not author:
                author = Author(name=author_name)
                db.session.add(author)
            authors_in_db.append(author)
        
        # 下载文件
        date_str = paper.published.strftime('%Y-%m-%d')
        sanitized_title = ArxivService.sanitize_filename(paper.title)[:80]
        paper_folder_name = f"{date_str} - {sanitized_title}"
        paper_folder_path = os.path.join(SAVE_PATH, paper_folder_name)
        os.makedirs(paper_folder_path, exist_ok=True)
        pdf_filename = f"{sanitized_title}.pdf"
        try:
            paper.download_pdf(dirpath=paper_folder_path, filename=pdf_filename)
        except Exception as e:
            print(f"Failed to download PDF for {paper.title}: {e}")

         # *** 新增功能: 提取图片 ***
        image_paths = []
        try:
            source_path = paper.download_source(dirpath=paper_folder_path)
            images_dir = os.path.join(paper_folder_path, "images")
            os.makedirs(images_dir, exist_ok=True)
            
            with tarfile.open(source_path, 'r:gz') as tar:
                for member in tar.getmembers():
                    if member.isfile() and member.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        filename = os.path.basename(member.name)
                        target_path = os.path.join(images_dir, filename)
                        with tar.extractfile(member) as source, open(target_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
                        # 存储相对路径以便前端访问
                        relative_path  = f"{os.path.basename(paper_folder_path)}/images/{filename}"
                        image_paths.append(relative_path)
            os.remove(source_path) # 清理源码压缩包
        except Exception as e:
            print(f"Could not download or extract source for images: {e}")

        # 创建文章记录
        new_article = Article(
            entry_id=paper.entry_id,
            title=paper.title,
            published=paper.published.replace(tzinfo=None),
            pdf_url=paper.pdf_url,
            original_summary=paper.summary,
            local_path=paper_folder_path,
            authors=authors_in_db,
            image_paths=image_paths
        )
        db.session.add(new_article)
        db.session.commit()
        print(f"Saved new article to DB: {new_article.title}")
        return new_article

def analyze_and_store_article(article):
    """对单个文章进行 AI 分析并存入数据库"""
    print(f"Analyzing article: {article.title}")
    # 获取简易分析
    summary_json = AnalysisService.get_summary_analysis(article.original_summary)
    if summary_json:
        summary_analysis = Analysis(article_id=article.id, analysis_type='summary', content=summary_json)
        db.session.add(summary_analysis)
    
    # 获取详细分析
    detailed_json = AnalysisService.get_detailed_analysis(article.original_summary)
    if detailed_json:
        detailed_analysis = Analysis(article_id=article.id, analysis_type='detailed', content=detailed_json)
        db.session.add(detailed_analysis)
    
    db.session.commit()
    print(f"Finished analysis for: {article.title}")

def regenerate_analysis_for_article(article):
    """删除现有分析并重新生成"""
    # 刪除舊的分析
    Analysis.query.filter_by(article_id=article.id).delete()
    db.session.commit()
    print(f"Deleted existing analyses for article: {article.title}")
    # 重新分析
    analyze_and_store_article(article)

def run_fetch_and_process_job():
    print("Running scheduled job: Fetching and processing papers...")
    keywords = [k.keyword for k in Keyword.query.all()]
    if not keywords:
        print("No keywords configured. Skipping fetch.")
        return
    
    search_query = " OR ".join(f'all:"{kw}"' for kw in keywords)
    search = arxiv.Search(query=search_query, max_results=MAX_RESULTS, sort_by=arxiv.SortCriterion.SubmittedDate)
    client = arxiv.Client()
    
    for paper in client.results(search):
        article_in_db = ArxivService.process_and_save_paper(paper)
        if article_in_db:
            analyze_and_store_article(article_in_db)
    print("Job finished.")

def batch_import_and_process(entry_ids):
    print(f"Starting batch import for {len(entry_ids)} articles.")
    # *** 再次修復 ***: 提取 /abs/ 後面的所有部分作為完整 ID
    # 這樣可以同時處理 'astro-ph/0004127v2' 和 '2401.12345' 這類格式
    paper_ids = [eid.split('/abs/')[-1] for eid in entry_ids if '/abs/' in eid]
    
    client = arxiv.Client()
    # 使用清理過的 paper_ids 進行搜索
    search = arxiv.Search(id_list=paper_ids)
    
    for paper in client.results(search):
        article_in_db = ArxivService.process_and_save_paper(paper)
        if article_in_db:
            analyze_and_store_article(article_in_db)
    print("Batch import finished.")
# services.py
import os
import re
import arxiv
from datetime import datetime
from openai import OpenAI
from models import db, Keyword, Author, Article, Analysis

# --- 配置 ---
DEEPSEEK_API_KEY = "sk-e08adb457e13469bbc2bc931a15dca44"
SAVE_PATH = "/Volumes/马学龙/arxiv_paper"
MAX_RESULTS = 5

# --- Prompt 設計 ---
SUMMARY_PROMPT = """
Please analyze the following academic paper abstract and provide a structured summary in JSON format.
The JSON object must contain these keys:
- "simplified_summary_zh": A summary in simple Chinese, about 300 characters.
- "keywords_en": An array of 3 to 5 most relevant English keywords.
- "innovation_rating": A rating from 1 to 5 (integer) on the potential novelty.
Abstract:
"""

DETAILED_PROMPT = """
Please provide a detailed analysis of the following academic paper abstract in JSON format.
The JSON object must contain these keys:
- "background": A brief introduction to the research area and the problem it addresses.
- "methodology": A description of the methods or techniques used in the paper.
- "key_innovations": A bullet-point list (array of strings) of the core innovations or contributions.
- "potential_impact": A discussion on the potential impact or future implications of this research.
Abstract:
"""

QNA_PROMPT_TEMPLATE = """
Based on the following context, please answer the user's question.
Context:
---
{context}
---
Question: {question}
Answer:
"""

class AnalysisService:
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
            return response.choices[0].message.content
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
            return "Sorry, I couldn't process the answer for your question."


class ArxivService:
    @staticmethod
    def sanitize_filename(name):
        return re.sub(r'[\\/*?:"<>|]', "", name)

    @staticmethod
    def fetch_and_store_papers():
        keywords = [k.keyword for k in Keyword.query.all()]
        if not keywords:
            print("No keywords configured. Skipping fetch.")
            return
        
        search_query = " OR ".join(f'all:"{kw}"' for kw in keywords)
        
        search = arxiv.Search(
            query=search_query,
            max_results=MAX_RESULTS,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        
        client = arxiv.Client()
        results = list(client.results(search))

        for paper in results:
            # 檢查文章是否已存在
            if Article.query.filter_by(entry_id=paper.entry_id).first():
                print(f"Skipping existing article: {paper.title}")
                continue

            # 創建或獲取作者
            authors_in_db = []
            for author_name in [a.name for a in paper.authors]:
                author = Author.query.filter_by(name=author_name).first()
                if not author:
                    author = Author(name=author_name)
                    db.session.add(author)
                authors_in_db.append(author)
            
            # 下載文件
            date_str = paper.published.strftime('%Y-%m-%d')
            sanitized_title = ArxivService.sanitize_filename(paper.title)[:80]
            paper_folder_name = f"{date_str} - {sanitized_title}"
            paper_folder_path = os.path.join(SAVE_PATH, paper_folder_name)
            os.makedirs(paper_folder_path, exist_ok=True)
            pdf_filename = f"{sanitized_title}.pdf"
            paper.download_pdf(dirpath=paper_folder_path, filename=pdf_filename)

            # 創建文章記錄
            new_article = Article(
                entry_id=paper.entry_id,
                title=paper.title,
                published=paper.published.replace(tzinfo=None),
                pdf_url=paper.pdf_url,
                original_summary=paper.summary,
                local_path=paper_folder_path,
                authors=authors_in_db
            )
            db.session.add(new_article)
            db.session.commit() # 提交以獲取 new_article.id
            yield new_article


def run_fetch_and_process_job():
    print("Running scheduled job: Fetching and processing papers...")
    for article in ArxivService.fetch_and_store_papers():
        print(f"Processing new article: {article.title}")
        # 獲取簡易分析
        summary_json = AnalysisService.get_summary_analysis(article.original_summary)
        if summary_json:
            summary_analysis = Analysis(article_id=article.id, analysis_type='summary', content=summary_json)
            db.session.add(summary_analysis)
        
        # 獲取詳細分析
        detailed_json = AnalysisService.get_detailed_analysis(article.original_summary)
        if detailed_json:
            detailed_analysis = Analysis(article_id=article.id, analysis_type='detailed', content=detailed_json)
            db.session.add(detailed_analysis)
        
        db.session.commit()
    print("Job finished.")


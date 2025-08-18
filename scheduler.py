# scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler

def start_scheduler(app):
    from services import run_fetch_and_process_job # 延遲導入
    
    scheduler = BackgroundScheduler(daemon=True)
    # 每天早上 7:30 運行
    scheduler.add_job(
        lambda: run_job_with_context(app), 
        'cron', 
        day_of_week='mon-fri', 
        hour=10, 
        minute=15
    )
    scheduler.start()

def run_job_with_context(app):
    with app.app_context():
        from services import run_fetch_and_process_job
        run_fetch_and_process_job()


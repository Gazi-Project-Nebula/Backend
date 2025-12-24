from apscheduler.schedulers.background import BackgroundScheduler

# Scheduler burada tek bir instance olarak tanımlanır.
# Hem main.py (başlatmak için) hem router (iş eklemek için) burayı kullanacak.
scheduler = BackgroundScheduler()
import os
from celery import Celery

# Thiết lập biến môi trường Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'map_web.settings')

app = Celery('map_web')

# Sử dụng cấu hình từ file settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Tự động tìm và đăng ký các tác vụ từ các file tasks.py
app.autodiscover_tasks()
from celery import shared_task
from django.contrib.auth.models import User
from chamu.models import UserInfo

@shared_task
def delete_stale_user_info():
    """Tác vụ để xóa các UserInfo không có User liên kết."""
    existing_user_ids = User.objects.values_list('id', flat=True)
    stale_user_info_count, _ = UserInfo.objects.exclude(user_id__in=existing_user_ids).delete()
    print(f'Successfully deleted {stale_user_info_count} stale UserInfo records.')
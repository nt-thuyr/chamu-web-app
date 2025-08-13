from django.core.management.base import BaseCommand
from chamu.models import UserInfo
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Deletes UserInfo records that are not linked to a User.'

    def handle(self, *args, **options):
        # Lấy tất cả các ID của User
        existing_user_ids = User.objects.values_list('id', flat=True)

        # Tìm và xóa các UserInfo không có User tương ứng
        stale_user_info_count, _ = UserInfo.objects.exclude(user_id__in=existing_user_ids).delete()

        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {stale_user_info_count} stale UserInfo records.'))
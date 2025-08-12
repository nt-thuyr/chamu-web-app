import csv
from django.core.management.base import BaseCommand
from chamu.models import Criteria # Đảm bảo tên model khớp


class Command(BaseCommand):
    help = 'Imports country data from a CSV file.'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The path to the CSV file to import.')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']

        self.stdout.write("Bắt đầu nhập dữ liệu...")

        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                # Bỏ qua dòng tiêu đề
                next(reader)

                for row in reader:
                    if len(row) >= 3:
                        criteria_name, left_label, right_label = row
                        criteria, _ = Criteria.objects.get_or_create(
                            name=criteria_name,
                            defaults={'left_label': left_label, 'right_label': right_label}
                        )

            self.stdout.write(self.style.SUCCESS("Nhập dữ liệu thành công!"))

        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'Không tìm thấy file: {csv_file_path}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Có lỗi xảy ra: {e}'))
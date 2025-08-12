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
                    # Ensure the row has at least 3 columns to avoid an error
                    if len(row) >= 3:
                        criteria_name, left_label, right_label = row[:3]

                        # Check if the row has a fourth column for 'is_reverse'
                        if len(row) >= 4:
                            is_reverse_str = row[3]
                            is_reverse_bool = (is_reverse_str.lower() == 'true')
                        else:
                            # If the fourth column is missing, default to False
                            is_reverse_bool = False

                        # Get the existing criteria or create a new one
                        criteria, created = Criteria.objects.get_or_create(
                            name=criteria_name,
                            defaults={
                                'left_label': left_label,
                                'right_label': right_label,
                                'is_reverse': is_reverse_bool  # Use the value from the CSV or the default
                            }
                        )

                        # If the object already existed and the is_reverse value from the CSV is different, update it.
                        # This handles cases where you update the value for an existing criteria.
                        if not created and criteria.is_reverse != is_reverse_bool:
                            criteria.is_reverse = is_reverse_bool
                            criteria.save()

            self.stdout.write(self.style.SUCCESS("Nhập dữ liệu thành công!"))

        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'Không tìm thấy file: {csv_file_path}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Có lỗi xảy ra: {e}'))
import csv
from django.core.management.base import BaseCommand
from chamu.models import Prefecture, Municipality  # Đảm bảo tên model khớp


class Command(BaseCommand):
    help = 'Imports prefecture and municipality data from a CSV file.'

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
                    # Kiểm tra độ dài của hàng
                    if len(row) < 3:
                        self.stderr.write(self.style.ERROR(f'Hàng bị thiếu dữ liệu: {row}'))
                        continue

                    # Bỏ qua cột đầu tiên (Number)
                    _, prefecture_name, municipality_name = row

                    # Bước 1: Tìm hoặc tạo đối tượng Prefecture
                    prefecture, _ = Prefecture.objects.get_or_create(name=prefecture_name)

                    # Bước 2: Tạo hoặc cập nhật đối tượng Municipality,
                    # và liên kết nó với Prefecture vừa tìm được.
                    Municipality.objects.update_or_create(
                        name=municipality_name,
                        defaults={'prefecture': prefecture}
                    )

            self.stdout.write(self.style.SUCCESS("Nhập dữ liệu thành công!"))

        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'Không tìm thấy file: {csv_file_path}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Có lỗi xảy ra: {e}'))
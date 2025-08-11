import os
import csv
from django.core.management.base import BaseCommand
from chamu.models import Municipality, Country, Criteria, MunicipalityBaseScore


def normalize_score(raw_value, min_value, max_value):
    if max_value == min_value:
        return 1
    score = (raw_value - min_value) / (max_value - min_value) * 4 + 1
    return max(1, min(5, round(score, 1)))


class Command(BaseCommand):
    help = 'Imports and normalizes base scores for a single CSV file. The filename defines the criteria.'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='The path to the CSV file to import.')

    def handle(self, *args, **options):
        file_path = options['file_path']

        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f'Không tìm thấy file: {file_path}'))
            return

        filename = os.path.basename(file_path)
        criteria_name = os.path.splitext(filename)[0]

        self.stdout.write(self.style.NOTICE(f'Bắt đầu nhập và chuẩn hóa điểm từ file "{filename}"'))

        countries = Country.objects.all()
        if not countries:
            self.stderr.write(
                self.style.ERROR('Không có dữ liệu Country trong cơ sở dữ liệu. Vui lòng thêm dữ liệu trước.'))
            return

        # Tạo hoặc lấy đối tượng Criteria từ tên file
        criteria, _ = Criteria.objects.get_or_create(name=criteria_name)

        # Bước 1: Đọc tất cả điểm số thô từ file vào bộ nhớ
        all_scores_data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)  # Bỏ qua tiêu đề
                for row in reader:
                    if len(row) >= 3:  # Đảm bảo có ít nhất 3 cột (Number, Municipality, Score)
                        _, municipality_name, base_score_str = row
                        all_scores_data.append({
                            'municipality_name': municipality_name,
                            'raw_score': float(base_score_str)
                        })
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Có lỗi khi đọc file {filename}: {e}'))
            return

        if not all_scores_data:
            self.stdout.write(self.style.WARNING(f'File {filename} không có dữ liệu để chuẩn hóa. Bỏ qua.'))
            return

        # Tính min và max từ tất cả các điểm số đã đọc
        raw_scores = [item['raw_score'] for item in all_scores_data]
        min_value = min(raw_scores)
        max_value = max(raw_scores)

        self.stdout.write(f'  => Giá trị Min: {min_value}, Max: {max_value}')

        # Bước 2: Lặp lại dữ liệu, chuẩn hóa và lưu vào database
        for item in all_scores_data:
            municipality, created = Municipality.objects.get_or_create(name=item['municipality_name'])

            normalized_score = normalize_score(item['raw_score'], min_value, max_value)

            for country in countries:
                MunicipalityBaseScore.objects.update_or_create(
                    municipality=municipality,
                    country=country,
                    criteria=criteria,
                    defaults={'base_score': normalized_score}
                )

        self.stdout.write(self.style.SUCCESS(f'Hoàn thành việc nhập và chuẩn hóa điểm từ file "{filename}".'))
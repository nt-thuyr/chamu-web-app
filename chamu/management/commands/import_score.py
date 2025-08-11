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
    help = 'Imports and normalizes base scores for municipalities from a directory of CSV files.'

    def add_arguments(self, parser):
        parser.add_argument('scores_dir', type=str, help='The path to the directory containing CSV files.')

    def handle(self, *args, **options):
        scores_dir = options['scores_dir']

        if not os.path.isdir(scores_dir):
            self.stderr.write(self.style.ERROR(f'Không tìm thấy thư mục: {scores_dir}'))
            return

        self.stdout.write(self.style.NOTICE(f'Bắt đầu nhập và chuẩn hóa điểm từ thư mục: {scores_dir}'))

        countries = Country.objects.all()
        if not countries:
            self.stderr.write(self.style.ERROR('Không có dữ liệu Country. Vui lòng thêm dữ liệu trước.'))
            return

        # Lặp qua tất cả các file trong thư mục
        for filename in os.listdir(scores_dir):
            if not filename.endswith('.csv'):
                continue

            file_path = os.path.join(scores_dir, filename)
            criteria_name = os.path.splitext(filename)[0]
            criteria, _ = Criteria.objects.get_or_create(name=criteria_name)

            self.stdout.write(self.style.SUCCESS(f'Đang xử lý file "{filename}" cho Tiêu chí "{criteria.name}"'))

            # Bước 1: Đọc tất cả điểm số thô từ file vào bộ nhớ
            all_scores_data = []
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    next(reader)  # Bỏ qua tiêu đề
                    for row in reader:
                        if len(row) >= 2:
                            _, municipality_name, raw_score_str = row
                            all_scores_data.append({
                                'municipality_name': municipality_name,
                                'raw_score': float(raw_score_str)
                            })
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Có lỗi khi đọc file {filename}: {e}'))
                continue

            if not all_scores_data:
                self.stdout.write(self.style.WARNING(f'File {filename} không có dữ liệu để chuẩn hóa. Bỏ qua.'))
                continue

            # Tính min và max từ tất cả các điểm số đã đọc
            raw_scores = [item['raw_score'] for item in all_scores_data]
            min_value = min(raw_scores)
            max_value = max(raw_scores)

            self.stdout.write(f'  => Giá trị Min: {min_value}, Max: {max_value}')

            # Bước 2: Lặp lại dữ liệu, chuẩn hóa và lưu vào database
            for item in all_scores_data:
                municipality, created = Municipality.objects.get_or_create(name=item['municipality_name'])

                normalized_score = normalize_score(item['raw_score'], min_value, max_value)

                # Lặp qua tất cả các Country và tạo/cập nhật bản ghi điểm
                for country in countries:
                    MunicipalityBaseScore.objects.update_or_create(
                        municipality=municipality,
                        country=country,
                        criteria=criteria,
                        defaults={'base_score': normalized_score}
                    )

        self.stdout.write(self.style.SUCCESS('Hoàn thành việc nhập và chuẩn hóa điểm từ file.'))
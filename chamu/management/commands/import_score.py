import os
import csv
from django.core.management.base import BaseCommand
from django.db import transaction
from chamu.models import Municipality, Country, Criteria, MunicipalityBaseScore


def normalize_score(raw_value, min_value, max_value, is_reverse=False):
    if max_value == min_value:
        score = 1.0
    else:
        score = ((raw_value - min_value) / (max_value - min_value)) * 4 + 1

    if is_reverse:
        score = 6 - score

    return max(1.0, min(5.0, round(score, 2)))


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

        criteria_is_reverse_map = {criteria.name: criteria.is_reverse for criteria in Criteria.objects.all()}

        # Lấy tất cả các quốc gia đã tồn tại từ database
        countries = list(Country.objects.all())
        if not countries:
            self.stderr.write(self.style.ERROR(
                'Không tìm thấy quốc gia nào trong database. Vui lòng thêm quốc gia trước khi chạy lệnh này.'))
            return

        # --- BƯỚC 1: XỬ LÝ TOÀN BỘ DỮ LIỆU TỪ CÁC FILE CSV ---
        all_data = []
        unique_municipalities = set()

        for filename in os.listdir(scores_dir):
            if not filename.endswith('.csv'):
                continue

            file_path = os.path.join(scores_dir, filename)
            criteria_name = os.path.splitext(filename)[0]

            self.stdout.write(self.style.SUCCESS(f'Đang xử lý file "{filename}" cho Tiêu chí "{criteria_name}"'))

            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    next(reader)  # Bỏ qua tiêu đề
                    for row in reader:
                        if len(row) >= 4:
                            _, _, municipality_name, raw_score_str = [val.strip() for val in row[:4]]

                            unique_municipalities.add(municipality_name)

                            all_data.append({
                                'criteria_name': criteria_name,
                                'municipality_name': municipality_name,
                                'raw_score': float(raw_score_str)
                            })
                        else:
                            self.stdout.write(self.style.WARNING(f'  Dòng bị bỏ qua do không đủ 4 cột: {row}'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'  Có lỗi khi đọc file {filename}: {e}'))
                continue

        # --- BƯỚC 2: TẠO VÀ LẤY TẤT CẢ OBJECT CẦN THIẾT TRONG BULK ---
        with transaction.atomic():
            # Tạo các Municipality chưa tồn tại
            existing_municipalities = Municipality.objects.filter(name__in=unique_municipalities).values_list('name',
                                                                                                              flat=True)
            municipalities_to_create = [Municipality(name=name) for name in unique_municipalities if
                                        name not in existing_municipalities]
            if municipalities_to_create:
                Municipality.objects.bulk_create(municipalities_to_create, ignore_conflicts=True)

            municipality_map = {m.name: m for m in Municipality.objects.filter(name__in=unique_municipalities)}
            criteria_map = {c.name: c for c in Criteria.objects.all()}

        # --- BƯỚC 3: CHUẨN HÓA VÀ TẠO BẢN GHI CHO BULK UPDATE/CREATE ---
        data_by_criteria = {}
        for item in all_data:
            criteria_name = item['criteria_name']
            if criteria_name not in data_by_criteria:
                data_by_criteria[criteria_name] = []
            data_by_criteria[criteria_name].append(item)

        all_score_objects = []
        for criteria_name, items in data_by_criteria.items():
            raw_scores = [item['raw_score'] for item in items]
            if not raw_scores:
                continue
            min_value = min(raw_scores)
            max_value = max(raw_scores)
            is_reverse = criteria_is_reverse_map.get(criteria_name, False)

            for item in items:
                normalized_score = normalize_score(item['raw_score'], min_value, max_value, is_reverse)

                # Vòng lặp qua tất cả các quốc gia đã lấy từ database
                for country in countries:
                    all_score_objects.append(
                        MunicipalityBaseScore(
                            municipality=municipality_map[item['municipality_name']],
                            country=country,
                            criteria=criteria_map[item['criteria_name']],
                            base_score=normalized_score
                        )
                    )

        if all_score_objects:
            with transaction.atomic():
                MunicipalityBaseScore.objects.bulk_create(all_score_objects, ignore_conflicts=True)
            self.stdout.write(self.style.SUCCESS(f'Đã tạo mới {len(all_score_objects)} bản ghi điểm số.'))

        self.stdout.write(self.style.SUCCESS('Hoàn thành việc nhập và chuẩn hóa điểm từ file.'))
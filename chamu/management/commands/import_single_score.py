import os
import csv
from django.core.management.base import BaseCommand
from django.db import transaction
from chamu.models import Municipality, Country, Criteria, MunicipalityBaseScore
from .import_score import normalize_score


class Command(BaseCommand):
    help = 'Nhập và chuẩn hóa điểm cơ sở cho một tiêu chí duy nhất từ một file CSV.'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Đường dẫn đến file CSV chứa điểm số.')

    def handle(self, *args, **options):
        file_path = options['file_path']

        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f'Không tìm thấy file: {file_path}'))
            return

        # Lấy tên tiêu chí từ tên file (ví dụ: "chi_phi_sinh_hoat.csv" -> "chi_phi_sinh_hoat")
        criteria_name = os.path.splitext(os.path.basename(file_path))[0]
        self.stdout.write(self.style.NOTICE(f'Đang xử lý file "{file_path}" cho Tiêu chí "{criteria_name}"'))

        # Lấy các đối tượng từ database
        try:
            criteria_obj = Criteria.objects.get(name=criteria_name)
        except Criteria.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'Không tìm thấy Tiêu chí "{criteria_name}" trong database.'))
            return

        countries = list(Country.objects.all())
        if not countries:
            self.stderr.write(self.style.ERROR(
                'Không tìm thấy quốc gia nào trong database. Vui lòng thêm quốc gia trước khi chạy lệnh này.'))
            return

        # --- BƯỚC 1: ĐỌC DỮ LIỆU TỪ FILE VÀ TÍNH MIN/MAX ĐỂ CHUẨN HÓA ---
        all_data = []
        unique_municipalities = set()
        raw_scores = []

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)  # Bỏ qua tiêu đề
                for row in reader:
                    if len(row) >= 4:
                        _, _, municipality_name, raw_score_str = [val.strip() for val in row[:4]]

                        raw_score = float(raw_score_str)
                        unique_municipalities.add(municipality_name)
                        raw_scores.append(raw_score)

                        all_data.append({
                            'municipality_name': municipality_name,
                            'raw_score': raw_score
                        })
                    else:
                        self.stdout.write(self.style.WARNING(f'  Dòng bị bỏ qua do không đủ 4 cột: {row}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'  Có lỗi khi đọc file {file_path}: {e}'))
            return

        if not all_data:
            self.stderr.write(self.style.ERROR(f'File "{file_path}" không có dữ liệu để nhập.'))
            return

        min_value = min(raw_scores)
        max_value = max(raw_scores)
        is_reverse = criteria_obj.is_reverse

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

        # --- BƯỚC 3: CHUẨN HÓA VÀ TẠO BẢN GHI CHO BULK CREATE ---
        all_score_objects = []
        for item in all_data:
            normalized_score = normalize_score(item['raw_score'], min_value, max_value, is_reverse)

            # Vòng lặp qua tất cả các quốc gia đã lấy từ database
            for country in countries:
                all_score_objects.append(
                    MunicipalityBaseScore(
                        municipality=municipality_map[item['municipality_name']],
                        country=country,
                        criteria=criteria_obj,
                        base_score=normalized_score
                    )
                )

        if all_score_objects:
            with transaction.atomic():
                MunicipalityBaseScore.objects.bulk_create(all_score_objects, ignore_conflicts=True)
            self.stdout.write(self.style.SUCCESS(
                f'Đã tạo mới {len(all_score_objects)} bản ghi điểm số cho tiêu chí "{criteria_name}".'))

        self.stdout.write(self.style.SUCCESS('Hoàn thành việc nhập và chuẩn hóa điểm từ file.'))
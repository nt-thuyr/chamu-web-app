from django.core.management.base import BaseCommand
from chamu.models import Municipality
from geopy.geocoders import Nominatim
import time

class Command(BaseCommand):
    help = 'Updates the latitude and longitude for all municipalities that do not have coordinates yet.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting coordinate update for un-updated municipalities..."))
        geolocator = Nominatim(user_agent="chamu-web-app")

        # Lọc các thành phố chưa có tọa độ (latitude là null)
        municipalities_to_update = Municipality.objects.filter(latitude__isnull=True)

        self.stdout.write(self.style.NOTICE(f"Found {municipalities_to_update.count()} municipalities to update."))

        if not municipalities_to_update:
            self.stdout.write(self.style.SUCCESS("All municipalities have been updated. Exiting."))
            return

        for muni in municipalities_to_update:
            try:
                full_address = f"{muni.name}, {muni.prefecture.name}, Japan"

                location = geolocator.geocode(full_address, timeout=10)

                if location:
                    muni.latitude = location.latitude
                    muni.longitude = location.longitude
                    muni.save()
                    self.stdout.write(
                        self.style.SUCCESS(f"Updated coordinates for {muni.name}: {muni.latitude}, {muni.longitude}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Could not find coordinates for {muni.name}"))

                time.sleep(1)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing {muni.name}: {e}"))

        self.stdout.write(self.style.SUCCESS("Coordinate update complete."))
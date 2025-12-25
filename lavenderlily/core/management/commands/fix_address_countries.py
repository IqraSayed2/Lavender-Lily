from django.core.management.base import BaseCommand
from core.models import UserAddress

class Command(BaseCommand):
    help = 'Fix country field for all user addresses to United Arab Emirates'

    def handle(self, *args, **options):
        addresses = UserAddress.objects.exclude(country='United Arab Emirates')
        count = addresses.update(country='United Arab Emirates')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated country to "United Arab Emirates" for {count} addresses'
            )
        )
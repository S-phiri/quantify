from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create a demo user for testing'

    def handle(self, *args, **options):
        # Check if demo user already exists
        if User.objects.filter(username='demo').exists():
            self.stdout.write(
                self.style.WARNING('Demo user already exists!')
            )
            return

        # Create demo user
        user = User.objects.create_user(
            username='demo',
            email='demo@wealthbuddy.com',
            password='demo123',
            first_name='Demo',
            last_name='User'
        )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created demo user: {user.username}')
        )
        self.stdout.write('Username: demo')
        self.stdout.write('Password: demo123')

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import random
from faker import Faker

fake = Faker()
User = get_user_model()

ALLOWED_EMOTIONS = ['joy', 'sadness', 'anger', 'fear', 'love', 'surprise']
ALLOWED_TAGS = [
    'party', 'work', 'relaxation', 'exercise', 'running', 'yoga',
    'driving', 'social gathering', 'morning_routine'
]

class Command(BaseCommand):
    help = 'Generate synthetic users'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=50)

    def handle(self, *args, **options):
        num_users = options['users']
        for i in range(num_users):
            username = f'user{i}'
            email = f'{username}@example.com'
            password = 'password123'
            age = random.randint(18, 45)
            emotions = random.sample(ALLOWED_EMOTIONS, k=random.randint(1, 3))
            tags = random.sample(ALLOWED_TAGS, k=random.randint(2, 4))
            bio = fake.sentence()

            User.objects.create_user(
                username=username,
                email=email,
                password=password,
                age=age,
                emotions=emotions,
                tags=tags,
                bio=bio
            )

        self.stdout.write(self.style.SUCCESS(f'Successfully created {num_users} users'))

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from api.models import Song, UserActivity  
import random
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate synthetic activity data for users'

    def add_arguments(self, parser):
        parser.add_argument('--activity', type=int, default=30)

    def handle(self, *args, **options):
        num_activities = options['activity']
        users = User.objects.all()
        songs = Song.objects.all()

        for user in users:
            # Find songs that match user emotion or tag
            song_queryset = songs.filter(
                emotion__in=user.emotions
            ).order_by('?')[:50]  # pick up to 50 relevant songs

            if not song_queryset.exists():
                continue

            for _ in range(random.randint(15, num_activities)):
                song = random.choice(song_queryset)
                UserActivity.objects.create(
                    user=user,
                    song=song,
                    rating=random.randint(3, 5),
                    liked=random.choice([True, False, None]),
                    bookmarked=random.choice([True, False, None]),
                    plays=random.randint(1, 10),
                    timestamp=timezone.now() - timedelta(days=random.randint(0, 60))
                )

        self.stdout.write(self.style.SUCCESS("User activities generated successfully."))

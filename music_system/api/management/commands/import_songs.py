from django.core.management.base import BaseCommand
import csv
from api.models import Song  

class Command(BaseCommand):
    help = 'Import songs from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        with open(csv_file, newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            songs = []
            for row in reader:
                song = Song(
                    artist=row['Artist(s)'],
                    song=row['song'],
                    text=row['text'],
                    length=row['Length'],
                    emotion=row['emotion'],
                    genre=row['Genre'],
                    album=row['Album'],
                    release_date=row['Release Date'],
                    key=row['Key'],
                    tempo=row['Tempo'],
                    loudness_db=row['Loudness (db)'],
                    time_signature=row['Time signature'],
                    popularity=row['Popularity'],
                    energy=row['Energy'],
                    danceability=row['Danceability'],
                    positiveness=row['Positiveness'],
                    speechiness=row['Speechiness'],
                    liveness=row['Liveness'],
                    acousticness=row['Acousticness'],
                    instrumentalness=row['Instrumentalness'],
                    good_for_party=row['Good for Party'],
                    good_for_work_study=row['Good for Work/Study'],
                    good_for_relaxation=row['Good for Relaxation/Meditation'],
                    good_for_exercise=row['Good for Exercise'],
                    good_for_running=row['Good for Running'],
                    good_for_yoga=row['Good for Yoga/Stretching'],
                    good_for_driving=row['Good for Driving'],
                    good_for_social=row['Good for Social Gatherings'],
                    good_for_morning=row['Good for Morning Routine'],
                    release_year=row['Release_Year']
                )
                songs.append(song)
            Song.objects.bulk_create(songs)
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {len(songs)} songs'))

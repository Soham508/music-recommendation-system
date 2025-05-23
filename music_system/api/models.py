from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone

ALLOWED_EMOTIONS = ['joy', 'sadness', 'anger', 'fear', 'love', 'surprise']
ALLOWED_TAGS = [
    'party', 'work', 'relaxation', 'exercise', 'running', 'yoga',
    'driving', 'social gathering', 'morning_routine'
]

def validate_emotions(value):
    if not isinstance(value, list):
        raise ValidationError("Emotion must be a list.")
    for item in value:
        if item not in ALLOWED_EMOTIONS:
            raise ValidationError(f"Invalid emotion: {item}")

def validate_tags(value):
    if not isinstance(value, list):
        raise ValidationError("Tags must be a list.")
    for item in value:
        if item not in ALLOWED_TAGS:
            raise ValidationError(f"Invalid tag: {item}")

class User(AbstractUser):
    email = models.EmailField()
    age = models.IntegerField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    emotions = models.JSONField(default=list, validators=[validate_emotions], blank=True)
    tags = models.JSONField(default=list, validators=[validate_tags], blank=True)

    def __str__(self):
        return self.username

class Song(models.Model):
    artist = models.CharField(max_length=255)
    song = models.CharField(max_length=255)
    text = models.TextField()
    length = models.CharField(max_length=50)
    emotion = models.CharField(max_length=50)
    genre = models.CharField(max_length=100)
    album = models.CharField(max_length=255)
    release_date = models.CharField(max_length=50)
    key = models.CharField(max_length=10)
    tempo = models.FloatField()
    loudness_db = models.FloatField()
    time_signature = models.CharField(max_length=20)
    popularity = models.FloatField()
    energy = models.FloatField()
    danceability = models.FloatField()
    positiveness = models.FloatField()
    speechiness = models.FloatField()
    liveness = models.FloatField()
    acousticness = models.FloatField()
    instrumentalness = models.FloatField()
    good_for_party = models.FloatField()
    good_for_work_study = models.FloatField()
    good_for_relaxation = models.FloatField()
    good_for_exercise = models.FloatField()
    good_for_running = models.FloatField()
    good_for_yoga = models.FloatField()
    good_for_driving = models.FloatField()
    good_for_social = models.FloatField()
    good_for_morning = models.FloatField()
    release_year = models.FloatField()

    def __str__(self):
        return f"{self.song} by {self.artist}"

class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='activities')
    
    rating = models.PositiveSmallIntegerField(default=3)  
    plays = models.PositiveIntegerField(default=1)
    
    liked = models.BooleanField(null=True, blank=True) 
    bookmarked = models.BooleanField(null=True, blank=True)  

    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['song']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.song.song} ({self.timestamp})"
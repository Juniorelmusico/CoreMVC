from django.contrib import admin
from .models import Artist, Genre, Mood, Track, Analysis

@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Mood)
class MoodAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'genre', 'mood', 'bpm', 'duration', 'created_at')
    search_fields = ('title', 'artist__name')
    list_filter = ('genre', 'mood', 'created_at')

@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ('track', 'analyzed_at')
    search_fields = ('track__title',)
from django.contrib import admin
from .models import Artist, Genre, Mood, Track, Analysis, MusicAnalysis

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
    list_display = ('title', 'artist', 'genre', 'mood', 'bpm', 'duration', 'uploaded_at')
    search_fields = ('title', 'artist__name')
    list_filter = ('genre', 'mood', 'uploaded_at')


@admin.register(MusicAnalysis)
class MusicAnalysisAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'artist', 'user', 'created_at', 'track')
    search_fields = ('title', 'artist', 'user__username')
    list_filter = ('user', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
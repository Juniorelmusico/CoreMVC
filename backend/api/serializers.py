from django.contrib.auth.models import User
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from rest_framework.exceptions import ValidationError
from .models import Note, Artist, Genre, Mood, Track, Analysis, UploadedFile, MusicFile


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="Este email ya está en uso.")]
    )
    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="Este nombre de usuario ya está en uso.")]
    )
    is_superuser = serializers.BooleanField(required=False)
    date_joined = serializers.DateTimeField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'confirm_password', 'is_superuser', 'date_joined')

    def validate_password(self, value):
        if value:
            validate_password(value)
        return value

    def validate(self, data):
        if data.get('password') or data.get('confirm_password'):
            if data.get('password') != data.get('confirm_password'):
                raise ValidationError({"confirm_password": "Las contraseñas no coinciden."})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        validated_data.pop('confirm_password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["id", "title", "content", "created_at", "author"]
        extra_kwargs = {"author": {"read_only": True}}


class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = ('id', 'name', 'user')
        read_only_fields = ('user',)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = '__all__'


class MoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mood
        fields = '__all__'


class AnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analysis
        fields = '__all__'


class TrackSerializer(serializers.ModelSerializer):
    artist = ArtistSerializer(read_only=True)
    genre = GenreSerializer(read_only=True)
    mood = MoodSerializer(read_only=True)
    analysis = AnalysisSerializer(read_only=True)
    
    class Meta:
        model = Track
        fields = (
            'id', 'title', 'artist', 'file', 'duration', 'bpm',
            'genre', 'mood', 'uploaded_at', 'fingerprint_status',
            'fingerprint_error', 'analysis', 'fingerprints_count'
        )
        read_only_fields = ('duration', 'bpm', 'genre', 'mood', 'fingerprint_status', 'fingerprint_error', 'fingerprints_count')


class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ['id', 'file', 'name', 'content_type', 'size', 'uploaded_at']
        read_only_fields = ['uploaded_by']


class TrackUploadSerializer(serializers.ModelSerializer):
    artist_name = serializers.CharField(write_only=True)
    
    class Meta:
        model = Track
        fields = ('title', 'file', 'artist_name')


class TrackCreateSerializer(serializers.ModelSerializer):
    def validate_bpm(self, value):
        if value is not None:
            if value < 0 or value > 200:
                raise serializers.ValidationError("El BPM debe estar entre 0 y 200.")
        return value
    class Meta:
        model = Track
        fields = ('title', 'artist', 'file', 'duration', 'bpm', 'genre', 'mood')


class MusicFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MusicFile
        fields = ['id', 'title', 'artist', 'file', 'duration', 'tempo', 'key', 'loudness', 'created_at']
        read_only_fields = ['duration', 'tempo', 'key', 'loudness', 'created_at']
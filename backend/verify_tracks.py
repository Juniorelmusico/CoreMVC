#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import Track, Artist, Genre, Mood, Recognition, UploadedFile

print("🔍 VERIFICACIÓN COMPLETA DEL SISTEMA")
print("===================================")

print("📊 ESTADÍSTICAS GENERALES:")
print(f"   👥 Artistas: {Artist.objects.count()}")
print(f"   🎵 Tracks totales: {Track.objects.count()}")
print(f"   📚 Tracks de referencia: {Track.objects.filter(is_reference_track=True).count()}")
print(f"   📁 Archivos subidos: {UploadedFile.objects.count()}")
print(f"   🎯 Reconocimientos: {Recognition.objects.count()}")
print(f"   🎼 Géneros: {Genre.objects.count()}")
print(f"   😊 Moods: {Mood.objects.count()}")

print(f"\n🎵 TRACKS DE REFERENCIA:")
ref_tracks = Track.objects.filter(is_reference_track=True).order_by('title')
if ref_tracks.exists():
    for track in ref_tracks:
        print(f"   ID {track.id}: '{track.title}' - {track.artist.name}")
        print(f"      Género: {track.genre.name if track.genre else 'Sin género'}")
        print(f"      Mood: {track.mood.name if track.mood else 'Sin mood'}")
        print(f"      Fingerprint: {track.fingerprint_status} ({track.fingerprints_count} fps)")
        print(f"      Archivo: {'Sí' if track.file else 'No'}")
        print()
else:
    print("   ❌ No hay tracks de referencia")

print(f"👥 ARTISTAS:")
artists = Artist.objects.all().order_by('name')
for artist in artists:
    track_count = Track.objects.filter(artist=artist).count()
    print(f"   {artist.name} ({track_count} tracks)")

print(f"\n🎯 ÚLTIMOS RECONOCIMIENTOS:")
recent_recognitions = Recognition.objects.order_by('-created_at')[:5]
if recent_recognitions.exists():
    for rec in recent_recognitions:
        status = "✅" if rec.recognition_status == 'found' else "❌"
        track_name = rec.recognized_track.title if rec.recognized_track else "Track eliminado"
        artist_name = rec.recognized_track.artist.name if rec.recognized_track else "Artista eliminado"
        print(f"   {status} {rec.uploaded_file.name} -> {track_name} - {artist_name} ({rec.confidence:.1%})")
else:
    print("   No hay reconocimientos")

print(f"\n📁 ÚLTIMOS ARCHIVOS SUBIDOS:")
recent_files = UploadedFile.objects.order_by('-uploaded_at')[:5]
if recent_files.exists():
    for file in recent_files:
        print(f"   {file.name} ({file.uploaded_at.strftime('%H:%M:%S')})")
else:
    print("   No hay archivos subidos")

print(f"\n🎼 GÉNEROS DISPONIBLES:")
for genre in Genre.objects.all():
    track_count = Track.objects.filter(genre=genre).count()
    print(f"   {genre.name} ({track_count} tracks)")

print(f"\n😊 MOODS DISPONIBLES:")
for mood in Mood.objects.all():
    track_count = Track.objects.filter(mood=mood).count()
    print(f"   {mood.name} ({track_count} tracks)")

print(f"\n✅ Verificación completada!")
print(f"\n💡 PARA PROBAR:")
print(f"   1. Sube 'Escribeme version Karaoke' -> Debería funcionar al 100%")
print(f"   2. Sube 'Sunshine Reggae' -> Debería funcionar correctamente ahora") 
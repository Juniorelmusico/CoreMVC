import base64
import hashlib
import hmac
import time
import requests
from typing import Dict, Optional, Any

class ACRCloudService:
    """
    Servicio de reconocimiento de música usando ACRCloud API
    Mucho más preciso que implementaciones caseras
    """
    
    def __init__(self, host: str, access_key: str, access_secret: str):
        self.host = host
        self.access_key = access_key
        self.access_secret = access_secret
        self.timeout = 10
    
    def recognize_file(self, file_path: str) -> Dict[str, Any]:
        """
        Reconocer archivo de audio usando ACRCloud
        """
        try:
            with open(file_path, 'rb') as f:
                audio_data = f.read()
            
            return self.recognize_audio(audio_data)
        except Exception as e:
            return {
                'success': False,
                'error': f'Error leyendo archivo: {str(e)}'
            }
    
    def recognize_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Reconocer datos de audio usando ACRCloud API
        """
        try:
            # Preparar request
            http_method = "POST"
            http_uri = "/v1/identify"
            data_type = "audio"
            signature_version = "1"
            timestamp = str(time.time())
            
            # Crear signature
            string_to_sign = f"{http_method}\n{http_uri}\n{self.access_key}\n{data_type}\n{signature_version}\n{timestamp}"
            signature = base64.b64encode(
                hmac.new(
                    self.access_secret.encode('utf-8'),
                    string_to_sign.encode('utf-8'),
                    hashlib.sha1
                ).digest()
            ).decode('utf-8')
            
            # Preparar datos
            files = {'sample': audio_data}
            data = {
                'access_key': self.access_key,
                'sample_bytes': len(audio_data),
                'timestamp': timestamp,
                'signature': signature,
                'data_type': data_type,
                'signature_version': signature_version
            }
            
            # Hacer request
            url = f"https://{self.host}{http_uri}"
            response = requests.post(url, files=files, data=data, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                return self.parse_acrcloud_response(result)
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error en reconocimiento: {str(e)}'
            }
    
    def parse_acrcloud_response(self, response: Dict) -> Dict[str, Any]:
        """
        Parsear respuesta de ACRCloud a formato estándar
        """
        try:
            status = response.get('status', {})
            
            if status.get('code') == 0:  # Éxito
                metadata = response.get('metadata', {})
                music = metadata.get('music', [])
                
                if music:
                    track_info = music[0]  # Primer resultado
                    
                    # Extraer información del artista
                    artists = track_info.get('artists', [])
                    artist_name = artists[0]['name'] if artists else 'Unknown Artist'
                    
                    # Extraer información del álbum
                    album = track_info.get('album', {})
                    album_name = album.get('name', 'Unknown Album')
                    
                    return {
                        'success': True,
                        'recognized': True,
                        'confidence': track_info.get('score', 0) / 100.0,  # Convertir a 0-1
                        'track_info': {
                            'title': track_info.get('title', 'Unknown Title'),
                            'artist': artist_name,
                            'album': album_name,
                            'duration': track_info.get('duration_ms', 0) // 1000,
                            'release_date': track_info.get('release_date'),
                            'genres': [genre['name'] for genre in track_info.get('genres', [])],
                            'acrid': track_info.get('acrid'),  # ID único de ACRCloud
                            'external_ids': track_info.get('external_ids', {}),
                            'spotify_id': track_info.get('external_ids', {}).get('spotify'),
                            'youtube_id': track_info.get('external_ids', {}).get('youtube'),
                        },
                        'offset_seconds': metadata.get('timestamp_utc'),
                        'raw_response': response
                    }
                else:
                    return {
                        'success': True,
                        'recognized': False,
                        'message': 'No se encontró coincidencia',
                        'raw_response': response
                    }
            else:
                return {
                    'success': False,
                    'error': f"ACRCloud error: {status.get('msg', 'Unknown error')}",
                    'raw_response': response
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error parseando respuesta: {str(e)}',
                'raw_response': response
            }


# Instancia global del servicio
acrcloud_service = None

def get_acrcloud_service():
    """
    Obtener instancia del servicio ACRCloud
    """
    global acrcloud_service
    
    if acrcloud_service is None:
        from django.conf import settings
        
        # Configuración desde settings.py
        host = getattr(settings, 'ACRCLOUD_HOST', 'identify-us-west-2.acrcloud.com')
        access_key = getattr(settings, 'ACRCLOUD_ACCESS_KEY', '')
        access_secret = getattr(settings, 'ACRCLOUD_ACCESS_SECRET', '')
        
        if not access_key or not access_secret:
            raise ValueError(
                'ACRCloud credentials not configured. '
                'Set ACRCLOUD_ACCESS_KEY and ACRCLOUD_ACCESS_SECRET in settings.py'
            )
        
        acrcloud_service = ACRCloudService(host, access_key, access_secret)
    
    return acrcloud_service 
import requests
import json
from typing import Dict, Any

class AudDService:
    """
    Servicio de reconocimiento de música usando AudD API (GRATUITO)
    Alternativa simple y gratuita a ACRCloud
    """
    
    def __init__(self, api_token: str = None):
        self.api_token = api_token
        self.base_url = "https://api.audd.io/"
        self.timeout = 30
    
    def recognize_file(self, file_path: str) -> Dict[str, Any]:
        """
        Reconocer archivo de audio usando AudD API
        """
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {'return': 'apple_music,spotify'}
                
                if self.api_token:
                    data['api_token'] = self.api_token
                
                response = requests.post(
                    self.base_url,
                    files=files,
                    data=data,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return self.parse_audd_response(result)
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
    
    def recognize_url(self, audio_url: str) -> Dict[str, Any]:
        """
        Reconocer audio desde URL usando AudD API
        """
        try:
            data = {
                'url': audio_url,
                'return': 'apple_music,spotify'
            }
            
            if self.api_token:
                data['api_token'] = self.api_token
            
            response = requests.post(
                self.base_url,
                data=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return self.parse_audd_response(result)
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
    
    def parse_audd_response(self, response: Dict) -> Dict[str, Any]:
        """
        Parsear respuesta de AudD a formato estándar
        """
        try:
            print(f"🔍 AudD Raw Response: {response}")  # DEBUG: Ver respuesta completa
            
            status = response.get('status')
            
            if status == 'success':
                result = response.get('result')
                
                if result and result != 'No result':
                    # Información básica
                    track_info = {
                        'title': result.get('title', 'Unknown Title'),
                        'artist': result.get('artist', 'Unknown Artist'),
                        'album': result.get('album', 'Unknown Album'),
                        'release_date': result.get('release_date'),
                        'label': result.get('label'),
                        'timecode': result.get('timecode'),
                        'song_link': result.get('song_link')
                    }
                    
                    # Información de servicios de streaming
                    if 'apple_music' in result:
                        apple_music = result['apple_music']
                        track_info['apple_music'] = {
                            'url': apple_music.get('url'),
                            'artwork': apple_music.get('artwork', {}).get('url'),
                            'genres': apple_music.get('genreNames', []),
                            'preview_url': apple_music.get('previewUrl')
                        }
                    
                    if 'spotify' in result:
                        spotify = result['spotify']
                        track_info['spotify'] = {
                            'id': spotify.get('id'),
                            'external_urls': spotify.get('external_urls', {}),
                            'preview_url': spotify.get('preview_url'),
                            'popularity': spotify.get('popularity'),
                            'artists': [artist.get('name') for artist in spotify.get('artists', [])]
                        }
                    
                    return {
                        'success': True,
                        'recognized': True,
                        'track_info': track_info,
                        'raw_response': response
                    }
                else:
                    print(f"⚠️ AudD: No result found")
                    return {
                        'success': True,
                        'recognized': False,
                        'message': 'No se encontró coincidencia',
                        'raw_response': response
                    }
            else:
                # Manejar errores específicos
                error_info = response.get('error', {})
                error_message = error_info.get('error_message', 'Unknown error')
                error_code = error_info.get('error_code', 'unknown')
                
                print(f"❌ AudD Error - Code: {error_code}, Message: {error_message}")
                
                # Detectar límite de cuota
                if 'limit' in error_message.lower() or 'quota' in error_message.lower() or error_code in ['400', '429']:
                    return {
                        'success': False,
                        'quota_exceeded': True,
                        'error': f"🚫 Límite de API alcanzado: {error_message}",
                        'message': 'Has alcanzado el límite diario de AudD (25 reconocimientos gratuitos)',
                        'raw_response': response
                    }
                else:
                    return {
                        'success': False,
                        'error': f"AudD error: {error_message}",
                        'raw_response': response
                    }
                
        except Exception as e:
            print(f"❌ Error parseando respuesta AudD: {str(e)}")
            return {
                'success': False,
                'error': f'Error parseando respuesta: {str(e)}',
                'raw_response': response
            }


# Instancia global del servicio
audd_service = None

def get_audd_service():
    """
    Obtener instancia del servicio AudD
    """
    global audd_service
    
    if audd_service is None:
        from django.conf import settings
        
        # API token es opcional para AudD (gratuito con límites)
        api_token = getattr(settings, 'AUDD_API_TOKEN', None)
        audd_service = AudDService(api_token)
    
    return audd_service 
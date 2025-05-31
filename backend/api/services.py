import librosa
import numpy as np
from typing import Dict, Any

def analyze_music_file(file_path: str) -> Dict[str, Any]:
    """
    Analyze a music file and extract its metadata using librosa.
    
    Args:
        file_path: Path to the music file
        
    Returns:
        Dictionary containing the extracted metadata
    """
    try:
        # Load the audio file
        y, sr = librosa.load(file_path)
        
        # Get duration
        duration = librosa.get_duration(y=y, sr=sr)
        
        # Get tempo
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        
        # Get key using chroma features
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        key_idx = np.argmax(np.mean(chroma, axis=1))
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        key = keys[key_idx]
        
        # Get loudness (RMS energy)
        rms = librosa.feature.rms(y=y)[0]
        loudness = float(np.mean(rms))
        
        return {
            'duration': duration,
            'tempo': tempo,
            'key': key,
            'loudness': loudness
        }
    except Exception as e:
        raise Exception(f"Error analyzing music file: {str(e)}") 
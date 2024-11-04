# game/models/song.py

import os
import json
import uuid
import wave
import contextlib
import mutagen  # Добавьте: pip install mutagen

class Song:
    """
    Class representing a song and its properties.
    """

    def __init__(self, song_dir):
        self.song_dir = song_dir
        self.info = {}
        self.id = str(uuid.uuid4())
        self.name = ""
        self.artist = ""
        self.album = ""
        self.year = ""
        self.genre = ""
        self.cover_image = ""
        self.background = ""
        self.audio_files = []
        self.midi_file = ""
        self.subtitle_file = ""
        self.video_file = ""
        self.difficulty = ""
        self.bpm = ""
        self.duration = 0
        self.load_info()

    def load_info(self):
        """Loads song information from the info.json file."""
        info_path = os.path.join(self.song_dir, 'info.json')
        if os.path.exists(info_path):
            with open(info_path, 'r', encoding='utf-8') as f:
                self.info = json.load(f)
            self.name = self.info.get('name', 'Unknown')
            self.artist = self.info.get('artist', 'Unknown')
            self.album = self.info.get('album', '')
            self.year = self.info.get('year', '')
            self.genre = self.info.get('genre', '')
            
            # Проверка существования файлов обложки и фона
            cover_path = os.path.join(self.song_dir, self.info.get('cover_image', ''))
            background_path = os.path.join(self.song_dir, self.info.get('background', ''))
            
            self.cover_image = cover_path if os.path.exists(cover_path) else 'assets/images/default_cover.png'
            self.background = background_path if os.path.exists(background_path) else 'assets/images/default_background.png'
            
            self.midi_file = os.path.join(self.song_dir, self.info.get('midi_file', ''))
            self.subtitle_file = os.path.join(self.song_dir, self.info.get('subtitle_file', ''))
            self.video_file = os.path.join(self.song_dir, self.info.get('video_file', ''))
            self.audio_files = []
            if len(self.info.get('audio_files', [])) > 0:
                for audio_file in self.info.get('audio_files', []):
                    full_path = os.path.join(self.song_dir, audio_file)
                    if os.path.exists(full_path):
                        self.audio_files.append(full_path)
            self.difficulty = self.info.get('difficulty', 'Normal')
            self.bpm = self.info.get('bpm', 'Unknown')

            # Calculate duration if not provided
            self.duration = self.info.get('duration', 0)
            if self.duration == 0 and self.audio_files:
                total_duration = 0
                for audio_file in self.audio_files:
                    try:
                        # Сначала пробуем mutagen для быстрого получения метаданных
                        audio = mutagen.File(audio_file)
                        if audio is not None:
                            total_duration = max(total_duration, audio.info.length)
                            continue
                        
                        # Для WAV файлов используем wave
                        if audio_file.lower().endswith('.wav'):
                            with contextlib.closing(wave.open(audio_file, 'r')) as f:
                                frames = f.getnframes()
                                rate = f.getframerate()
                                duration = frames / float(rate)
                                total_duration = max(total_duration, duration)
                    except Exception:
                        # Если не удалось определить длительность, установим значение по умолчанию
                        total_duration = max(total_duration, 180)  # 3 минуты по умолчанию
                    
                self.duration = total_duration

        else:
            raise FileNotFoundError(f"info.json file not found in directory {self.song_dir}")

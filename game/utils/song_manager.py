# game/utils/song_manager.py

import os
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from models.song import Song

class SongManager:
    """
    Manages loading and accessing songs.
    """

    def __init__(self, songs_directory='assets/songs'):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.songs_directory = songs_directory
        self.songs = []
        self.loading_complete = threading.Event()
        self._load_songs_async()

    def _load_songs_async(self):
        """Асинхронная загрузка песен"""
        def load_worker():
            with ThreadPoolExecutor(max_workers=4) as executor:
                if not os.path.exists(self.songs_directory):
                    self.logger.error(f"Songs directory '{self.songs_directory}' not found.")
                    return

                song_folders = [
                    os.path.join(self.songs_directory, folder)
                    for folder in os.listdir(self.songs_directory)
                    if os.path.isdir(os.path.join(self.songs_directory, folder))
                ]

                # Загружаем песни параллельно
                futures = []
                for song_dir in song_folders:
                    future = executor.submit(self._load_single_song, song_dir)
                    futures.append(future)

                # Собираем результаты
                for future in futures:
                    try:
                        song = future.result()
                        if song:
                            self.songs.append(song)
                    except Exception as e:
                        self.logger.exception("Error loading song")

            self.loading_complete.set()
            self.logger.info(f"Loaded {len(self.songs)} songs")

        threading.Thread(target=load_worker, daemon=True).start()

    def _load_single_song(self, song_dir):
        """Загрузка одной песни"""
        try:
            return Song(song_dir)
        except Exception as e:
            self.logger.exception(f"Error loading song from '{song_dir}'")
            return None

    def get_all_songs(self):
        """Returns a list of all loaded songs."""
        if not self.loading_complete.is_set():
            self.logger.info("Waiting for songs to load...")
            self.loading_complete.wait(timeout=5)  # Ждем максимум 5 секунд
        return self.songs

    def get_song_by_id(self, song_id):
        """
        Returns a song by its ID.
        """
        for song in self.songs:
            if song.id == song_id:
                return song
        return None

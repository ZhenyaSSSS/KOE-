import threading
import sounddevice as sd
import numpy as np
import logging
import soundfile as sf
import time

class AudioController:
    """
    Controller for managing audio playback.
    """

    # Статический кэш для хранения предзагруженных превью
    _preview_cache = {}
    
    @classmethod
    def clear_cache(cls):
        """Очищает кэш превью."""
        cls._preview_cache.clear()
        
    def __init__(self, audio_files, output_device=None, preview_mode=False):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.audio_files = audio_files
        self.output_device = self.get_valid_output_device(output_device)
        self.stream = None
        self.stop_event = threading.Event()
        self.thread = None
        self.volumes = {track: 1.0 for track in audio_files}
        self.volume_lock = threading.Lock()  # Добавлен обратно
        self.lock = threading.Lock()  # Добавлен обратно
        self.start_time = None
        self.is_playing_flag = False
        self.preview_mode = preview_mode
        self.audio_data = {}
        self.sample_rate = None
        self.original_audio_data = {}  # Добавляем хранилище оригинальных данных
        
        if preview_mode:
            self.load_from_cache()
        else:
            self.load_audio()

    def get_valid_output_device(self, preferred_device):
        try:
            if preferred_device is not None:
                # Attempt to get device index from string
                device_index = int(preferred_device.split(":")[0])
                # Check if device exists
                sd.query_devices(device_index)
                return device_index
        except Exception as e:
            self.logger.warning(f"Preferred output device '{preferred_device}' not found. Using default device. Error: {e}")
        
        # Use default device if preferred device is not found
        return None

    def load_from_cache(self):
        """Загружает аудио из кэша или создает новый кэш."""
        try:
            cache_key = tuple(sorted(self.audio_files))
            
            if cache_key in self._preview_cache:
                self.logger.debug(f"Using cached audio for {cache_key}")
                self.original_audio_data, self.sample_rate = self._preview_cache[cache_key]
                self.audio_data = {k: v.copy() for k, v in self.original_audio_data.items()}
                return
            
            self.logger.debug(f"Loading and caching audio for {cache_key}")
            # Загрузка только аудио файлов
            for audio_file in self.audio_files:
                if not audio_file.lower().endswith(('.mp3', '.wav', '.ogg')):
                    self.logger.warning(f"Skipping non-audio file: {audio_file}")
                    continue
                    
                info = sf.info(audio_file)
                if self.sample_rate is None:
                    self.sample_rate = info.samplerate
                
                frames_to_read = int(30 * info.samplerate)
                data, _ = sf.read(
                    audio_file,
                    dtype='float32',
                    frames=frames_to_read,
                    always_2d=True
                )
                self.original_audio_data[audio_file] = data
            
            if self.original_audio_data:  # Проверяем, что есть что кэшировать
                self._preview_cache[cache_key] = (self.original_audio_data.copy(), self.sample_rate)
                self.audio_data = {k: v.copy() for k, v in self.original_audio_data.items()}
            
        except Exception as e:
            self.logger.exception(f"Error loading audio files: {e}")

    def load_audio(self):
        """Загружает полные аудио файлы для режима игры."""
        try:
            for audio_file in self.audio_files:
                info = sf.info(audio_file)
                if self.sample_rate is None:
                    self.sample_rate = info.samplerate
                
                data, _ = sf.read(
                    audio_file,
                    dtype='float32',
                    always_2d=True
                )
                self.audio_data[audio_file] = data
                # Сохраняем копию оригинальных данных
                self.original_audio_data[audio_file] = data.copy()
                
        except Exception as e:
            self.logger.exception("Error loading audio files")

    def play(self):
        """Starts audio playback."""
        try:
            if not self.is_playing_flag:
                self.stop()
                
                # Восстанавливаем аудио данные из оригинальных
                self.audio_data = {k: v.copy() for k, v in self.original_audio_data.items()}
                
                self.stop_event.clear()
                self.start_time = time.time()
                self.thread = threading.Thread(target=self.audio_playback, daemon=True)
                self.thread.start()
                self.is_playing_flag = True
                self.logger.info("Audio playback started")
        except Exception as e:
            self.logger.error(f"Error starting playback: {e}")

    def on_stream_finished(self):
        """Callback для завершения потока вывода."""
        # Убираем лишнее логирование
        with self.lock:
            self.is_playing_flag = False
            self.start_time = None

    def audio_playback(self, retry_count=0, max_retries=3):
        if retry_count > max_retries:
            self.logger.error("Maximum retry count reached.")
            return
        try:
            def callback(outdata, frames, time_info, status):
                try:
                    if status:
                        # Используем более легкий способ логирования для callback'а
                        print(f"Callback status: {status}")
                    if self.stop_event.is_set():
                        raise sd.CallbackAbort

                    mixed_data = np.zeros((frames, 2), dtype='float32')
                    all_tracks_empty = True

                    with self.volume_lock:
                        for track, data in self.audio_data.items():
                            if len(data) > 0:
                                all_tracks_empty = False
                                volume = self.volumes.get(track, 1.0)
                                end = min(frames, len(data))
                                track_data = data[:end]
                                if track_data.ndim == 1:
                                    track_data = track_data[:, np.newaxis]
                                    track_data = np.repeat(track_data, 2, axis=1)
                                mixed_data[:end] += track_data * volume
                                self.audio_data[track] = data[end:]
                    
                    # Если все треки закончились и мы в режиме превью - перезапускаем их
                    if all_tracks_empty and self.preview_mode:
                        self.audio_data = {k: v.copy() for k, v in self.original_audio_data.items()}
                        # Рекурсивно вызываем callback для заполнения текущего буфера
                        return callback(outdata, frames, time_info, status)
                    
                    outdata[:] = mixed_data

                    if all_tracks_empty and not self.preview_mode:
                        raise sd.CallbackStop

                except Exception as e:
                    # Избегаем сложного логирования в callback'е
                    print(f"Error in audio callback: {e}")
                    raise

            with sd.OutputStream(
                samplerate=self.sample_rate,
                channels=2,
                callback=callback,
                device=self.output_device,
                dtype='float32',
                finished_callback=self.on_stream_finished
            ) as self.stream:
                self.logger.info("Output stream opened.")
                while not self.stop_event.is_set():
                    sd.sleep(10)

        except (sd.CallbackStop, sd.CallbackAbort):
            self.logger.info("Audio playback stopped normally.")
        except Exception as e:
            self.logger.error(f"Error during audio playback: {e}")
            if self.output_device is not None:
                self.logger.info("Attempting to use default device.")
                self.output_device = None
                self.audio_playback(retry_count=retry_count+1)

    def stop(self):
        """Stops audio playback."""
        if not self.is_playing_flag:  # Добавляем проверку
            return
        
        try:
            self.stop_event.set()
            if self.stream:
                self.stream.abort()
                self.stream = None
            
            self.is_playing_flag = False
            self.start_time = None
            self.thread = None
            self.logger.debug("Audio playback stopped.")  # Меняем уровень логирования на debug
        except Exception as e:
            self.logger.error(f"Error stopping playback: {e}")

    def set_volumes(self, volumes):
        """Sets the volume for each track."""
        self.volumes.update(volumes)
        # Убираем избыточное логирование

    def set_volume(self, track, volume):
        """Sets the volume for a single track."""
        with self.volume_lock:
            if track in self.volumes:
                self.volumes[track] = volume
                self.logger.info(f"Volume for track '{track}' set to {volume}")
            else:
                self.logger.warning(f"Track '{track}' not found. Cannot set volume.")

    def is_playing(self):
        """Returns True if audio is currently playing."""
        return self.is_playing_flag

    def get_time(self):
        """Returns the current playback time in seconds."""
        if self.start_time is None or not self.is_playing():
            return 0
        return time.time() - self.start_time

# game/controllers/subtitle_controller.py

import threading
import time
import logging
from models.subtitle import SubtitleParser

class SubtitleController:
    """
    Контроллер для управления субтитрами во время воспроизведения песни.
    """

    def __init__(self, subtitle_file):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.subtitle_file = subtitle_file
        self.subtitles = []
        self.current_subtitle = None
        self.running = False
        self.thread = None
        self.start_time = 0.0
        self.load_subtitles()

    def load_subtitles(self):
        """Загружает субтитры из файла."""
        try:
            parser = SubtitleParser(self.subtitle_file)
            self.subtitles = parser.parse()
            self.logger.info("Субтитры успешно загружены.")
        except Exception as e:
            self.logger.exception("Ошибка при загрузке субтитров.")

    def start(self):
        """Запускает поток обновления субтитров."""
        self.running = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self.update_subtitles)
        self.thread.start()

    def stop(self):
        """Останавливает поток обновления субтитров."""
        self.running = False
        if self.thread:
            self.thread.join()

    def update_subtitles(self):
        """Обновляет текущий субтитр в соответствии с временем."""
        idx = 0
        while self.running and idx < len(self.subtitles):
            current_time = time.time() - self.start_time
            subtitle = self.subtitles[idx]
            if current_time >= subtitle.start_time:
                if current_time <= subtitle.end_time:
                    self.current_subtitle = subtitle
                else:
                    idx += 1
                    self.current_subtitle = None
            else:
                self.current_subtitle = None
            time.sleep(0.1)
        self.current_subtitle = None

    def get_current_subtitle(self):
        """Возвращает текущий субтитр."""
        return self.current_subtitle

# game/utils/resource_loader.py

import os
import json
import random
import pyglet
import logging

class ResourceLoader:
    """
    Класс для загрузки и управления ресурсами игры.
    Предоставляет методы для загрузки изображений, аудио, локализаций и других ресурсов с кэшированием.
    """

    def __init__(self, resource_path='assets'):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.resource_path = resource_path
        self.image_cache = {}
        self.audio_cache = {}
        self.font_cache = {}
        self.backgrounds = []
        self._load_backgrounds()

    def _load_backgrounds(self):
        """Загружает пути к фоновым изображениям из директории."""
        backgrounds_dir = os.path.join(self.resource_path, 'backgrounds')
        if os.path.exists(backgrounds_dir):
            for filename in os.listdir(backgrounds_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    self.backgrounds.append(os.path.join('backgrounds', filename))
            self.logger.info(f"Загружено {len(self.backgrounds)} фоновых изображений.")
        else:
            self.logger.warning(f"Директория с фонами не найдена: {backgrounds_dir}")

    def load_image(self, path):
        """
        Загружает изображение с кэшированием.

        :param path: Путь к изображению относительно директории ресурсов.
        :return: Экземпляр pyglet.image.AbstractImage.
        """
        if path in self.image_cache:
            return self.image_cache[path]
        else:
            full_path = os.path.join(self.resource_path, path)
            if os.path.exists(full_path):
                try:
                    image = pyglet.image.load(full_path)
                    self.image_cache[path] = image
                    self.logger.info(f"Изображение загружено: {path}")
                    return image
                except Exception as e:
                    self.logger.exception(f"Ошибка при загрузке изображения: {path}")
                    return None
            else:
                self.logger.error(f"Изображение не найдено: {full_path}")
                return None

    def load_audio(self, path):
        """
        Загружает аудио с кэшированием.

        :param path: Путь к аудио файлу относительно директории ресурсов.
        :return: Экземпляр pyglet.media.Source.
        """
        if path in self.audio_cache:
            return self.audio_cache[path]
        else:
            full_path = os.path.join(self.resource_path, path)
            if os.path.exists(full_path):
                try:
                    audio = pyglet.media.load(full_path, streaming=False)
                    self.audio_cache[path] = audio
                    self.logger.info(f"Аудио загружено: {path}")
                    return audio
                except Exception as e:
                    self.logger.exception(f"Ошибка при загрузке аудио: {path}")
                    return None
            else:
                self.logger.error(f"Аудио файл не найден: {full_path}")
                return None

    def load_font(self, path):
        """
        Загружает шрифт.

        :param path: Путь к файлу шрифта относительно директории ресурсов.
        """
        if path not in self.font_cache:
            full_path = os.path.join(self.resource_path, path)
            if os.path.exists(full_path):
                try:
                    pyglet.font.add_file(full_path)
                    font_name = pyglet.font.load(full_path).name
                    self.font_cache[path] = font_name
                    self.logger.info(f"Шрифт загружен: {path}")
                except Exception as e:
                    self.logger.exception(f"Ошибка при загрузке шрифта: {path}")
            else:
                self.logger.error(f"Файл шрифта не найден: {full_path}")

    def get_random_background(self):
        """
        Возвращает случайное фоновое изображение из загруженных.

        :return: Экземпляр pyglet.image.AbstractImage или None.
        """
        if self.backgrounds:
            bg_path = random.choice(self.backgrounds)
            return self.load_image(bg_path)
        else:
            self.logger.warning("Нет доступных фоновых изображений.")
            return None

    def clear_cache(self):
        """Очищает все кэши ресурсов."""
        self.image_cache.clear()
        self.audio_cache.clear()
        self.font_cache.clear()
        self.logger.info("Кэш ресурсов очищен.")

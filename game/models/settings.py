# game/models/settings.py

import json
import os
import logging

class Settings:
    """
    Класс для управления настройками игры.
    Поддерживает загрузку, сохранение, валидацию и уведомление об изменениях настроек.
    """

    SETTINGS_FILE = 'settings.json'
    DEFAULTS = {
        'language': 'en',
        'resolution': (1280, 720),
        'display_mode': 'windowed',
        'microphone': None,
        'volume': 50,
        'input_device': None,
        'output_device': None,
        'blur_background': True,
    }

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._settings = self.DEFAULTS.copy()
        self._on_change_callbacks = []

    @property
    def language(self):
        return self._settings['language']
    
    @property
    def blur_background(self):
        return self._settings.get('blur_background', False)

    @blur_background.setter
    def blur_background(self, value):
        self._settings['blur_background'] = value
        self._notify_change()

    @language.setter
    def language(self, value):
        if isinstance(value, str):
            self._settings['language'] = value
            self._notify_change()
        else:
            self.logger.error("Некорректное значение языка.")

    @property
    def resolution(self):
        return self._settings['resolution']

    @resolution.setter
    def resolution(self, value):
        if isinstance(value, (list, tuple)) and len(value) == 2:
            self._settings['resolution'] = tuple(map(int, value))
            self._notify_change()
        else:
            self.logger.error("Некорректное значение разрешения.")

    @property
    def display_mode(self):
        return self._settings['display_mode']

    @display_mode.setter
    def display_mode(self, value):
        if value in ['windowed', 'fullscreen', 'borderless']:
            self._settings['display_mode'] = value
            self._notify_change()
        else:
            self.logger.error("Некорректное значение режима отображения.")

    @property
    def microphone(self):
        return self._settings['microphone']

    @microphone.setter
    def microphone(self, value):
        self._settings['microphone'] = value
        self._notify_change()

    @property
    def volume(self):
        return self._settings['volume']

    @volume.setter
    def volume(self, value):
        if 0 <= value <= 100:
            self._settings['volume'] = value
            self._notify_change()
        else:
            self.logger.error("Громкость должна быть в диапазоне от 0 до 100.")

    @property
    def input_device(self):
        return self._settings.get('input_device')

    @input_device.setter
    def input_device(self, value):
        self._settings['input_device'] = value
        self._notify_change()

    @property
    def output_device(self):
        return self._settings.get('output_device')

    @output_device.setter
    def output_device(self, value):
        self._settings['output_device'] = value
        self._notify_change()

    def add_on_change_callback(self, callback):
        """
        Добавляет функцию обратного вызова, которая будет вызвана при изменении настроек.

        :param callback: Функция, принимающая один аргумент - экземпляр Settings.
        """
        if callable(callback):
            self._on_change_callbacks.append(callback)

    def _notify_change(self):
        """Уведомляет все зарегистрированные функции обратного вызова об изменении настроек."""
        for callback in self._on_change_callbacks:
            try:
                callback(self)
            except Exception as e:
                self.logger.exception("Ошибка в функции обратного вызова настроек.")

    def load(self):
        """Загружает настройки из файла JSON."""
        if os.path.exists(self.SETTINGS_FILE):
            try:
                with open(self.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._settings.update(data)
                self.logger.info("Настройки успешно загружены.")
            except (json.JSONDecodeError, IOError) as e:
                self.logger.exception("Ошибка при загрузке настроек, используются настройки по умолчанию.")
        else:
            self.logger.warning("Файл настроек не найден, используются настройки по умолчанию.")

    def save(self):
        """Сохраняет текущие настройки в файл JSON."""
        try:
            with open(self.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, ensure_ascii=False, indent=4)
            self.logger.info("Настройки сохранены.")
        except IOError as e:
            self.logger.exception("Ошибка при сохранении настроек.")

    def reset_to_defaults(self):
        """Сбрасывает настройки к значениям по умолчанию."""
        self._settings = self.DEFAULTS.copy()
        self._notify_change()
        self.logger.info("Настройки сброшены к значениям по умолчанию.")

    def get_all_settings(self):
        """Возвращает копию всех настроек."""
        return self._settings.copy()

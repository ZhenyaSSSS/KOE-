# game/utils/localization_manager.py

import os
import json
import logging

class LocalizationManager:
    """
    Класс для управления локализацией игры.
    Загружает файлы локализации и предоставляет доступ к локализованным строкам с поддержкой форматирования.
    """
    def __init__(self, language_code='en', default_language='en'):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_language = language_code
        self.default_language = default_language
        self.locales = {}
        self.load_locale(self.default_language)
        if self.current_language != self.default_language:
            self.load_locale(self.current_language)

    def load_locale(self, language_code):
        """Загружает файл локализации для указанного языка."""
        locale_path = os.path.join('assets', 'locales', f'{language_code}.json')
        try:
            with open(locale_path, 'r', encoding='utf-8') as f:
                self.locales[language_code] = json.load(f)
            self.logger.info(f"Локализация '{language_code}' успешно загружена.")
        except FileNotFoundError:
            self.logger.error(f"Файл локализации '{language_code}' не найден.")
            self.locales[language_code] = {}
        except Exception as e:
            self.logger.exception(f"Ошибка при загрузке локализации '{language_code}': {e}")
            self.locales[language_code] = {}

    def set_language(self, language_code):
        """Устанавливает текущий язык локализации."""
        if language_code not in self.locales:
            self.load_locale(language_code)
        self.current_language = language_code

    def get(self, key, **kwargs):
        """
        Возвращает локализованную строку по ключу с поддержкой форматирования.
        Если строка не найдена в текущем языке, используется язык по умолчанию.

        :param key: Ключ строки (например, 'menu.title').
        :param kwargs: Переменные для форматирования строки.
        :return: Локализованная и отформатированная строка.
        """
        # Попытка получить строку в текущем языке
        text = self._get_text_from_locale(self.current_language, key)
        if text is None:
            # Попытка получить строку в языке по умолчанию
            text = self._get_text_from_locale(self.default_language, key)
            if text is None:
                # Строка не найдена, возвращаем ключ
                self.logger.warning(f"Локализованная строка '{key}' не найдена.")
                return key
        # Форматируем строку с переданными аргументами
        try:
            return text.format(**kwargs)
        except KeyError as e:
            self.logger.error(f"Ошибка форматирования строки '{key}': отсутствует переменная '{e.args[0]}'")
            return text

    def _get_text_from_locale(self, language_code, key):
        """Получает строку по ключу из указанного языка."""
        locale = self.locales.get(language_code, {})
        keys = key.split('.')
        for k in keys:
            locale = locale.get(k)
            if locale is None:
                return None
        return locale

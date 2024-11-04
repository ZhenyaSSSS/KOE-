# game/models/subtitle.py

import re
import logging

class Subtitle:
    """
    Класс для представления одного субтитра.
    """

    def __init__(self, start_time, end_time, text, colors=None):
        self.start_time = start_time
        self.end_time = end_time
        self.text = text
        self.colors = colors or []

    def __repr__(self):
        return f"Subtitle({self.start_time}, {self.end_time}, {self.text}, {self.colors})"

class SubtitleParser:
    """
    Класс для парсинга субтитров из файла в формате SRT с поддержкой тегов <font color="#HEX">.
    """

    TIMESTAMP_PATTERN = re.compile(
        r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s+-->\s+"
        r"(\d{2}):(\d{2}):(\d{2}),(\d{3})"
    )
    FONT_TAG_PATTERN = re.compile(r'<font color="#([0-9A-Fa-f]{6})">(.*?)</font>', re.DOTALL)

    def __init__(self, subtitle_file):
        self.subtitle_file = subtitle_file
        self.logger = logging.getLogger(self.__class__.__name__)

    def parse_time(self, hours, minutes, seconds, milliseconds):
        """Преобразует время из строк в секунды."""
        return (
            int(hours) * 3600 +
            int(minutes) * 60 +
            int(seconds) +
            int(milliseconds) / 1000.0
        )

    def parse(self):
        """Парсит субтитры из файла и возвращает список объектов Subtitle."""
        subtitles = []
        try:
            with open(self.subtitle_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            self.logger.error(f"Файл субтитров не найден: {self.subtitle_file}")
            return subtitles
        except Exception as e:
            self.logger.exception(f"Ошибка при чтении файла субтитров: {e}")
            return subtitles

        entries = content.strip().split('\n\n')
        for entry in entries:
            lines = entry.strip().split('\n')
            if len(lines) >= 3:
                # Пропускаем номер субтитра
                timestamp_line = lines[1]
                match = self.TIMESTAMP_PATTERN.match(timestamp_line)
                if match:
                    start_time = self.parse_time(*match.groups()[0:4])
                    end_time = self.parse_time(*match.groups()[4:8])

                    # Обрабатываем текст субтитра
                    text_lines = lines[2:]
                    text = '\n'.join(text_lines)
                    colors = []

                    # Извлекаем информацию о цветах и очищенный текст
                    def replace_font_tags(match):
                        color = match.group(1)
                        content = match.group(2)
                        colors.append(color)
                        return content

                    clean_text = re.sub(self.FONT_TAG_PATTERN, replace_font_tags, text)
                    subtitles.append(Subtitle(start_time, end_time, clean_text, colors))
                else:
                    self.logger.warning(f"Неверный формат временной метки: {timestamp_line}")
            else:
                self.logger.warning(f"Неверный формат записи субтитра: {entry}")

        self.logger.info(f"Успешно распознано {len(subtitles)} субтитров.")
        return subtitles

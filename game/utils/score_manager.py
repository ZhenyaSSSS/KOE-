# game/utils/score_manager.py

import json
import os
import logging
from datetime import datetime

class ScoreManager:
    """
    Класс для управления сохранением и загрузкой результатов (очков) игроков.
    Поддерживает сохранение результатов по игрокам и песням, хранит детальную статистику.
    """

    SCORE_FILE = 'scores.json'

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.scores = {}
        self.load_scores()

    def load_scores(self):
        """Загружает результаты из файла JSON."""
        if os.path.exists(self.SCORE_FILE):
            try:
                with open(self.SCORE_FILE, 'r', encoding='utf-8') as f:
                    self.scores = json.load(f)
                self.logger.info("Результаты успешно загружены.")
            except (json.JSONDecodeError, IOError) as e:
                self.logger.exception("Ошибка при загрузке результатов, используется пустой словарь.")
                self.scores = {}
        else:
            self.logger.warning("Файл результатов не найден, используется пустой словарь.")
            self.scores = {}

    def save_scores(self):
        """Сохраняет текущие результаты в файл JSON."""
        try:
            with open(self.SCORE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.scores, f, ensure_ascii=False, indent=4)
            self.logger.info("Результаты сохранены.")
        except IOError as e:
            self.logger.exception("Ошибка при сохранении результатов.")

    def add_score(self, player_name, song_id, score, accuracy, max_combo):
        """
        Добавляет результат для определенного игрока и песни.

        :param player_name: Имя игрока.
        :param song_id: Идентификатор песни.
        :param score: Набранные очки.
        :param accuracy: Точность в процентах.
        :param max_combo: Максимальное комбо.
        """
        if player_name not in self.scores:
            self.scores[player_name] = {}
        if song_id not in self.scores[player_name]:
            self.scores[player_name][song_id] = []

        play_data = {
            'score': score,
            'accuracy': accuracy,
            'max_combo': max_combo,
            'date': datetime.now().isoformat()
        }

        self.scores[player_name][song_id].append(play_data)
        # Сортируем результаты по убыванию очков
        self.scores[player_name][song_id] = sorted(
            self.scores[player_name][song_id],
            key=lambda x: x['score'],
            reverse=True
        )[:10]  # Оставляем топ-10 результатов

        self.logger.info(f"Добавлен новый результат для игрока '{player_name}', песня '{song_id}': {play_data}")
        self.save_scores()

    def get_player_scores(self, player_name):
        """
        Возвращает результаты игрока по всем песням.

        :param player_name: Имя игрока.
        :return: Словарь с результатами по песням.
        """
        return self.scores.get(player_name, {})

    def get_song_scores(self, song_id):
        """
        Возвращает результаты по песне для всех игроков.

        :param song_id: Идентификатор песни.
        :return: Словарь с результатами по игрокам.
        """
        song_scores = {}
        for player_name, songs in self.scores.items():
            if song_id in songs:
                song_scores[player_name] = songs[song_id]
        return song_scores

    def get_player_song_scores(self, player_name, song_id):
        """
        Возвращает результаты игрока по определенной песне.

        :param player_name: Имя игрока.
        :return: Список с результатами.
        """
        return self.scores.get(player_name, {}).get(song_id, [])

    def get_top_scores(self, song_id, limit=10):
        """
        Возвращает топ результатов по песне среди всех игроков.

        :param song_id: Идентификатор песни.
        :param limit: Максимальное количество результатов.
        :return: Список с топ результатами.
        """
        all_scores = []
        for player_name, songs in self.scores.items():
            if song_id in songs:
                for play_data in songs[song_id]:
                    entry = play_data.copy()
                    entry['player_name'] = player_name
                    all_scores.append(entry)
        top_scores = sorted(all_scores, key=lambda x: x['score'], reverse=True)[:limit]
        return top_scores

    def get_recent_plays(self, player_name, limit=10):
        """
        Возвращает последние игры игрока.

        :param player_name: Имя игрока.
        :param limit: Максимальное количество результатов.
        :return: Список с последними играми.
        """
        recent_plays = []
        player_scores = self.get_player_scores(player_name)
        for song_id, plays in player_scores.items():
            for play_data in plays:
                entry = play_data.copy()
                entry['song_id'] = song_id
                recent_plays.append(entry)
        recent_plays = sorted(recent_plays, key=lambda x: x['date'], reverse=True)[:limit]
        return recent_plays

    def reset_scores(self):
        """Сбрасывает все результаты."""
        self.scores = {}
        self.save_scores()
        self.logger.info("Все результаты сброшены.")

    def delete_player_scores(self, player_name):
        """
        Удаляет результаты определенного игрока.

        :param player_name: Имя игрока.
        """
        if player_name in self.scores:
            del self.scores[player_name]
            self.save_scores()
            self.logger.info(f"Результаты игрока '{player_name}' удалены.")

    def delete_song_scores(self, song_id):
        """
        Удаляет результаты по определенной песне для всех игроков.

        :param song_id: Идентификатор песни.
        """
        for player_name in self.scores:
            if song_id in self.scores[player_name]:
                del self.scores[player_name][song_id]
        self.save_scores()
        self.logger.info(f"Результаты по песне '{song_id}' удалены.")

    def export_scores(self, file_path):
        """
        Экспортирует результаты в указанный файл.

        :param file_path: Путь к файлу экспорта.
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.scores, f, ensure_ascii=False, indent=4)
            self.logger.info(f"Результаты экспортированы в файл '{file_path}'.")
        except IOError as e:
            self.logger.exception("Ошибка при экспорте результатов.")

    def import_scores(self, file_path):
        """
        Импортирует результаты из указанного файла.

        :param file_path: Путь к файлу импорта.
        """
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_scores = json.load(f)
                # Объединяем результаты
                for player_name, songs in imported_scores.items():
                    if player_name not in self.scores:
                        self.scores[player_name] = songs
                    else:
                        for song_id, plays in songs.items():
                            if song_id not in self.scores[player_name]:
                                self.scores[player_name][song_id] = plays
                            else:
                                self.scores[player_name][song_id].extend(plays)
                                # Сортируем и оставляем топ-10
                                self.scores[player_name][song_id] = sorted(
                                    self.scores[player_name][song_id],
                                    key=lambda x: x['score'],
                                    reverse=True
                                )[:10]
                self.save_scores()
                self.logger.info(f"Результаты импортированы из файла '{file_path}'.")
            except (json.JSONDecodeError, IOError) as e:
                self.logger.exception("Ошибка при импорте результатов.")
        else:
            self.logger.error(f"Файл для импорта результатов не найден: {file_path}")

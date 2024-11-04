# game/states/result_state.py

import pyglet
from .base_state import BaseState
from ui.elements import Label, Button
from pyglet.graphics import Group


class ResultState(BaseState):
    """
    Состояние результатов после окончания песни.
    """

    def on_enter(self):
        super().on_enter()
        self.batch = pyglet.graphics.Batch()
        self.ui_elements = []

        width, height = self.window.get_size()

        # Создание фона
        self.create_background()

        # Создание UI элементов
        self.create_ui_elements()

        # Расположение элементов на экране
        self.layout()

    def create_background(self):
        """Создает и масштабирует фоновое изображение для экрана результатов."""
        self.background_image = self.game.resource_loader.get_random_background()
        if self.background_image:
            self.background_sprite = pyglet.sprite.Sprite(
                img=self.background_image,
                batch=self.batch,
                group=Group(order=-10)
            )
            self.update_background_position()
        else:
            self.background_sprite = None

    def update_background_position(self):
        """Обновляет позицию и масштаб фона."""
        if self.background_sprite:
            window_width, window_height = self.window.get_size()
            image_width = self.background_sprite.image.width
            image_height = self.background_sprite.image.height

            window_ratio = window_width / window_height
            image_ratio = image_width / image_height

            if window_ratio > image_ratio:
                scale = window_width / image_width
            else:
                scale = window_height / image_height

            self.background_sprite.scale = scale
            self.background_sprite.x = (window_width - image_width * scale) / 2
            self.background_sprite.y = (window_height - image_height * scale) / 2

    def create_ui_elements(self):
        """Создает все UI элементы для экрана результатов."""
        width, height = self.window.get_size()
        group = Group(order=10)

        # Заголовок
        title_text = self.game.localization.get('results.title') or "Результаты"
        self.title_label = Label(
            x=width / 2,
            y=height - 100,
            text=title_text,
            font_size=36,
            anchor_x='center',
            anchor_y='center',
            batch=self.batch,
            group=Group(order=group.order + 10),
            outline=True
        )
        self.ui_manager.add(self.title_label)
        self.ui_elements.append(self.title_label)

        # Отображение результатов
        # score = self.game.score_manager.get_last_score() or 1000000
        # accuracy = self.game.score_manager.get_last_accuracy() or 100
        # max_combo = self.game.score_manager.get_last_max_combo() or 100
        score = 1000000
        accuracy = 100
        max_combo = 100

        score_text = self.game.localization.get('results.score', score=score) or f"Счет: {score}"
        self.score_label = Label(
            x=width / 2,
            y=height - 200,
            text=score_text,
            font_size=24,
            anchor_x='center',
            anchor_y='center',
            batch=self.batch,
            group=Group(order=group.order + 8),
            outline=True
        )
        self.ui_manager.add(self.score_label)
        self.ui_elements.append(self.score_label)

        accuracy_text = self.game.localization.get('results.accuracy', accuracy=accuracy) or f"Точность: {accuracy}%"
        self.accuracy_label = Label(
            x=width / 2,
            y=height - 250,
            text=accuracy_text,
            font_size=24,
            anchor_x='center',
            anchor_y='center',
            batch=self.batch,
            group=Group(order=group.order + 8),
            outline=True
        )
        self.ui_manager.add(self.accuracy_label)
        self.ui_elements.append(self.accuracy_label)

        max_combo_text = self.game.localization.get('results.max_combo', max_combo=max_combo) or f"Макс.combo: {max_combo}"
        self.combo_label = Label(
            x=width / 2,
            y=height - 300,
            text=max_combo_text,
            font_size=24,
            anchor_x='center',
            anchor_y='center',
            batch=self.batch,
            group=Group(order=group.order + 8),
            outline=True
        )
        self.ui_manager.add(self.combo_label)
        self.ui_elements.append(self.combo_label)

        # Кнопка повторного воспроизведения
        replay_text = self.game.localization.get('results.replay') or "Повторить"
        self.replay_button = Button(
            x=width / 2,
            y=height - 400,
            width=200,
            height=50,
            text=replay_text,
            callback=self.on_replay,
            batch=self.batch,
            group=Group(order=group.order + 5)
        )
        self.ui_manager.add(self.replay_button)
        self.ui_elements.append(self.replay_button)

        # Кнопка возврата в меню
        menu_text = self.game.localization.get('results.back_to_menu') or "В меню"
        self.menu_button = Button(
            x=width / 2,
            y=height - 460,
            width=200,
            height=50,
            text=menu_text,
            callback=self.on_menu,
            batch=self.batch,
            group=Group(order=group.order + 5)
        )
        self.ui_manager.add(self.menu_button)
        self.ui_elements.append(self.menu_button)

    def layout(self):
        """Располагает UI элементы на экране."""
        width, height = self.window.get_size()

        # Обновление позиций элементов
        self.title_label.update_position(width / 2, height - 100)
        self.score_label.update_position(width / 2, height - 200)
        self.accuracy_label.update_position(width / 2, height - 250)
        self.combo_label.update_position(width / 2, height - 300)
        self.replay_button.update_position(width / 2, height - 400)
        self.menu_button.update_position(width / 2, height - 460)

        # Обновление позиции фона
        self.update_background_position()

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self.layout()

    def on_exit(self):
        """Обрабатывает выход из состояния результатов."""
        super().on_exit()
        self.ui_manager.clear()  # Предполагается, что есть метод для очистки UI
        self.ui_elements.clear()

    def on_replay(self):
        """Обработчик кнопки повторного воспроизведения."""
        self.game.state_manager.change_state('game')

    def on_menu(self):
        """Обработчик кнопки возврата в меню."""
        self.game.state_manager.change_state('song_select')

    def draw(self):
        """Отрисовка состояния результатов."""
        self.batch.draw()

# game/states/base_state.py

import pyglet
import logging
from abc import ABC, abstractmethod

class BaseState(ABC):
    """
    Абстрактный базовый класс для всех состояний игры.
    Предоставляет общий функционал и интерфейс для состояний.
    """

    def __init__(self, game):
        self.game = game
        self.window = game.window
        self.ui_manager = game.ui_manager
        self.batch = pyglet.graphics.Batch()
        self.ui_elements = []
        self.background_sprite = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.enable_background = True  # Флаг для включения/отключения фона
        self.needs_background_update = True  # Флаг для обновления фона при изменении размера
        self.background_offset_x = 0.0
        self.background_offset_y = 0.0
        self.target_offset_x = 0.0
        self.target_offset_y = 0.0

    @abstractmethod
    def on_enter(self):
        """Вызывается при переходе в данное состояние."""
        self.logger.info(f"Вход в состояние '{self.__class__.__name__}'.")
        if self.enable_background:
            self.load_background()
            self.needs_background_update = True

    @abstractmethod
    def on_exit(self):
        """Вызывается при выходе из данного состояния."""
        self.logger.info(f"Выход из состояния '{self.__class__.__name__}'.")
        self.cleanup_ui()

    def on_draw(self):
        """Отрисовка состояния."""
        self.window.clear()
        if self.enable_background and self.background_sprite:
            self.draw_background()
        self.batch.draw()
        self.ui_manager.draw()

    def draw_background(self):
        """Update the position and scale of the background image."""
        window_width, window_height = self.window.get_size()

        if self.needs_background_update:
            # Update scale and size only when the window size changes
            bg_width, bg_height = self.background_sprite.image.width, self.background_sprite.image.height

            scale_x = window_width / bg_width
            scale_y = window_height / bg_height
            self.scale = max(scale_x, scale_y) * 1.05

            self.scaled_bg_width = bg_width * self.scale
            self.scaled_bg_height = bg_height * self.scale

            self.needs_background_update = False

        # Adjust position based on background offset
        x = int((window_width - self.scaled_bg_width) / 2 + self.background_offset_x)
        y = int((window_height - self.scaled_bg_height) / 2 + self.background_offset_y)

        self.background_sprite.update(
            x=x,
            y=y,
            scale=self.scale
        )

    def load_background(self):
        """Загрузка фонового изображения."""
        try:
            bg_image = self.game.resource_loader.get_random_background()
            if bg_image:
                self.background_sprite = pyglet.sprite.Sprite(
                    bg_image,
                    batch=self.batch,
                    group=pyglet.graphics.Group(order=0)  # Фон должен быть на заднем плане
                )
                self.logger.info("Фоновое изображение загружено успешно.")
                self.needs_background_update = True  # Устанавливаем флаг
            else:
                self.logger.warning("Фоновое изображение не найдено.")
        except Exception as e:
            self.logger.exception("Ошибка при загрузке фонового изображения.")

    def handle_event(self, event_name, *args, **kwargs):
        """Универсальный обработчик событий для UI-элементов."""
        for element in self.ui_elements:
            handler = getattr(element, event_name, None)
            if callable(handler):
                if handler(*args, **kwargs):
                    return True
        return False

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            return self.handle_escape()
        return self.handle_event('on_key_press', symbol, modifiers)

    def handle_escape(self):
        # По умолчанию, возвращаемся в главное меню
        self.on_exit()
        self.game.state_manager.change_state('menu')
        return True

    def on_key_release(self, symbol, modifiers):
        return self.handle_event('on_key_release', symbol, modifiers)

    def on_mouse_press(self, x, y, button, modifiers):
        return self.handle_event('on_mouse_press', x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        return self.handle_event('on_mouse_release', x, y, button, modifiers)

    def on_mouse_motion(self, x, y, dx, dy):
        self.handle_event('on_mouse_motion', x, y, dx, dy)
        window_width, window_height = self.window.get_size()
        max_offset_x = 50  # Maximum horizontal offset in pixels
        max_offset_y = 30  # Maximum vertical offset in pixels

        # Normalize mouse position to range [-1, 1]
        norm_x = (x / window_width - 0.5) * 2
        norm_y = (y / window_height - 0.5) * 2

        # Non-linear mapping function for smoother movement
        def easing_function(t):
            return t ** 3  # Cubic easing

        self.target_offset_x = easing_function(norm_x) * max_offset_x
        self.target_offset_y = easing_function(norm_y) * max_offset_y

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        return self.handle_event('on_mouse_drag', x, y, dx, dy, buttons, modifiers)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        return self.handle_event('on_mouse_scroll', x, y, scroll_x, scroll_y)

    def on_text(self, text):
        self.handle_event('on_text', text)

    def on_text_motion(self, motion):
        self.handle_event('on_text_motion', motion)

    def on_resize(self, width, height):
        """Обработка изменения размера окна."""
        self.needs_background_update = True

    def on_settings_changed(self):
        """Обработка изменения настроек."""
        self.logger.info("Настройки изменены.")

    def update(self, dt):
        """Обновление состояния."""
        for element in self.ui_elements:
            element.update(dt)
        alpha = 0.1  # Smoothing factor (0 < alpha <= 1)
        self.background_offset_x += (self.target_offset_x - self.background_offset_x) * alpha
        self.background_offset_y += (self.target_offset_y - self.background_offset_y) * alpha

    def cleanup_ui(self):
        """Очистка UI-элементов."""
        self.logger.info("Очистка UI-элементов.")
        for element in self.ui_elements:
            self.ui_manager.remove(element)
        self.ui_elements.clear()

    def cleanup(self):
        """Очистка ресурсов состояния."""
        self.logger.info(f"Очистка ресурсов состояния '{self.__class__.__name__}'.")
        self.cleanup_ui()
        if self.background_sprite:
            self.background_sprite.delete()
            self.background_sprite = None

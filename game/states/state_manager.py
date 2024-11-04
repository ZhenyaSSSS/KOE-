# game/states/state_manager.py

import logging

from states.menu_state import MenuState
from states.settings_state import SettingsState
from states.song_select_state import SongSelectState
from states.game_state import GameState
from states.result_state import ResultState

class StateManager:
    """
    Менеджер для управления состояниями игры.
    Отвечает за переключение между состояниями и делегирование событий.
    """

    def __init__(self, game):
        self.game = game
        self.logger = logging.getLogger(self.__class__.__name__)
        self.states = {}
        self.current_state = None
        self._init_states()

    def _init_states(self):
        """Инициализация всех состояний игры."""
        self.logger.info("Инициализация состояний игры.")
        try:
            self.states['menu'] = MenuState(self.game)
            self.states['settings'] = SettingsState(self.game)
            self.states['song_select'] = SongSelectState(self.game)
            self.states['game'] = GameState(self.game)
            self.states['result'] = ResultState(self.game)

            # Установка начального состояния
            self.change_state('menu')
        except Exception as e:
            self.logger.exception("Ошибка при инициализации состояний.")
            raise e

    def change_state(self, state_name):
        """Переключение на другое состояние игры."""
        self.logger.info(f"Переключение на состояние '{state_name}'.")
        if self.current_state:
            try:
                self.current_state.on_exit()
            except Exception as e:
                self.logger.exception(f"Ошибка при выходе из состояния '{self.current_state.__class__.__name__}'.")

        new_state = self.states.get(state_name)
        if new_state:
            self.current_state = new_state
            try:
                self.current_state.on_enter()
                self.logger.info(f"Текущее состояние: '{state_name}'.")
            except Exception as e:
                self.logger.exception(f"Ошибка при входе в состояние '{state_name}'.")
        else:
            self.logger.error(f"Состояние '{state_name}' не найдено.")
            self.current_state = None

    def on_draw(self):
        if self.current_state:
            self.current_state.on_draw()

    def on_event(self, event_name, *args, **kwargs):
        """Обработка событий, делегируя их текущему состоянию."""
        if self.current_state:
            handler = getattr(self.current_state, event_name, None)
            if callable(handler):
                return handler(*args, **kwargs)
        return False

    def on_key_press(self, symbol, modifiers):
        if self.current_state:
            return self.current_state.on_key_press(symbol, modifiers)
        return False

    def on_key_release(self, symbol, modifiers):
        return self.on_event('on_key_release', symbol, modifiers)

    def on_mouse_press(self, x, y, button, modifiers):
        return self.on_event('on_mouse_press', x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        return self.on_event('on_mouse_release', x, y, button, modifiers)

    def on_mouse_motion(self, x, y, dx, dy):
        self.on_event('on_mouse_motion', x, y, dx, dy)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        return self.on_event('on_mouse_drag', x, y, dx, dy, buttons, modifiers)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        return self.on_event('on_mouse_scroll', x, y, scroll_x, scroll_y)

    def on_text(self, text):
        self.on_event('on_text', text)

    def on_text_motion(self, motion):
        self.on_event('on_text_motion', motion)

    def on_resize(self, width, height):
        if self.current_state:
            self.current_state.on_resize(width, height)

    def on_settings_changed(self):
        """Уведомляет все состояния об изменении настроек."""
        self.logger.info("Настройки изменены, обновление состояний.")
        for state in self.states.values():
            try:
                state.on_settings_changed()
            except Exception as e:
                self.logger.exception(f"Ошибка при обновлении состояния '{state.__class__.__name__}' после изменения настроек.")

    def update(self, dt):
        if self.current_state:
            try:
                self.current_state.update(dt)
            except Exception as e:
                self.logger.exception(f"Ошибка при обновлении состояния '{self.current_state.__class__.__name__}'.")

    def cleanup(self):
        """Очистка ресурсов всех состояний."""
        self.logger.info("Очистка ресурсов всех состояний.")
        for state in self.states.values():
            try:
                state.cleanup()
            except Exception as e:
                self.logger.exception(f"Ошибка при очистке состояния '{state.__class__.__name__}'.")

# game/states/menu_state.py

from .base_state import BaseState
from ui.elements import Label, Button

class MenuState(BaseState):
    """
    Главное меню игры.
    """

    def on_enter(self):
        super().on_enter()
        width, height = self.window.get_size()

        # Получаем batch и group из UIManager
        batch = self.ui_manager.batch
        group = self.ui_manager.default_group

        # Заголовок
        title_text = self.game.localization.get('menu.title')
        self.title_label = Label(width / 2, height - 100, title_text, font_size=160, outline=True, batch=batch, group=group, color=(255, 20, 147, 255))
        self.ui_manager.add(self.title_label)

        # Кнопки
        button_y = height / 2
        play_text = self.game.localization.get('menu.play')
        self.play_button = Button(width / 2, button_y, 200, 50, play_text, self.on_play, batch=batch, group=group)
        self.ui_manager.add(self.play_button)

        settings_text = self.game.localization.get('menu.settings')
        self.settings_button = Button(width / 2, button_y - 60, 200, 50, settings_text, self.on_settings, batch=batch, group=group)
        self.ui_manager.add(self.settings_button)

        exit_text = self.game.localization.get('menu.exit')
        self.exit_button = Button(width / 2, button_y - 120, 200, 50, exit_text, self.on_exit_game, batch=batch, group=group)
        self.ui_manager.add(self.exit_button)

        # Добавляем элементы в ui_elements для обработки событий
        self.ui_elements.extend([self.title_label, self.play_button, self.settings_button, self.exit_button])

    def on_exit(self):
        super().on_exit()

    def on_play(self):
        self.game.state_manager.change_state('song_select')

    def on_settings(self):
        self.game.state_manager.change_state('settings')

    def on_exit_game(self):
        self.game.window.close()

    def handle_escape(self):
        # В главном меню ESC закрывает игру
        self.game.window.close()
        return True

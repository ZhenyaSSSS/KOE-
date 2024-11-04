# game/main.py

import pyglet
pyglet.options['search_local_libs'] = True

from pyglet.math import Mat4
import logging
import sys
import ctypes
from models.settings import Settings
from utils.resource_loader import ResourceLoader
from utils.localization_manager import LocalizationManager
from ui.manager import UIManager
from ui.notification_manager import NotificationManager
from states.state_manager import StateManager
from utils.score_manager import ScoreManager
from utils.notification_handler import NotificationHandler
from utils.song_manager import SongManager
from pyglet.gl import glClear, GL_STENCIL_BUFFER_BIT
ctypes.windll.user32.SetProcessDPIAware()
pyglet.options['audio'] = ('silent',) 

print(pyglet.media.have_ffmpeg())
class KOE:
    """
    Основной класс приложения для KOE.
    Инициализирует и управляет основными компонентами игры.
    """

    def __init__(self):
        # Настройка логирования
        self._setup_logging()

        self.logger.info("Инициализация игры...")

        # Загрузка настроек
        self.settings = Settings()
        self.settings.load()

        # Инициализация менеджера локализации
        self.localization = LocalizationManager(language_code=self.settings.language)

        # Инициализация окна приложения
        self.window = self._create_window()

        # Загрузка ресурсов
        self.resource_loader = ResourceLoader()

        # Инициализация менеджеров
        self.ui_manager = UIManager()
        self.notification_manager = NotificationManager(self.window)
        self.state_manager = StateManager(self)
        self.score_manager = ScoreManager()
        self.song_manager = SongManager(songs_directory='assets/songs')  # Добавлен менеджер песен

        # Настройка обработчика уведомлений для логирования
        notification_handler = NotificationHandler(self.notification_manager)
        notification_handler.setLevel(logging.WARNING)
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        notification_handler.setFormatter(formatter)
        logging.getLogger().addHandler(notification_handler)

        # Регистрация обработчиков событий
        self._register_events()

        self.logger.info("Инициализация завершена.")

    def _setup_logging(self):
        """Настройка параметров логирования."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s:%(name)s: %(message)s',
            handlers=[
                logging.FileHandler("game.log", mode='w', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def _create_window(self):
        """Создает окно приложения с учетом настроек."""
        try:
            display = pyglet.canvas.get_display()
            screen = display.get_default_screen()
            max_width, max_height = screen.width, screen.height

            requested_width, requested_height = self.settings.resolution

            if requested_width > max_width or requested_height > max_height:
                self.logger.warning(
                    f"Requested resolution {requested_width}x{requested_height} exceeds "
                    f"display capabilities {max_width}x{max_height}. Adjusting to maximum."
                )
                requested_width = min(requested_width, max_width)
                requested_height = min(requested_height, max_height)
                self.settings.resolution = (requested_width, requested_height)

            display_mode = self.settings.display_mode
            style = pyglet.window.Window.WINDOW_STYLE_DEFAULT

            if display_mode == 'borderless':
                style = pyglet.window.Window.WINDOW_STYLE_BORDERLESS

            config = pyglet.gl.Config(
                major_version=3,
                minor_version=3,
                forward_compatible=True,
                core_profile=True,
                double_buffer=True,
                sample_buffers=1,
                samples=8,
                stencil_size=8,
                depth_size=24,
                srgb=True,
                red_size=8,
                green_size=8,
                blue_size=8,
                alpha_size=8,
                accum_red_size=16,
                accum_green_size=16,
                accum_blue_size=16,
                accum_alpha_size=16,
            )
            window = pyglet.window.Window(
                width=requested_width,
                height=requested_height,
                fullscreen=display_mode == 'fullscreen',
                caption="KOE!",
                resizable=True,
                style=style,
                config=config
            )
            # Установка проекции
            window.projection = Mat4.orthogonal_projection(0, requested_width, 0, requested_height, -255, 255)
            # window.view = Mat4.identity()  # Установка матрицы вида

            window.set_vsync(True)
            return window
        except Exception as e:
            self.logger.exception("Ошибка при создании окна приложения.")
            sys.exit(1)

    def _register_events(self):
        """Регистрация обработчиков событий окна."""

        @self.window.event
        def on_draw():
            self.on_draw()

        @self.window.event
        def on_key_press(symbol, modifiers):
            self.state_manager.on_key_press(symbol, modifiers)

        @self.window.event
        def on_key_release(symbol, modifiers):
            self.state_manager.on_key_release(symbol, modifiers)

        @self.window.event
        def on_mouse_press(x, y, button, modifiers):
            self.state_manager.on_mouse_press(x, y, button, modifiers)

        @self.window.event
        def on_mouse_release(x, y, button, modifiers):
            self.state_manager.on_mouse_release(x, y, button, modifiers)

        @self.window.event
        def on_mouse_motion(x, y, dx, dy):
            self.state_manager.on_mouse_motion(x, y, dx, dy)

        @self.window.event
        def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
            self.state_manager.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

        @self.window.event
        def on_mouse_scroll(x, y, scroll_x, scroll_y):
            self.state_manager.on_mouse_scroll(x, y, scroll_x, scroll_y)

        @self.window.event
        def on_text(text):
            self.state_manager.on_text(text)

        @self.window.event
        def on_text_motion(motion):
            self.state_manager.on_text_motion(motion)

        @self.window.event
        def on_resize(width, height):
            self.state_manager.on_resize(width, height)

        @self.window.event
        def on_close():
            # self.on_exit()
            self.logger.info("Выход из приложения")
            self.cleanup()
            pyglet.app.exit()

    def apply_settings(self):
        """
        Применение новых настроек к окну и другим компонентам.
        Вызывается при изменении настроек пользователем.
        """
        self.logger.info("Применение новых настроек...")
        try:
            display_mode = self.settings.display_mode
            new_width, new_height = self.settings.resolution
            current_fullscreen = self.window.fullscreen
            current_width, current_height = self.window.get_size()

            if display_mode == 'fullscreen':
                # Получаем доступные режимы отображения для текущего экрана
                screen = self.window.display.get_default_screen()
                available_modes = screen.get_modes()
                available_resolutions = [(mode.width, mode.height) for mode in available_modes]

                if (new_width, new_height) not in available_resolutions:
                    self.logger.error(f"Разрешение {new_width}x{new_height} не поддерживается текущим экраном.")
                    raise ValueError("Неподдерживаемое разрешение.")

                if not current_fullscreen:
                    # Найдём режим отображения с нужным разрешением
                    target_mode = None
                    for mode in available_modes:
                        if mode.width == new_width and mode.height == new_height:
                            target_mode = mode
                            break
                    if target_mode:
                        self.window.set_size(target_mode.width, target_mode.height)
                        self.logger.info(f"Установлено разрешение {new_width}x{new_height} в полноэкранном режиме.")
                    else:
                        self.logger.warning(f"Разрешение {new_width}x{new_height} не найдено среди доступных режимов.")
                    # Переключаемся в полноэкранный режим
                    self.window.set_fullscreen(True)
                    self.logger.info("Переключено в полноэкранный режим.")

                else:
                    # Если уже в полноэкранном режиме, проверить и изменить разрешение при необходимости
                    if (new_width, new_height) != (current_width, current_height):
                        # Поскольку изменение разрешения в текущем полноэкранном режиме невозможно напрямую, придётся выйти и войти обратно
                        self.window.set_fullscreen(False)
                        self.logger.info("Выход из полноэкранного режима для изменения разрешения.")

                        # Найдём режим отображения с нужным разрешением
                        target_mode = None
                        for mode in available_modes:
                            if mode.width == new_width and mode.height == new_height:
                                target_mode = mode
                                break

                        if target_mode:
                            # Переключаемся обратно в полноэкранный режим с новым разрешением
                            self.window.set_size(target_mode.width, target_mode.height)
                            self.window.set_fullscreen(True)
                            self.logger.info("Переключено обратно в полноэкранный режим.")
                        else:
                            self.logger.warning(f"Разрешение {new_width}x{new_height} не найдено среди доступных режимов.")
            else:
                if current_fullscreen:
                    # Выключаем полноэкранный режим
                    self.window.set_fullscreen(False)
                    self.logger.info("Выключен полноэкранный режим.")

                # Устанавливаем новый размер окна, если он отличается
                if (new_width, new_height) != (current_width, current_height):
                    self.window.set_size(new_width, new_height)
                    self.logger.info(f"Изменено разрешение окна на {new_width}x{new_height}")

            # Обновляем проекцию и расположение UI элементов независимо от режима
            updated_width, updated_height = self.window.get_size()
            self.update_projection(updated_width, updated_height)

            # Уведомление текущего состояния об обновлении настроек
            self.state_manager.on_settings_changed()

            self.logger.info("Новые настройки успешно применены.")
        except Exception as e:
            self.logger.exception("Ошибка при приме��ении новых настроек.")

    def update_projection(self, width, height):
        """Обновляет проекцию окна после изменения размера."""
        self.logger.info("Обновление проекции окна.")
        try:
            self.window.projection = Mat4.orthogonal_projection(0, width, 0, height, -255, 255)
            # Если используется матрица вида, измените её при необходимости
            # self.window.view = Mat4.identity()
            self.logger.info("Проекция успешно обновлена.")
        except Exception as e:
            self.logger.exception("Ошибка при о��новлении проекции.")

    def show_map_settings_popup(self):
        """
        Opens the map settings popup where users can adjust individual track volumes.
        """
        # Implementation to open the map settings popup
        self.logger.info("Opening map settings popup.")
        self.state_manager.current_state.show_map_settings_popup()

    def show_display_settings_popup(self):
        """
        Opens the display settings popup (from TopBar settings button).
        """
        # Implementation to open the display settings popup
        self.logger.info("Opening display settings popup.")
        self.state_manager.current_state.show_display_settings_popup()

    def show_mods_popup(self):
        """
        Opens the mods selection popup.
        """
        # Implementation to open the mods popup
        self.logger.info("Opening mods popup.")
        self.state_manager.current_state.show_mods_popup()

    def start_game(self):
        """
        Starts the game with the selected song and settings.
        """
        self.state_manager.current_state.start_game()
    
    def start_game_with_song(self, song, track_volumes, mods):
        """
        Starts the game with the selected song and settings.
        """
        self.logger.info("Starting the game.")
        self.selected_song = song
        self.track_volumes = track_volumes
        self.mods = mods
        # Преобразуем громкости в диапазон 0.0 - 1.0
        self.normalized_track_volumes = {track: volume / 100 for track, volume in track_volumes.items()}
        self.state_manager.change_state('game')

    def run(self):
        """Запуск игрового цикла."""
        self.logger.info("Запуск игрового цикла.")
        pyglet.clock.schedule_interval(self.update, 1 / 60.0)
        try:
            pyglet.app.run()
        except Exception as e:
            self.logger.exception("Критическая ошибка в игровом цикле.")
            self.cleanup()
            sys.exit(1)

    def update(self, dt):
        """Обновление текущего состояния игры."""
        self.state_manager.update(dt)
        self.notification_manager.update(dt)

    def on_draw(self):
        """Отрисовка текущего состояния игры и уведомлений."""
        self.window.clear()
        glClear(GL_STENCIL_BUFFER_BIT)
        self.state_manager.on_draw()
        self.notification_manager.draw()

    def cleanup(self):
        """Очистка ресурсов перед выходом."""
        self.logger.info("Очистка ресурсов перед выходом.")
        try:
            self.state_manager.cleanup()
            self.window.close()
        except Exception as e:
            self.logger.exception("Ошибка при очистке ресурсов.")


if __name__ == "__main__":
    game = KOE()
    game.run()

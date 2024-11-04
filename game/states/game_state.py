# game/states/game_state.py

from .base_state import BaseState
from controllers.audio_controller import AudioController
from controllers.subtitle_controller import SubtitleController
from ui.elements import Label
import pyglet.media
from pyglet.graphics import Group
import os
import time

class GameState(BaseState):
    """
    Игровое состояние, где происходит воспроизведение песни и запись голоса пользователя.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_frame_time = 0
        self.background_player = None
        self.audio_controller = None
        self.enable_background = False  # Отключаем базовый фон из BaseState

    def on_enter(self):
        super().on_enter()
        self.logger.info(f"Вход в состояние '{self.__class__.__name__}'.")
        self.song = self.game.selected_song
        self.volumes = self.game.normalized_track_volumes
        self.setup_audio()
        self.setup_subtitles()
        self.score = 0
        self.accuracy = 0.0
        self.max_combo = 0
        self.current_combo = 0

        # Инициализация элементов интерфейса
        self.setup_ui()

        # Настройка фона (видео или обложка)
        self.setup_background()

        # Инициализация аудио и видео
        if not self.audio_controller.is_playing():
            self.audio_controller.play()
        if self.background_player:
            self.background_player.seek(0.0)
            self.background_player.play()

    def on_exit(self):
        """Обрабатывает выход из игрового состояния."""
        super().on_exit()
        self.audio_controller.stop()
        self.subtitle_controller.stop()
        if self.background_player:
            self.background_player.pause()
            self.background_player.delete()  # Освобождаем ресурсы
            self.background_player = None

    def setup_audio(self):
        """Настраивает аудио контроллер для воспроизведения песни."""
        if self.audio_controller:
            self.audio_controller.stop()  # Останавливаем предыдущий контроллер, если он существует
        
        self.audio_controller = AudioController(
                    audio_files=self.song.audio_files,
                    output_device=self.game.settings.output_device
                )
        self.audio_controller.set_volumes(self.volumes)

    def setup_subtitles(self):
        """Настраивает контроллер субтитров."""
        self.subtitle_controller = SubtitleController(self.song.subtitle_file)
        self.subtitle_controller.start()

    def setup_ui(self):
        """Создает элементы интерфейса для игрового состояния."""
        width, height = self.window.get_size()
        self.subtitle_labels = []

        # Создаем несколько меток для отображения разных строк с разными цветами
        for i in range(2):  # Предполагаем, что максимум 2 строки в субтитре
            label = Label(
                width / 2, height / 4 - i * 30, "",
                font_size=24, outline=True, batch=self.batch
            )
            self.subtitle_labels.append(label)
            self.ui_elements.append(label)

    def update(self, dt):
        super().update(dt)
        # Обновление субтитров
        current_subtitle = self.subtitle_controller.get_current_subtitle()
        if current_subtitle:
            lines = current_subtitle.text.split('\n')
            colors = current_subtitle.colors
            for i, label in enumerate(self.subtitle_labels):
                if i < len(lines):
                    label.set_text(lines[i])
                    if i < len(colors):
                        # Устанавливаем цвет текста
                        hex_color = colors[i]
                        rgb_color = tuple(int(hex_color[j:j+2], 16) for j in (0, 2, 4)) + (255,)
                        label.label.color = rgb_color
                    else:
                        label.label.color = (255, 255, 255, 255)
                else:
                    label.set_text("")
        else:
            for label in self.subtitle_labels:
                label.set_text("")

        # Обновление очков и состояния игры
        if not self.audio_controller.is_playing():
            self.on_song_end()
    
    def on_resize(self, width, height):
        super().on_resize(width, height)
        # Обновить позицию субтитров
        for i, label in enumerate(self.subtitle_labels):
            label.update_position(width / 2, height / 4 - i * 30)
        # Обновить позицию фона
        self.update_background_position()

    def on_song_end(self):
        """Обработка окончания песни и переход к экрану результатов."""
        self.audio_controller.stop()
        if self.background_player:
            self.background_player.set_pause(True)
        self.game.state_manager.change_state('result')

    def setup_background(self):
        """Настраивает фон, либо видео, либо обложку используя pyglet.media."""
        if self.background_player:
            self.background_player.pause()
            self.background_player.delete()
            self.background_player = None

        video_file = self.song.video_file
        if os.path.exists(video_file) and os.path.isfile(video_file):
            try:
                media_source = pyglet.media.load(video_file)
                self.background_player = pyglet.media.Player()
                self.background_player.queue(media_source)
                self.background_player.volume = 0  # Отключаем звук видео
                self.logger.info(f"Video player initialized for {video_file}")
            except Exception as e:
                self.logger.exception(f"Ошибка при загрузке видео файла {video_file}")
                self.load_cover_image()
        else:
            self.logger.warning(f"Видео файл {video_file} не найден. Загружаем обложку.")
            self.load_cover_image()

    def load_cover_image(self):
        """Загружает обложку как фон без размытия."""
        if os.path.exists(self.song.cover_image):
            try:
                bg_image = pyglet.image.load(self.song.cover_image)
                self.background_sprite = pyglet.sprite.Sprite(
                    img=bg_image,
                    batch=self.batch,
                    group=Group(order=-10)
                )
                self.update_background_position()
            except Exception as e:
                self.logger.exception("Ошибка при загрузке фонового изображения.")
                self.load_default_background()
        else:
            self.logger.warning(f"Фоновое изображение {self.song.cover_image} не найдено.")
            self.load_default_background()

    def load_default_background(self):
        """Загружает стандартный фоновый рисунок."""
        self.background_image = self.game.resource_loader.get_random_background()
        if self.background_image:
            self.background_sprite = pyglet.sprite.Sprite(
                img=self.background_image,
                batch=self.batch,
                group=Group(order=-10)
            )
            self.update_background_position()
        else:
            self.logger.warning("Нет доступного стандартного фонового изображения.")

    def on_draw(self):
        """Отрисовка игрового состояния."""
        self.window.clear()
        if self.background_player and self.background_player.playing:
            texture = self.background_player.texture  # Используем texture напрямую
            if texture:
                texture.blit(0, 0, width=self.window.width, height=self.window.height)
        self.batch.draw()

    def update_background_position(self):
        """Обновляет позицию фонового спрайта."""
        if hasattr(self, 'background_sprite'):
            window_width = self.window.width
            window_height = self.window.height
            
            # Вычисляем масштаб для заполнения окна
            scale_x = window_width / self.background_sprite.image.width
            scale_y = window_height / self.background_sprite.image.height
            scale = max(scale_x, scale_y)
            
            # Устанавливаем масштаб
            self.background_sprite.scale = scale
            
            # Центрируем спрайт
            self.background_sprite.x = (window_width - self.background_sprite.width) / 2
            self.background_sprite.y = (window_height - self.background_sprite.height) / 2
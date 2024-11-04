# game/states/song_select_state.py

import pyglet
from .base_state import BaseState
from ui.elements import (
    TopBar, BottomBar, SongCarousel, SongInfoArea,
    TextInput, Label, Button, Slider, Checkbox, TriangleBackground
)
from pyglet import shapes
import datetime
import os
from pyglet.graphics import Group
from PIL import Image, ImageFilter
from controllers.audio_controller import AudioController


class SongSelectState(BaseState):
    """
    Состояние для выбора песни для игры.
    """

    def __init__(self, game):
        super().__init__(game)  # Вызываем конструктор родительского класса
        self.available_songs = []
        self.current_song = None
        self.audio_controller = None
        
        # Предзагружаем превью для всех песен
        self._preload_previews()
        
    def _preload_previews(self):
        """Предзагружает превью для всех песен."""
        try:
            for song in self.available_songs:
                if song.audio_files:
                    AudioController(song.audio_files, preview_mode=True)
        except Exception as e:
            self.logger.warning(f"Ошибка при предзагрузке превью: {e}")

    def on_enter(self):
        super().on_enter()
        self.batch = pyglet.graphics.Batch()
        self.ui_elements = []

        # Создание фона
        self.create_background()

        # Инициализация переменных
        self.current_song = None
        self.preview_player = None
        self.track_volumes = {}
        self.mods = []
        self.popup_open = False  # Для предотвращения открытия нескольких всплывающих окон

        # Создание UI элементов
        self.create_ui_elements()

        # Расположение элементов на экране
        self.layout()

        # Запуск обновления времени
        pyglet.clock.schedule_interval(self.update_time_label, 1)

    def create_background(self):
        """Создает и масштабирует фоновое изображение."""
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
        """Updates the position and scale of the background image."""
        if not self.background_sprite:
            return
            
        try:
            window_width, window_height = self.window.get_size()
            
            # Изображение уже нужного размера, просто центрируем его
            self.background_sprite.scale = 1.0
            self.background_sprite.x = (window_width - self.background_sprite.image.width) / 2
            self.background_sprite.y = (window_height - self.background_sprite.image.height) / 2
            
        except Exception as e:
            self.logger.exception("Ошибка при обновлении позиции фона")

    def create_ui_elements(self):
        """Creates all UI elements for song selection."""
        window_width, window_height = self.window.get_size()
        group = Group(order=10)

        # # Создание треугольного фона
        # self.triangle_background = TriangleBackground(
        #     x=0,
        #     y=0,
        #     width=window_width,
        #     height=window_height,
        #     batch=self.batch,
        #     group=Group(order=group.order - 2)
        # )
        # self.ui_elements.append(self.triangle_background)

        # Top Bar
        self.top_bar = TopBar(
            x=0,
            y=window_height - 50,  # Position at the top
            width=window_width,
            height=50,  # Fixed height for top bar
            batch=self.batch,
            group=Group(order=group.order + 10),
            game=self.game
        )
        self.ui_manager.add(self.top_bar)
        self.ui_elements.append(self.top_bar)

        # Bottom Bar
        self.bottom_bar = BottomBar(
            # x=0,
            # y=0,  # Position at the bottom
            width=window_width,
            batch=self.batch,
            group=Group(order=group.order + 10),
            game=self.game
        )
        self.ui_manager.add(self.bottom_bar)
        self.ui_elements.append(self.bottom_bar)

        # Sort Label
        sort_label_x = window_width * 0.85  # 85% of window width
        sort_label_y = window_height - 80  # Adjusted position below top bar
        self.sort_label = Label(
            x=sort_label_x,
            y=sort_label_y,
            text=self.game.localization.get('song_select.sort_by') or 'Sort By',
            font_size=14,
            anchor_x='center',
            anchor_y='center',
            batch=self.batch,
            group=Group(order=group.order + 4)
        )
        self.ui_manager.add(self.sort_label)
        self.ui_elements.append(self.sort_label)

        # Sort Buttons
        self.sort_options = ['Name', 'Artist', 'Duration']
        self.sort_buttons = []
        button_width = 80
        button_height = 30
        button_spacing = 10
        total_buttons_width = len(self.sort_options) * (button_width + button_spacing) - button_spacing
        start_x = sort_label_x - total_buttons_width / 2

        for idx, option in enumerate(self.sort_options):
            button_x = start_x + idx * (button_width + button_spacing)
            button_y = sort_label_y - 40
            button = Button(
                x=button_x,
                y=button_y,
                width=button_width,
                height=button_height,
                text=option,
                callback=lambda opt=option: self.sort_songs(opt),
                batch=self.batch,
                group=Group(order=group.order + 4)
            )
            self.ui_manager.add(button)
            self.ui_elements.append(button)
            self.sort_buttons.append(button)

        # Song Carousel
        self.song_carousel = SongCarousel(
            songs=self.game.song_manager.get_all_songs(),
            x=window_width * 0.5,  # центрируем карусель
            y=0,  # центрируем карусель
            width=window_width * 0.5,  # ширина области карусели
            height=window_height,  # высота области карусели
            batch=self.batch,
            group=Group(order=group.order),
            on_song_select=self.on_song_select,
            game=self.game
        )
        self.ui_manager.add(self.song_carousel)
        self.ui_elements.append(self.song_carousel)

        # Song Info Area
        song_info_width = window_width * 0.45
        song_info_height = window_height * 0.35 
        song_info_x = 10
        song_info_y = window_height - song_info_height - 60
        self.song_info_area = SongInfoArea(
            x=song_info_x,
            y=song_info_y,
            width=song_info_width,
            height=song_info_height,
            batch=self.batch,
            group=Group(order=group.order + 6),
            window=self.window
        )
        self.ui_manager.add(self.song_info_area)
        self.ui_elements.append(self.song_info_area)

        # Top Overlay
        self.top_overlay = shapes.Rectangle(
            x=0,
            y=window_height - window_height * 0.2,  # Adjusted to the height of the top bar
            width=window_width,
            height=window_height * 0.2,
            color=(0, 0, 0),
            batch=self.batch,
            group=Group(order=group.order + 3)
        )
        self.top_overlay.opacity = 150

    def layout(self):
        """Positions UI elements on the screen."""
        window_width, window_height = self.window.get_size()

        # # Обновляем размер треугольного фона
        # self.triangle_background.update_size(window_width, window_height)

        # Update positions of top bar and bottom bar
        self.top_bar.update_position(0, window_height - self.top_bar.height)
        # self.bottom_bar.update_position(0, 0)

        # Update positions of sort label and buttons
        sort_label_x = window_width * 0.85
        sort_label_y = window_height - 80
        self.sort_label.update_position(sort_label_x, sort_label_y)

        total_buttons_width = len(self.sort_buttons) * (self.sort_buttons[0].width + 10) - 10
        start_x = sort_label_x - total_buttons_width / 2

        for idx, button in enumerate(self.sort_buttons):
            button_x = start_x + idx * (button.width + 10)
            button_y = sort_label_y - 40
            button.update_position(button_x, button_y)

            # Update the size and position of the song carousel
        self.song_carousel.update_size(
            width=window_width * 0.5,  # Right half of the screen
            height=window_height
        )
        self.song_carousel.x = window_width * 0.5
        self.song_carousel.y = 0

        # Update song info area position and size
        song_info_width = window_width * 0.45
        song_info_height = window_height * 0.35
        song_info_x = 10
        song_info_y = window_height - song_info_height - 60
        self.song_info_area.update_position(
            x=song_info_x,
            y=song_info_y
        )
        # self.song_info_area.update_size(
        #     width=song_info_width,
        #     height=song_info_height
        # )

        # Update top overlay
        self.top_overlay.position = (0, window_height - (window_height * 0.2))
        self.top_overlay.width = window_width
        self.top_overlay.height = window_height * 0.2

        # Update background position
        self.update_background_position()


    def update_time_label(self, dt):
        """Обновляет отображение текущего времени на верхней панели."""
        current_time = datetime.datetime.now().strftime("%H:%M")
        self.top_bar.update_time(current_time)

    def on_search_text_change(self, text):
        """Фильтрует список песен на основе текста поиска."""
        filtered_songs = [song for song in self.game.song_manager.get_all_songs() 
                         if text.lower() in song.name.lower() or 
                         text.lower() in song.artist.lower()]
        self.song_carousel.all_songs = filtered_songs
        self.song_carousel.create_song_items()

    def on_song_select(self, song):
        """Обрабатывает выбор песни из списка."""
        # Останавливаем текущее воспроизведение перед загрузкой новой песни
        self.stop_preview()
        
        self.current_song = song
        self.song_info_area.display_song_info(song)
        
        # Инициализация громкости треков
        self.track_volumes = {track: 100 for track in song.audio_files}  # Громкость от 0 до 100
        
        # Отложенная загрузка фона и аудио
        pyglet.clock.schedule_once(self.delayed_load, 0.1)

    def delayed_load(self, dt):
        """Отложенная загрузка тяжелых ресурсов."""
        # Загружаем фон
        self.update_background(self.current_song)
        # Запускаем предпрослушивание
        self.start_preview()

    def update_background(self, song):
        """Обновляет фоновое изображение на основе выбранной песни."""
        try:
            # Отложенная загрузка изображения в отдельном потоке
            def load_background():
                try:
                    # Загружаем изображение через PIL
                    from PIL import Image
                    window_width, window_height = self.window.get_size()
                    
                    # Открываем изображение
                    with Image.open(song.cover_image) as img:
                        # Вычисляем целевые размеры (108% ширины экрана)
                        target_width = int(window_width * 1.08)
                        image_ratio = img.width / img.height
                        target_height = int(target_width / image_ratio)
                        
                        # Ресайз изображения с сохранением пропорций
                        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                        
                        # Конвертируем в формат, который поддерживает pyglet
                        img = img.convert('RGBA')
                        
                        # Создаем pyglet изображение
                        raw_image = img.tobytes()
                        bg_image = pyglet.image.ImageData(
                            target_width,
                            target_height,
                            'RGBA',
                            raw_image,
                            pitch=-target_width * 4
                        )
                    
                    def update_sprite(dt):
                        if self.background_sprite:
                            self.background_sprite.image = bg_image
                        else:
                            self.background_sprite = pyglet.sprite.Sprite(
                                img=bg_image,
                                batch=self.batch,
                                group=Group(order=-10)
                            )
                        self.update_background_position()
                        if self.game.settings.blur_background:
                            self.enable_blur()
                    
                    # Планируем обновление спрайта в главном потоке
                    pyglet.clock.schedule_once(update_sprite, 0)
                    
                except Exception as e:
                    self.logger.exception("Ошибка при загрузке фонового изображения.")
                    
                    def set_default_background(dt):
                        try:
                            default_bg = self.game.resource_loader.get_default_background()
                            if self.background_sprite:
                                self.background_sprite.image = default_bg
                            else:
                                self.background_sprite = pyglet.sprite.Sprite(
                                    img=default_bg,
                                    batch=self.batch,
                                    group=Group(order=-10)
                                )
                            self.update_background_position()
                        except Exception as e:
                            self.logger.exception("Ошибка при установке фонового изображения по умолчанию.")
                    
                    pyglet.clock.schedule_once(set_default_background, 0)
            
            # Запускаем загрузку в отдельном потоке
            import threading
            thread = threading.Thread(target=load_background)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            self.logger.exception("Ошибка при обновлении фонового изображения.")

    def sort_songs(self, sort_by):
        """Сортирует список песен по выбранному критерию."""
        try:
            if sort_by == 'Name':
                sorted_songs = sorted(self.song_carousel.all_songs, key=lambda s: s.name)
            elif sort_by == 'Artist':
                sorted_songs = sorted(self.song_carousel.all_songs, key=lambda s: s.artist)
            elif sort_by == 'Duration':
                sorted_songs = sorted(self.song_carousel.all_songs, key=lambda s: s.duration)
            else:
                self.logger.warning(f"Неизвестный критерий сортировки: {sort_by}")
                return

            self.song_carousel.all_songs = sorted_songs
            self.song_carousel.create_song_items()
        except Exception as e:
            self.logger.exception("Ошибка при сортировке песен.")

    def on_settings_changed(self):
        """Обрабатывает изменения настроек игры."""
        super().on_settings_changed()
        if self.game.settings.blur_background:
            self.enable_blur()
        else:
            self.disable_blur()

    def enable_blur(self):
        """Применяет размытие к фоновому изображению."""
        if not self.background_sprite or not self.background_sprite.image:
            self.logger.warning("Фоновый спрайт отсутствует, не могу применить размытие.")
            return
        try:
            image_data = self.background_sprite.image.get_image_data()
            format = 'RGBA'
            pitch = -(image_data.width * len(format))
            data = image_data.get_data(format, pitch)
            image = Image.frombytes(format, (image_data.width, image_data.height), data)
            blurred_image = image.filter(ImageFilter.GaussianBlur(radius=10))
            blurred_image_data = blurred_image.tobytes()
            new_image = pyglet.image.ImageData(
                image.width,
                image.height,
                format,
                blurred_image_data,
                pitch=pitch
            )
            self.background_sprite.image = new_image
            self.update_background_position()
        except Exception as e:
            self.logger.exception("Ошибка при применении размытия к фону.")

    def disable_blur(self):
        """Удаляет размытие с фонового изображения."""
        if self.current_song and os.path.exists(self.current_song.cover_image):
            try:
                bg_image = pyglet.image.load(self.current_song.cover_image)
                self.background_sprite.image = bg_image
                self.update_background_position()
            except Exception as e:
                self.logger.exception("Ошибка при удалении размытия с фона.")
        else:
            self.logger.warning("Не удалось отключить размытие: фоновое изображение отсутствует.")

    def show_map_settings_popup(self):
        """Отображает всплывающее окно настроек карты."""
        if self.popup_open:
            self.close_map_settings_popup()
            return
        if not self.current_song:
            self.game.notification_manager.add_notification(
                self.game.localization.get('song_select.select_song_first') or "Пожалуйста, выберите песню сначала."
            )
            return
        self.popup_open = True

        window_width, window_height = self.window.get_size()
        group = Group(order=20)

        try:
            # Фоновый прямоугольник всплывающего окна
            self.map_settings_popup = shapes.Rectangle(
                x=window_width / 2 - 200,
                y=window_height / 2 - 150,
                width=400,
                height=300,
                color=(50, 50, 50),
                batch=self.batch,
                group=group
            )
            self.map_settings_popup.opacity = 220

            # Отключение взаимодействия с другими элементами
            self.ui_manager.modal_elements.append(self.map_settings_popup)

            # Заголовок
            self.map_settings_title = Label(
                x=window_width / 2,
                y=window_height / 2 + 120,
                text=self.game.localization.get('map_settings.title') or 'Map Settings',
                font_size=20,
                anchor_x='center',
                anchor_y='center',
                batch=self.batch,
                group=Group(group.order + 1)
            )
            self.ui_manager.add(self.map_settings_title)
            self.ui_elements.append(self.map_settings_title)

            # Слайдеры громкости для каждого трека
            self.track_sliders = []
            self.track_labels = []
            for idx, track in enumerate(self.current_song.audio_files):
                label = Label(
                    x=window_width / 2 - 150,
                    y=window_height / 2 + 80 - idx * 40,
                    text=os.path.basename(track),
                    font_size=14,
                    anchor_x='right',
                    anchor_y='center',
                    batch=self.batch,
                    group=Group(group.order + 1)
                )
                self.ui_manager.add(label)
                self.ui_elements.append(label)
                self.track_labels.append(label)

                slider = Slider(
                    x=window_width / 2 - 140,
                    y=window_height / 2 + 80 - idx * 40,
                    width=300,
                    height=20,
                    min_value=0,
                    max_value=100,
                    value=self.track_volumes.get(track, 100),
                    step=1,
                    batch=self.batch,
                    group=Group(group.order + 1),
                    on_change=lambda value, t=track: self.on_track_volume_change(t, value)
                )
                self.ui_manager.add(slider)
                self.ui_elements.append(slider)
                self.track_sliders.append(slider)

            # Кнопка закрытия всплывающего окна
            self.close_map_settings_button = Button(
                x=window_width / 2,
                y=window_height / 2 - 130,
                width=100,
                height=30,
                text=self.game.localization.get('map_settings.close') or 'Close',
                callback=self.close_map_settings_popup,
                batch=self.batch,
                group=Group(group.order + 1)
            )
            self.ui_manager.add(self.close_map_settings_button)
            self.ui_elements.append(self.close_map_settings_button)

        except Exception as e:
            self.logger.exception("Ошибка при создании всплывающего окна настроек карты.")
            self.popup_open = False
            self.close_map_settings_popup()

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self.layout()

    def on_track_volume_change(self, track, value):
        """Обрабатывает изменение громкости трека через слайдер."""
        try:
            # Обновление громкости трека
            self.track_volumes[track] = value
            if self.preview_player:
                self.preview_player.set_volume(track, value / 100)  # Преобразование в диапазон 0.0 - 1.0
        except Exception as e:
            self.logger.exception(f"Ошибка при изменении громкости трека {track}.")

    def close_map_settings_popup(self):
        """Закрывает всплывающее окно настроек карты."""
        if not hasattr(self, 'map_settings_popup'):
            return
        try:
            # Удаление фонового прямоугольника
            self.ui_manager.modal_elements.remove(self.map_settings_popup)
            del self.map_settings_popup

            # Удаление заголовка
            self.ui_manager.remove(self.map_settings_title)
            self.ui_elements.remove(self.map_settings_title)
            del self.map_settings_title

            # Удаление слайдеров и меток
            for slider, label in zip(self.track_sliders, self.track_labels):
                self.ui_manager.remove(slider)
                self.ui_manager.remove(label)
                self.ui_elements.remove(slider)
                self.ui_elements.remove(label)
            self.track_sliders.clear()
            self.track_labels.clear()

            # Удаление кнопки закрытия
            self.ui_manager.remove(self.close_map_settings_button)
            self.ui_elements.remove(self.close_map_settings_button)
            del self.close_map_settings_button

            self.popup_open = False
        except Exception as e:
            self.logger.exception("Ошибка при закрытии всплывающего окна настроек карты.")

    def show_display_settings_popup(self):
        """Отображает всплывающее окно настроек отображения."""
        if self.popup_open:
            self.close_display_settings_popup()
            return
        self.popup_open = True

        window_width, window_height = self.window.get_size()
        group = Group(order=20)

        try:
            # Фоновый прямоугольник всплывающего окна
            self.display_settings_popup = shapes.Rectangle(
                x=window_width / 2 - 200,
                y=window_height / 2 - 100,
                width=400,
                height=200,
                color=(50, 50, 50),
                batch=self.batch,
                group=group
            )
            self.display_settings_popup.opacity = 220

            # Отключение взаимодействия с другими элементами
            self.ui_manager.modal_elements.append(self.display_settings_popup)

            # Заголовок
            self.display_settings_title = Label(
                x=window_width / 2,
                y=window_height / 2 + 70,
                text=self.game.localization.get('display_settings.title') or 'Display Settings',
                font_size=20,
                anchor_x='center',
                anchor_y='center',
                batch=self.batch,
                group=Group(group.order + 1)
            )
            self.ui_manager.add(self.display_settings_title)
            self.ui_elements.append(self.display_settings_title)

            # Чекбокс "Размытие фона"
            self.blur_background_checkbox = Checkbox(
                x=window_width / 2 - 150,
                y=window_height / 2 + 30,
                checked=self.game.settings.blur_background,
                callback=self.on_blur_background_toggle,
                batch=self.batch,
                group=Group(group.order + 1)
            )
            self.ui_manager.add(self.blur_background_checkbox)
            self.ui_elements.append(self.blur_background_checkbox)

            self.blur_background_label = Label(
                x=window_width / 2 - 120,
                y=window_height / 2 + 30,
                text=self.game.localization.get('settings.blur_background') or 'Blur Background',
                font_size=14,
                anchor_x='left',
                anchor_y='center',
                batch=self.batch,
                group=Group(group.order + 1)
            )
            self.ui_manager.add(self.blur_background_label)
            self.ui_elements.append(self.blur_background_label)

            # Кнопка закрытия всплывающего окна
            self.close_display_settings_button = Button(
                x=window_width / 2,
                y=window_height / 2 - 70,
                width=100,
                height=30,
                text=self.game.localization.get('display_settings.close') or 'Close',
                callback=self.close_display_settings_popup,
                batch=self.batch,
                group=Group(group.order + 1)
            )
            self.ui_manager.add(self.close_display_settings_button)
            self.ui_elements.append(self.close_display_settings_button)

        except Exception as e:
            self.logger.exception("Ошибка при создании всплывающего окна настроек отображения.")
            self.popup_open = False
            self.close_display_settings_popup()

    def on_blur_background_toggle(self, checked):
        """Обрабатывает переключение чекбокса размытия фона."""
        try:
            self.game.settings.blur_background = checked
            self.game.settings.save()
            if checked:
                self.enable_blur()
            else:
                self.disable_blur()
        except Exception as e:
            self.logger.exception("Ошибка при переключении размытия фона.")

    def close_display_settings_popup(self):
        """Закрывает всплывающее окно настроек отображения."""
        if not hasattr(self, 'display_settings_popup'):
            return
        try:
            # Удаление фонового прямоугольника
            self.ui_manager.modal_elements.remove(self.display_settings_popup)
            del self.display_settings_popup

            # Удаление заголовка
            self.ui_manager.remove(self.display_settings_title)
            self.ui_elements.remove(self.display_settings_title)
            del self.display_settings_title

            # Удаление чекбокса и метки
            self.ui_manager.remove(self.blur_background_checkbox)
            self.ui_manager.remove(self.blur_background_label)
            self.ui_elements.remove(self.blur_background_checkbox)
            self.ui_elements.remove(self.blur_background_label)

            # Удаление кнопки закрытия
            self.ui_manager.remove(self.close_display_settings_button)
            self.ui_elements.remove(self.close_display_settings_button)
            del self.close_display_settings_button

            self.popup_open = False
        except Exception as e:
            self.logger.exception("Ошибка при закрытии всплывающего окна настроек отображения.")

    def show_mods_popup(self):
        """Отображает всплывающее окно модификаций."""
        if self.popup_open:
            self.close_mods_popup()
            return
        self.popup_open = True

        window_width, window_height = self.window.get_size()
        group = Group(order=20)

        try:
            # Фоновый прямоугольник всплывающего окна
            self.mods_popup = shapes.Rectangle(
                x=window_width / 2 - 200,
                y=window_height / 2 - 100,
                width=400,
                height=200,
                color=(50, 50, 50),
                batch=self.batch,
                group=group
            )
            self.mods_popup.opacity = 220

            # Отключение взаимодействия с другими элементами
            self.ui_manager.modal_elements.append(self.mods_popup)

            # Заголовок
            self.mods_title = Label(
                x=window_width / 2,
                y=window_height / 2 + 70,
                text=self.game.localization.get('mods.title') or 'Mods',
                font_size=20,
                anchor_x='center',
                anchor_y='center',
                batch=self.batch,
                group=Group(group.order + 1)
            )
            self.ui_manager.add(self.mods_title)
            self.ui_elements.append(self.mods_title)

            # Чекбокс модификации "Hidden"
            self.hidden_mod_checkbox = Checkbox(
                x=window_width / 2 - 150,
                y=window_height / 2 + 30,
                checked='Hidden' in self.mods,
                callback=self.on_hidden_mod_toggle,
                batch=self.batch,
                group=Group(group.order + 1)
            )
            self.ui_manager.add(self.hidden_mod_checkbox)
            self.ui_elements.append(self.hidden_mod_checkbox)

            self.hidden_mod_label = Label(
                x=window_width / 2 - 120,
                y=window_height / 2 + 30,
                text="Hidden",
                font_size=14,
                anchor_x='left',
                anchor_y='center',
                batch=self.batch,
                group=Group(group.order + 1)
            )
            self.ui_manager.add(self.hidden_mod_label)
            self.ui_elements.append(self.hidden_mod_label)

            # Кнопка закрытия всплывающего окна
            self.close_mods_button = Button(
                x=window_width / 2,
                y=window_height / 2 - 70,
                width=100,
                height=30,
                text=self.game.localization.get('mods.close') or 'Close',
                callback=self.close_mods_popup,
                batch=self.batch,
                group=Group(group.order + 1)
            )
            self.ui_manager.add(self.close_mods_button)
            self.ui_elements.append(self.close_mods_button)

        except Exception as e:
            self.logger.exception("Ошибка при создании всплывающего окна модификаций.")
            self.popup_open = False
            self.close_mods_popup()

    def on_hidden_mod_toggle(self, checked):
        """Обрабатывает переключение чекбокса модификации 'Hidden'."""
        try:
            if checked:
                if 'Hidden' not in self.mods:
                    self.mods.append('Hidden')
            else:
                if 'Hidden' in self.mods:
                    self.mods.remove('Hidden')
        except Exception as e:
            self.logger.exception("Ошибка при переключении модификации 'Hidden'.")

    def close_mods_popup(self):
        """Закрывает всплывающее окно модификаций."""
        if not hasattr(self, 'mods_popup'):
            return
        try:
            # Удаление фонового прямоугольника
            if hasattr(self, 'mods_popup'):
                if self.mods_popup in self.ui_manager.modal_elements:
                    self.ui_manager.modal_elements.remove(self.mods_popup)
                delattr(self, 'mods_popup')

            # Удаление заголовка
            if hasattr(self, 'mods_title'):
                self.ui_manager.remove(self.mods_title)
                if self.mods_title in self.ui_elements:
                    self.ui_elements.remove(self.mods_title)
                delattr(self, 'mods_title')

            # Удаление чекбокса и метки
            for attr in ['hidden_mod_checkbox', 'hidden_mod_label']:
                if hasattr(self, attr):
                    element = getattr(self, attr)
                    if element is not None:
                        self.ui_manager.remove(element)
                        if element in self.ui_elements:
                            self.ui_elements.remove(element)
                        # element.delete()
                    delattr(self, attr)

            # Удаление кнопки закрытия
            if hasattr(self, 'close_mods_button'):
                self.ui_manager.remove(self.close_mods_button)
                if self.close_mods_button in self.ui_elements:
                    self.ui_elements.remove(self.close_mods_button)
                delattr(self, 'close_mods_button')

            self.popup_open = False
        except Exception as e:
            self.logger.exception("Ошибка при закрытии всплывающего окна модификаций.")

    def start_game(self):
        """Запускает игру с выбранной песней и настройками."""
        if self.current_song:
            try:
                self.stop_preview()
                self.game.start_game_with_song(
                    song=self.current_song,
                    track_volumes=self.track_volumes,
                    mods=self.mods
                )
            except Exception as e:
                self.logger.exception("Ошибка при запуске игры с выбранной песней.")
                self.game.notification_manager.add_notification(
                    self.game.localization.get('song_select.start_game_error') or "Ошибка при запуске игры."
                )
        else:
            self.game.notification_manager.add_notification(
                self.game.localization.get('song_select.select_song_first') or "Пожалуйста, выберите песню сначала."
            )

    def start_preview(self):
        """Запускает предпрослушивание выбранной песни."""
        try:
            # Остановка существующего предпрослушивания
            if self.preview_player:
                self.preview_player.stop()
                del self.preview_player
                self.preview_player = None

            # Запуск нового предпрослушивания
            if self.current_song and self.current_song.audio_files:
                from controllers.audio_controller import AudioController
                self.preview_player = AudioController(
                    audio_files=self.current_song.audio_files,
                    output_device=self.game.settings.output_device,
                    preview_mode=True  # Включаем режим превью
                )
                # Преобразование громкости треков в диапазон 0.0 - 1.0
                volumes = {track: volume / 100 for track, volume in self.track_volumes.items()}
                self.preview_player.set_volumes(volumes)
                self.preview_player.play()
        except Exception as e:
            self.logger.exception("Ошибка при запуске предпрослушивания аудио.")
            self.preview_player = None
            self.game.notification_manager.add_notification(
                self.game.localization.get('song_select.preview_error') or "Ошибка при предпрослушивании аудио."
            )

    def on_exit(self):
        """Обрабатывает выход из состояния выбора песни."""
        pyglet.clock.unschedule(self.update_time_label)
        self.stop_preview()
        super().on_exit()

    def handle_escape(self):
        if self.popup_open:
            # Если открыто всплывающее окно, закрываем его
            if hasattr(self, 'map_settings_popup'):
                self.close_map_settings_popup()
            elif hasattr(self, 'display_settings_popup'):
                self.close_display_settings_popup()
            elif hasattr(self, 'mods_popup'):
                self.close_mods_popup()
            return super().handle_escape()
        else:
            # Если нет открытых окон, возвращаемся в главное меню
            return super().handle_escape()
        
    def stop_preview(self):
        """Останавливает предпрослушивание и очищает ресурсы."""
        if self.preview_player:
            try:
                self.preview_player.stop()
                self.preview_player = None  # Просто обнуляем ссылку, сборщик мусора сам очистит объект
            except Exception as e:
                self.logger.exception("Ошибка при остановке предпрослушивания.")

    def update(self, dt):
        """Updates the state."""
        super().update(dt)
        # Добавляем обновление карусели
        if hasattr(self, 'song_carousel'):
            self.song_carousel.update(dt)






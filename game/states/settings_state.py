# game/states/settings_state.py

from .base_state import BaseState
from ui.elements import Label, Button, Slider, Dropdown, VolumeIndicator
import pyglet
import sounddevice as sd
import numpy as np

class SettingsState(BaseState):
    """
    Состояние настроек игры.
    """

    def on_enter(self):
        try:
            super().on_enter()
            batch = self.ui_manager.batch
            group = self.ui_manager.default_group

            # Инициализация списков перед их использованием
            self.ui_elements = []

            # Инициализация атрибута stream
            self.stream = None
            self.microphone_volume = 0.0
            self.is_stream_running = False

            # Создание UI элементов
            self.create_ui_elements(batch, group)

            # Обновление UI элементов в соответствии с текущими настройками
            self.update_ui_elements_from_settings()

            # Расположение элементов на экране
            self.layout()

            # Запуск потока для чтения микрофона
            self.start_microphone_stream()

            # Запуск обновления индикатора громкости
            pyglet.clock.schedule_interval(self.update_volume_indicator, 0.1)
        except Exception as e:
            self.logger.exception("Ошибка при входе в состояние настроек.")

    def create_ui_elements(self, batch, group):
        """Создает все UI элементы для настроек."""

        # Заголовок
        title_text = self.game.localization.get('settings.title')
        self.title_label = Label(0, 0, title_text, font_size=36, outline=True, batch=batch, group=group)
        self.ui_manager.add(self.title_label)

        # Динамическое получение списка поддерживаемых разрешений
        display = pyglet.canvas.get_display()
        screen = display.get_default_screen()
        supported_resolutions = [f"{mode.width}x{mode.height}" for mode in screen.get_modes()]
        supported_resolutions = list(set(supported_resolutions))  # Удаляем дубликаты
        supported_resolutions.sort(key=lambda x: int(x.split('x')[0]), reverse=True)  # Сортируем по ширине

        # Список языков
        languages = ['en', 'ru']

        # Выбор языка
        language_text = self.game.localization.get('settings.language')
        self.language_label = Label(0, 0, language_text, font_size=18, outline=True, batch=batch, group=group)
        self.ui_manager.add(self.language_label)

        self.language_dropdown = Dropdown(
            0, 0, 250, 30, languages,
            callback=self.on_language_change, font_size=16, batch=batch, group=group,
            max_option_width=240
        )
        self.ui_manager.add(self.language_dropdown)

        # Регулировка громкости
        volume_text = self.game.localization.get('settings.volume')
        self.volume_label = Label(0, 0, volume_text, font_size=18, outline=True, batch=batch, group=group)
        self.ui_manager.add(self.volume_label)

        self.volume_slider = Slider(
            0, 0, 250, 30,
            min_value=0, max_value=100, value=self.game.settings.volume,
            step=1, batch=batch, group=group
        )
        self.ui_manager.add(self.volume_slider)

        # Выбор режима отображения
        display_mode_text = self.game.localization.get('settings.display_mode')
        self.display_mode_label = Label(0, 0, display_mode_text, font_size=18, outline=True, batch=batch, group=group)
        self.ui_manager.add(self.display_mode_label)

        display_modes = ['windowed', 'fullscreen', 'borderless']
        self.display_mode_dropdown = Dropdown(
            0, 0, 250, 30, display_modes,
            callback=self.on_display_mode_change, font_size=16, batch=batch, group=group
        )
        self.ui_manager.add(self.display_mode_dropdown)

        # Выбор разрешения
        resolution_text = self.game.localization.get('settings.resolution')
        self.resolution_label = Label(0, 0, resolution_text, font_size=18, outline=True, batch=batch, group=group)
        self.ui_manager.add(self.resolution_label)

        self.resolution_dropdown = Dropdown(
            0, 0, 250, 30, supported_resolutions,
            callback=self.on_resolution_change, font_size=16, batch=batch, group=group
        )
        self.ui_manager.add(self.resolution_dropdown)

        # Получение списка драйверов
        hostapis = sd.query_hostapis()
        hostapi_names = [f"{idx}: {hostapi['name']}" for idx, hostapi in enumerate(hostapis)]

        # Dropdown для выбора драйвера
        hostapi_text = self.game.localization.get('settings.audio_driver')
        self.hostapi_label = Label(0, 0, hostapi_text, font_size=18, outline=True, batch=batch, group=group)
        self.ui_manager.add(self.hostapi_label)

        self.hostapi_dropdown = Dropdown(
            0, 0, 250, 30, hostapi_names,
            callback=self.on_hostapi_change, font_size=16, batch=batch, group=group,
            max_option_width=240
        )
        self.ui_manager.add(self.hostapi_dropdown)

        # Создание пустых списков устройств
        self.input_device_dropdown = Dropdown(
            0, 0, 250, 30, [],
            callback=self.on_input_device_change, font_size=16, batch=batch, group=group,
            max_option_width=240
        )
        self.ui_manager.add(self.input_device_dropdown)

        self.output_device_dropdown = Dropdown(
            0, 0, 250, 30, [],
            callback=self.on_output_device_change, font_size=16, batch=batch, group=group,
            max_option_width=240
        )
        self.ui_manager.add(self.output_device_dropdown)

        # Обновляем списки устройств
        self.update_device_lists()

        # Метка для устройства ввода
        input_device_text = self.game.localization.get('settings.input_device')
        self.input_device_label = Label(0, 0, input_device_text, font_size=18, outline=True, batch=batch, group=group)
        self.ui_manager.add(self.input_device_label)

        # Индикатор громкости микрофона
        volume_indicator_text = self.game.localization.get('settings.volume_indicator')
        self.volume_indicator_label = Label(0, 0, volume_indicator_text, font_size=18, outline=True, batch=batch, group=group)
        self.ui_manager.add(self.volume_indicator_label)

        self.volume_indicator = VolumeIndicator(
            0, 0, 250, 30, batch=batch, group=group
        )
        self.ui_manager.add(self.volume_indicator)

        # Метка для устройства вывода
        output_device_text = self.game.localization.get('settings.output_device')
        self.output_device_label = Label(0, 0, output_device_text, font_size=18, outline=True, batch=batch, group=group)
        self.ui_manager.add(self.output_device_label)

        # Кнопка сохранения настроек
        save_text = self.game.localization.get('settings.save')
        self.save_button = Button(0, 0, 200, 50, save_text, self.on_save, batch=batch, group=group)
        self.ui_manager.add(self.save_button)

        # Кнопка возврата в меню
        back_text = self.game.localization.get('settings.back')
        self.back_button = Button(0, 0, 200, 50, back_text, self.on_back, batch=batch, group=group)
        self.ui_manager.add(self.back_button)

        # Добавляем элементы в ui_elements для обработки событий
        self.ui_elements.extend([
            self.title_label,
            self.language_label,
            self.language_dropdown,
            self.volume_label,
            self.volume_slider,
            self.display_mode_label,
            self.display_mode_dropdown,
            self.resolution_label,
            self.resolution_dropdown,
            self.hostapi_label,
            self.hostapi_dropdown,
            self.output_device_label,
            self.output_device_dropdown,
            self.input_device_label,
            self.input_device_dropdown,
            self.volume_indicator_label,
            self.volume_indicator,
            self.save_button,
            self.back_button,
        ])

    def update_ui_elements_from_settings(self):
        """Обновляет UI элементы в соответствии с текущими настройками."""
        # Язык
        self.language_dropdown.selected_option = self.game.settings.language

        # Громкость
        self.volume_slider.value = self.game.settings.volume

        # Режим отображения
        self.display_mode_dropdown.selected_option = self.game.settings.display_mode

        # Разрешение
        current_resolution = f"{self.game.settings.resolution[0]}x{self.game.settings.resolution[1]}"
        if current_resolution in self.resolution_dropdown.options:
            self.resolution_dropdown.selected_option = current_resolution
        else:
            self.logger.warning(f"Текущее разрешение {current_resolution} отсутствует в списке поддерживаемых разрешений.")
            self.resolution_dropdown.options.insert(0, current_resolution)
            self.resolution_dropdown.update_options()
            self.resolution_dropdown.selected_option = current_resolution

        # Устройства ввода/вывода
        if self.game.settings.input_device:
            self.input_device_dropdown.selected_option = self.game.settings.input_device
        if self.game.settings.output_device:
            self.output_device_dropdown.selected_option = self.game.settings.output_device

    def layout(self):
        """Располагает UI элементы на экране."""
        width, height = self.window.get_size()
        padding = 20
        label_x = width / 2 - 200  # Сдвигаем метки влево на 200 пикселей
        control_x = width / 2 + 50
        start_y = height - 100
        y_offset = start_y

        elements = [
            (self.language_label, self.language_dropdown),
            (self.volume_label, self.volume_slider),
            (self.display_mode_label, self.display_mode_dropdown),
            (self.resolution_label, self.resolution_dropdown),
            (self.hostapi_label, self.hostapi_dropdown),
            (self.output_device_label, self.output_device_dropdown),
            (self.input_device_label, self.input_device_dropdown),
            (self.volume_indicator_label, self.volume_indicator),
        ]

        for label, control in elements:
            label.update_position(label_x, y_offset)
            control.update_position(control_x, y_offset)
            y_offset -= control.height + padding

        # Расположение кнопок
        self.save_button.update_position(width / 2 - 110, y_offset - 40)
        self.back_button.update_position(width / 2 + 110, y_offset - 40)

        # Обновление позиции заголовка
        self.title_label.update_position(width / 2, height - 50)

    def update_volume_indicator(self, dt):
        try:
            if self.stream and self.volume_indicator:
                self.volume_indicator.set_volume(self.microphone_volume)
        except Exception as e:
            self.logger.exception("Ошибка при обновлении индикатора громкости.")

    def on_resolution_change(self, selected_resolution):
        width, height = map(int, selected_resolution.split('x'))
        self.game.settings.resolution = (width, height)

    def on_exit(self):
        try:
            self.stop_microphone_stream()
            pyglet.clock.unschedule(self.update_volume_indicator)
            # Скрываем все опции при выходе
            for element in self.ui_elements:
                if isinstance(element, Dropdown):
                    element.hide_options()
            self.cleanup_ui()
            super().on_exit()
        except Exception as e:
            self.logger.exception("Ошибка при выходе из состояния настроек.")

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self.layout()
        # Обновляем положение подсказок при изменении размера
        for element in self.ui_elements:
            if isinstance(element, Dropdown) and element.expanded:
                element.hide_tooltip()

    def on_language_change(self, selected_language):
        self.logger.info(f"Язык изменён на {selected_language}.")
        self.game.settings.language = selected_language
        self.game.localization.set_language(selected_language)
        self.update_texts()

    def on_display_mode_change(self, selected_mode):
        self.logger.info(f"Режим отображения изменён на {selected_mode}.")
        self.game.settings.display_mode = selected_mode

    def on_save(self):
        try:
            self.game.settings.volume = self.volume_slider.value
            self.game.settings.save()
            self.game.apply_settings()
            notification_text = self.game.localization.get('settings.saved')
            self.game.notification_manager.add_notification(notification_text)
            self.logger.info("Настройки сохранены и применены.")
        except Exception as e:
            self.logger.exception("Ошибка при сохранении настроек.")

    def on_back(self):
        self.logger.info("Возврат в главное меню.")
        self.game.state_manager.change_state('menu')

    def update_texts(self):
        """Обновляет тексты элементов при смене языка."""
        self.title_label.set_text(self.game.localization.get('settings.title'))
        self.language_label.set_text(self.game.localization.get('settings.language'))
        self.volume_label.set_text(self.game.localization.get('settings.volume'))
        self.display_mode_label.set_text(self.game.localization.get('settings.display_mode'))
        self.resolution_label.set_text(self.game.localization.get('settings.resolution'))
        self.hostapi_label.set_text(self.game.localization.get('settings.audio_driver'))
        self.input_device_label.set_text(self.game.localization.get('settings.input_device'))
        self.output_device_label.set_text(self.game.localization.get('settings.output_device'))
        self.volume_indicator_label.set_text(self.game.localization.get('settings.volume_indicator'))
        self.save_button.label.set_text(self.game.localization.get('settings.save'))
        self.back_button.label.set_text(self.game.localization.get('settings.back'))

    def on_settings_changed(self):
        """Обновляет элементы при изменении настроек."""
        self.logger.info("Настройки изменены, обновление UI элементов.")
        self.update_ui_elements_from_settings()
        self.update_texts()

    def start_microphone_stream(self):
        try:
            self.stop_microphone_stream()
            selected_option = self.input_device_dropdown.selected_option
            if selected_option:
                device_index = int(selected_option.split(":")[0])
                volume = self.volume_slider.value / 100.0
                self.stream = sd.InputStream(
                    device=device_index,
                    channels=1,
                    callback=self.audio_callback,
                    blocksize=1024,
                    dtype='float32',
                    latency='low'
                )
                self.stream.start()
                self.is_stream_running = True
                self.logger.info("Поток микрофона запущен.")
            else:
                self.logger.warning("Устройство ввода не выбрано, поток микрофона не запущен.")
        except Exception as e:
            self.logger.exception("Ошибка при запуске аудиопотока микрофона.")
            self.stream = None
            self.is_stream_running = False
            error_message = self.game.localization.get('error.microphone_stream_failed')
            self.game.notification_manager.add_notification(error_message)

    def stop_microphone_stream(self):
        if self.stream and self.is_stream_running:
            try:
                self.stream.stop()
                self.stream.close()
                self.stream = None
                self.is_stream_running = False
                self.logger.info("Поток микрофона остановлен.")
            except Exception as e:
                self.logger.exception("Ошибка при остановке аудиопотока микрофона.")

    def audio_callback(self, indata, frames, time, status):
        try:
            volume = self.volume_slider.value / 100.0
            indata *= volume
            self.microphone_volume = min(np.linalg.norm(indata) * 10 / 10, 1.0)
        except Exception as e:
            self.logger.exception("Ошибка в audio_callback.")
            raise sd.CallbackAbort

    def on_hostapi_change(self, selected_hostapi):
        self.game.settings.hostapi = selected_hostapi
        self.update_device_lists()

    def update_device_lists(self):
        try:
            selected_hostapi_index = int(self.hostapi_dropdown.selected_option.split(":")[0])
            devices = sd.query_devices()
            
            input_devices = [f"{idx}: {device['name']}" for idx, device in enumerate(devices)
                             if device['hostapi'] == selected_hostapi_index and device['max_input_channels'] > 0]
            output_devices = [f"{idx}: {device['name']}" for idx, device in enumerate(devices)
                              if device['hostapi'] == selected_hostapi_index and device['max_output_channels'] > 0]
            
            self.input_device_dropdown.options = input_devices
            self.input_device_dropdown.update_options()
            if input_devices:
                self.input_device_dropdown.selected_option = input_devices[0]
            else:
                self.input_device_dropdown.selected_option = None
            
            self.output_device_dropdown.options = output_devices
            self.output_device_dropdown.update_options()
            if output_devices:
                self.output_device_dropdown.selected_option = output_devices[0]
            else:
                self.output_device_dropdown.selected_option = None
            
            self.start_microphone_stream()
        except Exception as e:
            self.logger.exception("Ошибка при обновлении списка устройств.")

    def on_input_device_change(self, selected_device):
        try:
            self.game.settings.input_device = selected_device
            self.start_microphone_stream()
            self.update_volume_indicator(0)
        except Exception as e:
            self.logger.exception("Ошибка при смене устройства ввода.")

    def on_output_device_change(self, selected_device):
        try:
            self.game.settings.output_device = selected_device
        except Exception as e:
            self.logger.exception("Ошибка при смене устройства вывода.")

    def cleanup_ui(self):
        """Удаляет UI элементы и очищает список."""
        for element in self.ui_elements:
            self.ui_manager.remove(element)
        self.ui_elements.clear()
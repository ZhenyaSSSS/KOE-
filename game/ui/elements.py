# game/ui/elements.py

import pyglet
from pyglet import shapes
from abc import ABC, abstractmethod
import os
from pyglet.gl import *
from pyglet import shapes
from pyglet.graphics import Group
import ctypes
import os
import time
from math import *
from pyglet import gl

def ease_out_quad(t):
    return t * (2 - t)

def ease_out_cubic(t):
    return 1 - pow(1 - t, 3)

def check_gl_error():
    err = glGetError()
    if err != GL_NO_ERROR:
        print(f"OpenGL error: {err}")
import numpy as np

class UIElement(ABC):
    """
    Абстрактный базовый класс для всех элементов пользовательского интерфейса.
    Предоставляет общие методы и интерфейс для наследников.
    """

    def __init__(self, x, y, width, height, batch, group):
        self.x = x  # Левая нижняя координата по X
        self.y = y  # Левая нижняя координата по Y
        self.width = width
        self.height = height
        self.visible = True
        self.batch = batch
        self.group = group
        self.children = []
        self.hovered = False
        self.pressed = False

    @abstractmethod
    def draw(self):
        """Отрисовка элемента интерфейса."""
        pass

    def update(self, dt):
        """Обновление состояния элемента интерфейса."""
        pass

    def add_child(self, child):
        """Добавляет дочерний элемент."""
        self.children.append(child)

    def remove_child(self, child):
        """Удаляет дочерний элемент."""
        if child in self.children:
            self.children.remove(child)

    def clear_children(self):
        """Очищает список дочерних элементов."""
        self.children.clear()

    def on_mouse_press(self, x, y, button, modifiers):
        """Обработка нажатия кнопки мыши."""
        handled = False
        for child in reversed(self.children):
            if child.on_mouse_press(x, y, button, modifiers):
                handled = True
                break
        return handled

    def on_mouse_release(self, x, y, button, modifiers):
        """Обработка отпускания кнопки мыши."""
        handled = False
        for child in reversed(self.children):
            if child.on_mouse_release(x, y, button, modifiers):
                handled = True
                break
        return handled

    def on_mouse_motion(self, x, y, dx, dy):
        """Обработка движения мыши."""
        for child in self.children:
            child.on_mouse_motion(x, y, dx, dy)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """Обработка перетаскивания мыши."""
        handled = False
        for child in reversed(self.children):
            if child.on_mouse_drag(x, y, dx, dy, buttons, modifiers):
                handled = True
                break
        return handled

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        """Обработка прокрутки колесика мыши."""
        handled = False
        for child in reversed(self.children):
            if child.on_mouse_scroll(x, y, scroll_x, scroll_y):
                handled = True
                break
        return handled

    def on_text(self, text):
        """Обработка текстового ввода."""
        for child in self.children:
            child.on_text(text)

    def on_text_motion(self, motion):
        """Обработка движения курсора в текстовом вводе."""
        for child in self.children:
            child.on_text_motion(motion)

    def hit_test(self, x, y):
        """Проверяет, находится ли точка (x, y) внутри элемента."""
        return self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height

    def delete(self):
        """Удаляет графические объекты, связанные с элементом."""
        for child in self.children:
            child.delete()
        self.children.clear()

    def dispatch_event_to_children(self, event_name, *args, **kwargs):
        for child in getattr(self, 'ui_elements', []):
            if hasattr(child, 'dispatch_event_to_children'):
                if child.dispatch_event_to_children(event_name, *args, **kwargs):
                    return True
            handler = getattr(child, event_name, None)
            if callable(handler):
                if handler(*args, **kwargs):
                    return True
        return False

class Label(UIElement):
    """
    Текстовая метка с возможностью обводки.
    """

    def __init__(self, x, y, text, font_size=14, color=(255, 255, 255, 255),
                 anchor_x='center', anchor_y='center', batch=None, group=None,
                 outline=True, outline_color=(0, 0, 0, 255), interactive=True):
        # Инициализируем UIElement с нулевыми размерами, они будут обновлены позже
        super().__init__(x, y, 0, 0, batch, group)
        self.text = text
        self.font_size = font_size
        self.color = color
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y
        self.outline = outline
        self.outline_color = outline_color
        self.interactive = interactive  # Новое свойство

        self.label = pyglet.text.Label(
            self.text,
            font_name='Arial',
            font_size=self.font_size,
            color=self.color,
            x=self.x,
            y=self.y,
            anchor_x=self.anchor_x,
            anchor_y=self.anchor_y,
            batch=self.batch,
            group=self.group
        )

        if self.outline:
            self.create_outline_labels()

        # Обновляем размеры метки после создания
        self.update_dimensions()

    def create_outline_labels(self):
        """Создает метки для обводки текста."""
        offsets = [(-1, 0), (1, 0), (0, -1), (0, 1),
                   (-1, -1), (-1, 1), (1, -1), (1, 1)]
        self.outline_labels = []

        # Проверяем наличие группы и корректность order
        if self.group and hasattr(self.group, 'order'):
            outline_group_order = self.group.order - 1
            if outline_group_order < 0:
                outline_group_order = 0
        else:
            outline_group_order = 0

        outline_group = Group(order=outline_group_order)
        for dx, dy in offsets:
            outline_label = pyglet.text.Label(
                self.text,
                font_name='Arial',
                font_size=self.font_size,
                color=self.outline_color,
                x=self.x + dx,
                y=self.y + dy,
                anchor_x=self.anchor_x,
                anchor_y=self.anchor_y,
                batch=self.batch,
                group=outline_group
            )
            self.outline_labels.append(outline_label)

    def set_text(self, text):
        """Устанавливает новый текст для метки."""
        self.text = text
        self.label.text = self.text
        if self.outline:
            for outline_label in self.outline_labels:
                outline_label.text = self.text
        self.update_dimensions()

    def update_dimensions(self):
        """Обновляет ширину и высоту метки."""
        self.width = self.label.content_width
        self.height = self.label.content_height

    def update_position(self, x, y):
        """Обновляет позицию метки."""
        self.x = x
        self.y = y
        self.label.x = x
        self.label.y = y
        if self.outline:
            for idx, (outline_label, (dx, dy)) in enumerate(zip(self.outline_labels, [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)])):
                outline_label.x = x + dx
                outline_label.y = y + dy

    def hit_test(self, x, y):
        """Проверяет, находится ли точка (x, y) внутри метки."""
        if not self.interactive:
            return False
        left = self.x - self.label.content_width * (0 if self.anchor_x == 'left' else 0.5 if self.anchor_x == 'center' else 1)
        right = left + self.label.content_width
        bottom = self.y - self.label.content_height * (0 if self.anchor_y == 'bottom' else 0.5 if self.anchor_y == 'center' else 1)
        top = bottom + self.label.content_height
        return left <= x <= right and bottom <= y <= top

    def delete(self):
        """Удаляет метку и связанные с ней ресурсы."""
        self.label.delete()
        if self.outline:
            for outline_label in self.outline_labels:
                outline_label.delete()
        super().delete()

    def draw(self):
        """Отрисовка метки."""
        if self.visible:
            if self.outline:
                for outline_label in self.outline_labels:
                    outline_label.draw()
            self.label.draw()

    def set_visible(self, visible):
        """Устанавливает видимость метки и её обводки."""
        self.visible = visible
        self.label.visible = visible
        if self.outline:
            for outline_label in self.outline_labels:
                outline_label.visible = visible


class Button(UIElement):
    """
    Кнопка с возможностью взаимодействия и визуальной обратной связью.
    """

    def __init__(self, x, y, width, height, text, callback,
                 font_size=14, color=(255, 255, 255, 255), bg_color=(50, 50, 50),
                 hover_color=(70, 70, 70), pressed_color=(90, 90, 90),
                 outline=True, outline_color=(0, 0, 0, 255), batch=None, group=None):
        super().__init__(x - width / 2, y - height / 2, width, height, batch, group)
        self.text = text
        self.callback = callback
        self.font_size = font_size
        self.color = color
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.pressed_color = pressed_color
        self.outline = outline
        self.outline_color = outline_color

        self.background = shapes.Rectangle(
            self.x, self.y, self.width, self.height, color=self.bg_color[:3], batch=self.batch, group=self.group
        )

        # Группа для текста должна быть выше группы фона
        text_group = Group(order=self.group.order + 2)

        self.label = Label(
            self.x + self.width / 2,
            self.y + self.height / 2,
            self.text,
            font_size=self.font_size,
            color=self.color,
            anchor_x='center',
            anchor_y='center',
            batch=self.batch,
            group=text_group,
            outline=self.outline,
            outline_color=self.outline_color
        )

    def on_mouse_press(self, x, y, button, modifiers):
        if self.visible and self.hit_test(x, y) and button == pyglet.window.mouse.LEFT:
            self.pressed = True
            self.background.color = self.pressed_color[:3]
            return True
        return False

    def on_mouse_release(self, x, y, button, modifiers):
        if self.pressed and button == pyglet.window.mouse.LEFT:
            self.pressed = False
            self.background.color = self.hover_color[:3] if self.hovered else self.bg_color[:3]
            if self.visible and self.hit_test(x, y):
                self.callback()
                return True
        return False

    def on_mouse_motion(self, x, y, dx, dy):
        if self.visible:
            self.hovered = self.hit_test(x, y)
            if not self.pressed:
                self.background.color = self.hover_color[:3] if self.hovered else self.bg_color[:3]

    def delete(self):
        """Удаляет кнопку и связанные с ней ресурсы."""
        if hasattr(self, 'background') and self.background is not None:
            self.background.delete()
        if hasattr(self, 'label') and self.label is not None:
            self.label.delete()
        super().delete()

    def draw(self):
        if self.visible:
            self.background.draw()
            self.label.draw()

    def update_position(self, x, y):
        """Обновляет позицию кнопки."""
        self.x = x - self.width / 2
        self.y = y - self.height / 2
        self.background.x = self.x
        self.background.y = self.y
        self.label.update_position(x, y)

class TextInput(UIElement):
    """
    Text input field with callback on text change.
    """

    def __init__(self, x, y, width, height, text='', font_size=14,
                 color=(255, 255, 255, 255), bg_color=(50, 50, 50, 255),
                 caret_color=(255, 255, 255), batch=None, group=None):
        super().__init__(x - width / 2, y - height / 2, width, height, batch, group)
        self.text = text
        self.font_size = font_size
        self.color = color
        self.bg_color = bg_color if len(bg_color) == 4 else bg_color + (255,)
        self.caret_color = caret_color
        self.active = False
        self.on_text_change_callback = None

        self.background = shapes.Rectangle(
            self.x, self.y, self.width, self.height,
            color=self.bg_color[:3], batch=self.batch, group=self.group
        )
        self.background.opacity = self.bg_color[3]

        self.document = pyglet.text.document.UnformattedDocument(self.text)
        self.document.set_style(0, len(self.document.text), dict(color=self.color, font_size=self.font_size))

        self.layout = pyglet.text.layout.IncrementalTextLayout(
            self.document, self.width - 10, self.height - 10, multiline=False, batch=self.batch,
            group=Group(order=self.group.order + 2)
        )
        self.layout.x = self.x + 5
        self.layout.y = self.y + (self.height - self.layout.height) / 2

        self.caret = pyglet.text.caret.Caret(self.layout, color=self.caret_color)
        self.caret.visible = False

    def set_on_text_change_callback(self, callback):
        """
        Sets the callback function when the text changes.
        """
        self.on_text_change_callback = callback

    def on_mouse_press(self, x, y, button, modifiers):
        if self.visible and self.hit_test(x, y):
            self.active = True
            self.caret.visible = True
            return True
        else:
            self.active = False
            self.caret.visible = False
            return False

    def on_text(self, text):
        if self.active:
            self.caret.on_text(text)
            if self.on_text_change_callback:
                self.on_text_change_callback(self.document.text)

    def on_text_motion(self, motion):
        if self.active:
            self.caret.on_text_motion(motion)
            if self.on_text_change_callback:
                self.on_text_change_callback(self.document.text)

    def on_text_motion_select(self, motion):
        if self.active:
            self.caret.on_text_motion_select(motion)
            if self.on_text_change_callback:
                self.on_text_change_callback(self.document.text)

    def delete(self):
        """Deletes the text input and associated resources."""
        self.background.delete()
        self.layout.delete()
        super().delete()

    def draw(self):
        if self.visible:
            self.background.draw()
            self.layout.draw()

class Slider(UIElement):
    """
    Ползунок для выбора значения из диапазона.
    """

    def __init__(self, x, y, width, height, min_value=0, max_value=100, value=0,
                 step=1, bg_color=(200, 200, 200), fg_color=(100, 100, 100),
                 knob_color=(50, 50, 50), batch=None, group=None, on_change=None):
        super().__init__(x - width / 2, y - height / 2, width, height, batch, group)
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.knob_color = knob_color
        self.dragging = False
        self.on_change = on_change  # Callback при изменении значения

        self.track_height = height / 4
        self.knob_radius = height / 2

        self.background = shapes.Rectangle(
            self.x, self.y + (self.height - self.track_height) / 2, self.width, self.track_height,
            color=self.bg_color[:3], batch=self.batch, group=self.group
        )
        self.background.opacity = self.bg_color[3] if len(self.bg_color) > 3 else 255

        self.foreground = shapes.Rectangle(
            self.x, self.y + (self.height - self.track_height) / 2, 0, self.track_height,
            color=self.fg_color[:3], batch=self.batch, group=self.group
        )
        self.foreground.opacity = self.fg_color[3] if len(self.fg_color) > 3 else 255

        self.knob = shapes.Circle(
            self.x, self.y + self.height / 2, self.knob_radius,
            color=self.knob_color[:3], batch=self.batch, group=self.group
        )
        self.knob.opacity = self.knob_color[3] if len(self.knob_color) > 3 else 255

        # Устанавливаем значение после инициализации knob
        self.value = value  # Это вызовет сеттер и update_knob_position()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value
        self.update_knob_position()

    def update_knob_position(self):
        """Обновляет позицию ползунка в соответствии со значением."""
        ratio = (self.value - self.min_value) / (self.max_value - self.min_value)
        self.knob.x = self.x + ratio * self.width
        self.foreground.width = ratio * self.width

    def on_mouse_press(self, x, y, button, modifiers):
        if self.visible and self.hit_test(x, y) and button == pyglet.window.mouse.LEFT:
            self.dragging = True
            self.on_mouse_drag(x, y, 0, 0, button, modifiers)
            return True
        return False

    def on_mouse_release(self, x, y, button, modifiers):
        if self.dragging and button == pyglet.window.mouse.LEFT:
            self.dragging = False
            return True
        return False

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.dragging:
            ratio = (x - self.x) / self.width
            ratio = min(max(ratio, 0), 1)
            value = self.min_value + ratio * (self.max_value - self.min_value)
            new_value = round(value / self.step) * self.step
            if new_value != self.value:
                self.value = new_value
                self.update_knob_position()
                if self.on_change:
                    self.on_change(self.value)
            return True
        return False

    def delete(self):
        """Удаляет слайдер и связанные с ним ресурсы."""
        self.background.delete()
        self.foreground.delete()
        self.knob.delete()
        super().delete()

    def draw(self):
        if self.visible:
            self.background.draw()
            self.foreground.draw()
            self.knob.draw()

    def update_position(self, x, y):
        """Обновляет позицию слайдера."""
        self.x = x - self.width / 2
        self.y = y - self.height / 2
        self.background.x = self.x
        self.background.y = self.y + (self.height - self.track_height) / 2
        self.foreground.x = self.x
        self.foreground.y = self.background.y
        self.knob.y = self.y + self.height / 2
        self.update_knob_position()

class Dropdown(UIElement):
    """
    Выпадающий список для выбора одного значения из списка.
    """
    next_group_order = 0  # Статический счетчик для уникальности групп

    def __init__(self, x, y, width, height, options, callback=None, font_size=14,
                 color=(255, 255, 255, 255), bg_color=(50, 50, 50, 255), batch=None, group=None,
                 max_option_width=None):
        super().__init__(x - width / 2, y - height / 2, width, height, batch, group)

        # Уникальный смещение для групп этого экземпляра
        self.group_order_offset = Dropdown.next_group_order
        Dropdown.next_group_order += 10  # Увеличиваем счетчик для следующего экземпляра

        self.options = options
        self.callback = callback
        self.font_size = font_size
        self.color = color
        self.bg_color = bg_color
        self.expanded = False
        self.option_height = height
        self.max_option_width = max_option_width or self.width - 20  # Добавлен отступ для текста

        # Убедимся, что self.group определён
        if self.group is None:
            self.group = Group(order=0)

        self.background = shapes.Rectangle(
            self.x, self.y, self.width, self.height, color=self.bg_color[:3], batch=self.batch,
            group=Group(order=self.group.order + self.group_order_offset)
        )
        self.background.opacity = self.bg_color[3]

        # Главная метка с обводкой
        self.label = Label(
            self.x + 5,
            self.y + self.height / 2,
            '',
            font_size=self.font_size,
            color=self.color,
            anchor_x='left',
            anchor_y='center',
            batch=self.batch,
            group=Group(order=self.group.order + self.group_order_offset + 2),
            outline=True,
            outline_color=(0, 0, 0, 255)
        )

        option_group_order = self.group.order + self.group_order_offset + 100
        # Инициализация опций
        self.option_labels = []
        self.option_backgrounds = []
        for idx, option in enumerate(self.options):
            # Фон опции
            bg = shapes.Rectangle(
                self.x, self.y - ((idx + 1) * self.option_height),
                self.width, self.option_height,
                color=self.bg_color[:3],
                batch=self.batch,
                group=Group(order=option_group_order)
            )
            bg.opacity = 0  # Скрываем фон опции
            bg.visible = False
            self.option_backgrounds.append(bg)

            # Метка опции с обводкой и обрезкой текста
            truncated_option = self.truncate_text(option, self.max_option_width)
            option_label = Label(
                self.x + 5,
                bg.y + self.option_height / 2,
                truncated_option,
                font_size=self.font_size,
                color=self.color,
                anchor_x='left',
                anchor_y='center',
                batch=self.batch,
                group=Group(order=option_group_order + 2),
                outline=True,  # Обеспечиваем наличие обводки
                outline_color=(0, 0, 0, 255)
            )
            option_label.full_text = option  # Сохраняем полный текст для подсказки
            option_label.visible = False  # Изначально скрыты
            self.option_labels.append(option_label)

        # Устанавливаем выбранную опцию
        self.selected_option = options[0] if options else ''

        # Инициализация метки подсказки
        self.tooltip_label = None

        self.hide_options()  # Скрываем опции при инициализации

    @property
    def selected_option(self):
        return self._selected_option

    @selected_option.setter
    def selected_option(self, value):
        self._selected_option = value
        if hasattr(self, 'label'):
            # Обрезаем текст, если он превышает ширину Dropdown
            display_text = self.truncate_text(value, self.max_option_width)
            self.label.set_text(display_text)

    def on_mouse_press(self, x, y, button, modifiers):
        if button != pyglet.window.mouse.LEFT:
            return False

        if self.expanded:
            # Проверяем клик по меткам опций вместо фонов
            for label in self.option_labels:
                if label.visible and label.hit_test(x, y):
                    self.selected_option = label.full_text
                    self.expanded = False
                    self.hide_options()
                    self.hide_tooltip()  # Скрываем подсказку при выборе
                    if self.callback:
                        self.callback(self.selected_option)
                    return True
            # Клик вне опций
            self.expanded = False
            self.hide_options()
            self.hide_tooltip()  # Скрываем подсказку при закрытии
            return False
        else:
            if self.visible and self.hit_test(x, y):
                self.expanded = True
                self.show_options()
                # Закрываем остальные dropdowns через UIManager
                if self.batch and hasattr(self.batch, 'ui_manager'):
                    self.batch.ui_manager.close_all_dropdowns(except_dropdown=self)
                return True
        return False

    def show_options(self):
        """Отображает опции."""
        self.expanded = True
        for bg, label in zip(self.option_backgrounds, self.option_labels):
            bg.visible = True
            bg.opacity = self.bg_color[3]
            label.set_visible(True)

    def hide_options(self):
        """Скрывает опции."""
        self.expanded = False
        for bg, label in zip(self.option_backgrounds, self.option_labels):
            bg.visible = False
            bg.opacity = 0
            label.set_visible(False)
        self.hide_tooltip()  # Убедимся, что подсказка скрыта

    def delete(self):
        """Удаляет выпадающий список и связанные с ним ресурсы."""
        self.background.delete()
        self.label.delete()
        for bg in self.option_backgrounds:
            bg.delete()
        for label in self.option_labels:
            label.delete()
        if self.tooltip_label is not None:
            self.tooltip_label.delete()
        super().delete()

    def draw(self):
        if self.visible:
            self.background.draw()
            self.label.draw()
            if self.expanded:
                for bg in self.option_backgrounds:
                    if bg.visible:
                        bg.draw()
                for label in self.option_labels:
                    if label.visible:
                        label.draw()
            if self.tooltip_label and self.tooltip_label.visible:
                # Добавляем обводку для подсказки
                if hasattr(self.tooltip_label, 'outline_labels'):
                    for outline_label in self.tooltip_label.outline_labels:
                        outline_label.draw()
                self.tooltip_label.draw()

    def update_position(self, x, y):
        """Обновл��ет позицию выпадающего списка."""
        self.x = x - self.width / 2
        self.y = y - self.height / 2
        self.background.x = self.x
        self.background.y = self.y
        self.label.update_position(self.x + 5, self.y + self.height / 2)
        for idx, (bg, label) in enumerate(zip(self.option_backgrounds, self.option_labels)):
            bg.x = self.x
            bg.y = self.y - ((idx + 1) * self.option_height)
            # Обрезаем текст каждой опции
            truncated_option = self.truncate_text(self.options[idx], self.max_option_width)
            label.set_text(truncated_option)
            label.update_position(self.x + 5, bg.y + self.option_height / 2)

    def update_options(self):
        """Обновляет опции выпадающего списка."""
        # Удаляем существующие опции
        for bg in self.option_backgrounds:
            bg.delete()
        for label in self.option_labels:
            label.delete()
        self.option_backgrounds.clear()
        self.option_labels.clear()

        # Пересоздаем опции
        option_group_order = self.group.order + self.group_order_offset + 100
        for idx, option in enumerate(self.options):
            # Фон опции
            bg = shapes.Rectangle(
                self.x, self.y - ((idx + 1) * self.option_height),
                self.width, self.option_height,
                color=self.bg_color[:3],
                batch=self.batch,
                group=Group(order=option_group_order)
            )
            bg.opacity = 0  # Скрываем фон опции
            bg.visible = False
            self.option_backgrounds.append(bg)

            # Метка опции с обводкой и обрезкой текста
            truncated_option = self.truncate_text(option, self.max_option_width)
            option_label = Label(
                self.x + 5,
                bg.y + self.option_height / 2,
                truncated_option,
                font_size=self.font_size,
                color=self.color,
                anchor_x='left',
                anchor_y='center',
                batch=self.batch,
                group=Group(order=option_group_order + 2),
                outline=True,  # Обеспечиваем наличие обводки
                outline_color=(0, 0, 0, 255)
            )
            option_label.full_text = option  # Сохраняем полный текст для подсказки
            option_label.visible = False  # Изначально скрыты
            self.option_labels.append(option_label)

        # Добавляем вызов hide_options() после обновления опций
        self.hide_options()

    def truncate_text(self, text, max_width):
        """Обрезает текст, если он превышает максимальную ширину, и добавляет '...'."""
        temp_label = pyglet.text.Label(
            text,
            font_name='Arial',
            font_size=self.font_size
        )
        if temp_label.content_width <= max_width:
            return text
        else:
            while temp_label.content_width > max_width and len(text) > 0:
                text = text[:-1]
                temp_label.text = text + '...'
            return temp_label.text

    def on_mouse_motion(self, x, y, dx, dy):
        if self.expanded:
            hovered = False
            for label in self.option_labels:
                if label.visible and label.hit_test(x, y):
                    hovered = True
                    # Отображение подсказки с полным текстом
                    self.show_tooltip(label.full_text, x, y)
                    break
            if not hovered:
                self.hide_tooltip()
        else:
            self.hide_tooltip()

    def show_tooltip(self, text, x, y):
        """Отображает подсказку с полным текстом."""
        if self.tooltip_label is None:
            self.tooltip_label = Label(
                x + 10, y + 10,
                text,
                font_size=self.font_size,
                color=(255, 255, 255, 255),  # Белый цвет текста
                anchor_x='left',
                anchor_y='bottom',
                batch=self.batch,
                group=Group(order=self.group.order + 1000),
                outline=True,  # Обеспечиваем наличие обводки
                outline_color=(0, 0, 0, 255),
                interactive=False  # Добавлено: метка неинтерактивна
            )
        else:
            self.tooltip_label.set_text(text)
            self.tooltip_label.update_position(x + 10, y + 10)
            self.tooltip_label.visible = True

    def hide_tooltip(self):
        """Скрывает подсказку."""
        if self.tooltip_label is not None:
            self.tooltip_label.delete()
            self.tooltip_label = None

class VolumeIndicator(UIElement):
    """
    Индикатор громкости для отображения уровня звука с микрофона.
    """
    def __init__(self, x, y, width, height, max_value=1.0, batch=None, group=None):
        super().__init__(x - width / 2, y - height / 2, width, height, batch, group)
        self.max_value = max_value
        self.current_value = 0.0

        self.background = shapes.Rectangle(
            self.x, self.y, self.width, self.height,
            color=(50, 50, 50), batch=self.batch, group=self.group
        )

        self.foreground = shapes.Rectangle(
            self.x, self.y, 0, self.height,
            color=(0, 255, 0), batch=self.batch, group=self.group
        )

    def set_volume(self, value):
        """Обновляет значение громкости и ширину индикатора."""
        self.current_value = min(max(value, 0.0), self.max_value)
        self.foreground.width = (self.current_value / self.max_value) * self.width

    def update_position(self, x, y):
        dx = x - (self.x + self.width / 2)
        dy = y - (self.y + self.height / 2)
        self.x += dx
        self.y += dy
        self.background.x = self.x
        self.background.y = self.y
        self.foreground.x = self.x
        self.foreground.y = self.y

    def delete(self):
        """Удаляет индикатор и связанные с ним ресурсы."""
        self.background.delete()
        self.foreground.delete()
        super().delete()

    def draw(self):
        if self.visible:
            self.background.draw()
            self.foreground.draw()

class TopBar(UIElement):
    """
    Top bar with settings icon and current time.
    """
    def __init__(self,x, y, width, height, batch, group, game):
        super().__init__(x, y, width, height, batch, group)
        self.height = height
        self.game = game
        self.create_elements()
        self.tooltip_label = None
        self.ui_elements = [self.settings_button, self.time_label]

    def create_elements(self):
        # Settings button
        self.settings_button = Button(
            x=self.x + 30, y=self.y + 25, width=30, height=30,
            text='⚙', callback=self.on_settings_click,
            batch=self.batch, group=self.group
        )
        # Current time label (showing real time)
        self.time_label = Label(
            x=self.x + self.width - 200, y=self.y + 25,
            text='', font_size=14,
            anchor_x='left', anchor_y='center',
            batch=self.batch, group=self.group
        )
        self.background = shapes.Rectangle(
            x=self.x,
            y=self.y,
            width=self.width,
            height=self.height,
            color=(80, 80, 80),
            batch=self.batch,
            group=Group(order=self.group.order - 1)
        )

    def on_settings_click(self):
        # Open settings popup
        if self.game:
            self.game.show_display_settings_popup()

    def update_time(self, time_str):
        self.time_label.set_text(time_str)

    def on_mouse_motion(self, x, y, dx, dy):
        for element in self.ui_elements:
            element.on_mouse_motion(x, y, dx, dy)
        if self.settings_button.hit_test(x, y):
            self.show_tooltip(self.game.localization.get('topbar.settings_tooltip'), x, y)
        elif self.time_label.hit_test(x, y):
            self.show_tooltip(self.game.localization.get('topbar.time_tooltip'), x, y)
        else:
            self.hide_tooltip()
    
    def on_mouse_press(self, x, y, button, modifiers):
        for element in self.ui_elements:
            if element.on_mouse_press(x, y, button, modifiers):
                return True
        return False

    def on_mouse_release(self, x, y, button, modifiers):
        for element in self.ui_elements:
            if element.on_mouse_release(x, y, button, modifiers):
                return True
        return False

    def show_tooltip(self, text, x, y):
        if self.tooltip_label is None:
            self.tooltip_label = Label(
                x=x + 10, y=y - 10,  # Adjusted to appear below the cursor
                text=text, font_size=12,
                color=(255, 255, 255, 255),
                anchor_x='left', anchor_y='top',  # Adjusted anchor to 'top'
                batch=self.batch, group=Group(order=self.group.order + 10),
                outline=True, outline_color=(0, 0, 0, 255)
            )
        else:
            self.tooltip_label.set_text(text)
            self.tooltip_label.update_position(x + 10, y - 10)
            self.tooltip_label.visible = True

    def hide_tooltip(self):
        if self.tooltip_label is not None:
            self.tooltip_label.delete()
            self.tooltip_label = None
    
    def update_position(self, x, y):
        self.x = x
        self.y = y
        self.background.x = self.x
        self.background.y = self.y
        self.settings_button.update_position(self.x + 30, self.y + 25)
        self.time_label.update_position(self.x + self.width - 200, self.y + 25)

    def draw(self):
        if self.visible:
            self.settings_button.draw()
            self.time_label.draw()
            if self.tooltip_label and self.tooltip_label.visible:
                self.tooltip_label.draw()

class BottomBar(UIElement):
    """
    Bottom bar with navigation and additional function buttons.
    """
    def __init__(self, width, batch, group, game):
        super().__init__(0, 0, width, 50, batch, group)
        self.game = game
        self.create_elements()
        self.ui_elements = [self.back_button, self.mods_button, self.map_settings_button, self.start_button]

    def create_elements(self):
        # Back button
        self.back_button = Button(
            x=self.x + 60, y=self.y + 25, width=100, height=30,
            text=self.game.localization.get('bottom_bar.back'), callback=self.on_back_click,
            batch=self.batch, group=self.group
        )
        # Mods button
        self.mods_button = Button(
            x=self.x + 180, y=self.y + 25, width=100, height=30,
            text=self.game.localization.get('bottom_bar.mods'), callback=self.on_mods_click,
            batch=self.batch, group=self.group
        )
        # Map settings button
        self.map_settings_button = Button(
            x=self.x + 310, y=self.y + 25, width=170, height=30,
            text=self.game.localization.get('bottom_bar.map_settings'), callback=self.on_map_settings_click,
            batch=self.batch, group=self.group
        )
        # Start button
        self.start_button = Button(
            x=self.x + self.width - 100, y=self.y + 25, width=100, height=30,
            text=self.game.localization.get('bottom_bar.start'), callback=self.on_start_click,
            batch=self.batch, group=self.group
        )
        self.background = shapes.Rectangle(
            x=self.x,
            y=self.y,
            width=self.width,
            height=self.height,
            color=(0, 0, 0),
            batch=self.batch,
            group=Group(order=self.group.order - 1)
        )
        self.background.opacity = 150

    def on_back_click(self):
        if self.game and self.game.state_manager:
            self.game.state_manager.change_state('menu')

    def on_mods_click(self):
        if self.game:
            self.game.show_mods_popup()

    def on_map_settings_click(self):
        if self.game:
            self.game.show_map_settings_popup()

    def on_start_click(self):
        if self.game:
            self.game.start_game()

    def draw(self):
        if self.visible:
            for element in self.ui_elements:
                element.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        for element in self.ui_elements:
            if element.on_mouse_press(x, y, button, modifiers):
                return True
        return False

    def on_mouse_release(self, x, y, button, modifiers):
        for element in self.ui_elements:
            if element.on_mouse_release(x, y, button, modifiers):
                return True
        return False

    def on_mouse_motion(self, x, y, dx, dy):
        for element in self.ui_elements:
            element.on_mouse_motion(x, y, dx, dy)

    def update_position(self, x, y):
        self.x = x
        self.y = y
        # Update positions of buttons
        self.back_button.update_position(self.x + 60, self.y + 25)
        self.mods_button.update_position(self.x + 180, self.y + 25)
        self.map_settings_button.update_position(self.x + 300, self.y + 25)
        self.start_button.update_position(self.x + self.width - 100, self.y + 25)

class RoundedRectangleStencilGroup(pyglet.graphics.Group):
    def __init__(self, x, y, width, height, radius, parent=None):
        super().__init__(parent=parent)
        self.x = int(x)
        self.y = int(y)
        self.width = int(width)
        self.height = int(height)
        self.radius = int(radius)
    
    def set_state(self):
        # Enable stencil test
        glEnable(GL_STENCIL_TEST)
        glClear(GL_STENCIL_BUFFER_BIT)

        # Configure stencil buffer to write 1s where rendered
        glStencilFunc(GL_ALWAYS, 1, 0xFF)
        glStencilOp(GL_KEEP, GL_KEEP, GL_REPLACE)
        glStencilMask(0xFF)

        # Disable color and depth writing
        glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
        glDepthMask(GL_FALSE)

        # Draw the rounded rectangle mask into the stencil buffer
        self.draw_rounded_rectangle_mask()

        # Re-enable color and depth writing
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
        glDepthMask(GL_TRUE)

        # Configure stencil test to only render where stencil buffer equals 1
        glStencilFunc(GL_EQUAL, 1, 0xFF)
        glStencilMask(0x00)
        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)

    def unset_state(self):
        # Disable stencil test
        glDisable(GL_STENCIL_TEST)

    def draw_rounded_rectangle_mask(self):
        num_segments = 64  # Увеличьте для более сглаженных углов

        vertices = []
        indices = []
        idx = 0

        # Центральный прямоугольник (без углов)
        central_vertices = [
            self.x + self.radius, self.y, 0,                             # Нижний левый
            self.x + self.width - self.radius, self.y, 0,                # Нижний правый
            self.x + self.width - self.radius, self.y + self.height, 0,  # Верхний правый
            self.x + self.radius, self.y + self.height, 0                 # Верхний левый
        ]
        central_indices = [idx, idx + 1, idx + 2, idx, idx + 2, idx + 3]
        vertices.extend(central_vertices)
        indices.extend(central_indices)
        idx += 4

        # Левый прямоугольник
        left_vertices = [
            self.x, self.y + self.radius, 0,
            self.x + self.radius, self.y + self.radius, 0,
            self.x + self.radius, self.y + self.height - self.radius, 0,
            self.x, self.y + self.height - self.radius, 0
        ]
        left_indices = [idx, idx + 1, idx + 2, idx, idx + 2, idx + 3]
        vertices.extend(left_vertices)
        indices.extend(left_indices)
        idx += 4

        # Правый прямоугольник
        right_vertices = [
            self.x + self.width - self.radius, self.y + self.radius, 0,
            self.x + self.width, self.y + self.radius, 0,
            self.x + self.width, self.y + self.height - self.radius, 0,
            self.x + self.width - self.radius, self.y + self.height - self.radius, 0
        ]
        right_indices = [idx, idx + 1, idx + 2, idx, idx + 2, idx + 3]
        vertices.extend(right_vertices)
        indices.extend(right_indices)
        idx += 4

        # Функция для добавления угловых вершин и индексов
        def add_corner(idx, cx, cy, radius, start_angle, end_angle):
            corner_vertices = []
            num_corner_vertices = num_segments + 1  # Только внешние точки

            for i in range(num_corner_vertices):
                angle = start_angle + (end_angle - start_angle) * i / num_segments
                x = cx + radius * cos(angle)
                y = cy + radius * sin(angle)
                corner_vertices.extend([x, y, 0])

            # Добавляем центральную вершину в начале
            corner_vertices = [cx, cy, 0] + corner_vertices

            # Индексы для треугольного фанатона
            corner_indices = []
            for i in range(1, num_corner_vertices):
                corner_indices.extend([idx, idx + i, idx + i + 1])

            return corner_vertices, corner_indices

        # Нижний левый угол
        bl_v, bl_i = add_corner(
            idx,
            self.x + self.radius, self.y + self.radius, self.radius, pi, 1.5 * pi)
        vertices.extend(bl_v)
        indices.extend(bl_i)
        idx += len(bl_v) // 3

        # Нижний правый угол
        br_v, br_i = add_corner(
            idx,
            self.x + self.width - self.radius, self.y + self.radius, self.radius, 1.5 * pi, 2 * pi)
        vertices.extend(br_v)
        indices.extend(br_i)
        idx += len(br_v) // 3

        # Верхний правый угол
        tr_v, tr_i = add_corner(
            idx,
            self.x + self.width - self.radius, self.y + self.height - self.radius, self.radius, 0, 0.5 * pi)
        vertices.extend(tr_v)
        indices.extend(tr_i)
        idx += len(tr_v) // 3

        # Верхний левый угол
        tl_v, tl_i = add_corner(
            idx,
            self.x + self.radius, self.y + self.height - self.radius, self.radius, 0.5 * pi, pi)
        vertices.extend(tl_v)
        indices.extend(tl_i)
        idx += len(tl_v) // 3

        # Преобразуем индексы в список целых чисел
        indices = list(map(int, indices))

        pyglet.graphics.draw_indexed(
            len(vertices) // 3,  # Исправлено с len(vertices) на количество вершин
            GL_TRIANGLES,
            indices,
            position=('f', vertices)
        )
class SongInfoArea(UIElement):
    """
    Area to display detailed information about the selected song.
    """
    def __init__(self, x, y, width, height, batch, group, window):
        super().__init__(x, y, width, height, batch, group)
        self.window = window

        self.cover_sprite = None
        self.song_selected = False
        self.stencil_group = RoundedRectangleStencilGroup(x, y, width, height, 60, parent=self.group)
        
        self.create_elements()

    def create_elements(self):
        # Groups for layering
        glow_group = Group(order=self.group.order - 2)
        panel_group = Group(order=self.group.order - 1)
        text_group = Group(order=self.group.order + 4)

        # Glow effect using layered shapes
        self.glow_effect = []
        colors = [(255, 255, 255)] * 5
        opacities = [50, 40, 30, 20, 10]
        increments = [0, 5, 10, 15, 20]

        for i in range(5):
            rect = shapes.RoundedRectangle(
                self.x - 10 - increments[i], self.y - 10 - increments[i],
                self.width + 20 + increments[i] * 2, self.height + 20 + increments[i] * 2,
                radius=60 + increments[i],
                color=colors[i],
                batch=self.batch,
                group=glow_group
            )
            rect.opacity = opacities[i]
            self.glow_effect.append(rect)

        # Panel with rounded corners
        self.panel = shapes.RoundedRectangle(
            self.x, self.y, self.width, self.height,
            radius=60,
            color=(220, 220, 220),
            batch=self.batch, group=panel_group
        )

        # Text labels with enhanced readability
        self.title_label = Label(
            x=self.x + 20, y=self.y + self.height - 40,
            text='', font_size=24, color=(255, 255, 255, 255),  # White color
            anchor_x='left', anchor_y='top',
            batch=self.batch, group=text_group
        )
        self.artist_label = Label(
            x=self.x + 20, y=self.y + self.height - 70,
            text='', font_size=18, color=(230, 230, 230, 255),  # Light gray
            anchor_x='left', anchor_y='top',
            batch=self.batch, group=text_group
        )
        self.difficulty_label = Label(
            x=self.x + 20, y=self.y + self.height - 100,
            text='', font_size=16, color=(200, 200, 200, 255),  # Gray
            anchor_x='left', anchor_y='top',
            batch=self.batch, group=text_group
        )
        self.duration_label = Label(
            x=self.x + 20, y=self.y + self.height - 130,
            text='', font_size=16, color=(200, 200, 200, 255),  # Gray
            anchor_x='left', anchor_y='top',
            batch=self.batch, group=text_group
        )

    def display_song_info(self, song):
        if song and os.path.exists(song.cover_image):
            image = pyglet.image.load(song.cover_image)
            if self.cover_sprite:
                self.cover_sprite.delete()
            self.cover_sprite = pyglet.sprite.Sprite(
                img=image, x=self.x, y=self.y,
                batch=self.batch, group=self.stencil_group
            )

            # Scale the sprite to fill the area
            scale_x = self.width / image.width
            scale_y = self.height / image.height
            scale = max(scale_x, scale_y)
            self.cover_sprite.scale = scale

            # Center the sprite
            self.cover_sprite.x = self.x + (self.width - image.width * scale) / 2
            self.cover_sprite.y = self.y + (self.height - image.height * scale) / 2

            self.song_selected = True

        else:
            if self.cover_sprite:
                self.cover_sprite.delete()
                self.cover_sprite = None
            self.song_selected = False

        # Update text labels
        if song:
            self.title_label.set_text(song.name)
            self.artist_label.set_text(song.artist)
            self.difficulty_label.set_text(f"Сложность: {song.difficulty}")
            self.duration_label.set_text(f"Длительность: {self.format_duration(song.duration)}")
        else:
            # Clear labels if no song is selected
            self.title_label.set_text('')
            self.artist_label.set_text('')
            self.difficulty_label.set_text('')
            self.duration_label.set_text('')

    def format_duration(self, duration_sec):
        minutes = int(duration_sec // 60)
        seconds = int(duration_sec % 60)
        return f"{minutes:02}:{seconds:02}"

    def delete(self):
        if self.cover_sprite:
            self.cover_sprite.delete()
        for rect in self.glow_effect:
            rect.delete()
        self.panel.delete()
        if hasattr(self, 'mask_vertex_list'):
            self.mask_vertex_list.delete()
        self.title_label.delete()
        self.artist_label.delete()
        self.difficulty_label.delete()
        self.duration_label.delete()
        super().delete()

    def update_position(self, x, y):
        dx = x - self.x
        dy = y - self.y
        self.x = x
        self.y = y

        increments = [0, 5, 10, 15, 20]
        for i, rect in enumerate(self.glow_effect):
            rect.position = (x - 10 - increments[i], y - 10 - increments[i])

        self.panel.position = (x, y)
        self.title_label.update_position(x + 20, y + self.height - 40)
        self.artist_label.update_position(x + 20, y + self.height - 70)
        self.difficulty_label.update_position(x + 20, y + self.height - 100)
        self.duration_label.update_position(x + 20, y + self.height - 130)

        if self.cover_sprite:
            scale = self.cover_sprite.scale
            self.cover_sprite.x = x + (self.width - self.cover_sprite.width) / 2
            self.cover_sprite.y = y + (self.height - self.cover_sprite.height) / 2

    def draw(self):
        if not self.visible:
            return

        # Draw glow effect (if needed)
        for rect in self.glow_effect:
            rect.draw()

        self.panel.draw()

        if self.cover_sprite:
            self.cover_sprite.draw()

        # Draw text labels
        self.title_label.draw()
        self.artist_label.draw()
        self.difficulty_label.draw()
        self.duration_label.draw()

class Checkbox(UIElement):
    """
    Простой элемент чекбокса.
    """
    def __init__(self, x, y, checked=False, callback=None, batch=None, group=None):
        super().__init__(x, y, width=20, height=20, batch=batch, group=group)
        self.checked = checked
        self.callback = callback

        # Рамка чекбокса
        self.box = shapes.Rectangle(
            x=self.x, y=self.y, width=self.width, height=self.height,
            color=(200, 200, 200), batch=self.batch, group=self.group
        )
        self.box.opacity = 255

        # Галочка
        self.checkmark = pyglet.sprite.Sprite(
            img=self.create_checkmark_image(),
            x=self.x, y=self.y,
            batch=self.batch, group=Group(order=self.group.order + 1)
        )
        self.checkmark.visible = self.checked

    def create_checkmark_image(self):
        # Создаем изображение галочки
        checkmark_img = pyglet.image.SolidColorImagePattern((0, 0, 0, 255)).create_image(20, 20)
        checkmark_img_data = checkmark_img.get_image_data()
        pixels = checkmark_img_data.get_data('RGBA', checkmark_img_data.width * 4)
        # Здесь можно добавить код для рисования галочки на пиксельном уровне
        return checkmark_img

    def on_mouse_press(self, x, y, button, modifiers):
        if self.visible and self.hit_test(x, y):
            self.checked = not self.checked
            self.checkmark.visible = self.checked
            if self.callback:
                self.callback(self.checked)
            return True
        return False

    def draw(self):
        if self.visible:
            self.box.draw()
            if self.checked:
                self.checkmark.draw()

    def delete(self):
        self.box.delete()
        self.checkmark.delete()
        super().delete()

    def update_position(self, x, y):
        dx = x - self.x
        dy = y - self.y
        self.x = x
        self.y = y
        self.box.x = self.x
        self.box.y = self.y
        self.checkmark.update(x=self.x, y=self.y)
import pyglet
from pyglet.gl import GL_TRIANGLES

class TriangleBackground(UIElement):
    def __init__(self, x, y, width, height, batch, group):
        super().__init__(x, y, width=width, height=height, batch=batch, group=group)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.batch = batch
        self.group = group
        self.vertex_list = None
        self.create_triangle()

    def create_triangle(self):
        if self.vertex_list:
            self.vertex_list.delete()

        # Define vertices for the triangle
        vertices = [
            self.x, self.y, 0,
            self.x, self.y + self.height, 0,
            self.x + self.width * 0.3, self.y + self.height, 0,
        ]

        # Define indices for the triangle
        indices = [0, 1, 2]

        pyglet.graphics.draw_indexed(
            len(vertices) // 3,
            GL_TRIANGLES,
            indices,
            position=('f', vertices)
        )

    def update_size(self, width, height):
        self.width = width
        self.height = height
        self.create_triangle()

    def delete(self):
        if self.vertex_list:
            self.vertex_list.delete()
        super().delete()
    
    def draw(self):
        """
        Метод draw не нужно реализовывать явно, так как отрисовка 
        происходит через vertex_list в batch
        """
        pass

from pyglet import shapes

class SongItem(UIElement):
    """
    Represents a song item in the song carousel.
    """

    def __init__(self, song, index, x, y, width, height, batch, group, on_select, game, song_spacing):
        super().__init__(x, y, width, height, batch, group)
        self.song = song
        self.index = index
        self.on_select = on_select
        self.game = game
        self.song_spacing = song_spacing

        # Visual elements
        self.cover_sprite = None

        # Parameters
        self.base_width = width
        self.base_height = 100  # Base height for song items
        self.scale = 1.0
        self.opacity = 255
        self.position_x = x
        self.position_y = y

        # Interaction states
        self.is_hovered = False
        self.is_selected = False

        # For smooth transitions
        self.target_scale = 1.0
        self.current_scale = 1.0
        self.target_opacity = 255
        self.current_opacity = 255

        self.create_visual_elements()

    def create_cropped_texture(self, image, target_width, target_height):
        # Calculate the aspect ratios
        image_ratio = image.width / image.height
        target_ratio = target_width / target_height

        if image_ratio > target_ratio:
            # Image is wider than the target; crop the sides
            new_height = image.height
            new_width = int(new_height * target_ratio)
            offset_x = (image.width - new_width) // 2
            offset_y = 0
        else:
            # Image is taller than the target; crop the top and bottom
            new_width = image.width
            new_height = int(new_width / target_ratio)
            offset_x = 0
            offset_y = (image.height - new_height) // 2

        # Create a region of the image with the new dimensions
        region = image.get_region(x=offset_x, y=offset_y, width=new_width, height=new_height)

        # Return the texture from the region
        return region.get_texture()

    def create_visual_elements(self):
        # Load cover image
        if self.song.cover_image and os.path.exists(self.song.cover_image):
            image = pyglet.image.load(self.song.cover_image)
        else:
            # Placeholder image
            image = pyglet.image.SolidColorImagePattern(color=(100, 100, 100, 255)).create_image(200, 200)

        # Create a texture region that covers the item area without distortion
        self.cover_texture = self.create_cropped_texture(image, self.base_width, self.base_height)

        # Create a sprite using the cropped texture
        self.cover_sprite = RoundedRectangleSprite(
            x=self.position_x,
            y=self.position_y - (self.base_height / 2),
            width=self.base_width,
            height=self.base_height,
            radius=10,
            texture=self.cover_texture,
            batch=self.batch,
            group=self.group
        )

        # Highlight rectangle
        self.highlight = shapes.RoundedRectangle(
            x=self.position_x,
            y=self.position_y - (self.base_height / 2),
            width=self.base_width,
            height=self.base_height,
            radius=10,  # Match the radius of the cover
            color=(255, 255, 255),
            batch=self.batch,
            group=Group(order=self.group.order + 1)
        )
        self.highlight.opacity = 0  # Start with transparent highlight

        # Title and artist labels
        self.title_label = Label(
            x=self.position_x + 10,
            y=self.position_y + self.base_height / 2 - 30,
            text=self.song.name,
            font_size=14,
            color=(255, 255, 255, 255),
            anchor_x='left',
            anchor_y='center',
            batch=self.batch,
            group=Group(order=self.group.order + 2)
        )
        self.artist_label = Label(
            x=self.position_x + 10,
            y=self.position_y - self.base_height / 2 + 20,
            text=self.song.artist,
            font_size=12,
            color=(200, 200, 200, 255),
            anchor_x='left',
            anchor_y='center',
            batch=self.batch,
            group=Group(order=self.group.order + 2)
        )

    def update(self, dt, scroll_offset, selected_index, hovered_index):
        window_height = self.game.window.height
        center_y = window_height / 2  # Center of the window

        # Update position relative to the center of the window
        self.position_y = center_y + ((self.index - selected_index) * self.song_spacing) - scroll_offset


        # Calculate scale based on distance from center
        distance = abs(self.position_y - center_y)
        max_distance = window_height / 2
        t = max(0.0, 1.0 - (distance / max_distance))
        self.target_scale = 0.8 + 0.2 * ease_out_quad(t)  # Scale between 0.8 and 1.0

        # Smoothly interpolate scale
        self.current_scale += (self.target_scale - self.current_scale) * dt * 10

        # Update size and position
        scaled_width = self.base_width * self.current_scale
        scaled_height = self.base_height * self.current_scale

        # Position X so that items align to the right edge
        window_width = self.game.window.width
        self.position_x = window_width - scaled_width

        # Update the position and size
        self.cover_sprite.update_position(
        x=self.position_x,
        y=self.position_y - (scaled_height / 2),
        width=scaled_width,
        height=scaled_height
    )

        # Update highlight rectangle
        self.highlight.x = self.cover_sprite.x
        self.highlight.y = self.cover_sprite.y
        self.highlight.width = scaled_width
        self.highlight.height = scaled_height
        self.highlight.radius = self.cover_sprite.radius

        # Update labels
        self.title_label.update_position(
            self.cover_sprite.x + 10,
            self.cover_sprite.y + scaled_height - 30
        )
        self.artist_label.update_position(
            self.cover_sprite.x + 10,
            self.cover_sprite.y + 20
        )

        # Update selection and hover states
        self.is_selected = (self.index == selected_index)
        self.is_hovered = (self.index == hovered_index)

        # Update opacity for highlight
        if self.is_selected:
            self.target_opacity = 150
        elif self.is_hovered:
            self.target_opacity = 100
        else:
            self.target_opacity = 0

        # Smoothly transition highlight opacity
        self.current_opacity += (self.target_opacity - self.current_opacity) * dt * 10
        self.highlight.opacity = int(self.current_opacity)

    def draw(self):
        if not self.visible:
            return
        self.cover_sprite.draw()
        self.highlight.draw()
        self.title_label.draw()
        self.artist_label.draw()

    def hit_test(self, x, y):
        scaled_width = self.base_width * self.current_scale
        scaled_height = self.base_height * self.current_scale
        return (self.cover_sprite.x <= x <= self.cover_sprite.x + scaled_width and
                self.cover_sprite.y <= y <= self.cover_sprite.y + scaled_height)

    def update_size(self, width, height):
        self.width = width
        self.base_width = width
        self.height = height

    def delete(self):
        # Delete graphical elements
        self.cover_sprite.delete()
        self.highlight.delete()
        self.title_label.delete()
        self.artist_label.delete()
        super().delete()

class SongCarousel(UIElement):
    """
    Scrollable carousel of songs with advanced features.
    """

    def __init__(self, songs, x, y, width, height, batch, group, on_song_select, game):
        super().__init__(x, y, width, height, batch, group)
        self.game = game
        self.all_songs = songs
        self.on_song_select = on_song_select
        self.center_index = 0
        self.target_center_index = 0
        self.scroll_offset = 0.0
        self.target_scroll_offset = 0.0
        self.momentum = 0.0
        self.is_dragging = False
        self.drag_start_y = 0.0
        self.drag_start_time = 0.0
        self.hovered_song_index = None
        self.selected_song_index = 0
        self.visible_songs = []
        self.song_items = []
        self.ui_elements = []

        # Parameters
        self.song_spacing = 115  # Space between songs vertically
        self.deceleration_rate = 0.98  # Rate at which momentum decreases
        self.momentum_multiplier = 0.03  # Speed control
        self.elastic_factor = 0.2  # How "stretchy" the over-scroll is
        self.max_over_scroll = 100  # Max pixels to over-scroll

        # Drawing order
        self.background_group = Group(order=self.group.order)
        self.items_group = Group(order=self.group.order + 1)
        self.foreground_group = Group(order=self.group.order + 2)

        # Remove vertical padding
        self.vertical_padding = 0  # Remove padding to use full height
        self.visible_area_start = self.y + self.vertical_padding
        self.visible_area_height = self.height - (self.vertical_padding * 2)

        # Parameters for click vs drag detection
        self.click_threshold = 5  # Maximum distance for click
        self.initial_click_pos = None  # Initial click position

        self.create_song_items()

    def create_song_items(self):
        """Creates SongItem instances for all songs."""
        self.song_items.clear()
        for idx, song in enumerate(self.all_songs):
            item = SongItem(
                song=song,
                index=idx,
                x=self.x,
                y=self.y,
                width=self.width,
                height=self.height,
                batch=self.batch,
                group=self.items_group,
                on_select=self.on_song_select_wrapper,
                game=self.game,
                song_spacing=self.song_spacing
            )
            self.song_items.append(item)

    def on_song_select_wrapper(self, song, index):
        self.selected_song_index = index
        self.target_center_index = index
        self.on_song_select(song)

    def on_mouse_press(self, x, y, button, modifiers):
        if not self.hit_test(x, y):
            return False

        if button == pyglet.window.mouse.LEFT:
            self.is_dragging = True
            self.drag_start_y = y
            self.drag_start_time = time.time()
            self.momentum = 0.0
            self.initial_click_pos = (x, y)
            return True
        return False

    def on_mouse_release(self, x, y, button, modifiers):
        if not self.is_dragging:
            return False

        self.is_dragging = False
        drag_duration = time.time() - self.drag_start_time

        if self.initial_click_pos:
            drag_distance = abs(y - self.initial_click_pos[1])

            if drag_distance < self.click_threshold and drag_duration < 0.2:
                for item in self.song_items:
                    if item.hit_test(*self.initial_click_pos):
                        self.on_song_select_wrapper(item.song, item.index)
                        self.initial_click_pos = None
                        return True

        if drag_duration > 0:
            self.momentum = -((y - self.drag_start_y) / drag_duration) * self.momentum_multiplier

        self.initial_click_pos = None
        return True

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if not self.is_dragging:
            return False

        if self.initial_click_pos:
            drag_distance = abs(y - self.initial_click_pos[1])
            if drag_distance >= self.click_threshold:
                self.initial_click_pos = None

        self.scroll_offset -= dy
        self.target_scroll_offset = self.scroll_offset
        return True

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.hit_test(x, y):
            self.scroll_offset -= scroll_y * 20  # Adjust scroll speed
            return True
        return False

    def on_mouse_motion(self, x, y, dx, dy):
        # Update hovered song index
        self.hovered_song_index = None
        for item in self.song_items:
            if item.hit_test(x, y):
                self.hovered_song_index = item.index
                break

    def update(self, dt):
        """Updates positions, handles momentum and animations."""
        # Apply momentum if not dragging
        if not self.is_dragging and abs(self.momentum) > 0.1:
            self.scroll_offset += self.momentum
            self.target_scroll_offset = self.scroll_offset
            self.momentum *= self.deceleration_rate
        else:
            self.momentum = 0.0

        # Check scroll boundaries
        max_offset = self.song_spacing * (len(self.all_songs) - 1)

        # Smoothly return if out of bounds
        if self.scroll_offset < 0:
            self.target_scroll_offset = 0
            self.scroll_offset += (self.target_scroll_offset - self.scroll_offset) * dt * 5
            self.momentum = 0
        elif self.scroll_offset > max_offset:
            self.target_scroll_offset = max_offset
            self.scroll_offset += (self.target_scroll_offset - self.scroll_offset) * dt * 5
            self.momentum = 0

        # Update song items
        for item in self.song_items:
            item.update(dt, self.scroll_offset, self.selected_song_index, self.hovered_song_index)

    def draw(self):
        if not self.visible:
            return

        window = self.game.window
        scale_factor = window.get_viewport_size()[1] / window.get_size()[1]  # Use height for scale

        # Adjust scissor area
        scissor_x = int(self.x * scale_factor)
        scissor_y = int(self.visible_area_start * scale_factor)
        scissor_width = int(self.width * scale_factor)
        scissor_height = int(self.visible_area_height * scale_factor)

        glEnable(GL_SCISSOR_TEST)
        glScissor(scissor_x, scissor_y, scissor_width, scissor_height)

        for item in self.song_items:
            item.draw()

        glDisable(GL_SCISSOR_TEST)

    def update_size(self, width, height):
        self.width = width
        self.height = height
        for item in self.song_items:
            item.update_size(width, height)

    def hit_test(self, x, y):
        # Ensure it covers the entire component area
        return (self.x <= x <= self.x + self.width and
                self.y <= y <= self.y + self.height)

import pyglet
from pyglet.gl import *
from pyglet import shapes

class RoundedRectangleSprite:
    def __init__(self, x, y, width, height, radius, texture, batch, group):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.radius = radius
        self.texture = texture
        self.batch = batch
        self.group = group

        # Create the sprite using the texture
        self.sprite = pyglet.sprite.Sprite(
            img=self.texture,
            x=self.x,
            y=self.y,
            batch=self.batch,
            group=self.group
        )

        # Scale the sprite to match the item dimensions
        self.sprite.scale_x = self.width / self.texture.width
        self.sprite.scale_y = self.height / self.texture.height

        # Adjust the sprite's position if needed
        self.sprite.x = self.x
        self.sprite.y = self.y

    def draw(self):
        # Use stencil buffer to create rounded corners
        glEnable(GL_STENCIL_TEST)
        glClear(GL_STENCIL_BUFFER_BIT)

        # Configure stencil function to draw the rounded rectangle mask
        glStencilFunc(GL_ALWAYS, 1, 0xFF)
        glStencilOp(GL_KEEP, GL_KEEP, GL_REPLACE)

        # Disable color writing
        glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
        glDepthMask(GL_FALSE)

        # Draw the rounded rectangle into the stencil buffer
        stencil_rect = shapes.RoundedRectangle(
            x=self.x,
            y=self.y,
            width=self.width,
            height=self.height,
            radius=self.radius,
            color=(0, 0, 0)
        )
        stencil_rect.draw()

        # Re-enable color writing
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
        glDepthMask(GL_TRUE)

        # Configure stencil to only draw where the stencil buffer equals 1
        glStencilFunc(GL_EQUAL, 1, 0xFF)
        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)

        # Draw the sprite
        self.sprite.draw()

        # Disable stencil testing
        glDisable(GL_STENCIL_TEST)
    def update_position(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        # Update sprite scaling
        self.sprite.scale_x = self.width / self.texture.width
        self.sprite.scale_y = self.height / self.texture.height

        # Update sprite position
        self.sprite.x = self.x
        self.sprite.y = self.y

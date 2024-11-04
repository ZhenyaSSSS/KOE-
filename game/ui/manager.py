# game/ui/manager.py

import pyglet
from .elements import Dropdown

class UIManager:
    """
    Менеджер для управления элементами пользовательского интерфейса.
    Обрабатывает отрисовку, обновление и события для UI-элементов.
    """

    def __init__(self):
        self.layers = {}
        self.elements = []
        self.modal_elements = []
        self.batch = pyglet.graphics.Batch()
        self.default_group = pyglet.graphics.Group(order=10)  # Изменено на Group с параметром order
        self.dropdown_elements = []  # Добавляем список для Dropdown
        self.batch.ui_manager = self  # Устанавливаем ссылку на UIManager в Batch

    def add(self, element, layer=0, modal=False):
        """
        Добавляет элемент интерфейса.
        """
        # Убедимся, что у элемента есть group и batch
        if element.group is None:
            element.group = pyglet.graphics.Group(order=layer + self.default_group.order)  # Изменено на Group с параметром order
        if element.batch is None:
            element.batch = self.batch

        if modal:
            self.modal_elements.append(element)
        else:
            self.elements.append(element)
            if isinstance(element, Dropdown):
                self.dropdown_elements.append(element)  # Добавляем Dropdown в отдельный список
        self.layers.setdefault(layer, []).append(element)

    def remove(self, element):
        """Удаляет элемент интерфейса."""
        try:
            # Удаление из основного списка элементов
            if element in self.elements:
                self.elements.remove(element)
            elif element in self.modal_elements:
                self.modal_elements.remove(element)

            # Удаление из слоя
            for layer_elements in self.layers.values():
                if element in layer_elements:
                    layer_elements.remove(element)

            # Удаление из списка dropdown элементов
            if isinstance(element, Dropdown):
                if element in self.dropdown_elements:
                    self.dropdown_elements.remove(element)

            # Удаление самого элемента
            if hasattr(element, 'delete'):
                element.delete()
        except Exception as e:
            self.logger.exception(f"Ошибка при удалении UI элемента: {e}")

    def clear(self):
        """Очищает все элементы интерфейса."""
        try:
            # Создаем копии списков для безопасного удаления
            elements_to_remove = self.elements[:] + self.modal_elements[:]
            
            # Удаляем каждый элемент
            for element in elements_to_remove:
                self.remove(element)

            # Очищаем все списки
            self.elements.clear()
            self.modal_elements.clear()
            self.layers.clear()
            self.dropdown_elements.clear()
        except Exception as e:
            self.logger.exception(f"Ошибка при очистке UI элементов: {e}")

    def update(self, dt):
        """Обновляет все элементы интерфейса."""
        for element in self.elements + self.modal_elements:
            element.update(dt)

    def close_all_dropdowns(self, except_dropdown=None):
        """Закрывает все открытые выпадающие списки, кроме указанного."""
        for dropdown in self.dropdown_elements:
            if dropdown != except_dropdown and dropdown.expanded:
                dropdown.hide_options()

    def dispatch_event(self, event_name, *args, **kwargs):
        event_handled = False
        # First, process modal elements
        for element in reversed(self.modal_elements):
            if element.visible:
                if self._dispatch_to_element(element, event_name, *args, **kwargs):
                    if event_name != 'on_mouse_motion':
                        return True
                    else:
                        event_handled = True
        # Then, process other elements by layers
        for layer in sorted(self.layers.keys(), reverse=True):
            for element in reversed(self.layers[layer]):
                if element.visible:
                    if self._dispatch_to_element(element, event_name, *args, **kwargs):
                        if event_name != 'on_mouse_motion':
                            return True
                        else:
                            event_handled = True
        return event_handled

    def _dispatch_to_element(self, element, event_name, *args, **kwargs):
        # Dispatch event to element and its children
        handler = getattr(element, event_name, None)
        if callable(handler):
            if handler(*args, **kwargs):
                return True
        for child in getattr(element, 'ui_elements', []):
            if self._dispatch_to_element(child, event_name, *args, **kwargs):
                return True
        return False

    def draw(self):
        """Отрисовывает все элементы интерфейса."""
        self.batch.draw()

    # Методы обработки событий
    def on_mouse_press(self, x, y, button, modifiers):
        return self.dispatch_event('on_mouse_press', x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        return self.dispatch_event('on_mouse_release', x, y, button, modifiers)

    def on_mouse_motion(self, x, y, dx, dy):
        self.dispatch_event('on_mouse_motion', x, y, dx, dy)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        return self.dispatch_event('on_mouse_drag', x, y, dx, dy, buttons, modifiers)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        return self.dispatch_event('on_mouse_scroll', x, y, scroll_x, scroll_y)

    def on_text(self, text):
        self.dispatch_event('on_text', text)

    def on_text_motion(self, motion):
        self.dispatch_event('on_text_motion', motion)

    def on_key_press(self, symbol, modifiers):
        return self.dispatch_event('on_key_press', symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        return self.dispatch_event('on_key_release', symbol, modifiers)

    def reinitialize(self):
        """Переинициализирует Batch и все UI-элементы."""
        self.logger.info("Переинициализация UIManager.")
        # Закрытие всех выпадающих списков, если они открыты
        self.close_all_dropdowns()
        
        # Очистка существующих элементов
        self.clear()
        
        # Переинициализация Batch и Group
        self.batch = pyglet.graphics.Batch()
        self.default_group = pyglet.graphics.Group(order=10)
        


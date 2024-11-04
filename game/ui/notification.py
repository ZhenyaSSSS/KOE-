# game/ui/notification.py

import pyglet
import time
from ui.elements import UIElement

class Notification(UIElement):
    """
    Класс для отображения всплывающих уведомлений.
    """
    def __init__(self, text, duration=3.0, font_size=16, color=(255, 255, 255, 255),
                 background_color=(0, 0, 0, 200), batch=None, group=None, window=None):
        super().__init__(0, 0, 0, 0, batch, group)
        self.window = window
        self.text = text
        self.duration = duration
        self.start_time = time.time()
        self.font_size = font_size
        self.color = color
        self.background_color = background_color

        self.label = pyglet.text.Label(
            self.text,
            font_name='Arial',
            font_size=self.font_size,
            color=self.color,
            x=0, y=0,
            anchor_x='center',
            anchor_y='center',
            batch=self.batch,
            group=pyglet.graphics.Group(self.group.order + 1)
        )

        self.background = pyglet.shapes.Rectangle(
            0, 0, 0, 0,
            color=self.background_color[:3],
            batch=self.batch,
            group=self.group
        )
        self.opacity = self.background_color[3]
        self.update_layout()

    def update_layout(self):
        """Обновляет позицию и размер уведомления."""
        window = self.window  # Используем переданное окно
        self.label.x = window.width / 2
        self.label.y = window.height - 100
        padding = 10
        text_width = self.label.content_width + padding * 2
        text_height = self.label.content_height + padding * 2
        self.background.x = self.label.x - text_width / 2
        self.background.y = self.label.y - text_height / 2
        self.background.width = text_width
        self.background.height = text_height

    def update(self, dt):
        """Обновляет состояние уведомления (анимация исчезновения)."""
        elapsed = time.time() - self.start_time
        if elapsed >= self.duration:
            self.visible = False
        elif elapsed >= self.duration - 1.0:
            fade = 1.0 - (elapsed - (self.duration - 1.0))
            alpha = int(self.opacity * fade)
            self.label.color = (*self.color[:3], alpha)
            self.background.opacity = alpha

    def draw(self):
        if self.visible:
            self.background.draw()
            self.label.draw()

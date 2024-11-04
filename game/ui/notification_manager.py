# game/ui/notification_manager.py

import pyglet
from ui.notification import Notification

class NotificationManager:
    """
    Класс для управления отображением уведомлений.
    """
    def __init__(self, window):
        self.window = window
        self.notifications = []
        self.batch = pyglet.graphics.Batch()
        self.group = pyglet.graphics.Group(10)  # Высокий приоритет отрисовки

    def add_notification(self, text, duration=3.0, color=(255, 255, 255, 255),
                         background_color=(0, 0, 0, 200)):
        notification = Notification(
            text, duration, font_size=16, color=color,
            background_color=background_color,
            batch=self.batch, group=self.group,
            window=self.window
        )
        self.notifications.insert(0, notification)  # Добавляем в начало списка
        self.update_positions()

    def update_positions(self):
        """Обновляет позиции уведомлений для предотвращения наложения."""
        y_offset = 100
        for notification in reversed(self.notifications):
            notification.label.y = self.window.height - y_offset
            notification.update_layout()
            y_offset += notification.background.height + 10


    def update(self, dt):
        """Обновляет уведомления и удаляет завершенные."""
        for notification in self.notifications[:]:
            notification.update(dt)
            if not notification.visible:
                self.notifications.remove(notification)
                self.update_positions()

    def draw(self):
        """Отрисовывает уведомления."""
        self.batch.draw()

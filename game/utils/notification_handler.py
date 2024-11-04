# game/utils/notification_handler.py

import logging

class NotificationHandler(logging.Handler):
    """
    Обработчик логов, отправляющий сообщения в NotificationManager.
    """
    def __init__(self, notification_manager):
        super().__init__()
        self.notification_manager = notification_manager

    def emit(self, record):
        level = record.levelno
        if level >= logging.ERROR:
            color = (255, 50, 50, 255)  # Красный для ошибок
        elif level >= logging.WARNING:
            color = (255, 165, 0, 255)  # Оранжевый для предупреждений
        else:
            color = (255, 255, 255, 255)  # Белый для информации
        message = self.format(record)
        self.notification_manager.add_notification(message, color=color)

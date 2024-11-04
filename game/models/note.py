# game/models/note.py

class Note:
    """
    Класс для представления музыкальной ноты.
    """

    def __init__(self, start_time, duration, pitch):
        self.start_time = start_time
        self.duration = duration
        self.pitch = pitch

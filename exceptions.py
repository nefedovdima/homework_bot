"""Пользовательские исключения."""


class CheckTokensError(Exception):
    """Ошибка при проверке токенов."""


class GetApiAnswerError(Exception):
    """Неверный ответ API."""


class IncorrectHomeworkStatus(Exception):
    """Неккорректный статус ДЗ."""

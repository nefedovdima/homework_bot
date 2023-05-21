"""Пользовательские исключения."""


class CheckTokensError(Exception):
    """Ошибка при проверке токенов."""


class GetApiAnswerError(Exception):
    """Неверный ответ API."""


class IncorrectHomeworkStatus(Exception):
    """Неккорректный статус ДЗ."""


class WrongStatusCodeError(Exception):
    """Код ответа отличен от 200."""

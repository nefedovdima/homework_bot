import os
import logging
import time
import sys
import requests
import telegram
from exceptions import (CheckTokensError,
                        IncorrectHomeworkStatus)
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет существование токенов."""
    if not (PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
        logging.critical('CheckTokensError: Отсутствие '
                         'обязательных переменных окружения')
        raise CheckTokensError('Отсутствие обязательных переменных окружения')
    logging.debug('Проверка токенов прошла успешно')


def send_message(bot, message):
    """Отправляет сообщение в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Сообщение в Telegram отправлено')
    except Exception:
        logging.error('SendMessageError: '
                      'Сбой при отправке сообщения в Telegram')


def get_api_answer(timestamp):
    """Получает ответ API по временной метке."""
    payload = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(ENDPOINT,
                                         headers=HEADERS,
                                         params=payload)
        if homework_statuses.status_code != 200:
            logging.error(f'При обращении к '
                          f'API получен код отличный от 200. '
                          f'Ваш код: {homework_statuses.status_code}')
            raise Exception(f'При обращении к API '
                            f'получен код отличный от 200. '
                            f'получен код отличный от 200. '
                            f'Ваш код: {homework_statuses.status_code}')

        logging.debug('Успешное обращение к эндпоинту')
        return homework_statuses.json()
    except requests.RequestException:
        logging.error('Недоступность эндпоинта '
                      'или другие ошибки при запросе к эндпоинту')


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        logging.error('Ответ API не соответствует документации: ответ API'
                      'приходит не в виде словаря')
        send_message(telegram.Bot(token=TELEGRAM_TOKEN),
                     'TypeError: Ответ API не соответствует документации:'
                     ' ответ API приходит не в виде словаря')
        raise TypeError('Ответ API не соответствует документации: ответ API'
                        'приходит не в виде словаря')
    if 'homeworks' not in response:
        logging.error(f'Ответ API не соответствует документации: '
                      f'в ответе API нет ключа "homeworks": '
                      f' {response}')
        raise TypeError('Ответ API не соответствует документации: '
                        'в ответе API нет ключа "homeworks"')
    if not isinstance(response['homeworks'], list):
        logging.error('Ответ API не соответствует документации: '
                      'в ответе API домашки под ключом "homeworks" '
                      'данные приходят не в виде списка')
        raise TypeError('Ответ API не соответствует документации: '
                        'в ответе API домашки под ключом "homeworks" '
                        'данные приходят не в виде списка')
    logging.debug('Проверка соответствия '
                  'ответа API документации выполнена успешно')


def parse_status(homework: dict):
    """Проверяет корректность статуса работы."""
    status = homework.get('status')
    if status in HOMEWORK_VERDICTS:
        try:
            homework_name = homework['homework_name']
        except KeyError:
            logging.error('KeyError: в ответе API'
                          ' домашки нет ключа homework_name')
        verdict = HOMEWORK_VERDICTS[status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    logging.error('Некорректный статус домашней работы')
    send_message(telegram.Bot(token=TELEGRAM_TOKEN),
                 'IncorrectHomeworkStatus: '
                 'Некорректный статус работы')
    raise IncorrectHomeworkStatus('Некорректный статус работы')


def main():
    """Запсукает работу бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    from_date = timestamp - RETRY_PERIOD
    while True:
        try:
            response = get_api_answer(from_date)
            check_response(response)
            homeworks = response['homeworks']
            if homeworks:
                homework = homeworks[0]
                status = parse_status(homework)
                send_message(bot, status)
            else:
                logging.debug('Статус дз не обновился')
            from_date = response['current_date']
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()

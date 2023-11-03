import logging
import traceback
import datetime
from bot.main import bot, develop_chat_id
from decouple import config  # позволяет скрывать критическую информацию (пароли, логины, ip)
from logging import StreamHandler, Handler, LogRecord

trigger_list = ['ERROR', 'WARNING', 'CRITICAL']
TOKEN = config("TEST_CREW_BOT_TOKEN", default='')
chat_id = config("DEVELOP_CHAT_ID", default='')


class LoggerNameFilter(logging.Filter):
    def __init__(self, logger_name):
        super().__init__()
        self.logger_name = logger_name

    def filter(self, record):
        return record.name == self.logger_name


class TelegramMsgLog(StreamHandler):

    def emit(self, record: LogRecord):
        try:
            message = f'{(record.levelname.upper())}:\n\n{record.message}'
                  # f'FileName: {record.pathname}\nFunc.: {record.funcName}\n' \
                  # f'StringNo: {record.lineno}\nName: {record.name}'
        except AttributeError:
            print('record:', record)
            print('MSG:', record.msg)
            # print('Info:', traceback.print_last())
            message = f'{(record.levelname.upper())}:\n\n' \
                      f'Нет сообщения\n' \
                      f'Смотреть в логах\n\n' \
                      f'<b>{record.name}</b>\n\n' \
                      f'<b>{datetime.datetime.now()}</b>'

        bot.send_message(chat_id=chat_id, text=message)



#from aiogram.fsm.storage.memory import MemoryStorage
from decouple import config  # позволяет скрывать критическую информацию (пароли, логины, ip)
#from aiogram import Bot, Dispatcher
import telebot  # библиотека работы с телеграм


#fsm_storage = MemoryStorage()  # Хранилище состояний
crewbot_token = config("TEST_CREW_BOT_TOKEN", default='')
develop_chat_id = config("DEVELOP_CHAT_ID", default='')

#dp = Dispatcher(storage=fsm_storage)
#bot = Bot(crewbot_token, parse_mode='html')
bot = telebot.TeleBot(crewbot_token, parse_mode='html')
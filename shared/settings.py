# if you want to use this settings, please include "overall" requirements.txt in your subproject
# it can be done by adding "-r ../shared/requirements/overall.txt" line to your requirements.txt

# don't forget to add shared requirements.txt to your Docker container!
from pathlib import Path

from dotenv import load_dotenv
from envparse import env

load_dotenv(env('DOTENV_FILE', default=None))

BASE_DIR = Path(__file__).resolve().parent.parent

ENVIRONMENT = env('ENVIRONMENT', default="local")

TELEGRAM_TOKEN = env('TELEGRAM_TOKEN', default="")

# postgresql
PG_USERNAME = env('POSTGRES_USER', default='hobrus')
PG_PASSWORD = env('POSTGRES_PASSWORD', default='123321')
PG_HOST = env('DB_HOST', default='127.0.0.1')
PG_PORT = env.int('DB_PORT', default=5432)
PG_DB = env('POSTGRES_DB', default='GeOSINT_db')
PG_PROTOCOL = env('POSTGRES_PROTOCOL', default='postgresql+asyncpg')
PG_URI_QUERY = env('POSTGRES_URI_QUERY', default=str())

#parser
PARSER_TG_NAME = env('PARSER_TG_NAME', default='')
PARSER_API_ID = env('PARSER_API_ID', default='')
PARSER_API_HASH = env('PARSER_API_HASH', default='')

#gpt
GPT_MODEL=env('GPT_MODEL', default='gpt-4o-2024-05-13')
GPT_API_KEY=env('GPT_API_KEY', default='')
PROMPT='Нужно составить краткую сводку по событиям в {city_name} на основе информации из новостных статей: {news_articles}'
TOTAL_PROMPT='Нужно составить краткую сводку по событиям на основе информации из новостных статей: {news_articles}. Напиши не более 3000 печатных символов.'


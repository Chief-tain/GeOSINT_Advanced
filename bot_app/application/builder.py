import json
from datetime import datetime, timedelta

import pymorphy3
from gensim.models import Word2Vec

from bot_app.application.map_creation import MapCreation
from bot_app.application.dedup import deduplication, deduplication_plus

import logging

class Builder:
    def __init__(self) -> None:

        with open("ua-cities.json", encoding="utf-8") as file:
            self.data = json.load(file)

        self.city_list = []
        self.city_lon = []
        self.city_lat = []

        for region in self.data[0]['regions']:
            for item in region['cities']:
                self.city_list.append(item['name'].lower())
                self.city_lon.append(item['lat'].lower())
                self.city_lat.append(item['lng'].lower())
                
        self.stop_list = ('сводка', 'обстановка', 'направление', 'хроника')
        self.model = Word2Vec.load("models/word2vec_300_100.model")
        self.morph = pymorphy3.MorphAnalyzer()
                
    def dict_cleaning(self):
        self.cities_dict = dict()
        self.strikes_dict = dict()
        self.reports_dict = dict()
        self.tag_dict = dict()

        for index in range(len(self.city_list)):
            self.cities_dict[str(self.city_list[index])] = []
            self.strikes_dict[str(self.city_list[index])] = []
            self.reports_dict[str(self.city_list[index])] = []
            self.tag_dict[str(self.city_list[index])] = []

    def link_building(
        self,
        sender: str,
        message_id: int
        ):
        return f'<a href={sender}/{message_id} target="_blank">{sender}/{message_id}</a>'
    
    def map_creation(
        self,
        dataset: list
        ):
        
        self.dict_cleaning()

        for index in range(len(dataset)):

            tokens = dataset[index]['TOKENS']

            for key in self.cities_dict:
                # if key in tokens and not any(self.stop_list) in tokens:
                if key in tokens:
                    message_and_link = [dataset[index]['TEXT'], self.link_building(dataset[index]['SENDER'], dataset[index]['MESSAGE_ID'])]
                    self.cities_dict[str(key)].append(message_and_link)
                    self.reports_dict[str(key)].append(str(dataset[index]['TEXT']))

        cleaned_dict, self.total_points = deduplication(self.cities_dict, 60)
        
        return MapCreation().map_creation(cleaned_dict)

    # def cities_map_creation(self, begin, end, cities_list, channels, username):
    #     cities_list = cities_list.split('\n')
    #     cities_list = [element.strip() for element in cities_list]
    #     processed_cities_list = []
    #     for full_name in regions_dict.keys():
    #         for region_name in cities_list:
    #             if region_name in full_name:
    #                 processed_cities_list.append(full_name)
    #     translated_cities_list = [regions_dict[element] if element in regions_dict else element for element in processed_cities_list]
    #     filter_cities_dict = dict()

    #     if channels == 'ru':
    #         cities_dict = self.cities_dict

    #         for region in self.data[0]['regions']:
    #             if region['name'] in processed_cities_list:
    #                 for element in region['cities']:
    #                     filter_cities_dict[element['name'].lower()] = []
            
    #         for city_name in processed_cities_list:
    #             filter_cities_dict[city_name.lower()] = []

    #     if channels == 'ua':
    #         cities_dict = self.cities_dict_ua

    #         for region in self.data_ua[0]['regions']:
    #             if region['name'] in translated_cities_list:
    #                 for element in region['cities']:
    #                     filter_cities_dict[element['name'].lower()] = []
            
    #         for city_name in translated_cities_list:
    #             filter_cities_dict[city_name.lower()] = []

    #     begin, end = self.data_building(begin, end)
    #     dataset = self.database.read_db(begin, end, channels)

    #     for index in range(len(dataset)):

    #         adv_text = json.loads(dataset[index]['ADV_MESSAGE'])

    #         for key in filter_cities_dict:

    #             if key in adv_text and 'сводка' not in adv_text and 'обстановка' not in adv_text \
    #                 and 'направление' not in adv_text and 'хроника' not in adv_text:
                    
    #                 link = self.link_building(dataset[index]['SENDER'], dataset[index]['MESSAGE_ID'])
    #                 message_and_link = [dataset[index]['MESSAGE'], link]
    #                 cities_dict[str(key)].append(message_and_link)

    #     cleaned_dict, self.total_points = fuzzy_cleaning_plus(cities_dict, 60)
    #     self.map.map_creation(channels, cleaned_dict, username, region=True)

    # async def city_summary_creation(self, begin, end, city_name, channels, username):

    #     if channels == 'ua':
    #         city_name = self.translator.translate(city_name, dest='uk').text.lower()
    #         if city_name not in self.city_list_ua:
    #             raise KeyError
            
    #     if channels == 'ru':
    #         if city_name.lower() not in self.city_list:
    #             raise KeyError
        
    #     begin, end = self.data_building(begin, end, days=3)
    #     dataset = self.database.read_db(begin, end, channels)
    #     answer = []

    #     for index in range(len(dataset)):

    #         adv_text = json.loads(dataset[index]['ADV_MESSAGE'])

    #         if city_name.lower() in adv_text and 'сводка' not in adv_text and 'обстановка' not in adv_text \
    #             and 'направление' not in adv_text and 'хроника' not in adv_text:
    #             answer.append(dataset[index]['MESSAGE'])

    #     cleaned_answer, self.total_points, self.row_amount, self.cleaned_amount = list_fuzzy_cleaning(answer, 60)

    #     if self.cleaned_amount < 2:
    #         raise ArithmeticError
        
    #     final_answer = "\n".join(cleaned_answer)
    #     self.summary = (await GPT().chat_complete(final_answer, channels))
    #     self.summary = self.summary.replace('.', '\.').replace('_', '\_').replace('-', '\-').replace(')', '\)').replace('(', '\(').replace('!', '\!')
    #     # print(self.summary)

    def tag_map_creation(
        self,
        dataset,
        tag_word
        ):

        self.dict_cleaning()
        tag_dict = self.tag_dict
        try:
            tag_word = self.morph.parse(tag_word)[0].normal_form
            self.all_tags = [el[0] for el in self.model.wv.most_similar(tag_word)[:7]]
        except Exception as error:
            logging.info(f'ERROR: {error}')
            self.all_tags = []
        self.all_tags.append(tag_word)
        
        logging.info(f'self.all_tags: {self.all_tags}')

        for index in range(len(dataset)):

            tokens = dataset[index]['TOKENS']

            for current_tag in self.all_tags:
                for key in self.cities_dict:
                    if current_tag in tokens and key in tokens:
                        link = self.link_building(dataset[index]['SENDER'], dataset[index]['MESSAGE_ID'])
                        message_text = dataset[index]['TEXT']
                        tag_dict[str(key)].append([message_text, link])
        
        cleaned_tag_dict, self.total_tag_points = deduplication_plus(tag_dict, 60)
        return MapCreation().tag_map_creation(cleaned_tag_dict, self.all_tags)

    # def tag_list_creation(self, begin, end, tag_word, channels, username):

    #     begin, end = self.data_building(begin, end)
    #     dataset = self.database.read_db(begin, end, channels)

    #     if channels == 'ru':
    #         tag_dict = self.tag_dict
    #         try:
    #             tag_word = self.morph.parse(tag_word)[0].normal_form
    #             self.all_tags = [el[0] for el in self.model.wv.most_similar(tag_word)[:7]]
    #         except:
    #             self.all_tags = []
    #         self.all_tags.append(tag_word)

    #     if channels == 'ua':
    #         tag_dict = self.tag_dict_ua
    #         try:
    #             tag_word = self.morph.parse(tag_word)[0].normal_form
    #             self.all_tags = [self.translator.translate(el[0], dest='uk').text for el in self.model.wv.most_similar(tag_word)[:7]]
    #         except:
    #             self.all_tags = []
    #         self.all_tags.append(self.translator.translate(tag_word, dest='uk').text)

    #     tag_dict['другие'] = []
    #     link_collector = []

    #     for index in range(len(dataset)):

    #         adv_text = json.loads(dataset[index]['ADV_MESSAGE'])

    #         for current_tag in self.all_tags:
                
    #             for key in tag_dict:
    #                 if key in adv_text and 'сводка' not in adv_text and 'обстановка' not in adv_text \
    #                     and 'направление' not in adv_text and 'хроника' not in adv_text and current_tag in adv_text:
    #                     link = str(dataset[index]['SENDER']) + '/' + str(dataset[index]['MESSAGE_ID'])
    #                     tag_dict[str(key)].append((link, current_tag, dataset[index]['DATE']))
    #                     link_collector.append(link)

    #             if 'сводка' not in adv_text and 'обстановка' not in adv_text \
    #                 and 'направление' not in adv_text and 'хроника' not in adv_text and current_tag in adv_text:
    #                 link = str(dataset[index]['SENDER']) + '/' + str(dataset[index]['MESSAGE_ID'])
    #                 if link not in link_collector:
    #                     tag_dict['другие'].append((link, current_tag, dataset[index]['DATE']))

    #     self.answer = {}           
    #     for key, value in tag_dict.items():
    #         if value:
    #             self.answer[key] = value

    #     self.total_length = sum(map(len, self.answer.values()))
    #     build_tag_report(self.answer, begin, end, tag_word, username)

    #     # self.result = ''

    #     # for key, value in self.answer.items():
    #     #     self.result += markdown.bold("🌏 Населенный пункт: ") + f'{key.capitalize()}\n' 
    #     #     for element in value:
    #     #         self.result += element[0].replace('.', '\.').replace('_', '\_')
    #     #         self.result += ' \- '
    #     #         self.result += element[1]
    #     #         self.result += '\n'

    #     # if not self.result:
    #     #     raise ValueError

    # def report_creation(self, begin, end, channels, username):

    #     begin, end = self.data_building(begin, end)
    #     dataset = self.database.read_db(begin, end, channels)

    #     if channels == 'ru':
    #         cities_dict = self.cities_dict
    #         reports_dict = self.reports_dict
    #     if channels == 'ua':
    #         cities_dict = self.cities_dict_ua
    #         reports_dict = self.reports_dict_ua

    #     for index in range(len(dataset)):

    #         adv_text = json.loads(dataset[index]['ADV_MESSAGE'])

    #         for key in cities_dict:

    #             if key in adv_text and 'сводка' not in adv_text and 'обстановка' not in adv_text and 'направление' not in adv_text:

    #                 link = self.link_building(dataset[index]['SENDER'], dataset[index]['MESSAGE_ID'])
    #                 message_and_link = [dataset[index]['MESSAGE'], link]
    #                 cities_dict[str(key)].append(message_and_link)
    #                 reports_dict[str(key)].append(str(dataset[index]['MESSAGE']))

    #     cleaned_report_dict, self.total_points = fuzzy_cleaning(reports_dict, 60)
    #     build_report(cleaned_report_dict, begin, end, 60, username)
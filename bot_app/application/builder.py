import json
import logging

import pymorphy3
from gensim.models import Word2Vec

from bot_app.application.map_creation import MapCreation
from bot_app.application.dedup import deduplication, fuzzy_cleaning
from bot_app.application.report_creation import build_report
from bot_app.application.gpt import GPT
from shared import settings

class Builder:
    def __init__(
        self,
        coords_path: str = 'coords/ua-cities.json',
        model_path: str = 'models/word2vec_300_100.model'
        ) -> None:

        with open(coords_path, encoding="utf-8") as file:
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
        self.model = Word2Vec.load(model_path)
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
        ) -> str:
        
        return f'<a href={sender}/{message_id} target="_blank">{sender}/{message_id}</a>'
    
    def map_creation(
        self,
        dataset: list
        ):
        
        self.dict_cleaning()

        for index in range(len(dataset)):

            tokens = dataset[index]['TOKENS']
            
            if len(tokens) >= 100:
                continue

            for key in self.cities_dict:
                if key in tokens:
                    message_and_link = [dataset[index]['TEXT'], self.link_building(dataset[index]['SENDER'], dataset[index]['MESSAGE_ID'])]
                    self.cities_dict[str(key)].append(message_and_link)
                    self.reports_dict[str(key)].append(str(dataset[index]['TEXT']))

        cleaned_dict, self.total_points = deduplication(self.cities_dict, 60)
        
        return MapCreation().map_creation(cleaned_dict)
    

    async def city_summary_creation(
        self,
        dataset: list,
        city_name: str
        ):
        
        answer = []

        for index in range(len(dataset)):
            tokens = dataset[index]['TOKENS']
            
            if len(tokens) >= 100:
                continue

            if city_name.lower() in tokens:
                answer.append(dataset[index]['TEXT'])

        response = (await GPT().process_chat_completions(promt_styling=settings.PROMPT.format(city_name=city_name, news_articles=answer))).choices[0].message.content
        response = response.replace('.', '\.').replace('_', '\_').replace('-', '\-').replace(')', '\)').replace('(', '\(').replace('!', '\!')
        return response
    
    async def total_summary_creation(
        self,
        dataset: list,
        ):
        
        answer = []

        for index in range(len(dataset)):
            tokens = dataset[index]['TOKENS']
            
            if len(tokens) >= 100:
                continue

            answer.append(dataset[index]['TEXT'])

        response = (await GPT().process_chat_completions(promt_styling=settings.TOTAL_PROMPT.format(news_articles=answer))).choices[0].message.content
        response = response.replace('.', '\.').replace('_', '\_').replace('-', '\-').replace(')', '\)').replace('(', '\(').replace('!', '\!')
        return response

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
            
            if len(tokens) >= 100:
                continue

            for current_tag in self.all_tags:
                for key in self.cities_dict:
                    if current_tag in tokens and key in tokens:
                        link = self.link_building(dataset[index]['SENDER'], dataset[index]['MESSAGE_ID'])
                        message_text = dataset[index]['TEXT']
                        tag_dict[str(key)].append([message_text, link])
        
        cleaned_tag_dict, self.total_tag_points = deduplication(tag_dict, 60)
        return MapCreation().tag_map_creation(cleaned_tag_dict, self.all_tags)


    def report_creation(
        self,
        dataset: list,
        start_date: str,
        end_date: str
        ):
        
        self.dict_cleaning()
        cities_dict = self.cities_dict
        reports_dict = self.reports_dict

        for index in range(len(dataset)):

            tokens = dataset[index]['TOKENS']
            
            if len(tokens) >= 100:
                continue

            for key in cities_dict:
                
                if key in tokens:

                    link = self.link_building(dataset[index]['SENDER'], dataset[index]['MESSAGE_ID'])
                    message_and_link = [dataset[index]['TEXT'], link]
                    cities_dict[str(key)].append(message_and_link)
                    reports_dict[str(key)].append(str(dataset[index]['TEXT']))

        cleaned_report_dict, self.total_points = fuzzy_cleaning(reports_dict, 60)
        return build_report(cleaned_report_dict, start_date, end_date, 60, self.total_points)
    
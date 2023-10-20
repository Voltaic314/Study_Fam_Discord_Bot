'''
Author: Logan Maupin
Date: 10/20/2023

This module is used to help with getting the advice strings for the discord commands
and statuses of the bot.
'''
import requests

class Advice:

    def __init__(self, endpoints: dict[str, str]) -> None:
        self.endpoints = endpoints
        self.search_api_endpoint = self.endpoints['search']
        self.id_search_api_endpoint = self.endpoints['id_search']
        self.random_advice_api_endpoint = self.endpoints['random']

    @staticmethod
    def get_json_from_web_request(url: str) -> str:
        request = requests.get(url=url).json()
        return request

    def search_advice_by_term(self, search_term: str) -> list[str]:
        search_url = self.search_api_endpoint + search_term
        advice_json = self.get_json_from_web_request(search_url)
        advice_results = []
        for advice in advice_json:
            advice_results.append(advice['slip']['advice'])

    def search_advice_by_id(self, id_to_search: int or str) -> str:
        search_url = self.id_search_api_endpoint + str(id_to_search)
        return self.get_json_from_web_request(search_url)['slip']['advice']

    def get_random_advice(self) -> str:
        return self.get_json_from_web_request(self.random_advice_api_endpoint)['slip']['advice']
    

'''
Author: Logan Maupin

This module contains the bing_ai class from g4f so we can use it for some 
really basic queries. Once we can verify its functionality, we can
explore it further for potential API purposes if need be. For now, on such
a small scale, this works.. or at least we'll see if it does anyway! 
'''

import g4f
from g4f.Provider import (
Bing,
HuggingChat,
OpenAssistant,
)


class Bing_AI:

    def __init__(self) -> None:
        self.initial_prompt = f"I will call you Study Bot instead of Bing AI. "

    def ask(self, question: str) -> str:
        '''
        This function asks the prompt to bing ai using the chat completion technique.

        Parameters:
        question: str - whatever prompt you wish to ask bing AI. 

        Returns: str - the response back from bing AI all in one string. 
        '''
        g4f.check_version = False  # Disable automatic version checking
        response = g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=[{"role": "user", "content": question}],
            provider=Bing,
            auth=True
        )
        return response

    def get_news(self, category='', time_frame='today', char_limit=None) -> str:
        '''
        Gets a few news articles from the specified category and time from bing AI.
        
        Parameters: 

        (optional)
        category: str - news category you wish to get news for.
        time_frame: str - any time frame you wish to get news for, there may be 
        limitations to this from bing AI though. 
        char_limit: int - the limit of how many characters you wish to limit bing's response to.
        (Not sure if this actually works tbh, but worth a try).

        Returns: str - response froom bing AI
        '''
        initial_prmopt_str = self.initial_prmopt

        news_prompt = f"What's the {category} news for {time_frame}?"
        
        if char_limit:
            news_prompt += f" (also please limit your response to {char_limit} characters). "
        
        final_prompt = initial_prmopt_str + news_prompt
        return self.ask(final_prompt)


    def get_weather(self, weather_area: str, time_frame='right now') -> str:
        '''
        Gets the weather for a specific area also with an optional time frame setting.

        Parameters:
        weather_area: str - any format really, probably like city, state, or city, country. Either way.
        time_frame (optional): a str argument of the specified time of the forecast, like tomorrow for example.

        Returns: str - Response from bing AI
        '''
        initial_prmopt_str = self.initial_prmopt
        weather_prompt = f"What's the weather forecast of {weather_area} for {time_frame}?"
        final_prompt = initial_prmopt_str + weather_prompt
        return self.ask(final_prompt)


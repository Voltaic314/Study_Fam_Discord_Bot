'''
Author: Logan Maupin

This module contains information for the instagram API stuff
'''
import config
import requests
from text_processing import Text_Processing
from file_processing import File_Processing


class Reel:
    def __init__(self, permalink) -> None:
        self.API_key = config.instagram_bot_credentials['Long_Lived_API_Access_Token']
        self.permalink = permalink

    @property
    def media_url(self) -> str:
        '''
        This function gets the reel media mp4 link from the reel url.

        Parameters:
        reel_url: str of reel permalink url

        Returns: str - reel media url like something.com/something.mp4
        '''

        reel_id = Text_Processing.extract_reel_id_from_url(reel_url=self.permalink)

        return requests.get(f'https://graph.instagram.com/v17.0/{reel_id}?fields=media_url&access_token={self.API_key}').text
    
    @property
    def file_size(self, media_url: str) -> int:
        '''
        This function gets the file size of the reel. 
        mainly this is for posting limitation purposes if necessary.
        
        Parameters:
        media_url: str of the url to the media as defined from the media_url attribute

        Returns: int in bytes of file size
        '''
        return requests.get(media_url).get("content-length")
    
    @property
    def media_is_under_file_size_limit(self) -> bool:
        '''
        This property is True if the file size is less than the limit
        as imposed by our posting service, discord in this case. Though 
        this never actually gets used because we're just posting links anyway.

        Returns: True if file is less than 25 MB in size
        '''
        self.size_limit = 25_000_000
        return File_Processing.check_file_size_of_media_url(self.media_url, self.size_limit)
    
    @property
    def id(self) -> str:
        '''
        id of the media based on the reel permalink text

        Returns: reel id string
        '''
        return Text_Processing.extract_reel_id_from_url(reel_url=self.permalink)
    
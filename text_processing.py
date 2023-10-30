"""
Author: Logan Maupin

The purpose of this python script is to house the text processing class which houses a bunch of methods for manipulating
strings and text files.
"""
import random


class Text_Processing:

    @staticmethod
    def list_of_lines_in_text_file(filename: str) -> list[str]:

        lines_of_file = []

        with open(filename, encoding="utf-8", mode="r") as file:
            for line in file:
                # This if statement is to prevent this from adding empty line strings to the list.
                if line:
                    lines_of_file.append(line.strip())

        return lines_of_file

    @staticmethod
    def remove_special_characters_from_string(input_string: str) -> str:
        new_string = ""
        for character in input_string:
            if character.isalnum() or character.isspace():
                new_string += character
        return new_string

    @staticmethod
    def get_random_string_from_list(list_of_strings: list[str]) -> str:
        return random.choice(list_of_strings)

    @staticmethod
    def get_random_line_from_text_file(filename: str) -> str:
        lines = Text_Processing.list_of_lines_in_text_file(filename)
        return Text_Processing.get_random_string_from_list(lines)

    @staticmethod
    def extract_video_url(message_contents: str) -> str:
        """
        This function takes a message string posted by Carl_bot and removes all the other fluff text to extract the
        video url from it.
        :param message: string from carl bot containing the entire message contents.
        :returns: new string of video url.
        """

        # Example message would look like this:
        # "Dr. K just uploaded a video. Go check it out! youtube.com/link"

        # Split up the message by word. This will create a list variable.
        # (The last spaced item will be the link)
        split_up_message = message_contents.split(" ")
        
        # Retrieve the link posted from the list variable, it will always be the last item in the list.
        YouTube_URL = split_up_message[-1]
        return YouTube_URL
    
    @staticmethod
    def format_file_name(video_title):
        return Text_Processing.remove_special_characters_from_string(video_title).replace(" ", "_") + ".txt"

    @staticmethod
    def format_title_of_vid_for_txt_file(video_title):
        return Text_Processing.remove_special_characters_from_string(video_title)


    @staticmethod
    def extract_vid_id_from_shortened_yt_url(shortened_url: str) -> str:
        '''
        This function takes a shortened youtube url like youtu.be links and 
        parses it for a video id. 

        Parameters: str of a youtu.be url

        Returns: video ID
        '''
        if not "/" in shortened_url:
            return ''

        return shortened_url.split('/')[-1]

    @staticmethod
    def string_contains_reel(input_string: str) -> bool:
        return 'instagram.com/reel' in input_string
    
    @staticmethod
    def extract_insagram_reel_urls_from_text(input_text: str) -> list[str]:
        split_up_text = input_text.split(" ")
        # this returns a list because the user could have posted multiple reeels 
        # in a single message so we want to account for that. If you just need the string
        # then just add a [0] at the end of this function call
        all_reel_links_from_message = []
        for string in split_up_text:
            if "instagram.com/reel" in string:
                all_reel_links_from_message.append(string)
        return all_reel_links_from_message
    
    @staticmethod
    def extract_text_from_string_minus_urls(input_string: str) -> str:
        '''
        This function takes a given input string, removes any instagram reel urls from it, 
        then returns a copy of the string without any special characters. 

        Parameters:
        input_str: any str object you wish to extract only the text from.
        
        returns: str - without instagram reel urls or special characters. 
        '''
        split_string = input_string.strip().split(" ")
        text_without_urls = [string for string in split_string if not Text_Processing.message_contains_reel(input_string=string)]
        text_without_special_characters = [Text_Processing.remove_special_characters_from_string(string) for string in text_without_urls]
        return ' '.join(text_without_special_characters)
    
    @staticmethod
    def extract_reel_id_from_url(reel_url: str) -> str:
        '''
        This function takes a reel url like this: 
        https://www.instagram.com/reel/Cx-UKRypv7Q/?igshid=MzRlODBiNWFlZA==
        and it extradcts the part between reel/ and /? to get the ID

        in this case being: Cx-UKRypv7Q

        Parameters:
        reel_url: str of the reel url link to parse through

        Returns: str - Reel ID string from the url
        '''
        # make sure the link is a real reel url
        if not Text_Processing.string_contains_reel(reel_url):
            return ''
        
        string_split_by_slash = reel_url.split("/")

        for index, element in enumerate(string_split_by_slash):
            if element == 'reel':
                return string_split_by_slash[index + 1]

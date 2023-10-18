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

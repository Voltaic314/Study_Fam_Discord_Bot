import os
import requests

from pytube import YouTube
import youtube_transcript_api
from youtube_transcript_api.formatters import TextFormatter

import config
from time_modulation import Time_Stuff
from text_processing import Text_Processing
from file_processing import File_Processing


class Video_Processing:

    @staticmethod
    def get_current_file_path(filename: str) -> str:
        """
        Gets the current absolute filepath of the file provided.
        :param filename: the name of the file you wish to get the path of.
        :returns: str of the actual absolute file path of the current directory.
        """
        current_directory = os.path.dirname(os.path.abspath(__file__))
        # Change the current working directory to the script's directory
        os.chdir(current_directory)
        file_path = os.path.join(current_directory, filename)
        return file_path

    @staticmethod
    def file_exists(filename: str, absolute_filepath: bool) -> bool:
        """
        Checks to see if the file actually exists within the directory you provided.
        :param filename: the name of the file you wish to check for if it exists or not.
        :param absolute_filepath: True or False on whether you used the absolute filepath or just the file's name.
        :returns: True if the file exists, False otherwise.
        """
        if absolute_filepath:
            return os.path.exists(filename)

        else:
            current_directory = os.path.dirname(os.path.abspath(__file__))
            # Change the current working directory to the script's directory
            os.chdir(current_directory)
            file_path = os.path.join(current_directory, filename)
            return os.path.exists(file_path)


    @staticmethod
    def get_video_title(url: str):
        youtube = YouTube(url)
        title_of_video = youtube.title
        return title_of_video
    
    @staticmethod
    def get_video_id(url: str) -> str:
        youtube = YouTube(url)
        return youtube.video_id
    

    @staticmethod
    def get_text_from_video(video_id):
        transcript = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(video_id=video_id)
        formatter = TextFormatter()
        txt_formatted = formatter.format_transcript(transcript=transcript)
        
        return txt_formatted
    
    @staticmethod
    def format_text_file_intro(video_id: str, video_title: str, video_url: str) -> str:
        """
        This function will take in a YT video object and spit out a formatted string
        with all the fancy information that we want at the top of our transcription txt file.
        
        :param video_id: a YT video id, usually a string.
        :param video_title: a UTF-8 txt file friendly formatted video title string
        :param video_url: the full YT watch url string
        
        :returns: formatted string to add to the top of the transcription txt file.
        """
        text_file_header = ""
        text_file_header += f"Date: {Time_Stuff.get_current_date()}\n"
        text_file_header += f"Video ID: {video_id}\n"
        text_file_header += f"Video Title: {video_title}\n"
        text_file_header += f"Video URL: {video_url}\n\n\n"

        return text_file_header
    
    @staticmethod
    def transcribe_yt_video_main(yt_url: str) -> bool:

        video_id = Video_Processing.get_video_id(yt_url)
        video_title = Video_Processing.get_video_title(yt_url)
        txt_filename = Text_Processing.format_file_name(video_title=video_title)
        txt_filename = File_Processing.get_abs_file_path(txt_filename)
        video_title = Text_Processing.format_title_of_vid_for_txt_file(video_title=video_title)

        try: 
            video_text = Video_Processing.get_text_from_video(video_id=video_id)
        
        except youtube_transcript_api._errors.TranscriptsDisabled(video_id=video_id):
            return False
        header_text = Video_Processing.format_text_file_intro(video_id, video_title, yt_url)
        total_txt_to_write = header_text + video_text
        File_Processing.write_string_to_text_file(txt_filename=txt_filename, string_to_write=total_txt_to_write)
        return os.path.exists(txt_filename)


    @staticmethod
    def is_yt_video_a_short(video_id: str) -> bool:
        '''
        This function takes a video ID and sees if it's actually a short or not.
        We have to use network requests to truly know this or not.

        Basically I noticed this trick with YouTube where if you take a normal video
        and put its ID into a shorts base link, it will kick you back to a normal
        YT video url. But with shorts it won't do this. So we can track this redirect
        and use it for our testing purposes.

        Parameters: video ID, that last bit at the end of the YT vid url.

        Returns: True if it is a short and false otherwise.
        '''
        yt_short_url = f'https://www.youtube.com/shorts/{video_id}'

        try:
            response = requests.get(yt_short_url)
            return response.url == yt_short_url
        except requests.exceptions.RequestException:
            return False

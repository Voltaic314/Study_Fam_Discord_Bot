import os
import requests

from pytube import YouTube
import pytube.exceptions
import youtube_transcript_api
from youtube_transcript_api.formatters import TextFormatter

import config
from time_modulation import Time_Stuff
from text_processing import Text_Processing
from file_processing import File_Processing


class Video(YouTube):

    def __init__(self, url) -> None:
        super().__init__(url)
        self.url = url
        self.id = Text_Processing.extract_vid_id_from_shortened_yt_url(self.url)

    @property
    def text_file_header(self) -> str:
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
        text_file_header += f"Video ID: {self.id}\n"
        text_file_header += f"Video Title: {self.title}\n"
        text_file_header += f"Video URL: {self.url}\n\n\n"

        return text_file_header

    @property
    def file_path(self) -> str:
        """
        Gets the current absolute filepath of the file provided.
        :param filename: the name of the file you wish to get the path of.
        :returns: str of the actual absolute file path of the current directory.
        """
        current_directory = os.path.dirname(os.path.abspath(__file__))
        # Change the current working directory to the script's directory
        os.chdir(current_directory)
        file_path = os.path.join(current_directory, self.filename)
        return file_path

    @property
    def file_exists(self) -> bool:
        """
        Checks to see if the file actually exists within the directory you provided.
        
        Returns: True if the file exists, False otherwise.
        """
        return os.path.exists(self.filename)
    
    @property
    def is_private(self) -> bool:
        '''
        This method returns True if the video is a private video or not.
        
        Returns: True if video is private, else False.
        '''

        try:
            self.streams
            return False
        
        except pytube.exceptions.VideoPrivate:
            return True
    
    @property
    def is_short(self) -> bool:
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

        yt_short_url = f'https://www.youtube.com/shorts/{self.id}'

        try:
            response = requests.get(yt_short_url)
            return response.url == yt_short_url
        except requests.exceptions.RequestException:
            return False
        
    @property
    def caption_text(self):
        try:
            transcript = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(video_id=self.id)
        
        except youtube_transcript_api._errors.TranscriptsDisabled(video_id=self.id):
            return ''
        
        formatter = TextFormatter()
        txt_formatted = formatter.format_transcript(transcript=transcript)
        
        return txt_formatted

    def transcribe_yt_video(self) -> bool:

        txt_filename = Text_Processing.format_file_name(video_title=self.title)
        txt_filename = File_Processing.get_abs_file_path(txt_filename)
        video_title = Text_Processing.format_title_of_vid_for_txt_file(video_title=self.title)
        if not self.caption_text:
            return False
        total_txt_to_write = self.text_file_header + self.caption_text
        File_Processing.write_string_to_text_file(txt_filename=txt_filename, string_to_write=total_txt_to_write)
        return os.path.exists(txt_filename)
    
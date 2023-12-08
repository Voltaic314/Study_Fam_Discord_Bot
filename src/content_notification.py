'''
Author: Logan Maupin

This module holds the dr k notification message class object.
Primarily this comes from carl bot's alert.
'''
from text_processing import Text_Processing
from video_processing import Video

class ContentNotification:

    def __init__(self, message_contents: str, author_id: int, channel_id: int) -> None:
        self.message_contents = message_contents
        self.author_id = author_id
        self.channel_id = channel_id

    @property
    def correct_channel(self):
        # First id is dr_k_content channel, second id is the bot labs channel. So if it was in either of those.
        return self.channel_id == 1078121853266165870 or self.channel_id == 1140698361318625382
        
    @property
    def from_carl(self):
        Carl_Bot_User_ID = 235148962103951360
        return self.author_id == Carl_Bot_User_ID
    
    @property
    def is_content_alert(self):
        return self.correct_channel and self.from_carl
    
    @property
    def video(self):
        if self.is_content_alert:
            video_url = Text_Processing.extract_video_url(self.message_contents)
            return Video(url=video_url)
    
    @property
    def is_twitch_stream(self):
        return "live" in self.message_contents

    @property
    def is_yt_video(self):
        return "youtu.be" in self.message_contents
    
    @property
    def yt_video_is_private(self):
        return self.video.is_private
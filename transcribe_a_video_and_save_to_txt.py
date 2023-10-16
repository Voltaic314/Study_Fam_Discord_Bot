'''
Author: Logan Maupin
GitHub: https://github.com/Voltaic314
Date: 10/16/2023

The purpose of this module is to transcribe a given YT video into a 
text file given the YT url provided from user input.
'''
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter


def get_video_url_to_transcribe() -> str:
    '''
    This function asks for user_input to get the video url you wish to transcribe.

    Returns: str of YT video url
    '''
    while True:
        video_to_transcribe = input("Please input the url to the video you wish to transcribe: ").strip()

        youtube_in_link = video_to_transcribe.count("youtube")
        youtu_be_in_link = video_to_transcribe.count("youtu.be")

        # adding safeguards because users are stupid lmao
        if not (youtube_in_link or youtu_be_in_link):
            print("Please input a valid YouTube url, not shortened please.")

        else:
            return video_to_transcribe


def get_video_info(video_url) -> tuple[str, str]:
        '''
        This function takes a YT url and returns its title and video ID.

        Parameters:
        video_url: str of the YT video url

        Returns: Tuple --> (video_title, video_id)
        '''
        youtube = YouTube(video_url)
        title_of_video = youtube.title
        video_id = youtube.video_id
        return title_of_video, video_id


def remove_special_characters_from_string(input_string: str) -> str:
    '''
    This function takes a given input string and removes all characters that aren't
    alpha-numeric or spaces. 

    Parameters:
    input_string: str you wish to format

    Returns: formatted str
    '''
    new_string = ""
    for character in input_string:
        if character.isalnum() or character.isspace():
            new_string += character
    return new_string


def format_filename(video_title) -> str:
    '''
    This function takes a YT video and removes any characters that aren't alphanumeric,
    then changes spaces to underscores, and adds the .txt extension so that we can use it
    as a txt filename. 

    Parameters: 
    video_title: str of a video title you wish to format into a txt filename

    Returns: formatted str
    '''
    return remove_special_characters_from_string(video_title).replace(" ", "_") + ".txt"


def format_text_file_intro(video_title: str, video_url: str) -> str:
    """
    This function will take in a YT video object and spit out a formatted string
    with all the fancy information that we want at the top of our transcription txt file.
    
    Parameters:
    video_id: a YT video id, usually a string.
    video_title: a UTF-8 txt file friendly formatted video title string
    ideo_url: the full YT watch url string
    
    Returns: formatted string to add to the top of the transcription txt file.
    """
    text_file_header = ""
    text_file_header += f"Video Title: {video_title}\n"
    text_file_header += f"Video URL: {video_url}\n\n"

    return text_file_header


def get_text_from_video(video_id) -> str:
    '''
    This function transcribes a youtube video given a youtube video ID. 
    You can extract the video ID from the url, it's that special character
    part at the end of the url after the = sign and before any & signs.

    Parameters:
    video_id: str of video id from the YT vid you wish to transcribe

    Returns: Str of transcribed text, formatted in plain text for a text file.
    '''
    transcript = YouTubeTranscriptApi.get_transcript(video_id=video_id)
    formatter = TextFormatter()
    txt_formatted = formatter.format_transcript(transcript=transcript)
    
    return txt_formatted


def write_string_to_text_file(txt_filename: str, string_to_write: str) -> None:
    '''
    This function appends a text file with the text you wish to write to it

    Parameters: 
    txt_filename: str representing the file name of the txt file you wish to write to.
    string_to_write: str of what you wish to write to the file.

    Returns: None
    '''
    with open(txt_filename, 'a') as txt_file:
        txt_file.write(string_to_write)


def transcribe_video():
    '''
    This function asks for the user to input a video url, then transcribes that video into text.
    It then saves that text to a txt file in the same directory as this script is in.

    Returns: None
    '''
    video_url = get_video_url_to_transcribe()
    video_title, video_id = get_video_info(video_url=video_url)
    video_title = remove_special_characters_from_string(video_title)
    txt_file_header = format_text_file_intro(video_title=video_title, video_url=video_url)
    txt_file_friendly_name = format_filename(video_title=video_title)
    txt_from_vid = get_text_from_video(video_id=video_id)
    total_txt_to_write = txt_file_header + txt_from_vid
    write_string_to_text_file(txt_file_friendly_name, total_txt_to_write)


if __name__ == "__main__":
    transcribe_video()

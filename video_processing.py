from pytube import YouTube
import speech_recognition as sr
import os
from time_modulation import Time_Stuff


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
        title_of_video = youtube.title.title()
        return title_of_video

    def download_video_as_mp3(self, url: str) -> (str, str) or bool:
        youtube = YouTube(url)
        title_of_video = youtube.title.title()
        video_id = youtube.video_id
        video = youtube.streams.get_audio_only()
        filename_to_save = title_of_video + ".mp3"
        video.download(output_path=filename_to_save)
        the_audio_saved_successfully = self.file_exists(filename_to_save)
        if the_audio_saved_successfully:
            return filename_to_save, video_id
        else:
            return False

    def convert_audio_to_speech_text(self, audio_filename: str, text_filename_to_save: str, 
                                     remove_audio_file: bool, text_file_header: str) -> None:
        recognizer = sr.Recognizer()
        full_audio_file_path = self.get_current_file_path(audio_filename)
        with sr.AudioFile(full_audio_file_path) as source:
            audio = recognizer.record(source)  # Record the entire audio file
        try:
            text = recognizer.recognize_google(audio)
            full_text_file_path = self.get_current_file_path(text_filename_to_save)
            with open(full_text_file_path, "w") as save_file:
                save_file.write(text_file_header)
                save_file.write(text)
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand the audio")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")

        if remove_audio_file:
            os.remove(full_audio_file_path)

    def transcribe_a_YT_video(self, YT_Video_Url: str) -> str:
        """
        This will take a YT URL and transcribe it to a text file. It will then return the text file name if successful.
        :param YT_Video_Url: the full YT URL link for the video.
        :returns: String of the text file name that the video was transcribed to.
        """
        audio_filename, video_id = self.download_video_as_mp3(url=YT_Video_Url)
        full_file_path = self.get_current_file_path(audio_filename)
        audio_download_was_successful = self.file_exists(full_file_path, True)
        if audio_download_was_successful:
            txt_filename = audio_filename[:-3] + f"_video_id={video_id}.txt"
            text_file_header = ""
            text_file_header += f"Date: {Time_Stuff.convert_epochs_to_human_readable_time(Time_Stuff.get_current_time_in_epochs)}\n"
            text_file_header += f"Video_ID: {video_id}\n"
            text_file_header += f"Video Title: {audio_filename[:-3]}"
            self.convert_audio_to_speech_text(self, audio_filename=audio_filename, text_filename_to_save=txt_filename, 
                                              remove_audio_file=True, text_file_header=text_file_header)
            text_file_path = self.get_current_file_path(txt_filename)
            text_transcription_saved_a_txt_file = self.file_exists(text_file_path, True)
            if text_transcription_saved_a_txt_file:
                return text_file_path

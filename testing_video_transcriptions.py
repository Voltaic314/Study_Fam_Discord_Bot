from text_processing import Text_Processing
from video_processing import Video_Processing

test_yt_vid_url = "https://www.youtube.com/watch?v=w5HhFDIoNEs"

transcribed_txt_file_path = Video_Processing.transcribe_a_YT_video(test_yt_vid_url)

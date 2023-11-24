'''
Author: Logan Maupin
Date: 10/18/2023

This is just for my own troubleshooting so I can test functions I make 
outside of the whole discord ecosystem, to make sure each individual
function works properly.
'''
from video_processing import Video_Processing
from text_processing import Text_Processing


def main():
    url = 'https://youtu.be/NL5NeKeFhxM'
    video_id = Text_Processing.extract_vid_id_from_shortened_yt_url(shortened_url=url)
    print(Video_Processing.is_yt_video_a_short(video_id=video_id))


if __name__ == "__main__":
    main()

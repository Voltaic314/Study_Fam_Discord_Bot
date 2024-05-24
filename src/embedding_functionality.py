import yt_dlp
import instaloader


def download_instagram_reel(url, output_path='.'):
    loader = instaloader.Instaloader()
    post = instaloader.Post.from_shortcode(loader.context, url.split('/')[-2])
    loader.download_post(post, target=output_path)


def download_yt_video(url, output_path='video.mp4'):
    ydl_opts = {
        'format': 'best[height<=720]',
        'outtmpl': output_path,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.DownloadError as e:
        print(f"Error downloading video: {e}")


def main():
    files_downloaded = 0

    # example usage 
    download_yt_video('https://www.youtube.com/watch?v=9bZkp7q19f0', output_path=f'src/media files/video{files_downloaded}.mp4')
    files_downloaded += 1

    # YT shorts as well:
    download_yt_video("https://youtube.com/shorts/o6VQpe_LJc0?si=7XxBpmSH3ZS8UPCq", output_path=f'src/media files/video{files_downloaded}.mp4')
    files_downloaded += 1

    # TODO: Implement something that can handle facebook videos and reels
    # Example usage for Facebook Reels
    # download_yt_video('https://www.facebook.com/9gag/videos/3010547732342868', output_path=f'src/media files/video{files_downloaded}.mp4')
    # files_downloaded += 1

    # # for reels
    # download_yt_video('https://www.facebook.com/reel/980634410400949', output_path=f'src/media files/video{files_downloaded}.mp4')
    # files_downloaded += 1

    download_instagram_reel('https://www.instagram.com/reels/C7HOcldLS8Z/', output_path=f'src/media files/video{files_downloaded}.mp4') # just a random reel I found lol
    files_downloaded += 1

    # we also need to control for if the video files are larger than the discord server can handle
    # but this can be handled in the logic of the discord bot utilizing it.
    # we won't put that abstraction within this script. 


if __name__ == '__main__':
    main()

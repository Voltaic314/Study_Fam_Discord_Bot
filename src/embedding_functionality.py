import yt_dlp
import instaloader
import os
import time
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc


# all this scraping nonsense just to get FB content. lol thanks Meta.
def download_media_from_snapsave(url, output_path='src/media files'):
    # Setup Selenium with undetected-chromedriver
    options = uc.ChromeOptions()
    options.headless = True
    driver = uc.Chrome(options=options)

    # Visit Snap-Save website for Facebook Reels download
    driver.get("https://snapsave.app/facebook-reels-download")

    # Find the input field and submit button, enter the URL
    input_field = driver.find_element(By.CSS_SELECTOR, "input#url")  # Adjust selector if necessary
    input_field.send_keys(url)
    submit_button = driver.find_element(By.CSS_SELECTOR, "button.is-download")  # Adjust selector if necessary
    submit_button.click()

    # Wait for the download button to appear in the table
    wait_time = 5  # Initial wait time
    max_wait_time = 60  # Maximum wait time
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        time.sleep(wait_time)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        download_buttons = soup.select('a.btn.btn-success')  # Update this based on actual HTML
        if download_buttons:
            break
    else:
        print("Timeout: Download button not found after waiting.")

    # Download the first link (assume the first link is the desired quality)
    if download_buttons:
        video_url = download_buttons[0]['href']
        response = requests.get(video_url)

        # Ensure output directory exists
        os.makedirs(output_path, exist_ok=True)

        # Write the file to disk
        file_path = os.path.join(output_path, 'video.mp4')
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded video to {file_path}")

    else:
        print("No download links found.")

    # Quit the driver (the download will be handled by the browser)
    driver.quit()


def download_instagram_reel(url, output_path='src/media files/video.mp4'):
    loader = instaloader.Instaloader()
    shortcode = url.split('/')[-2]
    post = instaloader.Post.from_shortcode(loader.context, shortcode)
    loader.download_post(post, target=output_path)

    # Move downloaded file to the correct path
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.startswith(shortcode):
                os.rename(os.path.join(root, file), output_path)
                break


def download_yt_video(url, output_path='src/media files/video.mp4'):
    ydl_opts = {
        'format': 'best[height<=720]',
        'outtmpl': output_path,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.DownloadError as e:
        print(f"Error downloading video: {e}")


# def download_facebook_video(post_url, output_path='src/media files/video.mp4'):
#     for post in get_posts(post_urls=[post_url], options={"comments": False}):
#         video_url = post['video']
#         if video_url:
#             response = requests.get(video_url)
#             with open(output_path, 'wb') as file:
#                 file.write(response.content)
#             return True
#     return False


def main():
    files_downloaded = 0

    # example usage
    download_yt_video('https://www.youtube.com/watch?v=9bZkp7q19f0', output_path=f'src/media files/video{files_downloaded}.mp4')
    files_downloaded += 1

    # YT shorts as well:
    download_yt_video("https://youtube.com/shorts/o6VQpe_LJc0?si=7XxBpmSH3ZS8UPCq", output_path=f'src/media files/video{files_downloaded}.mp4')
    files_downloaded += 1

    ## TODO: This currently has a dependency issue with websockets that will require a separete environment to run. Will need to implement that somehow to make this work. 
    ## that will be a crap ton of work though, so I'm not sure if it's worth it.
    ## will tackle it some other time.
    # download_facebook_video('https://www.facebook.com/9gag/videos/3010547732342868', output_path=f'src/media files/video{files_downloaded}.mp4')
    # files_downloaded += 1

    # for Facebook reels
    ## TODO: Actually impolement this because the current implementation is not sufficient to get around FB's anti-scraping measures.
    # download_facebook_reel('https://www.facebook.com/reel/980634410400949', output_path=f'src/media files/video{files_downloaded}.mp4')
    # files_downloaded += 1

    # Example usage for Instagram Reels
    download_instagram_reel('https://www.instagram.com/reels/C7HOcldLS8Z/', output_path=f'src/media files/video{files_downloaded}.mp4')
    files_downloaded += 1

    # Additional logic to handle file size for Discord can be implemented here

if __name__ == '__main__':
    main()
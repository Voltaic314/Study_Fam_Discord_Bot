'''
Author: Logan Maupin

This is a collection of functions I use for image processing related stuff.
'''
import os
import requests
from bs4 import BeautifulSoup
import config
import imagehash
from PIL import Image
from io import BytesIO


class Image_Processing:

    @staticmethod
    def difference_image_hashing(filename: str) -> hash:

        # first confirm the file exists
        file_exists = os.path.exists(filename)
        if file_exists:
            try:
                img_hash = imagehash.dhash(Image.open(filename))
                return img_hash
            
            except AttributeError:
                return False
            
    @staticmethod
    def resize_image_to_512x512(img_filename: str) -> None:
        try:
            # Open the image file
            img = Image.open(img_filename)
            
            # Resize the image to 512x512
            img = img.resize((512, 512))
            
            # Save the resized image
            img.save(img_filename)
            print(f"Image '{img_filename}' resized to 512x512 and saved.")
        except Exception as e:
            print(f"An error occurred: {e}")

    @staticmethod
    def get_random_image() -> bool:
        # The URL of the website
        url = 'https://thispersondoesnotexist.com/'

        # Send a GET request to the website
        response = requests.get(url)

        # Check if the image request was successful
        if response.status_code == 200:
            # Open the image and save it
            
            with open('Profile_Picture.jpg', 'wb') as file:
                file.write(response.content)

                if os.path.exists('Profile_Picture.jpg'):
                    Image_Processing.resize_image_to_512x512('Profile_Picture.jpg')

        return os.path.exists('Profile_Picture.jpg')
    

    @staticmethod
    def get_img_filesize(image_filename: str) -> int:
        return os.stat(image_filename)
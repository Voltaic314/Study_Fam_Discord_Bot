'''
The purpose of this module is to contain the Emote class object
which comprises of the emote url and the corresponding hash. 
'''
import requests
import os
import imagehash
from PIL import Image


class Emote:

    def __init__(self, emoji):
        self.url = emoji.url
        self.id = emoji.id
        self.name = emoji.name

    def write_image(self) -> bool:
        """
        This function downloads an image and saves it to a new emote object attribute.

        :returns: True if the file was successfully saved
        """
        self.filename = 'image.jpg'
        self.file_path = os.path.abspath(self.filename)

        with open(self.filename, 'wb') as f:
            f.write(requests.get(self.url).content)

        return os.path.exists(self.file_path)

    def remove_file(self) -> bool:
        '''
        This function removes the file that was saved after 
        hashing once this funcion is called.
        
        Returns: True if file did actually get removed
        '''
        file = self.file_path

        # first check to see if the file exists at all
        file_exists = os.path.exists(file)

        if file_exists:
            os.remove(file)
            # check to make sure that actually worked
            file_exists = os.path.exists(file)

        self.file_path = None
        self.filename = None

    @property
    def hash_string(self):
        """
        Run a difference hash and return the hash string from the given image specified in the file name.

        :param filename: Name of the image file you wish to hash, must include full file name, so extension as well.
        :returns: difference hash string that can be used to compare against other image hashes to find similar images.
        """

        self.write_image()

        hashed_image_string = str(imagehash.dhash(Image.open(self.file_path)))

        self.remove_file()

        return hashed_image_string

'''
Author: Logan Maupin

This is a collection of functions I use for image processing related stuff.
'''
import os
import imagehash
from PIL import Image


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

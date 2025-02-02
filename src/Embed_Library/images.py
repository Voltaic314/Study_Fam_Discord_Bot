import gallery_dl
import os
import json
import subprocess
from response_handler import Response


class Image:
    """A class representing a single image."""
    
    MAX_FILE_SIZE_MB = 25  # Discord file size limit

    def __init__(self, url, filename, filesize):
        self.url = url
        self.filename = filename
        self.filesize = filesize

    def exists_locally(self):
        """Checks if the image has been downloaded."""
        return os.path.exists(self.filename)

    def download(self):
        """Downloads the image and returns the file path."""
        try:
            gallery_dl.download(self.url)
            
            if not os.path.exists(self.filename):
                response = Response(success=False)
                response.add_error(
                    error_type="DownloadError",
                    message="An error occurred while downloading the image."
                )
                return response
            
            if self.filesize > self.MAX_FILE_SIZE_MB:
                print(f"File {self.filename} is too large, compressing...")
                compressed_response = self.compress()
                if self.filesize > self.MAX_FILE_SIZE_MB:
                    self.delete_file()
                    print(f"Compressed file {self.filename} is still too large. Deleting...")
                return compressed_response
            
            return Response(success=True, response=self.filename)
        except Exception as e:
            response = Response(success=False)
            response.add_error(
                error_type="DownloadError",
                message="An error occurred while downloading the image.",
                details=str(e)
            )
            return response
    
    def compress(self, quality=85):
        """Compresses the image using ffmpeg and returns the new file path."""
        if not self.exists_locally():
            raise FileNotFoundError("Downloaded image not found.")
        
        output_filename = f"Compressed_{self.filename}"
        
        command = [
            "ffmpeg", "-i", self.filename, "-q:v", str(quality), output_filename
        ]
        
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.delete_file()
        os.rename(output_filename, self.filename)
        return Response(success=True)
    
    def delete_file(self):
        """Deletes the downloaded and/or compressed image file."""
        if self.exists_locally():
            os.remove(self.filename)

class Images:
    """A container for multiple Image objects."""
    
    def __init__(self, url):
        self.url = url
        self.images = []
        self.downloaded_images = []
        self._extract_metadata()
    
    def _extract_metadata(self):
        """Extracts metadata and initializes Image objects with session cookies if available."""
        try:

            # Load `gallery-dl` configuration
            gallery_dl.config.load()

            # Now create the job AFTER configuring cookies
            job = gallery_dl.job.DownloadJob(self.url)

            # Extract metadata
            entries = job.extractor.items()
            if not entries:
                response = Response(success=False)
                response.add_error(
                    error_type="MetadataError",
                    message="No images found in the URL."
                )
                return response
            
            for index, entry in enumerate(entries):
                ext = entry.get('extension', 'jpg')  # Extract extension safely
                filename = f"downloaded_image_{index}.{ext}"
                filesize = entry.get("filesize", 0) / (1024 * 1024)  # Convert bytes to MB
                self.images.append(Image(self.url, filename, filesize))

        except Exception as e:
            response = Response(success=False)
            response.add_error(
                error_type="MetadataError",
                message="An error occurred while extracting metadata.",
                details=str(e)
            )
            return response
        
    def download(self):
        """Downloads all images in the list."""
        responses = []
        for image in self.images:
            response = image.download()
            if response.success:
                self.downloaded_images.append(image)
            responses.append(response)
        return responses
    
    def delete_all(self):
        """Deletes all downloaded images."""
        for image in self.downloaded_images:
            image.delete_file()

    def to_dict(self):
        """Converts the Images object to a dictionary for serialization or logging."""
        return {
            "url": self.url,
            "images": [image.to_dict() for image in self.images]
        }

    def __str__(self):
        return json.dumps(self.to_dict(), indent=4)

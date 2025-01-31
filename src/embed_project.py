import yt_dlp
import subprocess
import os

class Video:
    """A class to download and compress videos."""
    
    MAX_FILE_SIZE_MB = 25  # Discord file size limit

    def __init__(self, url):
        self.url = url
        self.title = None
        self.duration = None
        self.uploader = None
        self.site = None
        self.filename = None
        self._extract_metadata()

    def _extract_metadata(self):
        """Extracts metadata for any supported video link without downloading."""
        ydl_opts = {"quiet": True, "noplaylist": True}
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(self.url, download=False)
            
            self.title = info_dict.get("title")
            self.duration = info_dict.get("duration")
            self.uploader = info_dict.get("uploader")
            self.site = info_dict.get("extractor_key")
            self.filename = f"downloaded_video.{info_dict.get('ext', 'mp4')}"
            self.filesize = info_dict.get("filesize", 0) / (1024 * 1024)  # Convert bytes to MB

    def download_audio(self):
        """Downloads and compresses the audio if necessary before returning the file path."""
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": self.filename,
            "quiet": True,
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            
            if os.path.getsize(self.filename) / (1024 * 1024) > self.MAX_FILE_SIZE_MB:
                print("Downloaded file is too large, compressing...")
                os.remove(self.filename)
                print("file is too large. Deleting...")
                return None
            
            return self.filename
        except Exception as e:
            print(f"Error downloading audio: {e}")
            return None  # Handle failure gracefully

    def download(self):
        """Downloads and compresses the media if necessary before returning the file path."""
        if self.filesize and self.filesize > self.MAX_FILE_SIZE_MB:
            print("File is too large, attempting compression...")
            compressed_filename = self.compress()
            if os.path.getsize(compressed_filename) / (1024 * 1024) > self.MAX_FILE_SIZE_MB:
                os.remove(compressed_filename)
                print("Compressed file is still too large. Deleting...")
                return None
            return compressed_filename
        
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": self.filename,
            "quiet": True,
            "merge_output_format": "mp4",
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            
            if os.path.getsize(self.filename) / (1024 * 1024) > self.MAX_FILE_SIZE_MB:
                print("Downloaded file is too large, compressing...")
                compressed_filename = self.compress()
                os.remove(self.filename)
                if os.path.getsize(compressed_filename) / (1024 * 1024) > self.MAX_FILE_SIZE_MB:
                    os.remove(compressed_filename)
                    print("Compressed file is still too large. Deleting...")
                    return None
                return compressed_filename
            
            return self.filename
        except Exception as e:
            print(f"Error downloading video: {e}")
            return None  # Handle failure gracefully
    
    def compress(self, target_bitrate="1M"):
        """Compresses the media using ffmpeg and returns the new file path."""
        if not os.path.exists(self.filename):
            raise FileNotFoundError("Downloaded media not found.")
        
        output_filename = f"compressed_{self.filename}"
        
        command = [
            "ffmpeg", "-i", self.filename, "-b:v", target_bitrate, "-c:a", "aac", "-strict", "-2", output_filename
        ]
        
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_filename
    
    def delete_file(self, compressed=False):
        """Deletes the downloaded and/or compressed video file."""
        if os.path.exists(self.filename):
            os.remove(self.filename)
        
        compressed_filename = f"compressed_{self.filename}"
        if compressed and os.path.exists(compressed_filename):
            os.remove(compressed_filename)

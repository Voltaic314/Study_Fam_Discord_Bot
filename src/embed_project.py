import yt_dlp
import subprocess
import os
from response_handler import Response, Warning, Error


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
                self.delete_file()
                print("file is too large. Deleting...")
                response = Response(success=False)
                response.add_error(
                    error_type="FileTooLarge",
                    message="File is too large. Please try again with a smaller file."
                )
                return response
            
            return Response(success=True, response=self.filename)
        
        except Exception as e:
            print(f"Error downloading audio: {e}")
            response = Response(success=False)
            response.add_error(
                error_type="DownloadError",
                message="An error occurred while downloading the audio.",
                details=str(e)
            )
            return response

    def download(self):
        """Downloads and compresses the media if necessary before returning the file path."""
        ydl_opts = {
            "format": "bestvideo+bestaudio/best", 
            "outtmpl": f"{self.filename}.mp4" if not self.filename.endswith(".mp4") else self.filename,
            "quiet": True,
            "merge_output_format": "mp4",
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            
            if self.filesize > self.MAX_FILE_SIZE_MB:
                print("Downloaded file is too large, compressing...")
                compressed_response = self.compress()
                if self.filesize > self.MAX_FILE_SIZE_MB:
                    self.delete_file()
                    print("Compressed file is still too large. Deleting...")
                    response = Response(success=False)
                    response.add_error(
                        error_type="FileTooLarge",
                        message="File is too large. Please try again with a smaller file."
                    )
                    return response
                return compressed_response
            
            # Check if we need to convert
            if not self._is_h264():
                print("Downloaded video is NOT H.264! Converting...")
                self.filename = self._convert_to_h264()
            
            return Response(success=True, response=self.filename)
        except Exception as e:
            print(f"Error downloading video: {e}")
            response = Response(success=False)
            response.add_error(
                error_type="DownloadError",
                message="An error occurred while downloading the video.",
                details=str(e)
            )
            return response
        
    def _is_h264(self):
        """Checks if the downloaded video is already H.264."""
        codec_info = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name", "-of", "csv=p=0", self.filename],
            capture_output=True, text=True
        ).stdout.strip()
        
        return codec_info == "h264"
    
    def _convert_to_h264(self):
        """Converts the video to H.264 using ffmpeg."""
        output_file = f"Converted_{self.filename.replace('.mp4', '')}.mp4"
        
        command = [
            "ffmpeg", "-i", self.filename,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-strict", "-2",
            output_file
        ]
        
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(self.filename)
        os.rename(output_file, self.filename)

        return output_file
    
    def compress(self, target_bitrate="1M"):
        """Compresses the media using ffmpeg and returns the new file path."""
        if not os.path.exists(self.filename):
            raise FileNotFoundError("Downloaded media not found.")
        
        output_filename = f"Compressed_{self.filename.replace('.mp4', '')}.mp4"
        
        command = [
            "ffmpeg", "-i", self.filename,
            "-c:v", "libx264", "-b:v", target_bitrate,  # Convert AV1 → H.264
            "-c:a", "aac", "-strict", "-2",
            output_filename
        ]
        
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(self.filename)
        os.rename(output_filename, self.filename)
        file_size = os.path.getsize(self.filename) / (1024 * 1024)
        self.filesize = file_size
        return Response(success=True)
    
    def delete_file(self):
        """Deletes the downloaded and/or compressed video file."""
        if os.path.exists(self.filename):
            os.remove(self.filename)


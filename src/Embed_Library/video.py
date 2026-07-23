import os
import json
import yt_dlp
import subprocess
import uuid
import ffmpeg  # Still using this for probe, but not for encoding
from response_handler import Response


class Video:
    """A class to download and compress videos."""

    COOKIES_FILENAME = "instagram.txt"

    def __init__(self, url, MAX_FILE_SIZE_MB=25):
        self.id = uuid.uuid4().hex
        self.url = url
        self.title = None
        self.duration = None
        self.uploader = None
        self.site = None
        self.filename = f"downloaded_video_{self.id}.mp4"
        self.MAX_FILE_SIZE_MB = MAX_FILE_SIZE_MB
        self.filesize = 0.0  # We'll store the final size (MB) here
        self.init_response = self._extract_metadata()

    @classmethod
    def cookies_path(cls):
        """Return path to session cookies file if it exists."""
        # src/Embed_Library/video.py -> project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        path = os.path.join(project_root, "session_cookies", cls.COOKIES_FILENAME)
        return path if os.path.isfile(path) else None

    def _base_ydl_opts(self, **extra):
        opts = {"quiet": True, "noplaylist": True, "no_warnings": True}
        opts.update(extra)
        cookies = self.cookies_path()
        if cookies:
            opts["cookiefile"] = cookies
        return opts

    def get_os_filesize(self):
        """Returns the file size of the video in MB."""
        return os.path.getsize(self.filename) / (1024 * 1024) if self.exists_locally() else 0.0

    def _extract_metadata(self):
        """Extracts metadata for any supported video link without downloading."""
        try:
            with yt_dlp.YoutubeDL(self._base_ydl_opts()) as ydl:
                info_dict = ydl.extract_info(self.url, download=False)

            self.title = info_dict.get("title")
            self.duration = info_dict.get("duration")
            self.uploader = info_dict.get("uploader")
            self.site = info_dict.get("extractor_key")
            self.filename = f"downloaded_video_{self.id}.{info_dict.get('ext', 'mp4')}"
            filesize = info_dict.get("filesize") or info_dict.get("filesize_approx") or 0
            self.filesize = filesize / (1024 * 1024)  # Convert bytes to MB
            return Response(success=True)
        except Exception as e:
            response = Response(success=False)
            response.add_error(
                error_type="MetadataError",
                message=(
                    "Couldn't fetch that video (site may be blocking downloads, "
                    "or cookies may need refreshing)."
                ),
                details=str(e),
            )
            return response

    def exists_locally(self):
        """Checks if the video file exists locally."""
        return os.path.exists(self.filename)

    def is_video(self):
        """Returns True if the URL is a video, False otherwise."""
        try:
            with yt_dlp.YoutubeDL(self._base_ydl_opts()) as ydl:
                info = ydl.extract_info(self.url, download=False)  # Get metadata only

                # Check if there are video streams available
                if (
                    "video" in info.get("categories", [])
                    or info.get("vcodec", "none") != "none"
                    or info.get("ext", "none") == "mp4"
                ):
                    return Response(success=True, response=True)
                return Response(success=True, response=False)
        except Exception as e:
            response = Response(success=False)
            response.add_error(
                error_type="VideoCheckError",
                message="An error occurred while checking the video",
                details=str(e),
            )
            return response

    def get_video_resolution(self):
        """Extracts the resolution of the downloaded video file using ffmpeg-python's probe."""
        if not os.path.exists(self.filename):
            return None

        try:
            probe = ffmpeg.probe(self.filename)
            video_streams = [stream for stream in probe["streams"] if stream["codec_type"] == "video"]
            if not video_streams:
                return None

            width = int(video_streams[0]["width"])
            height = int(video_streams[0]["height"])
            return width, height
        except Exception as e:
            print(f"Error probing video: {e}")
            return None

    def download_audio(self):
        """Downloads and extracts audio as MP3 before returning the file path."""

        if not self.init_response.success:
            return self.init_response

        is_video_response = self.is_video()
        if not is_video_response.success:
            return is_video_response
        if not is_video_response.response:
            response = Response(success=False)
            response.add_error(
                error_type="NotVideoError",
                message="The provided URL is not a video."
            )
            return response

        # Use a dedicated audio basename. FFmpegExtractAudio rewrites the extension to .mp3,
        # so we must not keep pointing at the original .mp4 metadata filename.
        audio_basename = f"downloaded_audio_{self.id}"
        self.filename = f"{audio_basename}.mp3"

        ydl_opts = self._base_ydl_opts(
            format="bestaudio/best",
            outtmpl=f"{audio_basename}.%(ext)s",
            postprocessors=[{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        )

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])

            if not os.path.exists(self.filename):
                # Fallback if yt-dlp left a slightly different name
                for candidate in (
                    f"{audio_basename}.mp3",
                    f"{audio_basename}.m4a",
                    f"{audio_basename}.webm",
                    f"{audio_basename}.opus",
                ):
                    if os.path.exists(candidate):
                        self.filename = candidate
                        break

            if not os.path.exists(self.filename):
                response = Response(success=False)
                response.add_error(
                    error_type="DownloadError",
                    message="Audio download finished but the output file was not found.",
                )
                return response

            file_size = self.get_os_filesize()
            if file_size > self.MAX_FILE_SIZE_MB:
                self.delete_file()
                response = Response(success=False)
                response.add_error(
                    error_type="FileTooLarge",
                    message="File is too large. Please try again with a smaller file."
                )
                return response

            return Response(success=True, response=self.filename)

        except Exception as e:
            print(f"Error downloading audio: {e}")
            self.delete_file()
            response = Response(success=False)
            response.add_error(
                error_type="DownloadError",
                message="An error occurred while downloading the audio.",
                details=str(e)
            )
            return response

    def adjust_resolution(self, target_height=720, target_bitrate="800k"):
        """Scales the video resolution down while maintaining aspect ratio and reducing bitrate."""
        if not os.path.exists(self.filename):
            raise FileNotFoundError("Downloaded video not found.")

        resolution = self.get_video_resolution()
        if not resolution or resolution[1] <= target_height:
            return self.filename  # No need to scale if already small enough

        output_filename = f"Resized_{self.filename}"
        try:
            # ffmpeg -i <input> -vf scale=-2:<target_height> -c:v libx264 -preset fast -b:v <target_bitrate> 
            #        -c:a aac -b:a 96k -movflags +faststart -profile:v main -level:v 4.1 -pix_fmt yuv420p <output>
            command = [
                "ffmpeg", "-y",  # -y to overwrite output
                "-i", self.filename,
                "-vf", f"scale=-2:{target_height}",
                "-c:v", "libx264", "-preset", "fast", "-b:v", target_bitrate,
                "-profile:v", "main", "-level:v", "4.1", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "96k",
                "-movflags", "+faststart",
                output_filename
            ]

            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            self.delete_file()
            os.rename(output_filename, self.filename)

            # Debug: Print new resolution & file size
            new_resolution = self.get_video_resolution()
            print(f"New resolution after scaling: {new_resolution}")
            print(f"New file size after scaling: {self.get_os_filesize()} MB")

        except subprocess.CalledProcessError as e:
            print(f"Error resizing video: {e}")

        return self.filename

    def download(self):
        """Downloads media if it fits the Discord upload limit.

        Temporary: oversized files are rejected instead of being resized/compressed,
        since that pipeline is unreliable on the current host.
        """

        if not self.init_response.success:
            return self.init_response

        # Reject early when yt-dlp already knows the file is too big
        if self.filesize and self.filesize > self.MAX_FILE_SIZE_MB:
            response = Response(success=False)
            response.add_error(
                error_type="FileTooLarge",
                message=(
                    f"That video is about {self.filesize:.1f} MB, which is over this "
                    f"server's {self.MAX_FILE_SIZE_MB:.0f} MB upload limit. "
                    "Compression is temporarily disabled, so please try a smaller video."
                ),
            )
            return response

        is_video_response = self.is_video()
        if not is_video_response.success:
            return is_video_response
        if not is_video_response.response:
            response = Response(success=False)
            response.add_error(
                error_type="NotVideoError",
                message="The provided URL is not a video."
            )
            return response

        # Force MP4 extension if needed
        outtmpl = f"{self.filename}.mp4" if not self.filename.endswith(".mp4") else self.filename
        ydl_opts = self._base_ydl_opts(
            format="bestvideo+bestaudio/best",
            outtmpl=outtmpl,
            merge_output_format="mp4",
        )

        try:
            # Download video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])

            if not self.exists_locally():
                response = Response(success=False)
                response.add_error(
                    error_type="DownloadError",
                    message="An error occurred while downloading the video."
                )
                return response

            # Ensure H.264 Compatibility for Discord playback
            is_h264_response = self.get_codec()
            if is_h264_response.success and is_h264_response.response != "h264":
                print("Downloaded video is NOT H.264! Converting...")
                conversion_response = self._convert_to_h264()
                if not conversion_response.success:
                    return conversion_response

            file_size = self.get_os_filesize()
            if file_size > self.MAX_FILE_SIZE_MB:
                # Temporary: do not resize/compress oversized media on this host.
                print(
                    f"Video is too large ({file_size:.1f} MB > "
                    f"{self.MAX_FILE_SIZE_MB:.0f} MB). Skipping compression and deleting."
                )
                self.delete_file()
                response = Response(success=False)
                response.add_error(
                    error_type="FileTooLarge",
                    message=(
                        f"File is too large ({file_size:.1f} MB). "
                        f"This server's upload limit is {self.MAX_FILE_SIZE_MB:.0f} MB. "
                        "Auto-compression is temporarily disabled."
                    ),
                )
                return response

            return Response(success=True, response=self.filename)

        except Exception as e:
            print(f"Error downloading video: {e}")
            if self.exists_locally():
                self.delete_file()
            response = Response(success=False)
            response.add_error(
                error_type="DownloadError",
                message="An error occurred while downloading the video.",
                details=str(e)
            )
            return response
        
    def get_codec(self):
        """Extracts the codec of the downloaded video file using ffmpeg-python's probe."""
        try:
            probe = ffmpeg.probe(self.filename)
            codec_info = next(
                (stream['codec_name'] for stream in probe['streams'] if stream['codec_type'] == 'video'),
                None
            )
            return Response(success=True, response=codec_info)
        except Exception as e:
            response = Response(success=False)
            response.add_error(
                error_type="FFprobeError",
                message="An error occurred while checking the codec.",
                details=str(e)
            )
            return response

    def _convert_to_h264(self):
        """Converts the video to H.264 using subprocess with system-installed ffmpeg."""
        output_file = f"Converted_{self.filename.replace('.mp4', '')}.mp4"

        try:
            command = [
                "ffmpeg", "-i", self.filename,
                "-vf", "scale=-2:720,fps=30", # Resize to 720p and 30fps
                "-c:v", "libx264", "-preset", "fast",
                "-profile:v", "main", "-level:v", "4.1", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart",
                output_file
            ]

            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            # Replace old file with converted file
            self.delete_file()
            os.rename(output_file, self.filename)

            return Response(success=True, response=self.filename)

        except subprocess.CalledProcessError as e:
            response = Response(success=False)
            response.add_error(
                error_type="H264ConversionError",
                message="An error occurred while converting to H.264.",
                details=str(e)
            )
            return response

    def compress(self, target_bitrate="1M"):
        """Compresses the media using ffmpeg and returns the new file path."""
        if not self.exists_locally():
            raise FileNotFoundError("Downloaded media not found.")

        output_filename = f"Compressed_{self.filename.replace('.mp4', '')}.mp4"

        # ffmpeg -i <input> -c:v libx264 -preset fast -profile:v main -level:v 4.1 
        #        -pix_fmt yuv420p -b:v <target_bitrate> -c:a aac -b:a 96k -movflags +faststart <output>
        command = [
            "ffmpeg", "-y",
            "-i", self.filename,
            "-c:v", "libx264", "-preset", "fast",
            "-profile:v", "main", "-level:v", "4.1", "-pix_fmt", "yuv420p",
            "-b:v", target_bitrate,
            "-c:a", "aac", "-b:a", "96k",
            "-movflags", "+faststart",
            output_filename
        ]

        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        self.delete_file()
        os.rename(output_filename, self.filename)
        file_size = os.path.getsize(self.filename) / (1024 * 1024)
        self.filesize = file_size
        return Response(success=True)

    def delete_file(self):
        """Delete the active output and any leftover video/audio files for this download."""
        candidates = set()
        if self.filename:
            candidates.add(self.filename)

        # Cover both video and audio outputs, plus common intermediates for this id.
        for prefix in (
            f"downloaded_video_{self.id}",
            f"downloaded_audio_{self.id}",
            f"Resized_downloaded_video_{self.id}",
            f"Converted_downloaded_video_{self.id}",
            f"Compressed_downloaded_video_{self.id}",
        ):
            for ext in (".mp4", ".mp3", ".m4a", ".webm", ".opus", ".mkv", ".mov", ".wav", ".part"):
                candidates.add(f"{prefix}{ext}")

        # Catch anything else in the cwd that includes this download id
        try:
            for name in os.listdir("."):
                if self.id in name and os.path.isfile(name):
                    candidates.add(name)
        except OSError:
            pass

        for path in candidates:
            if os.path.isfile(path):
                try:
                    os.remove(path)
                except OSError as e:
                    print(f"Failed to delete {path}: {e}")

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "title": self.title,
            "duration": self.duration,
            "uploader": self.uploader,
            "site": self.site,
            "filename": self.filename,
            "filesize": self.filesize
        }

    def __str__(self):
        return json.dumps(self.to_dict(), indent=4)

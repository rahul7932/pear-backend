import ffmpeg

def extract_audio(video_path, audio_output_path):
    """
    Extracts the audio from the given MP4 file and saves it as an MP3 file.

    :param video_path: Path to the input MP4 file.
    :param audio_output_path: Path to save the extracted audio file.
    """
    # Extract audio stream in MP3 format
    ffmpeg.input(video_path).output(audio_output_path, acodec='libmp3lame').run()

# Example usage
extract_audio('../data/input.mp4', '../data/output_audio.mp3')
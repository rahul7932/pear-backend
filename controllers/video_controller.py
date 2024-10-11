import ffmpeg
import os

def extract_audio(video_path, audio_output_path):
    """
    Extracts the audio from the given MP4 file and saves it as an MP3 file.

    :param video_path: Path to the input MP4 file.
    :param audio_output_path: Path to save the extracted audio file.
    """
    # Extract audio stream in MP3 format
    ffmpeg.input(video_path).output(audio_output_path, acodec='libmp3lame').run()

def extract_screenshots(input_file, output_folder):
    """
    Takes a screenshot of the video every 2 seconds and stores them in the specified directory.

    :param input_file: Path to the input video file.
    :param output_folder: Directory to save the screenshots.
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Extract screenshots every 2 seconds
    (
        ffmpeg
        .input(input_file)
        .output(f'{output_folder}/screenshot%04d.png', vf='fps=1')
        .run()
    )

# Example usage
extract_screenshots('../data/input.mp4', '../data/input/screenshots')

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

def process_video(video_path, screenshot_to_time_map):
    """
    Process video by extracting audio chunks based on screenshot timestamps.

    This function takes a dictionary mapping screenshot URLs to their corresponding
    start and end times in the video. For each entry, it extracts the audio chunk
    from the recording and saves it to a temporary directory with the filename
    format 'start_time-end_time.mp3'.

    Args:
        screenshot_to_time_map (dict): A dictionary where keys are screenshot URLs
                                       and values are tuples of (start_time, end_time).

    Returns:
        dict: A dictionary mapping screenshot URLs to the paths of their
              corresponding extracted audio files.

    Note:
        This function assumes that the necessary video processing libraries
        (e.g., ffmpeg-python) are imported and available.
    """
    temp_audio_dir = "temp_audio_chunks"
    os.makedirs(temp_audio_dir, exist_ok=True)
    
    audio_file_map = {}
    
    for screenshot_url, (start_time, end_time) in screenshot_to_time_map.items():
        output_filename = f"{start_time}-{end_time}.mp3"
        output_path = os.path.join(temp_audio_dir, output_filename)
        
        # Extract audio chunk
        (
            ffmpeg
            .input(video_path, ss=start_time, t=end_time-start_time)
            .output(output_path, acodec='libmp3lame')
            .run(overwrite_output=True)
        )
        
        audio_file_map[screenshot_url] = output_path
    
    return audio_file_map

def generate_audio_summary(video_path, start_time, end_time):
    """Extract and summarize the audio portion between start_time and end_time."""
    return

def transcribe_audio(video_clip):
    #Insert audio to text model 
    return "Transcribed text of the audio from the video clip."
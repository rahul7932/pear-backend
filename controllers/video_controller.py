import ffmpeg
import os
from openai import OpenAI
import base64
from typing import List, Dict, Tuple

client = OpenAI(api_key='')

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

def group_images(images: List[str]) -> Dict[str, Tuple[int, int]]:
    """
    Given an ordered list of images (taken at 1-second intervals) that contain screenshots from a video detailing a workflow,
    remove unnecessary screenshots (where the screen doesn't change).
    Generate start and end times for each screen we keep and return a dictionary using GPT-4V as the VLM.
    
    :param images: list of image paths (ordered by time)
    :return: dictionary mapping each image path to a tuple (start_time, end_time)
    """
    screen_changes = {}
    previous_summary = None
    screen_start_time = None
    current_image_path = None
    previous_image_path = None

    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    for i, image_path in enumerate(images):
        timestamp = i
        base64_image = encode_image(image_path)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Please summarize this screenshot."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ],
                }
            ],
            max_tokens=300,
        )
        current_summary = response.choices[0].message.content.strip()

        if previous_summary is None:
            previous_summary = current_summary
            screen_start_time = timestamp
            previous_image_path = image_path
            continue

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f'Did the screen change between these two images: "{previous_summary}" and this new screenshot? Answer with "Yes" or "No". Respond with only lowercase yes or lowercase no followed by no punctuation'},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ],
                }
            ],
            max_tokens=300,
        )
        screen_changed = response.choices[0].message.content.strip().lower() == 'yes'

        if screen_changed:
            screen_changes[previous_image_path] = (screen_start_time, timestamp - 1)  # Correct interval for the previous screen
            # Update the start time and summary for the new screen
            screen_start_time = timestamp
            previous_summary = current_summary
            previous_image_path = image_path
        else:
            continue

    if screen_start_time is not None:
        screen_changes[previous_image_path] = (screen_start_time, len(images) - 1)  

    return screen_changes


#Get the first 20 images from screenshots folder. Here is the folder's relative path pear-backend/screenshots
images = ['../screenshots/' + img for img in sorted(os.listdir('../screenshots'))[:20]]
grouped_images = group_images(images)
print(grouped_images)
print(images)


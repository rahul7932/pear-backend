import base64
from typing import Dict, List, Tuple, Union, Any
import ffmpeg
import os
from openai import OpenAI
import json

client = OpenAI()

def extract_audio(video_path: str, audio_output_path: str) -> None:
    """
    Extracts the audio from the given MP4 file and saves it as an MP3 file.
    """
    ffmpeg.input(video_path).output(audio_output_path, acodec='libmp3lame').run()

def extract_screenshots(input_file: str, output_folder: str) -> None:
    """
    Takes a screenshot of the video every 3 seconds and stores them in the specified directory.
    """
    os.makedirs(output_folder, exist_ok=True)
    (
        ffmpeg
        .input(input_file)
        .filter('fps', fps=1/3)
        .output(f'{output_folder}/screenshot%04d.png')
        .run()
    )

def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def group_images(images: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Group images and generate summaries.
    """
    sorted_images = sorted(images)
    screen_changes = {}
    previous_summary = None
    screen_start_time = None

    for i, image_path in enumerate(sorted_images):
        timestamp = i
        base64_image = encode_image(image_path)
        print(f"Processing image {i+1} of {len(images)}: {image_path}")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "SUMMARIZE THIS SCREENSHOT."},
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
            continue

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f'DID THE SCREEN CHANGE BETWEEN THESE TWO IMAGES: "{previous_summary}" AND THIS NEW SCREENSHOT? ANSWER WITH "YES" OR "NO". RESPOND WITH ONLY LOWERCASE YES OR LOWERCASE NO FOLLOWED BY NO PUNCTUATION'},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ],
                }
            ],
            max_tokens=300,
        )
        screen_changed = response.choices[0].message.content.strip().lower() == 'yes'

        if screen_changed:
            screen_changes[sorted_images[i-1]] = {
                "interval": (screen_start_time, timestamp - 1),
                "summary": previous_summary
            }
            screen_start_time = timestamp
            previous_summary = current_summary

    if screen_start_time is not None:
        screen_changes[sorted_images[-1]] = {
            "interval": (screen_start_time, len(sorted_images) - 1),
            "summary": previous_summary
        }

    return screen_changes

def process_video(video_path: str, screenshot_to_time_map: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
    """
    Process video by extracting audio chunks based on screenshot timestamps.
    """
    temp_audio_dir = "temp_audio_chunks"
    os.makedirs(temp_audio_dir, exist_ok=True)
    
    audio_file_map = {}
    
    for screenshot_url, info in screenshot_to_time_map.items():
        start_time, end_time = info['interval']
        output_filename = f"{start_time}-{end_time}.mp3"
        output_path = os.path.join(temp_audio_dir, output_filename)
        
        (
            ffmpeg
            .input(video_path, ss=start_time, t=end_time-start_time)
            .output(output_path, acodec='libmp3lame')
            .run(overwrite_output=True)
        )
        
        audio_file_map[f"{start_time}-{end_time}"] = output_path
    
    return audio_file_map

def transcribe_audio_files(audio_file_map: Dict[str, str], video_duration: float) -> Dict[str, str]:
    """
    Transcribe audio files using OpenAI's Whisper model, including 5 seconds after each interval if available.
    """
    transcriptions = {}
    
    # Sort intervals by start time
    sorted_intervals = sorted(audio_file_map.keys(), key=lambda x: int(x.split('-')[0]))
    
    for i, interval_str in enumerate(sorted_intervals):
        start, end = map(int, interval_str.split('-'))
        
        # Determine the extended end time (5 seconds more or until the next interval starts)
        if i < len(sorted_intervals) - 1:
            next_start = int(sorted_intervals[i+1].split('-')[0])
            extended_end = min(end + 5, next_start, int(video_duration))
        else:
            extended_end = min(end + 5, int(video_duration))
        
        # If we can extend the audio, do so
        if extended_end > end:
            temp_extended_audio = f"temp_extended_{interval_str}.mp3"
            (
                ffmpeg
                .input(audio_file_map[interval_str])
                .filter('atrim', duration=extended_end-start)
                .output(temp_extended_audio)
                .overwrite_output()
                .run(quiet=True)
            )
            audio_to_transcribe = temp_extended_audio
        else:
            audio_to_transcribe = audio_file_map[interval_str]
        
        with open(audio_to_transcribe, 'rb') as audio:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                response_format="text"
            )
            transcriptions[interval_str] = response
        
        # Clean up temporary file if it was created
        if extended_end > end:
            os.remove(temp_extended_audio)

    print("\n--- Transcription results ---")
    print(json.dumps(transcriptions, indent=2))

    return transcriptions

def combine_workflow_data(screenshot_info: Dict[str, Dict[str, Any]], 
                          transcriptions: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Combine screenshot info and transcriptions into a single workflow data structure.
    """
    combined_data = []
    
    for screenshot_path, info in screenshot_info.items():
        start_time, end_time = info['interval']
        interval_str = f"{start_time}-{end_time}"
        combined_data.append({
            "screenshot": screenshot_path,
            "interval": {"start": start_time, "end": end_time},
            "summary": info['summary'],
            "transcription": transcriptions.get(interval_str, "")
        })
    
    return combined_data

def process_workflow(video_path: str, screenshot_dir: str) -> List[Dict[str, Any]]:
    """
    Process a video file: extract screenshots, group images, process audio, and transcribe.
    """
    # Get video duration
    video_duration = get_video_duration(video_path)

    # Extract screenshots
    extract_screenshots(video_path, screenshot_dir)

    # Get list of screenshot paths
    screenshot_paths = [os.path.join(screenshot_dir, f) for f in os.listdir(screenshot_dir) if f.endswith('.png')]

    # Group images
    grouped_images = group_images(screenshot_paths)

    # Process video to get audio clips
    audio_file_map = process_video(video_path, grouped_images)

    # Transcribe audio clips
    transcriptions = transcribe_audio_files(audio_file_map, video_duration)  # Pass video_duration here

    # Combine workflow data
    return combine_workflow_data(grouped_images, transcriptions)

def get_video_duration(video_path: str) -> float:
    """Get the duration of the video in seconds."""
    probe = ffmpeg.probe(video_path)
    video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    return float(video_info['duration'])

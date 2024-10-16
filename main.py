from fastapi import FastAPI, UploadFile, File, HTTPException
import os
import tempfile
import json
from pathlib import Path
from controllers.video_controller import extract_audio, extract_screenshots, group_images, process_video, transcribe_audio_files, combine_workflow_data
from controllers.lavague_controller import run_lavague_workflow  # Import the new function

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to the Workflow Creation API"}

@app.post("/create_new_workflow")
async def create_new_workflow(workflow_data: dict):
    print("\n--- Starting new workflow creation ---\n")

    video_filename = workflow_data.get("video_filename", "input.mp4")
    data_dir = Path("data")
    video_path = data_dir / video_filename

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    print(f"Processing video: {video_filename}")

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"\nCreated temporary directory: {temp_dir}")

        # Copy the video to the temp directory
        temp_video_path = os.path.join(temp_dir, video_filename)
        with open(video_path, "rb") as src_file, open(temp_video_path, "wb") as dst_file:
            dst_file.write(src_file.read())
        
        print(f"Copied video to: {temp_video_path}")

        # Extract audio
        audio_path = os.path.join(temp_dir, f"{video_filename}.mp3")
        extract_audio(temp_video_path, audio_path)
        print(f"Extracted audio to: {audio_path}")
        
        # Extract screenshots
        screenshots_dir = os.path.join(temp_dir, "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        extract_screenshots(temp_video_path, screenshots_dir)
        print(f"Extracted screenshots to: {screenshots_dir}")

        # Group images
        screenshot_paths = [os.path.join(screenshots_dir, f) for f in os.listdir(screenshots_dir) if f.endswith('.png')]
        screenshot_info = group_images(screenshot_paths)
        print("\n--- Screenshot grouping results ---")
        print(json.dumps(screenshot_info, indent=2))

        # Process video to get audio clips
        audio_clips_dir = os.path.join(temp_dir, "audio_clips")
        os.makedirs(audio_clips_dir, exist_ok=True)
        audio_file_map = process_video(temp_video_path, screenshot_info)
        print("\n--- Audio file mapping ---")
        print(json.dumps({k: v for k, v in audio_file_map.items()}, indent=2))

        # Transcribe audio clips
        transcriptions = transcribe_audio_files(audio_file_map)
        print("\n--- Transcription results ---")
        print(json.dumps({k: v for k, v in transcriptions.items()}, indent=2))

        # Combine all the data
        combined_workflow_data = combine_workflow_data(screenshot_info, transcriptions)
        print("\n--- Combined workflow data ---")
        print(json.dumps(combined_workflow_data, indent=2))

        print("\n--- Workflow creation completed ---\n")

        return {
            "status": "Success",
            "video_filename": video_filename,
            "workflow_data": combined_workflow_data
        }

@app.post("/run_workflow")
async def execute_lavague_workflow(workflow_data: dict):
    print("\n--- Starting La Vague workflow execution ---\n")

    trace = workflow_data.get("trace")
    hint = workflow_data.get("hint")
    url = workflow_data.get("url")

    if not trace or not hint or not url:
        raise HTTPException(status_code=400, detail="Missing required parameters: trace, hint, or url")

    try:
        # Convert trace to string if it's not already
        if isinstance(trace, dict):
            trace = json.dumps(trace)
        
        # Run the La Vague workflow
        result = run_lavague_workflow(trace, hint, url)
        
        print("\n--- La Vague workflow execution completed ---\n")

        return {
            "status": "Success",
            "workflow_result": result
        }
    except Exception as e:
        print(f"Error during La Vague workflow execution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during workflow execution: {str(e)}")

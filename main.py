from fastapi import FastAPI, UploadFile, File
from moviepy.editor import VideoFileClip
from transformers import pipeline
import uuid
import os

app = FastAPI()

text_summarizer = pipeline("summarization", model="facebook/bart-large-cnn")


# API endpoint to accept video and screenshots
@app.post("/upload/")
async def upload_workflow(video: UploadFile = File(...), screenshots: list[UploadFile] = File(...), times: list[dict] = None):
    video_path = f"temp/{video.filename}"
    os.makedirs("temp", exist_ok=True)
    
    # Save the video file temporarily
    with open(video_path, "wb") as f:
        f.write(await video.read())

    workflow = Workflow()
    previous_screenshot_id = None

    # Process each screenshot and corresponding time
    for i, screenshot in enumerate(screenshots):
        screenshot_id = str(uuid.uuid4())  # Generate unique screenshot ID
        start_time = times[i]['start_time']
        end_time = times[i]['end_time']

        # Save screenshot temporarily
        screenshot_path = f"temp/{screenshot.filename}"
        with open(screenshot_path, "wb") as f:
            f.write(await screenshot.read())

        # Generate audio summary for the time period
        summary = generate_audio_summary(video_path, start_time, end_time)

        # Add to the workflow
        workflow.add_node(screenshot_id, start_time, end_time, video_path, summary, previous_screenshot_id)

        # Insert the screenshot data into Supabase
        supabase.table('workflow').insert({
            "screenshotID": screenshot_id,
            "start_time": start_time,
            "end_time": end_time,
            "video_url": video_path,  # Replace with your Supabase video storage link if needed
            "video_summary": summary,
            "next_screenshotID": previous_screenshot_id  # Point to the previous screenshot
        }).execute()

        # Update the previous screenshot ID for the next iteration
        previous_screenshot_id = screenshot_id

    return {"status": "Success"}


from fastapi import FastAPI, UploadFile, File
from supabase import create_client, Client
from moviepy.editor import VideoFileClip
from transformers import pipeline
import uuid
import os

app = FastAPI()
SUPABASE_URL = "https://<your-project>.supabase.co"
SUPABASE_KEY = "<your-anon-key>"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

text_summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

class WorkflowNode:
    def __init__(self, screenshot_id, start_time, end_time, video_url, action_summary, next_screenshot_id=None):
        self.screenshot_id = screenshot_id
        self.start_time = start_time
        self.end_time = end_time
        self.video_url = video_url
        self.action_summary = action_summary
        self.next_screenshot_id = next_screenshot_id

class Workflow:
    def __init__(self):
        self.head = None
        self.nodes = []

    def add_node(self, screenshot_id, start_time, end_time, video_url, action_summary, next_screenshot_id=None):
        new_node = WorkflowNode(screenshot_id, start_time, end_time, video_url, action_summary, next_screenshot_id)
        if not self.head:
            self.head = new_node
        else:
            current = self.head
            while current.next_screenshot_id:
                current = current.next_screenshot_id
            current.next_screenshot_id = new_node.screenshot_id
        self.nodes.append(new_node)
def generate_audio_summary(video_path, start_time, end_time):
    """Extract and summarize the audio portion between start_time and end_time."""
    video = VideoFileClip(video_path).subclip(start_time, end_time)
    audio_text = transcribe_audio(video) 
    summary = text_summarizer(audio_text, max_length=100, min_length=30, do_sample=False)
    
    return summary[0]['summary_text']

def transcribe_audio(video_clip):
    #Insert audio to text model 
    return "Transcribed text of the audio from the video clip."

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


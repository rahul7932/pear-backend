from typing import Dict, Any
from lavague.drivers.selenium import SeleniumDriver
from lavague.core import ActionEngine, WorldModel
from lavague.core.agents import WebAgent
from openai import OpenAI
import json

class PromptOptimizer:
    def __init__(self):
        self.client = OpenAI()

    def gpt_api_call(self, prompt: str) -> str:
        """Make a call to the GPT API."""
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content

    def generate_main_objective(self, trace: str, hint: str) -> str:
        """Generate the main objective based on the trace and hint."""
        prompt = (
            f"{trace}\n"
            "GIVEN A SET OF SEQUENTIAL ACTIONS DESCRIBED IN THE JSON TRACE ABOVE, "
            "YOUR TASK IS TO GENERATE A COMPACT BUT DESCRIPTIVE MAIN OBJECTIVE OF THE ACTION "
            f"WHILE EMPHASIZING AND INCORPORATING THE HINT: {hint}."
        )
        return self.gpt_api_call(prompt)

    def generate_context(self, trace: str, hint: str) -> str:
        """Generate the context based on the trace and hint."""
        prompt = (
            f"{trace}\n"
            "GIVEN A SET OF SEQUENTIAL ACTIONS DESCRIBED IN THE JSON TRACE ABOVE, "
            "YOUR TASK IS TO GENERATE A COMPACT LIST OF ACTIONS WHILE INCORPORATING "
            f"THE HINT: {hint}. TO DO THIS, FOLLOW THE FOLLOWING:\n"
            "1. UNDERSTAND THE CONTEXT: BEGIN BY UNDERSTANDING THE SEQUENCE OF ACTIONS "
            "PROVIDED IN THE TRACE. THIS WILL GIVE YOU A BASELINE FOR INTERACTING WITH "
            "THE WEBSITE AND PERFORMING THE INITIAL STEPS.\n"
            "2. INCORPORATE THE HINT: AS YOU PROCEED THROUGH THE STEPS, KEEP THE HINT IN MIND. "
            "THE HINT MAY REQUIRE ACTIONS OUTSIDE THE ORIGINAL SEQUENCE, SO BE PREPARED TO "
            "DEVIATE AS NECESSARY.\n"
            "3. FINALLY, OUTPUT A CONCISE LIST OF ACTIONS TO TAKE TO ACHIEVE THIS MAIN OBJECTIVE."
        )
        return self.gpt_api_call(prompt)

    def create_lavague_prompt(self, trace: str, hint: str) -> str:
        """Create the final prompt for La Vague."""
        main_objective = self.generate_main_objective(trace, hint)
        context = self.generate_context(trace, hint)
        
        return (
            f"CONTEXT: {context}\n"
            f"OBJECTIVE: {main_objective}\n"
            "INSTRUCTIONS: ADAPT DYNAMICALLY: EXPLORE THE INTERFACE BEYOND THE EXACT STEPS "
            "PROVIDED IN THE TRACE. WHILE FOLLOWING THE GENERAL FLOW OF ACTIONS, ALWAYS BE "
            "AWARE OF THE END GOAL DESCRIBED IN THE HINT, AND ADJUST YOUR STEPS ACCORDINGLY. "
            "EXPLORATION IS ENCOURAGED WHERE NECESSARY. THINK STEP BY STEP."
        )

    def run_agent(self, url: str, lavague_prompt: str) -> Any:
        """Run the La Vague agent with the given prompt."""
        driver = SeleniumDriver(headless=False)
        action_engine = ActionEngine(driver)
        world_model = WorldModel()
        agent = WebAgent(world_model, action_engine)
        
        agent.get(url)
        return agent.run(lavague_prompt)

def optimize_prompt(workflow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Main function to optimize the prompt and run the agent."""
    hint = workflow_data.get("hint", "")
    trace = workflow_data.get("trace", "")
    url = workflow_data.get("url", "")

    optimizer = PromptOptimizer()
    lavague_prompt = optimizer.create_lavague_prompt(trace, hint)
    result = optimizer.run_agent(url, lavague_prompt)

    return {
        "status": "Success",
        "lavague_prompt": lavague_prompt,
        "result": result
    }

# Load the trace data
with open('../data/demo_trace.json', 'r') as file:
    trace_data = json.load(file)

# Create the workflow_data dictionary
workflow_data = {
    "hint": "Search for 'The Great Gatsby' by F. Scott Fitzgerald and find its average rating",
    "trace": json.dumps(trace_data),  # Convert the trace data to a JSON string
    "url": trace_data["start_url"]  # Use the start_url from the trace data
}

# Now you can use this workflow_data to call optimize_prompt
result = optimize_prompt(workflow_data)

print(result)

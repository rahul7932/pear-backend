from typing import Dict, Any
from lavague.drivers.selenium import SeleniumDriver
from lavague.core import ActionEngine, WorldModel
from lavague.core.agents import WebAgent
from openai import OpenAI
import json

client = OpenAI()

def gpt_api_call(prompt: str) -> str:
    """Make a call to the GPT API."""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content

def generate_main_objective(trace: str, hint: str) -> str:
    """Generate the main objective based on the trace and hint."""
    prompt = (
        f"{trace}\n"
        "GIVEN A SET OF SEQUENTIAL ACTIONS DESCRIBED IN THE JSON TRACE ABOVE, "
        "YOUR TASK IS TO GENERATE A COMPACT BUT DESCRIPTIVE MAIN OBJECTIVE OF THE ACTION "
        f"WHILE EMPHASIZING AND INCORPORATING THE HINT: {hint}."
    )
    return gpt_api_call(prompt)

def generate_context(trace: str, hint: str) -> str:
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
    return gpt_api_call(prompt)

def create_lavague_prompt(trace: str, hint: str) -> str:
    """Create the final prompt for La Vague."""
    main_objective = generate_main_objective(trace, hint)
    context = generate_context(trace, hint)
    
    return (
        f"CONTEXT: {context}\n"
        f"OBJECTIVE: {main_objective}\n"
        "INSTRUCTIONS: ADAPT DYNAMICALLY: EXPLORE THE INTERFACE BEYOND THE EXACT STEPS "
        "PROVIDED IN THE TRACE. WHILE FOLLOWING THE GENERAL FLOW OF ACTIONS, ALWAYS BE "
        "AWARE OF THE END GOAL DESCRIBED IN THE HINT, AND ADJUST YOUR STEPS ACCORDINGLY. "
        "EXPLORATION IS ENCOURAGED WHERE NECESSARY. THINK STEP BY STEP."
    )

def run_agent(url: str, lavague_prompt: str) -> Any:
    """Run the La Vague agent with the given prompt."""
    driver = SeleniumDriver(headless=False, user_data_dir = "/Users/rahulkumar/Library/Application Support/Google/Chrome/Profile 2")
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

    lavague_prompt = create_lavague_prompt(trace, hint)
    result = run_agent(url, lavague_prompt)

    return {
        "status": "Success",
        "lavague_prompt": lavague_prompt,
        "result": result
    }

def run_lavague_workflow(trace: str, hint: str, url: str) -> Dict[str, Any]:
    """
    Runner function that executes the entire La Vague workflow.
    
    Args:
    trace (str): A string representation of the sequential actions.
    hint (str): A hint or modification for the actions.
    url (str): The starting URL for the web agent.

    Returns:
    Dict[str, Any]: A dictionary containing the workflow results.
    """
    print("Starting La Vague workflow...")

    workflow_result = {
        "trace": trace,
        "hint": hint,
        "url": url
    }

    try:
        # Step 1: Generate the main objective
        print("Generating main objective...")
        main_objective = generate_main_objective(trace, hint)
        print(f"Main objective: {main_objective}")
        workflow_result["main_objective"] = main_objective

        # Step 2: Generate the context
        print("Generating context...")
        context = generate_context(trace, hint)
        print(f"Context generated: {context[:100]}...")  # Print first 100 chars for brevity
        workflow_result["context"] = context

        # Step 3: Create the La Vague prompt
        print("Creating La Vague prompt...")
        lavague_prompt = create_lavague_prompt(trace, hint)
        print(f"La Vague prompt created: {lavague_prompt[:100]}...")  # Print first 100 chars for brevity
        workflow_result["lavague_prompt"] = lavague_prompt

        # Step 4: Run the La Vague agent
        print("Running La Vague agent...")
        print(url, lavague_prompt)
        agent_result = run_agent(url=url, lavague_prompt=lavague_prompt)
        print("Agent execution completed.")
        workflow_result["agent_result"] = agent_result
        workflow_result["status"] = "success"

    except Exception as e:
        print(f"Error during La Vague workflow execution: {str(e)}")
        workflow_result["status"] = "failed"
        workflow_result["error"] = str(e)

    print("La Vague workflow completed.")
    return workflow_result

# Example usage
if __name__ == "__main__":
    # Load the trace data
    with open('../data/actions.json', 'r') as file:
        trace_data = json.load(file)

    # Convert trace data to string
    trace_str = json.dumps(trace_data)

    # Set up the workflow parameters
    hint = "Go to github.com and stay on the page. Don't do or click anything else."
    url = "http://github.com"  # Assuming the start_url is in the trace data

    # Run the La Vague workflow
    result = run_lavague_workflow(trace_str, hint, url)

    # Print the result
    print(json.dumps(result, indent=2))

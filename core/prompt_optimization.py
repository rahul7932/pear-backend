from lavague.drivers.selenium import SeleniumDriver
from lavague.core import ActionEngine, WorldModel
from lavague.core.agents import WebAgent
from openai import OpenAI

client = OpenAI(api_key="YOUR_API_KEY")

# fetch from database FE
hint = "" 
trace = ""

# get main objective
objective =  (trace + "\n Given a set of sequential actions described in the JSON trace above, your task is to generate a compact but descriptive main objective of the action while emphasizing and incoporating the hint " + hint + ".")


# define prompt to fetch lavague prompt based on the given hint and trace data
prompt = (trace + "\n Given a set of sequential actions described in the JSON trace above, your task is to generate a compact list of actions while incorporating the hint " + hint + ". To do this, follow the following:"
"Understand the context: Begin by understanding the sequence of actions provided in the trace. This will give you a baseline for interacting with the website and performing the initial steps."
"Incorporate the hint: As you proceed through the steps, keep the hint in mind. The hint may require actions outside the original sequence, so be prepared to deviate as necessary." 
"Finally, output a concise list of actions to take to achieve this main objective.")


def gpt_api_call(prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content

main_objective = gpt_api_call(objective)
context = gpt_api_call(prompt)                  


lavague_prompt = ("CONTEXT: " + context + "."
"OBJECTIVE: " + main_objective + "."
"INSTRUCTIONS: Adapt dynamically: Explore the interface beyond the exact steps provided in the trace. While following the general flow of actions, always be aware of the end goal described in the hint, and adjust your steps accordingly. Exploration is encouraged where necessary. Think step by step.")

# Set up our three key components: Driver, Action Engine, World Model
driver = SeleniumDriver(headless=False)
action_engine = ActionEngine(driver)
world_model = WorldModel()

# Create Web Agent
agent = WebAgent(world_model, action_engine)

# fetch from FE
url = ""

# Set URL
agent.get(url)

# Run agent with a specific objective
agent.run(lavague_prompt)







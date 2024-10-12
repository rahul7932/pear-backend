# Install necessary elements
from lavague.drivers.selenium import SeleniumDriver
from lavague.core import ActionEngine, WorldModel
from lavague.core.agents import WebAgent

# Set up our three key components: Driver, Action Engine, World Model
driver = SeleniumDriver(headless=False)
action_engine = ActionEngine(driver)
world_model = WorldModel()

# Create Web Agent
agent = WebAgent(world_model, action_engine)

# high_level_plan = gpt.create_multistep_plan() --> [("go to aws and do xyz" + 'our generated trace context if we have',  "aws.com"), 
#                                                    ("go to jira and log abc" + 'our generated trace context if we have', "jira.com")]

# result_cache = []

# for item in high_level_plan:
#     agent.get(item[1])
#     res = agent.run(item[0])
#     result_cache.append(res)

# final = gpt.synthesize_report(result_cache[-1], 'post processing instructions')

# print(final)
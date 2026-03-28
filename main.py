from dotenv import load_dotenv
from clawforge import DynamicAgent

load_dotenv()

agent = DynamicAgent("plan.json")
results = agent.run()

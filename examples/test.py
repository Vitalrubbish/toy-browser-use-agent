"""
Setup:
1. Get your API key from https://cloud.browser-use.com/new-api-key
2. Set environment variable: export BROWSER_USE_API_KEY="your-key"
"""

from dotenv import load_dotenv

from browser_use import Agent, ChatBrowserUse

load_dotenv()

agent = Agent(
	task='Please fetch the latest commit message of Github repo assassyn',
	llm=ChatBrowserUse(model='bu-2-0'),
	use_memory=True,
)
agent.run_sync()

# Expected output: The latest commit message of the assassyn repository on GitHub.

# another_agent = Agent(
#	task='Please fetch the second latest commit message of Github repo pytorch',
#	llm=ChatBrowserUse(model='bu-2-0'),
# )
# another_agent.run_sync()
# Expected output: The second latest commit message of the pytorch repository on GitHub.
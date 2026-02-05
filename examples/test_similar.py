"""
Setup:
1. Get your API key from https://cloud.browser-use.com/new-api-key
2. Set environment variable: export BROWSER_USE_API_KEY="your-key"
"""

from dotenv import load_dotenv

from browser_use import Agent, ChatBrowserUse

load_dotenv()

agent = Agent(
	task='Please fetch the latest second commit message of Github repo pytorch',
	llm=ChatBrowserUse(model='bu-2-0'),
	use_memory=True,
)
agent.run_sync()

import os
import requests
import asyncio
import chainlit as cl
from dotenv import load_dotenv

# Langroid imports
from agents import Agent, Runner, OpenAIChatCompletionsModel, AsyncOpenAI, set_tracing_disabled, function_tool

# Disable tracing and load environment variables
set_tracing_disabled(disabled=True)
load_dotenv()

# Load Gemini API Key
API_KEY = os.getenv("GEMINI_API_KEY")

# Create Langroid-compatible OpenAI Client for Gemini
client = AsyncOpenAI(
    api_key=API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai"
)

# Setup model with Gemini
model = OpenAIChatCompletionsModel(
    openai_client=client,
    model="gemini-1.5-flash"
)

# Define the crypto price tool
@function_tool
def get_crypto_price(crypto_name: str) -> str:
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_name.lower()}&vs_currencies=usd"
        response = requests.get(url)
        data = response.json()
        if crypto_name.lower() in data:
            price = data[crypto_name.lower()]["usd"]
            return f"The current price of {crypto_name} is ${price}."
        else:
            return f"Could not find the price for {crypto_name}."
    except Exception as e:
        return f"An error occurred while fetching the price: {str(e)}"

# Setup agent
agent = Agent(
    name="CRYPTOBOT",
    instructions="You are a crypto trading bot that tells the real-time price of a cryptocurrency.",
    model=model,
    tools=[get_crypto_price]
)

# ✅ Chainlit UI callback — this makes it work with the UI!
@cl.on_message
async def main(message: cl.Message):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: Runner.run_sync(
            starting_agent=agent,
            input=message.content
        )
    )
    await cl.Message(content=result.final_output).send()

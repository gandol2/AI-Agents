from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

MODEL = LiteLlm("openai/gpt-4o")

def get_weather(city:str):
    return f"The weather in {city} is sunny."

def convert_units(degrees:int):
    return f"That is 40 Farenheit"

geo_agent = Agent(
    name="GeoAgent",
    instruction = "You are a geo agent that can answer questions about the weather.",
    model = MODEL,
    description="Transfer to this agent when you have a geo related question.",
)
weather_agent = Agent(
    name = "WeatherAgent",
    instruction = "You are a weather agent that can answer questions about the weather.",
    model = MODEL,
    tools = [get_weather,convert_units],
    sub_agents = [geo_agent]
)

root_agent = weather_agent
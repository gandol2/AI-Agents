from google.genai import types

from google.adk.tools import ToolContext
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.models.lite_llm import LiteLlm
from .sub_agents.data_analyst import data_analyst
from .sub_agents.financial_analyst import financial_analyst
from .sub_agents.news_analyst import news_analyst
from .prompt import PROMPT

MODEL = LiteLlm("openai/gpt-4o")


async def save_advice_report(tool_context: ToolContext, summary: str, ticker: str):
    state = tool_context.state
    data_analyst_result = state.get("data_analyst_result")
    data_financial_analyst_result = state.get("data_financial_analyst_result")
    data_news_analyst_result = state.get("data_news_analyst_result")

    report = f"""
    # 총평 : 
    {summary}

    ## 데이터 애널리스트 보고서 :
    {data_analyst_result}

    ## 재무 애널리스트 보고서 :
    {data_financial_analyst_result}

    ## 뉴스 애널리스트 보고서 :
    {data_news_analyst_result}
    """

    state["report"] = report

    filename = f"{ticker}_investment_advice.md"
    artifact = types.Part(
        inline_data=types.Blob(
            mime_type="text/markdown",
            data=report.encode("utf-8")
        ),

    )

    await tool_context.save_artifact(filename, artifact)

    return {
        "success": True,
    }


financial_advisor = Agent(
    name="FinancialAdvisor",
    instruction=PROMPT,
    model=MODEL,
    tools=[
        AgentTool(agent=financial_analyst),
        AgentTool(agent=news_analyst),
        AgentTool(agent=data_analyst),
        save_advice_report,
    ],
)

root_agent = financial_advisor

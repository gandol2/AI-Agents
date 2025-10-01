# run command : streamlit run main.py
import dotenv
dotenv.load_dotenv()
from openai import OpenAI
import asyncio
import streamlit as st
from agents import (
    Runner, 
    SQLiteSession, 
    function_tool,
    RunContextWrapper
)
from models import UserAccountContext

# @function_tool
# def get_user_tier(wrapper: RunContextWrapper[UserAccountContext]):
#     return f"The user {wrapper.context.customer_id} has {wrapper.context.tier} account."

client = OpenAI()

user_account_context = UserAccountContext(
    customer_id=1,
    name="슈터시기",
    tier="basic"
)


# ========================================================== [Logic] ==========================================================
if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession("chat-history", "chat-gpt-clone-memory.db")
session = st.session_state["session"]

async def paint_history():
    messages = await session.get_items()
    for message  in messages:
        if "role" in message:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])                    
                else:
                    if message["type"] == "message":
                        st.write(message["content"][0]["text"].replace("$", "\$"))

asyncio.run(paint_history())


async def run_agent(message):
    with st.chat_message("ai"):  
        status_container = st.status("⌛ 생각중...", expanded=False)
        text_placeholder = st.empty()
        response = ""

        st.session_state["text_placeholder"] = text_placeholder

        stream = Runner.run_streamed(
                agent,
                message, 
                session=session,
                context=user_account_context
            )
        async for event in stream.stream_events():
            if event.type == "raw_response_event":

                if event.data.type == "response.output_text.delta":    
                    response += event.data.delta                                
                    text_placeholder.write(response)

                

# ========================================================== [UI] ==========================================================
message = st.chat_input("무엇이든 물어보세요")

if message:
    if "text_placeholder" in st.session_state:
        st.session_state["text_placeholder"].empty()  

    if message:
        with st.chat_message("human"):
            st.write(message)
        asyncio.run( run_agent(message))
    

with st.sidebar:
    reset = st.button("Reset memory")
    if reset:
        asyncio.run( session.clear_session())
    st.write(asyncio.run(session.get_items()))
        
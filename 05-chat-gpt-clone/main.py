# run command : streamlit run main.py
import dotenv
dotenv.load_dotenv()
import asyncio
import base64
import streamlit as st
from openai import OpenAI
from agents import (Agent, Runner, SQLiteSession, function_tool, WebSearchTool, FileSearchTool, ImageGenerationTool, CodeInterpreterTool )

client = OpenAI()

VECTOR_STORE_ID = "vs_68dce504c51c81918f1c7f2d40144e40"

# ========================================================== [Logic] ==========================================================
if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        name="ChatGPT Clone",
        # model="gpt-4o-mini", 
        instructions="""
                    You are a helpful assistant.

                    You have access to the followign tools:
                        - Web Search Tool: Use this when the user asks a questions that isn't in your training data. Use this tool when the users asks about current or future events, when you think you don't know the answer, try searching for it in the web first.
                        - File Search Tool: Use this tool when the user asks a question about facts related to themselves. Or when they ask questions about specific files.
                        - Code Interpreter Tool: Use this tool when use need to write and run code to answer the user's question.
                """,
        tools=[
            WebSearchTool(),
            FileSearchTool(
                vector_store_ids=[
                    VECTOR_STORE_ID
                ],
                max_num_results=3                
            ),
            ImageGenerationTool(
                tool_config={
                    "type": "image_generation",
                    "quality": "high",
                    "output_format": "jpeg",
                    "moderation": "low",
                    "partial_images": 1
                }
            ),
            CodeInterpreterTool(
                tool_config={
                    "type": "code_interpreter",
                    "container": {
                        "type": "auto",
                    }
                }
            )

        ],
    )
agent = st.session_state["agent"]

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession("chat-history", "chat-gpt-clone-memory.db")
session = st.session_state["session"]

async def paint_history():
    messages = await session.get_items()

    for message  in messages:
        if "role" in message:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    content = message["content"]
                    if isinstance(content, str):
                        st.write(content)
                    elif isinstance(content, list):
                        for part in content:
                            if "image_url" in part:
                                st.image(part["image_url"])
                            
                else:
                    if message["type"] == "message":
                        st.write(message["content"][0]["text"])
        if "type" in message:
            message_type = message["type"]
            if message_type == "web_search_call":
                with st.chat_message("ai"):
                    st.write("🌎 Searching web...")
            elif message_type == "file_search_call":
                with st.chat_message("ai"):
                    st.write("📂 Searching your uploaded files...")
            elif message_type == "image_generation_call":
                image = base64.b64decode(message["result"])
                with st.chat_message("ai"):
                    st.image(image)
            elif message_type == "code_interpreter_call":
                with st.chat_message("ai"):
                    st.code(message["code"])


        

asyncio.run(paint_history())

def update_status(status_container, event):
    status_messages ={
        'response.web_search_call.completed' : ("✅ Web search completed.", "complete"),
        'response.web_search_call.in_progress' : ("🔍 Starting web search...", "running"),
        'response.web_search_call.searching' : ("🌍 Web search in progress...", "running"),

        'response.file_search_call.completed':("✅ File search completed.", "complete"),
        'response.file_search_call.in_progress':("📂 Starting file search...", "running"),
        'response.file_search_call.searching':("📂 File search in progress...", "running"),

        # 'response.image_generation_call.completed':("",""),
        'response.image_generation_call.generating':("🖼 Drawing image...","running"),
        'response.image_generation_call.in_progress':("🖼 Drawing image...","running"),
        # 'response.image_generation_call.partial_image':("",""),

        # 'response.code_interpreter_call_code.delta': ("🤖 Ran code.", "complete"),
        'response.code_interpreter_call_code.done': ("🤖 Ran code.", "complete"),
        'response.code_interpreter_call.completed': ("🤖 Ran code.", "complete"),
        'response.code_interpreter_call.in_progress': ("🤖 Running code...", "running"),
        'response.code_interpreter_call.interpreting': ("🤖 Running code...", "running"),

        'response.completed' : (" ", "complete"),        
    }

    if event in status_messages:
        label, state = status_messages[event]
        status_container.update(label=label, state=state)
            

async def run_agent(message):
    with st.chat_message("ai"):  
        status_container = st.status("⌛ 생각중...", expanded=False)
        code_placeholder = st.empty()
        image_placeholder = st.empty()
        text_placeholder = st.empty()
        response = ""
        code_response = ""

        st.session_state["code_placeholder"] = code_placeholder
        st.session_state["image_placeholder"] = image_placeholder
        st.session_state["text_placeholder"] = text_placeholder

        stream = Runner.run_streamed(agent,message, session=session)
        async for event in stream.stream_events():
            if event.type == "raw_response_event":
                update_status(status_container, event.data.type)
                if event.data.type == "response.output_text.delta":    
                    response += event.data.delta                                
                    text_placeholder.write(response)

                if event.data.type == "response.code_interpreter_call_code.delta":
                    code_response += event.data.delta
                    code_placeholder.code(code_response)

                elif event.data.type == "response.image_generation_call.partial_image":
                    image = base64.b64decode(event.data.partial_image_b64)
                    image_placeholder.image(image)

                

# ========================================================== [UI] ==========================================================

prompt = st.chat_input(
    "무엇이든 물어보세요",
    accept_file=True,
    file_type=["txt", "jpg", "jpeg", "png"],
)

if prompt:

    if "code_placeholder" in st.session_state:
        st.session_state["code_placeholder"].empty()
    if "image_placeholder" in st.session_state:
        st.session_state["image_placeholder"].empty()
    if "text_placeholder" in st.session_state:
        st.session_state["text_placeholder"].empty()

    for file in prompt.files:
        if file.type.startswith("text/"):
            with st.chat_message("ai"):
                with st.status("⌛ 파일 업로드중...") as status:
                    # https://platform.openai.com/storage/files 에 파일 업로드
                    uploaded_file = client.files.create(
                        file=(file.name, file.getvalue()),
                        purpose="user_data"
                    )
                    status.update(label="⌛ 파일 등록중...")

                    # https://platform.openai.com/storage/vector_stores 벡터스토어에 파일 추가
                    client.vector_stores.files.create(
                        file_id=uploaded_file.id,
                        vector_store_id=VECTOR_STORE_ID
                    )
                    status.update(label="✅ 파일 업로드 완료!", state="complete")
        elif file.type.startswith("image/"):
            with st.status("🖼 이미지 업로드중...") as status:
                file_bytes = file.getvalue()
                base64_data = base64.b64encode(file_bytes).decode("utf-8")
                data_uri = f"data:{file.type};base64,{base64_data}"
                st.write(data_uri)
                asyncio.run(
                    session.add_items(
                        [
                            {
                                "role":"user",
                                "content":[{
                                    "type":"input_image",
                                    "detail":"auto",
                                    "image_url":data_uri
                                }]
                            }
                        ]
                    )
                )
                status.update(label="✅ 이미지 업로드 완료!", state="complete")
            with st.chat_message("human"):
                st.image(data_uri)

            

    if prompt.text:
        with st.chat_message("human"):
            st.write(prompt.text)
        asyncio.run( run_agent(prompt.text))
    

with st.sidebar:
    reset = st.button("Reset memory")
    if reset:
        asyncio.run( session.clear_session())

    st.write(asyncio.run( session.get_items()))
        
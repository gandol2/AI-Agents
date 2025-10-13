from langgraph.graph import END, START, StateGraph
from langgraph.types import Send, interrupt, Command
from typing import TypedDict
import subprocess
from openai import OpenAI
import textwrap
from langchain.chat_models import init_chat_model
from typing_extensions import Annotated
import operator
import base64


llm = init_chat_model("openai:gpt-4o-mini")


class State(TypedDict):

    video_file: str  # 비디오파일 경로
    audio_file: str  # 오디오파일 경로
    transcription: str  # 추출된 음성
    summaries: Annotated[list[str], operator.add]  # 요약 문장 목록
    final_summary: str

    thumbnail_prompts: Annotated[list[str], operator.add]
    thumbnail_sketches: Annotated[list[str], operator.add]

    user_feedback: str
    chosen_prompt: str


def extract_audio(state: State):
    # Using ffmpeg to extract audio from video
    output_file = state["video_file"].replace("mp4", "mp3")
    command = [
        "ffmpeg",
        "-i",
        state["video_file"],
        "-filter:a",
        "atempo=1.7",
        "-y",
        output_file
    ]
    subprocess.run(command)
    return {
        "audio_file": output_file
    }


WHISPER_PROMPT = (
    "이 오디오는 ‘돈타클로스’ 유튜브 채널의 ‘상표등록 방법’ 안내입니다. 한국 특허청(KIPO)과 KIPRIS를 전제로 상표검색, 출원, 심사, 보정, "
    "의견제출통지, 거절이유, 등록결정, 갱신을 설명합니다. 니스 국제분류(1~45류), 유사군코드, 지정상품, "
    "출원수수료/등록료 등 숫자와 분류표기는 정확히 숫자로 표기하세요(예: 35류, 45류). "
    "브랜드·셀러(쿠팡, 스마트스토어, 아마존)는 한글 그대로 표기하고, 고유명사는 오탈자 없이 적습니다. "
    "핵심 용어: 상표등록, 상표출원, 상표검색, 지식재산권, 브랜드보호, 지정상품, 유사군코드, 출원번호, 거절이유, "
    "등록결정, 갱신, KIPRIS, 특허청. "
    "English terms: KIPO, KIPRIS, Nice Classification, Classes 1–45, trademark search, office action, refusal, registration decision, renewal."
)


def transcribe_audio(state: State):
    # use audio file
    client = OpenAI()
    with open(state["audio_file"], "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            response_format="text",
            file=audio_file,
            language="ko",
            prompt=WHISPER_PROMPT
        )
        return {
            "transcription": transcription
        }


def dispatch_summarizers(state: State):
    transcription = state["transcription"]
    chunks = []
    for idx, chunk in enumerate(textwrap.wrap(transcription, 500)):
        chunks.append({
            "id": idx+1,
            "chunk": chunk
        })
    return [Send("summarize_chunk", chunk) for chunk in chunks]


def summarize_chunk(chunk):
    chunk_id = chunk["id"]
    chunk_text = chunk["chunk"]

    response = llm.invoke(
        f"""이 문장을 요약해줘.
            Text : {chunk_text}"""
    )
    summary = f"[Chunk {chunk_id}] {response.content}"
    return {
        "summaries": [summary]
    }


def finalize_summary(state: State):
    all_summaries = "\n".join(state["summaries"])

    prompt = f"""
        you are given multiple summarise of different chunks from a video transcription.
        
        Please create a comprehensive final summary the combines all the key points.

        Individual summaries :        

        {all_summaries}
    """

    response = llm.invoke(prompt)
    return {
        "final_summary": response.content
    }


def dispatch_artists(state: State):
    # return [Send("generate_thumbnail", state) for i in [1, 2, 3]]
    return [
        Send(
            "generate_thumbnail",
            {
                "id": i,
                "summary": state["final_summary"],
            }
        )
        for i in [1, 2, 3, 4, 5]
    ]


def generate_thumbnail(args):
    concept_id = args["id"]
    summary = args["summary"]

    prompt = f"""
        You are an expert Korean thumbnail designer AI generating an image with the GPT-image-1 model.

        🎯 GOAL:
        Create a YouTube thumbnail that attracts Korean viewers based on the following video summary.
        This thumbnail must look professional, eye-catching, and optimized for Korean YouTube audiences.

        ⚠️ LANGUAGE RULES (IMPORTANT):
        - **All visible text in the thumbnail must be written in Korean (Hangul only)**.
        - **Never use English letters or Romanized Korean.**
        - **Do not translate Korean text into English.**
        - The Korean text must be perfectly rendered — no broken or corrupted Hangul characters.
        - Use proper spacing, alignment, and typographic consistency for Hangul.
        - Prioritize accurate Hangul rendering over stylistic effects.
        - If the model struggles to draw Hangul text, focus on producing realistic, clean Korean lettering.
        - Use strong, readable Korean title fonts such as **Noto Sans KR**, **Pretendard Bold**, or **Nanum Gothic ExtraBold**.

        🧩 INSTRUCTIONS:
        Generate a detailed visual prompt that includes:
        1. **Main visual elements** — Describe characters, objects, or icons that represent the topic.
        2. **Color scheme** — Suggest harmonious, bright color palettes suitable for Korean audiences.
        3. **Text overlay (Korean phrases only)** — Propose 2–3 short, catchy Korean phrases to display on the thumbnail.
        4. **Overall composition** — Describe the layout, focal points, and balance between text and visuals.

        🖋 STYLE GUIDELINES:
        - The thumbnail should look modern, clean, and professional.
        - Avoid clutter; maintain focus on the main message.
        - Korean text should stand out clearly against the background.
        - Use contrast (dark text on bright background or vice versa).
        - Recommended aspect ratio: 16:9 (YouTube thumbnail standard).

        💬 EXAMPLE:
        If the summary is about "상표등록 방법",
        - Text overlay suggestions: 
            - "5분 만에 끝내는 상표등록"
            - "초보도 가능한 브랜드 등록 꿀팁"
        - Visual: smiling Korean entrepreneur holding a trademark certificate, with the KIPO (특허청) building faintly visible.
        - Background: light blue and white gradient conveying trust and clarity.

        📄 VIDEO SUMMARY:
        {summary}
    """

    response = llm.invoke(prompt)

    thumbnail_prompt = response.content

    client = OpenAI()
    image = client.images.generate(
        model="gpt-image-1",
        prompt=thumbnail_prompt,
        quality="low",
        moderation="low",
        size="auto",

    )

    image_bytes = base64.b64decode(image.data[0].b64_json)

    filename = f"thumbnail_{concept_id}.jpg"

    with open(filename, "wb") as file:
        file.write(image_bytes)

    return {
        "thumbnail_prompts": [thumbnail_prompt],
        "thumbnail_sketches": [filename]
    }


def human_feedback(state: State):
    answer = interrupt({
        "chosen_thumbnail": "어떤 썸네일이 가장 마음에 드나요?",
        "feedback": "썸네일에 대한 피드백을 주세요."
    })

    user_feedback = answer["user_feedback"]
    chosen_prompt = answer["chosen_prompt"]

    return {
        "user_feedback": user_feedback,
        "chosen_prompt": state["thumbnail_prompts"][chosen_prompt-1]
    }


def generate_hd_thumbnail(state: State):
    chosen_prompt = state["chosen_prompt"]
    user_feedback = state["user_feedback"]

    prompt = f"""
        You are a professional YouTube thumbnail designer. Take this original thumbnail prompt and create an enhanced version that incorporates the user's specific feedback.

        ORIGINAL PROMPT:
        {chosen_prompt}

        USER FEEDBACK TO INCORPORATE:
        {user_feedback}

        Create an enhanced prompt that:
            1. Maintains the core concept from the original prompt
            2. Specifically addresses and implements the user's feedback requests
            3. Adds professional YouTube thumbnail specifications:
                - High contrast and bold visual elements
                - Clear focal points that draw the eye
                - Professional lighting and composition
                - Optimal text placement and readability with generous padding from edges
                - Colors that pop and grab attention
                - Elements that work well at small thumbnail sizes
                - IMPORTANT: Always ensure adequate white space/padding between any text and the image borders
    """

    response = llm.invoke(prompt)

    final_thumbnail_prompt = response.content

    client = OpenAI()
    image = client.images.generate(
        model="gpt-image-1",
        prompt=final_thumbnail_prompt,
        quality="high",
        moderation="low",
        size="auto",

    )

    image_bytes = base64.b64decode(image.data[0].b64_json)

    with open("thumbnail_final.jpg", "wb") as file:
        file.write(image_bytes)


graph_builder = StateGraph(State)

graph_builder.add_node("extract_audio", extract_audio)
graph_builder.add_node("transcribe_audio", transcribe_audio)
graph_builder.add_node("summarize_chunk", summarize_chunk)
graph_builder.add_node("finalize_summary", finalize_summary)
graph_builder.add_node("generate_thumbnail", generate_thumbnail)
graph_builder.add_node("human_feedback", human_feedback)
graph_builder.add_node("generate_hd_thumbnail", generate_hd_thumbnail)


graph_builder.add_edge(START, "extract_audio")
graph_builder.add_edge("extract_audio", "transcribe_audio")
graph_builder.add_conditional_edges(
    "transcribe_audio", dispatch_summarizers, ["summarize_chunk"])
graph_builder.add_edge("summarize_chunk", "finalize_summary")
graph_builder.add_conditional_edges(
    "finalize_summary", dispatch_artists, ["generate_thumbnail"])
graph_builder.add_edge("generate_thumbnail", "human_feedback")
graph_builder.add_edge("human_feedback", "generate_hd_thumbnail")
graph_builder.add_edge("human_feedback", END)

graph = graph_builder.compile(name="mr_thumbs")

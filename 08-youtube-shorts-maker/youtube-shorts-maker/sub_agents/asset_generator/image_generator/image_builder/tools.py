import base64
from google.genai import types
from openai import OpenAI
from google.adk.tools.tool_context import ToolContext

client = OpenAI()


async def generate_images(tool_context: ToolContext):
    # 1. state["prompt_builder_output"] 가져오기
    prompt_builder_output = tool_context.state.get("prompt_builder_output")

    # 2. state["prompt_builder_output"]["optimized_prompts"] 가져오기
    optimized_prompts = prompt_builder_output.get("optimized_prompts")

    # 3. 생성된 artifacts 가져오기 (중복생성 방지)
    existing_artifacts = await tool_context.list_artifacts()

    #
    generated_images = []

    for prompt in optimized_prompts:
        scene_id = prompt.get("scene_id")
        enhanced_prompt = prompt.get("enhanced_prompt")
        filename = f"scene_{scene_id}_image.jpeg"

        # artifacts에 파일이 존재 하는 경우 다음 프롬프트로
        if filename in existing_artifacts:
            generated_images.append(
                {
                    "scene_id": scene_id,
                    "prompt": enhanced_prompt[:100],
                    "filename": filename


                }
            )
            continue

        # GPT Client를 사용해 이미지 생성
        image = client.images.generate(
            model="gpt-image-1",
            prompt=enhanced_prompt,
            n=1,
            quality="low",
            moderation="low",
            output_format="jpeg",
            background="opaque",
            size="1024x1536"
        )

        # GPT 이미지 생성 결과는 base64 인코딩 된 상태로 응답
        image_bytes = base64.b64decode(image.data[0].b64_json)

        artifact = types.Part(
            inline_data=types.Blob(
                mime_type="image/jpeg",
                data=image_bytes,
            )
        )

        await tool_context.save_artifact(filename=filename, artifact=artifact)

        generated_images.append(
            {
                "scene_id": scene_id,
                "prompt": enhanced_prompt[:100],
                "filename": filename,


            }
        )

        return {
            "total_images": len(generated_images),
            "status": "complete",
            "generated_images": generated_images,
        }

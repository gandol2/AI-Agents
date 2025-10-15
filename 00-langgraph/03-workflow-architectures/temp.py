# langgraph 기반 상세페이지 Evaluator–Optimizer 워크플로우
# (LangGraph 공식 Python SDK 스타일)

from langgraph.graph import Graph, END
from langgraph.graph.message import Message
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# -------------------------------
# 1️⃣ 모델 정의
# -------------------------------
generator = ChatOpenAI(model="gpt-5.1", temperature=0.7)
evaluator = ChatOpenAI(model="gpt-5.1", temperature=0.3)

# -------------------------------
# 2️⃣ 평가 스키마 정의
# -------------------------------


class EvalResult(BaseModel):
    score: float = Field(..., ge=0, le=100)
    pass_: bool = Field(..., alias="pass")
    violations: List[Dict[str, Any]] = []
    revise_instructions: List[str] = []

# -------------------------------
# 3️⃣ 노드 함수 정의
# -------------------------------


def llm_call_generator(state: Dict[str, Any]) -> Dict[str, Any]:
    """상세페이지 초안 생성"""
    meta = state["meta"]
    feedback = state.get("feedback", None)
    prompt = f"""
다음 제품에 대한 상세페이지 초안을 작성하세요.

제품명: {meta['product_name']}
타깃: {meta['target_audience']}
키워드: {', '.join(meta['seo_keywords'])}
인증: {meta.get('certs_or_tests', '없음')}
금지어: {', '.join(meta.get('banned_terms', []))}

구성(필수):
1) Hook
2) 3 Key Benefits (수치/근거 포함)
3) Specs 표
4) Usage
5) Care & Notice
6) FAQ
7) CTA

톤: 신뢰감 있고 친근하게
형식: 마크다운
"""
    if feedback:
        prompt += f"\n이전 피드백을 반영하세요:\n{feedback}"

    resp = generator.invoke(prompt)
    return {"draft": resp.content}


def llm_call_evaluator(state: Dict[str, Any]) -> Dict[str, Any]:
    """초안 평가"""
    draft = state["draft"]
    meta = state["meta"]
    eval_prompt = f"""
아래 상세페이지 초안을 루브릭에 따라 평가하고 JSON으로만 출력하세요.

금지 표현: 완치, 100%, 부작용 없음, 기적, 의사 추천 등

초안:
{draft}
"""
    resp = evaluator.invoke(eval_prompt)
    try:
        parsed = EvalResult.parse_raw(resp.content)
    except Exception:
        parsed = EvalResult(score=0, pass_=False,
                            revise_instructions=["JSON 형식 오류 수정 필요."])

    return {"evaluation": parsed.dict(by_alias=True)}

# -------------------------------
# 4️⃣ 상태 업데이트 로직
# -------------------------------


def decide_next(state: Dict[str, Any]) -> str:
    eval_res = state["evaluation"]
    if eval_res["pass"] and eval_res["score"] >= 90:
        return "accepted"
    return "feedback"


def feedback_loop(state: Dict[str, Any]) -> Dict[str, Any]:
    eval_res = state["evaluation"]
    feedback = "\n".join(eval_res.get("revise_instructions", []))
    return {"feedback": feedback}


# -------------------------------
# 5️⃣ 그래프 정의
# -------------------------------
graph = Graph()

graph.add_node("Generator", llm_call_generator)
graph.add_node("Evaluator", llm_call_evaluator)
graph.add_node("Feedback", feedback_loop)

# 연결 정의
graph.add_edge("Generator", "Evaluator")
graph.add_conditional_edges(
    "Evaluator",
    decide_next,
    {
        "accepted": END,
        "feedback": "Feedback",
    },
)
graph.add_edge("Feedback", "Generator")

graph.set_entry_point("Generator")

# -------------------------------
# 6️⃣ 실행 예시
# -------------------------------
if __name__ == "__main__":
    meta = {
        "product_name": "AEMICA 스테인리스 주방 수세미 세트",
        "target_audience": "자취생 및 주부",
        "seo_keywords": ["스테인리스 수세미", "주방 청소", "위생 세척"],
        "certs_or_tests": "KC인증 완료",
        "banned_terms": ["완벽", "기적", "100%"],
    }

    state = {"meta": meta}
    result = graph.run(state, max_iterations=3)
    print("\n✅ 최종 결과:")
    print(result)

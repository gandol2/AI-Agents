# AI Agents

AI 에이전트 프로젝트 모음입니다.

## 프로젝트 목록

### example-agent
- 기본 AI 에이전트 예제
- OpenAI API를 사용한 챗봇 구현
- 함수 호출 기능 포함

### my-first-agent
- 첫 번째 AI 에이전트 프로젝트
- GPT-4o-mini 모델 사용
- 날씨 조회 도구 포함
- 대화형 인터페이스

## 공통 설정

모든 프로젝트는 `uv`를 사용하여 의존성을 관리합니다.

```bash
# 프로젝트별 의존성 설치
cd example-agent
uv sync

cd ../my-first-agent
uv sync
```

## 요구사항

- Python 3.13+
- uv 패키지 매니저
- OpenAI API 키

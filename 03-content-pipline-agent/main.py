from crewai.flow.flow import Flow, listen, start, router, and_, or_
from pydantic import BaseModel

class ContentPiplineFlowState(BaseModel):

    # Inputs
    content_type: str = ""
    topic: str = ""

    # Internal
    max_length: int = 0
    score: int = 0

    #Content
    blog_post: str = ""
    tweet_post: str = ""
    linkedin_post: str = ""

class ContentPiplineFlow(Flow[ContentPiplineFlowState]):

    @start()
    def init_content_pipline(self):
        if self.state.content_type not in ["tweet", "blog", "linkedin"]:
            raise ValueError(f"알수 없는 콘텐츠 타입 입니다 : {self.state.content_type}")

        if self.topic == "":
            raise ValueError(f"토픽이 비어있습니다 : {self.state.topic}")

        if self.state.content_type == "tweet":
            self.state.max_length = 150
        elif self.state.content_type == "blog":
            self.state.max_length = 800
        elif self.state.content_type == "linkedin":
            self.state.max_length = 500

    @listen(init_content_pipline)
    def conduct_research(self):
        print("콘텐츠를 찾는중 입니다...")
        return True

    @router(conduct_research)
    def conduct_research_router(self):
        content_type = self.state.content_type

        if content_type == "tweet":
            return "make_tweet"
        elif content_type == "blog":
            return "make_blog"
        elif content_type == "linkedin":
            return "make_linkedin"
        else:
            raise ValueError(f"알수 없는 콘텐츠 타입 입니다 : {content_type}")

    @listen(or_("make_blog", "remake_blog"))
    def handle_make_blog(self):
        # 블로그 포스트가 생성된적 있다면, 이전 블로그 포스트를 AI에게 제공하고 더 좋게 수정하도록 합니다.
        # 그렇지 않다면 생성 합니다.
        print("블로그 콘텐츠를 만드는중 입니다...")
    
    @listen(or_("make_tweet", "remake_tweet"))
    def handle_make_tweet(self):
        # 트윗 콘텐츠가 생성된적 있다면, 이전 트윗 콘텐츠를 AI에게 제공하고 더 좋게 수정하도록 합니다.
        # 그렇지 않다면 생성 합니다.
        print("트윗 콘텐츠를 만드는중 입니다...")
    
    @listen(or_("make_linkedin", "remake_linkedin"))
    def handle_make_linkedin(self):
        # 링크드인 콘텐츠가 생성된적 있다면, 이전 링크드인 콘텐츠를 AI에게 제공하고 더 좋게 수정하도록 합니다.
        # 그렇지 않다면 생성 합니다.
        print("링크드인 콘텐츠를 만드는중 입니다...")

    @listen(handle_make_blog)
    def check_seo(self):
        print("[블로그] SEO 체크중 입니다...")

    @listen(or_(handle_make_tweet, handle_make_linkedin))
    def check_virality(self):
        print("[트윗, 링크드인] 화제성 체크중 입니다...")

    @router(or_(check_seo, check_virality))
    def score_router(self):
        content_type = self.state.content_type
        score = self.state.score

        if score >= 8:
            return "check_passed"
        else:
            if content_type == "blog":
                return "remake_blog"
            elif content_type == "linkedin":
                return "remake_linkedin"
            else:
                return "remake_tweet"


    @listen("check_passed")
    def finalize_content(self):
        print("콘텐츠를 완성하는중 입니다...")


flow = ContentPiplineFlow()
flow.plot()
# flow.kickoff({
#     "content_type": "tweet",
#     "topic": "AI dog image",
# })
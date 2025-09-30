from typing import List
from crewai.flow.flow import Flow, listen, start, router, and_, or_
from crewai import LLM
from crewai import Agent
from pydantic import BaseModel
from seo_crew import SEOCrew

from tools import web_search_tool

class BlogPost(BaseModel):
    title: str
    subtitle: str
    sections: List[str]

class TweetPost(BaseModel):
    content: str
    hashtags: str

class LinkedinPost(BaseModel):
    hook: str
    content: str
    call_to_action: str

class Score(BaseModel):
    score: int = 0
    reason: str = ""

class ContentPiplineFlowState(BaseModel):

    # Inputs
    content_type: str = ""
    topic: str = ""

    # Internal
    max_length: int = 0
    score: Score | None = None
    research: str = ""
    

    #Content
    blog_post: BlogPost | None = None
    tweet: TweetPost | None = None
    linkedin_post: LinkedinPost | None = None

class ContentPiplineFlow(Flow[ContentPiplineFlowState]):

    @start()
    def init_content_pipline(self):
        if self.state.content_type not in ["tweet", "blog", "linkedin"]:
            raise ValueError(f"알수 없는 콘텐츠 타입 입니다 : {self.state.content_type}")

        if self.state.topic == "":
            raise ValueError(f"토픽이 비어있습니다 : {self.state.topic}")

        if self.state.content_type == "tweet":
            self.state.max_length = 150
        elif self.state.content_type == "blog":
            self.state.max_length = 800
        elif self.state.content_type == "linkedin":
            self.state.max_length = 500

    @listen(init_content_pipline)
    def conduct_research(self):
        content_research_agent = Agent(
            role="Head Researcher",
            backstory="당신은 흥미로운 사실과 통찰을 파헤치는 것을 좋아하는 디지털 탐정과 같습니다. 다른 사람들이 놓치는 가치 있는 정보를 찾아내는 능력이 뛰어납니다.",
            goal=f"{self.state.topic}에 대한 가장 흥미롭고 유용한 정보를 찾아 주세요",
            verbose=True,
            tools=[web_search_tool],
        )
        self.state.research = content_research_agent.kickoff(f"{self.state.topic}에 대한 가장 흥미롭고 유용한 정보를 찾아 주세요")
        # print("콘텐츠를 찾는중 입니다...")
        # return True

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
        blog_post = self.state.blog_post

        llm = LLM(model="openai/o4-mini", response_format=BlogPost)

        if blog_post is None:
            result = llm.call(f"""

                                    Make a blog post with SEO practices in korean. lengt limit is {self.state.max_length} characters. about the following topic: {self.state.topic} using the following research: {self.state.research}

                                    <research>
                                    ================
                                    {self.state.research}
                                    ================
                                    </research>
                                    """)
            
        else:
            result = llm.call(f"""
                                    당신이 {self.state.topic}에 대한 블로그 포스트를 작성했지만, SEO 점수가 낮습니다. 
                                    
                                    SEO 점수가 낮은 이유 : {self.state.score.reason}.
                                    
                                    더 좋은 블로그 포스트를 작성해주세요.

                                    <blog post>
                                    {self.state.blog_post.model_dump_json()}
                                    </blog post>
                                    
                                    Use the following research

                                    <research>
                                    ================
                                    {self.state.research}
                                    ================
                                    </research>
                                    """)
        self.state.blog_post = BlogPost.model_validate_json(result)
    
    @listen(or_("make_tweet", "remake_tweet"))
    def handle_make_tweet(self):
        tweet = self.state.tweet

        llm = LLM(model="openai/o4-mini", response_format=BlogPost)
        
        if tweet is None:
            result = llm.call(f"""

                                    Make a tweet that can go viral in korean. lengt limit is {self.state.max_length} characters. about the following topic: {self.state.topic} using the following research: {self.state.research}

                                    <research>
                                    ================
                                    {self.state.research}
                                    ================
                                    </research>
                                    """)
            
        else:
            result = llm.call(f"""
                                    당신이 {self.state.topic}에 대한 tweet을 작성했지만, 이슈성 점수가 낮습니다. 
                                    
                                    이슈성 점수가 낮은 이유 : {self.state.score.reason}.
                                    
                                    더 좋은 tweet을 작성해주세요.

                                    <tweet>
                                    {self.state.tweet.model_dump_json()}
                                    </tweet>
                                    
                                    Use the following research

                                    <research>
                                    ================
                                    {self.state.research}
                                    ================
                                    </research>
                                    """)
        
        self.state.tweet = TweetPost.model_validate_json(result)
    
    @listen(or_("make_linkedin", "remake_linkedin"))
    def handle_make_linkedin(self):
        linkedin_post = self.state.linkedin_post

        llm = LLM(model="openai/o4-mini", response_format=BlogPost)
        
        if linkedin_post is None:
            result = llm.call(f"""

                                    Make a linkedin post that can go viral in korean. lengt limit is {self.state.max_length} characters. about the following topic: {self.state.topic} using the following research: {self.state.research}

                                    <research>
                                    ================
                                    {self.state.research}
                                    ================
                                    </research>
                                    """)
            
        else:
            result = llm.call(f"""
                                    당신이 {self.state.topic}에 대한 linkedin post를 작성했지만, 이슈성 점수가 낮습니다. 
                                    
                                    이슈성 점수가 낮은 이유 : {self.state.score.reason}.
                                    
                                    더 좋은 linkedin post를 작성해주세요.

                                    <linkedin post>
                                    {self.state.linkedin_post.model_dump_json()}
                                    </linkedin post>
                                    
                                    Use the following research

                                    <research>
                                    ================
                                    {self.state.research}
                                    ================
                                    </research>
                                    """)

        self.state.linkedin_post = LinkedinPost.model_validate_json(result)

    @listen(handle_make_blog)
    def check_seo(self):
        result = SEOCrew().crew().kickoff(inputs={"topic": self.state.topic, "blog_post": self.state.blog_post.model_dump_json()})

        self.state.score = result.pydantic

    @listen(or_(handle_make_tweet, handle_make_linkedin))
    def check_virality(self):
        print(self.state.tweet)
        print(self.state.linkedin_post)
        print("[트윗, 링크드인] 화제성 체크중 입니다...")

    @router(or_(check_seo, check_virality))
    def score_router(self):
        content_type = self.state.content_type
        score = self.state.score

        print(score)

        if score.score >= 8:
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
#flow.plot()
flow.kickoff({
    "content_type": "blog",
    "topic": "3D 프린터 생태계",
})
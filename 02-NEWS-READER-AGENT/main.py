import dotenv

dotenv.load_dotenv()

# https://docs.crewai.com/ko/introduction
from crewai import Agent, Crew, Task
from crewai.project import CrewBase, agent, task, crew

@CrewBase
class 번역Crew:
    # https://docs.crewai.com/ko/concepts/agents
    @agent
    def 번역_agent(self):
        return Agent(config=self.agents_config["번역_agent"])

    # https://docs.crewai.com/ko/concepts/tasks
    @task
    def 번역_task(self):    
        return Task(
            config=self.tasks_config["번역_task"],
        )

    @task
    def 재번역_task(self):    
        return Task(
            
            config=self.tasks_config["재번역_task"],
            
        )

    @crew
    def 번역_crew(self):
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True,
        )

번역Crew().번역_crew().kickoff(inputs={"sentence": "안녕하세요. 저는 홍길동입니다. 나는 부산 어린이 대공원에서 자전거를 타는것을 좋아합니다."})
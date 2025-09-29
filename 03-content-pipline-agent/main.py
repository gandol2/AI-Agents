from crewai.flow.flow import Flow, listen, start, router, and_, or_
from pydantic import BaseModel

class MyFirstFlowState(BaseModel):
    user_id: int = 1
    is_admin: bool = True


class MyFirstFlow(Flow[MyFirstFlowState]):

    @start()
    def first(self):
        # self.state["whatever"] = 1
        print(self.state.user_id)
        print("Hello")

    
    @listen(first)
    def second(self):
        # print(self.state["whatever"])
        print("World")

    @listen(first)
    def third(self):
        print(" !! ")

    @listen(and_(second, third))
    def final(self):
        # self.state["whatever"] = 2
        self.state.user_id = 2
        print(":)")

    @router(final)
    def route(self):
        a = self.state.user_id
        if a == 2:
            return 'even'
        else:
            return 'odd'

    @listen('even')
    def handle_even(self):
        print("Even")

    @listen('odd')
    def handle_odd(self):
        print("Odd")



flow = MyFirstFlow()

flow.plot() # 플로우 다이어그램 그리기 -> html 파일로 저장됨
flow.kickoff()
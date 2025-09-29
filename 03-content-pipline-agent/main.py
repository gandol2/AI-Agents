from crewai.flow.flow import Flow, listen, start, router, and_, or_



class MyFirstFlow(Flow):

    @start()
    def first(self):
        print("Hello")

    
    @listen(first)
    def second(self):
        print("World")

    @listen(first)
    def third(self):
        print(" !! ")

    @listen(and_(second, third))
    def final(self):
        print(":)")

flow = MyFirstFlow()

#flow.plot() # 플로우 다이어그램 그리기 -> html 파일로 저장됨
flow.kickoff()
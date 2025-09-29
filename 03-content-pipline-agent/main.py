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

    @router(final)
    def route(self):
        a = 2
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
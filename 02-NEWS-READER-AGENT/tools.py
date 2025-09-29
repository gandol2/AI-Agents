from crewai.tools import tool

@tool
def count_letters(sentence:str):
    """ 
    이 함수는 sentence의 글자수를 세는 함수 입니다.
    input은 'sentence' string
    output은 number 입니다. 
    """
    return len(sentence)
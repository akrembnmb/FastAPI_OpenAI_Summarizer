from pydantic import BaseModel

class Completion (BaseModel):
    model :str = "gpt-3.5-turbo-instruct"
    temperature : float =1
    max_tokens:int 
    prompt :str = "sumariz this text"
    
    
    
class SummarizeParams(BaseModel):
    text:str
    lmax:int
    typ:str




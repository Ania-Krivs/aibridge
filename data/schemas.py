from pydantic import BaseModel



class CreateToken(BaseModel):
    openai_key: str 
    id: int
    tokens: int


class Statistics(BaseModel):
    date: str
    request_tokens: int
    response_tokens: int
    
    
class UserData(BaseModel):
    user_key: str
    tokens: int
    
    


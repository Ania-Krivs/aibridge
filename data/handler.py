from fastapi import HTTPException, WebSocket
from datetime import datetime
from data.models import  Statistics, User
from data.db import sessions
from sqlalchemy import func
from config import ADMIN_KEY


# creating a session
def get_db():
    sess = sessions()
    try:
        yield sess
    finally:
        sess.close()
        


async def admin_authorization(token: str):
    if token != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Authorization token invalid")


async def user_authorisation(token: str, sess):
    find_key = sess.query(User).filter_by(openai_key=token).first()
    if find_key is None:
        return
    
    return find_key
    


class WebsocketsManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    

async def create_statistics(user_key, create, request_tokens, response_tokens):
    sess = sessions()
    
    create = Statistics(
        openai_key=user_key,
        date=create,
        request_tokens=request_tokens,
        response_tokens=response_tokens
    )
    
    sess.add(create)
    sess.commit()
    sess.refresh(create)
    sess.close()
    
async def statistics_for_mounth(user_token):
    sess = sessions()
    
    auth = await user_authorisation(user_token, sess)
    
    if not auth:
        raise HTTPException(status_code=403, detail="Authorization token invalid")
    
    current_time = datetime.utcnow()
    first_day_of_mounth = current_time.replace(day=1)
    
    try:
        res = sess.query(func.date(Statistics.date),
                            func.sum(Statistics.request_tokens),
                        func.sum(Statistics.response_tokens)
                        ).filter(Statistics.date >= first_day_of_mounth, Statistics.openai_key==user_token
                        ).group_by(func.date(Statistics.date)).all()
                        
        return [{"data": i[0], "request_tokens": i[1], "response_tokens": i[2]} for i in res]

    finally:
        sess.close()
        
  

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
    
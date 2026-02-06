from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Header
from sqlalchemy.orm import Session
from data.handler import user_authorisation, get_db, WebsocketsManager, admin_authorization
from config import OPENAI_KEY
from typing import Annotated, List, Optional

import openai
import datetime
import json

router = APIRouter(prefix="/user", tags=["user"])

openai.api_key = OPENAI_KEY

class Action():
    info = "info"
    request = "request"
    
    
models = ["gpt-4o", "chatgpt-4o-latest", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]


@router.post("/{user_token}/prompt")    
async def request_for_openai(user_token: str, model: str, prompt: str, sess: Session = Depends(get_db)):

    find_key = await user_authorisation(user_token, sess)

    if find_key is not None:
        if model in models:
            resp = openai.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": f"{prompt}"}],
                max_tokens=2000,
                temperature= 0.5
            )

            return (resp.choices[0].message.content.strip())
        
        else:
            return {"Error": "Model invalid"}
    else:
        return {"Error": "Authorization token invalid"}
    

manager = WebsocketsManager()

async def request_for_openai(websocket: WebSocket, user_token: str, model: str, prompt: str, stream: bool, sess):

    find_key = await user_authorisation(user_token, sess)

    if find_key is not None:
        if model in models:
            if stream is True:
                resp = openai.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": f"{prompt}"}],
                    max_tokens=2000,
                    temperature= 0.5,
                    stream=stream,
                    stream_options={"include_usage": True}
                )
                
            else:
                 resp = openai.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": f"{prompt}"}],
                    max_tokens=2000,
                    temperature= 0.5
                )
                     
                     

            if stream == False:
                return (resp.choices[0].message.content.strip())
            
            else:
                for r in resp:
                    if r is not None:
                        if len(r.choices) > 0:
                            msg = r.choices[0].delta.content
                            # print(msg)

                        if msg is not None:
                            await websocket.send_text(json.dumps(msg))
                        
                return
        
        else:
            return {"Error": "Model invalid"}
    
    else:
        return {"Error": "Authorization token invalid"}


@router.websocket('/ws/{user_token}')
async def websocket(websocket: WebSocket, user_token: str, sess: Session = Depends(get_db)):
    user = await user_authorisation(user_token, sess)
    
    if not user:
        await websocket.close()
        return
    
    await manager.connect(websocket)
    
    try:
        while True:
            data2 = await websocket.receive_text()
            data2_ = json.loads(data2)
            
            if "action" in data2_:
                action = data2_["action"]
                
                if action == Action.info:
                    user = await get_user(user_token, sess)
                    resp = {
                        "user_key": user.openai_key
                    }
                    
                elif action == Action.request:
                    user_token = data2_["user_token"]
                    model = data2_["model"]
                    prompt = data2_["prompt"]
                    stream = data2_["stream"]
                    resp = await request_for_openai(websocket, user_token, model, prompt, stream, sess)
                    
                                     
            await websocket.send_text(json.dumps(resp))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def get_user(user_token: str, sess):
    user = await user_authorisation(user_token, sess)
    return user


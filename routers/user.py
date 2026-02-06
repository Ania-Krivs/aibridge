from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Header
from sqlalchemy.orm import Session
from data.handler import user_authorisation, get_db, create_statistics, WebsocketsManager, admin_authorization
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
    find_quantity_tokens = find_key.tokens

    if find_key is not None:

        if find_quantity_tokens > 0:
            
            if model in models:

                resp = openai.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": f"{prompt}"}],
                    max_tokens=2000,
                    temperature= 0.5
                )

                #consumption statistics
                create = datetime.datetime.fromtimestamp(resp.created)
                request_tokens = resp.usage.prompt_tokens
                response_tokens = resp.usage.completion_tokens               
                await create_statistics(user_token, create, request_tokens, response_tokens)

                #count used tokens 
                find_key.tokens -= request_tokens
                sess.add(find_key)
                sess.commit()
                sess.refresh(find_key)

                return (resp.choices[0].message.content.strip())
            
            else:
                return {"Error": "Model invalid"}

        else:   
            return {"Error": "Tokens over"}
        
    else:
        return {"Error": "Authorization token invalid"}
    

@router.post("/moderation")
async def moderation(admin_token: Annotated[str, Header()], texts: Optional[List[str]]= None, image_urls: Optional[List[str]] = None):
    await admin_authorization(admin_token)
    
    data = []

    if texts and not image_urls:
        for text in texts:
            if texts:
                data.append({"type": "text", "text": text})

    if image_urls and not texts:
        for image_url in image_urls:
            if image_url:
                data.append({
                    "type": "image_url",
                    "image_url": {
                        "url": image_url,
                    }
                })
            
    if image_urls and texts:
        for image_url in image_urls:
            data.append({
                "type": "image_url",
                "image_url": {
                    "url": image_url,
                }
            })
            
        for text in texts:
            data.append({"type": "text", "text": text})
            
    resp = openai.moderations.create(
        model="omni-moderation-latest",
        input=data,
    )
      
    resp = [result.flagged for result in resp.results]  

    if any(resp):
        return "Unacceptable content"
    
    
    return "OK"
    

manager = WebsocketsManager()

async def request_for_openai(websocket: WebSocket, user_token: str, model: str, prompt: str, stream: bool, sess):

    find_key = await user_authorisation(user_token, sess)
    find_quantity_tokens = find_key.tokens

    if find_key is not None:

        if find_quantity_tokens > 0:
            
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
                    #consumption statistics
                    create = datetime.datetime.fromtimestamp(resp.created)
                    request_tokens = resp.usage.prompt_tokens
                    response_tokens = resp.usage.completion_tokens               
                    await create_statistics(user_token, create, request_tokens, response_tokens)

                    #count used tokens 
                    find_key.tokens -= request_tokens
                    sess.add(find_key)
                    sess.commit()
                    sess.refresh(find_key)

                    return (resp.choices[0].message.content.strip())
                
                else:
                    for r in resp:
                        if r is not None:
                            if len(r.choices) > 0:
                                msg = r.choices[0].delta.content
                                # print(msg)

                            if msg is not None:
                                await websocket.send_text(json.dumps(msg))

                        # else:
                        #     print(0)
                        #     await websocket.send_text(json.dumps("Error"))
                        #     return
                        if r.usage is not None:
                            request_tokens = r.usage.prompt_tokens
                            response_tokens = r.usage.completion_tokens
                            
                            # create = datetime.datetime.fromtimestamp(resp.created)
                            create = datetime.datetime.now()
                            await create_statistics(user_token, create, request_tokens, response_tokens)
                            
                            find_key.tokens -= request_tokens
                            sess.add(find_key)
                            sess.commit()
                            sess.refresh(find_key)
                            
                    return
            
            else:
                return {"Error": "Model invalid"}

        else:   
            return {"Error": "Tokens over"}
        
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
                        "user_key": user.openai_key,
                        "tokens": user.tokens
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


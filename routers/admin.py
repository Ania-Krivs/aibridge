from fastapi import APIRouter, Depends, HTTPException, Header
from data.handler import get_db, admin_authorization
from sqlalchemy.orm import Session
from data.models import User, Statistics
import data.schemas as resp
from typing import Annotated

import secrets

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get('/create_token')
async def create_key(
    admin_token: Annotated[str, Header()], sess: Session = Depends(get_db)
) -> resp.CreateToken:
    
    await admin_authorization(admin_token)
    
    openai_key = secrets.token_hex(16)
    
    create = User(
        openai_key=openai_key,
        tokens=0
    )
    sess.add(create)
    sess.commit()
    sess.refresh(create)
    return create


@router.delete('/{user_token}/delete')
async def delete(
    user_token: str, admin_token: Annotated[str, Header()], sess: Session = Depends(get_db)
):
    
    await admin_authorization(admin_token)
    
    find_key = sess.query(User).filter_by(openai_key=user_token).first()
    
    if find_key is None:
        raise HTTPException(status_code=404, detail="Token is not found")
    
    sess.query(Statistics).filter_by(openai_key=user_token).delete(synchronize_session=False)
    sess.delete(find_key)
    sess.commit()
    sess.close()
    return "Successfully deleted"

    
@router.patch('/{user_token}/push_prepaid')
async def push_prepaid(
    user_token: str, admin_token: Annotated[str, Header()], quantity_tokens: int, sess: Session = Depends(get_db)
):
    
    await admin_authorization(admin_token)
    
    find_key = sess.query(User).filter_by(openai_key=user_token).first()
    
    if find_key is None:
        raise HTTPException(status_code=404, detail="Token is not found")
    
    find_key.tokens += quantity_tokens
    sess.add(find_key)
    sess.commit()
    sess.refresh(find_key)
    return {'Tokens added': quantity_tokens}

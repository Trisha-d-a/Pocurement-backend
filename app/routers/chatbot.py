from fastapi import APIRouter, Depends, HTTPException
from app.routers.auth import get_current_user

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

@router.post("/")
def chat(message: str, user: str = Depends(get_current_user)):
    """
    Chatbot endpoint protected by JWT authentication.
    """
    try:
        if not message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        response = f"Hello {user}, I received your message: '{message}'"
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chatbot message: {str(e)}")
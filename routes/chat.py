from fastapi import APIRouter, HTTPException, status
from models.schemas import ChatMessage, ChatResponse
from utils.huggingface import hf_service
from utils.auth import generate_unique_id
from datetime import datetime

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/", response_model=ChatResponse)
async def send_message(message_data: ChatMessage):
    """Send a message to the PCOS assistant (no auth required for testing)"""
    
    try:
        # Generate response using Hugging Face
        ai_response = await hf_service.generate_response(message_data.message)
        
        # Generate unique message ID
        message_id = generate_unique_id()
        
        return ChatResponse(
            message_id=message_id,
            response=ai_response,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        print(f"Chat error: {e}")  # Log the error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )
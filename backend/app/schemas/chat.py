from pydantic import BaseModel, Field

"""
Schemas for chat endpoints.

These models define the request payloads accepted by the RAG chat API.
"""


class ChatStreamRequest(BaseModel):
    """
    Request body for streaming a chat response from an analyzed video session.
    """

    # Links the chat turn to metadata, transcripts, and vector chunks created
    # during the video analysis flow.
    session_id: str = Field(..., description="Session returned by /analyze")

    # The user's question or instruction for the RAG assistant.
    message: str = Field(..., description="Creator's chat question")

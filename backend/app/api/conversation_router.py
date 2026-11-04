"""/api/conversations: chat with the AI and conversation history.

Every route requires a login and only ever touches the caller's own
conversations; an unknown or someone else's conversation is a 404 either
way. Creating and sending need an active, verified account; viewing and
deleting your own history are allowed while suspended (access and erasure
rights, POPIA). Admins have no route to any conversation (NFR-013).
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.config.dependencies import (
    enforce_screening_rate_limit,
    get_active_user,
    get_chat_service,
    get_current_user,
)
from app.config.lazy import Provider
from app.domain import User
from app.schemas.conversation_schema import (
    ConversationDetailResponse,
    ConversationResponse,
    CreateConversationRequest,
    SendMessageRequest,
    SendMessageResponse,
)
from app.schemas.error_schema import AUTH_ERROR_RESPONSES, ErrorResponse
from app.service.conversation.i_chat_service import IChatService

router = APIRouter(
    prefix="/api/conversations",
    tags=["conversations"],
    responses={**AUTH_ERROR_RESPONSES, 404: {"model": ErrorResponse, "description": "No such conversation"}},
)

CurrentUser = Annotated[User, Depends(get_current_user)]
ActiveUser = Annotated[User, Depends(get_active_user)]
Chat = Annotated[Provider[IChatService], Depends(get_chat_service)]


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: CreateConversationRequest, user: ActiveUser, chat: Chat
) -> ConversationResponse:
    conversation = await chat.get().create_conversation(user, body.channel, body.title)
    return ConversationResponse.from_conversation(conversation)


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(user: CurrentUser, chat: Chat) -> list[ConversationResponse]:
    return [ConversationResponse.from_conversation(c) for c in await chat.get().list_conversations(user)]


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: UUID, user: CurrentUser, chat: Chat
) -> ConversationDetailResponse:
    return ConversationDetailResponse.from_detail(
        await chat.get().get_conversation(user, str(conversation_id))
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_conversation(conversation_id: UUID, user: CurrentUser, chat: Chat) -> Response:
    """Permanently deletes the conversation and its messages (FR-020)."""
    await chat.get().delete_conversation(user, str(conversation_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{conversation_id}/messages",
    response_model=SendMessageResponse,
    dependencies=[Depends(enforce_screening_rate_limit)],
)
async def send_message(
    conversation_id: UUID, body: SendMessageRequest, user: ActiveUser, chat: Chat
) -> SendMessageResponse:
    """Screen the prompt; if clean, or the student chose to send anyway, the
    prompt (with rule-detected values redacted) goes to the AI and both
    messages are saved. Otherwise status is "needs_decision" and nothing is
    sent or saved (FR-007, FR-008)."""
    outcome = await chat.get().send(user, str(conversation_id), body.text, send_anyway=body.send_anyway)
    return SendMessageResponse.from_outcome(outcome)

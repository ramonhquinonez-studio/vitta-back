from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.deps import get_current_user, get_db, require_role
from app.core.notify import send_push_to_tokens
from app.core.storage import save_upload
from app.schemas.messaging import MessageIn, MessageOut

from ..application.messaging_service import MessagingService
from ..infrastructure.mongo_messaging_repository import MongoMessagingRepository

router = APIRouter(
    prefix="/patients",
    tags=["messaging"],
    dependencies=[Depends(require_role("nutritionist"))],
)


def get_messaging_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> MessagingService:
    return MessagingService(MongoMessagingRepository(db))


def _owner_id(current) -> str:
    owner_id = current.get("sub") or current.get("id")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid user payload")
    return owner_id


def _serialize(message) -> MessageOut:
    return MessageOut(
        id=message.id,
        sender_role=message.sender_role,
        text=message.text,
        created_at=message.created_at,
        read_at=message.read_at,
        attachment_url=message.attachment_url,
        attachment_type=message.attachment_type,
    )


@router.get("/{patient_id}/messages", response_model=list[MessageOut])
async def list_messages(
    patient_id: str,
    since: datetime | None = Query(None),
    current=Depends(get_current_user),
    service: MessagingService = Depends(get_messaging_service),
):
    try:
        messages = await service.list_for_thread(_owner_id(current), patient_id, since=since)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [_serialize(m) for m in messages]


@router.post("/{patient_id}/messages", response_model=MessageOut, status_code=201)
async def send_message(
    patient_id: str,
    payload: MessageIn,
    current=Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
    service: MessagingService = Depends(get_messaging_service),
):
    try:
        message = await service.send_from_nutritionist(
            _owner_id(current),
            patient_id,
            payload.text,
            attachment_url=payload.attachment_url,
            attachment_type=payload.attachment_type,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Push the patient's own account (patients.user_id), not the patient
    # chart id itself.
    patient_doc = await db.patients.find_one({"_id": ObjectId(patient_id)})
    if patient_doc and patient_doc.get("user_id"):
        tokens = [
            d["token"]
            async for d in db.devices.find({"user_id": patient_doc["user_id"]}, {"token": 1, "_id": 0})
        ]
        send_push_to_tokens(
            tokens,
            "Nuevo mensaje de tu nutriólogo",
            payload.text[:120] or "Foto",
            {"type": "chat_message", "patientId": patient_id},
        )

    return _serialize(message)


@router.post("/{patient_id}/messages/attachment", response_model=dict)
async def upload_message_attachment(
    patient_id: str,
    file: UploadFile = File(...),
    current=Depends(get_current_user),
):
    content_type = file.content_type or ""
    allowed = (
        content_type.startswith("image/")
        or content_type.startswith("video/")
        or content_type == "application/pdf"
    )
    if not allowed:
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen, video o PDF.")
    owner_id = _owner_id(current)
    try:
        attachment_url, saved_content_type = await save_upload(
            file,
            subfolder=f"messaging/{owner_id}/{patient_id}",
            max_size_bytes=25 * 1024 * 1024,
        )
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    return {"attachment_url": attachment_url, "content_type": saved_content_type}

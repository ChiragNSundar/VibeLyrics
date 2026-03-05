"""
Training Router
REST API for training data export/import, LM Studio model discovery,
and fine-tuning pipeline management.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import io

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends
from ..database import get_db
from ..models import LyricSession, LyricLine, LineVersion
from ..services.training_data import (
    TrainingDataGenerator,
    LMStudioTrainingManager,
    SuggestionTracker,
)

router = APIRouter()

_generator = TrainingDataGenerator()
_lm_manager = LMStudioTrainingManager()
_suggestion_tracker = SuggestionTracker()


# ── Pydantic models ────────────────────────────────────────────────

class TrainingConfigUpdate(BaseModel):
    base_model: Optional[str] = None
    lora_rank: Optional[int] = None
    lora_alpha: Optional[int] = None
    epochs: Optional[int] = None
    learning_rate: Optional[float] = None
    batch_size: Optional[int] = None
    max_seq_length: Optional[int] = None
    warmup_steps: Optional[int] = None
    weight_decay: Optional[float] = None
    gradient_accumulation_steps: Optional[int] = None
    quantization: Optional[str] = None
    dataset_format: Optional[str] = None


class SuggestionFeedback(BaseModel):
    suggestion_id: str
    status: str  # "accepted" or "rejected"


# ── Dataset endpoints ──────────────────────────────────────────────

@router.get("/status")
async def get_training_status():
    """Get dataset statistics and metadata."""
    stats = _generator.get_stats()
    return {"success": True, **stats}


@router.get("/preview")
async def preview_dataset(n: int = 10):
    """Preview first N training pairs."""
    pairs = _generator.preview(n)
    return {"success": True, "pairs": pairs, "total": len(pairs)}


@router.get("/formats")
async def get_formats():
    """List available export formats."""
    return {"success": True, "formats": _generator.get_available_formats()}


@router.post("/generate")
async def generate_dataset(db: AsyncSession = Depends(get_db)):
    """Regenerate the full training dataset from all current data sources."""
    try:
        # Fetch sessions
        result = await db.execute(select(LyricSession))
        sessions = [s.to_dict() for s in result.scalars().all()]

        # Fetch lines
        result = await db.execute(select(LyricLine))
        lines = [l.to_dict() for l in result.scalars().all()]

        # Fetch versions
        result = await db.execute(select(LineVersion))
        versions = [v.to_dict() for v in result.scalars().all()]

        metadata = _generator.generate(sessions, lines, versions)
        return {"success": True, **metadata}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_dataset(format: str = "zip"):
    """
    Download training dataset in the specified format.
    Formats: zip, alpaca, jsonl, text
    """
    try:
        if format == "zip":
            data = _generator.export_zip()
            return StreamingResponse(
                io.BytesIO(data),
                media_type="application/zip",
                headers={
                    "Content-Disposition": "attachment; filename=vibelyrics_training_data.zip"
                },
            )
        elif format == "alpaca":
            alpaca = _generator.get_alpaca_json()
            content = json.dumps(alpaca, indent=2)
            return StreamingResponse(
                io.BytesIO(content.encode()),
                media_type="application/json",
                headers={
                    "Content-Disposition": "attachment; filename=alpaca.json"
                },
            )
        elif format == "jsonl":
            entries = _generator.get_jsonl_conversations()
            content = "\n".join(json.dumps(e) for e in entries)
            return StreamingResponse(
                io.BytesIO(content.encode()),
                media_type="application/jsonl",
                headers={
                    "Content-Disposition": "attachment; filename=conversations.jsonl"
                },
            )
        elif format == "text":
            corpus = _generator.get_text_corpus()
            return StreamingResponse(
                io.BytesIO(corpus.encode()),
                media_type="text/plain",
                headers={
                    "Content-Disposition": "attachment; filename=corpus.txt"
                },
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown format: {format}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
async def import_dataset(file: UploadFile = File(...)):
    """Import a training dataset (Alpaca JSON or JSONL format)."""
    try:
        content = await file.read()
        text = content.decode("utf-8")

        # Detect format
        if file.filename and file.filename.endswith(".jsonl"):
            entries = [json.loads(line) for line in text.strip().split("\n") if line.strip()]
            # Convert JSONL to Alpaca format
            alpaca = []
            for entry in entries:
                messages = entry.get("messages", [])
                user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
                assistant_msg = next(
                    (m["content"] for m in messages if m["role"] == "assistant"), ""
                )
                if user_msg and assistant_msg:
                    alpaca.append({
                        "instruction": user_msg,
                        "input": "",
                        "output": assistant_msg,
                    })
            result = _generator.import_dataset(alpaca)
        else:
            data = json.loads(text)
            if not isinstance(data, list):
                raise HTTPException(
                    status_code=400, detail="Expected a JSON array of training pairs"
                )
            result = _generator.import_dataset(data)

        return {"success": True, **result}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Suggestion feedback ────────────────────────────────────────────

@router.post("/suggestion-feedback")
async def suggestion_feedback(data: SuggestionFeedback):
    """Mark an AI suggestion as accepted or rejected."""
    if data.status not in ("accepted", "rejected"):
        raise HTTPException(status_code=400, detail="Status must be 'accepted' or 'rejected'")
    _suggestion_tracker.update_status(data.suggestion_id, data.status)
    return {"success": True, "id": data.suggestion_id, "status": data.status}


# ── LM Studio endpoints ───────────────────────────────────────────

@router.get("/lmstudio/models")
async def get_lmstudio_models():
    """Discover models loaded in LM Studio."""
    models = _lm_manager.discover_lmstudio_models()
    return {
        "success": True,
        "models": models,
        "server_available": len(models) > 0,
    }


@router.get("/lmstudio/config")
async def get_training_config():
    """Get current training configuration."""
    return {"success": True, "config": _lm_manager.get_config()}


@router.post("/lmstudio/config")
async def update_training_config(data: TrainingConfigUpdate):
    """Update training configuration."""
    update = {k: v for k, v in data.model_dump().items() if v is not None}
    current = _lm_manager.get_config()
    current.update(update)
    _lm_manager.save_config(current)
    return {"success": True, "config": _lm_manager.get_config()}


@router.post("/lmstudio/start")
async def start_training():
    """Generate the training script and prepare for fine-tuning."""
    import os

    dataset_path = _generator.DATASET_FILE
    if not os.path.exists(dataset_path):
        raise HTTPException(
            status_code=400,
            detail="No training dataset found. Generate one first via POST /api/training/generate",
        )

    # Export as Alpaca JSON for the training script
    alpaca = _generator.get_alpaca_json()
    if not alpaca:
        raise HTTPException(
            status_code=400,
            detail="Training dataset is empty. Add more data and regenerate.",
        )

    alpaca_path = os.path.join("data", "training", "alpaca.json")
    os.makedirs(os.path.dirname(alpaca_path), exist_ok=True)
    with open(alpaca_path, "w") as f:
        json.dump(alpaca, f, indent=2)

    result = _lm_manager.start_training(alpaca_path)
    return {"success": True, **result}


@router.get("/lmstudio/status")
async def get_pipeline_status():
    """Check training pipeline status."""
    return {"success": True, **_lm_manager.get_status()}

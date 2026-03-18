"""
Training Router — Advanced
REST API for training data management, DPO export, multi-LoRA profiles,
micro-feedback, auto-train pipeline, and LM Studio integration.
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
    MicroFeedbackTracker,
    LoRAProfileManager,
    RLHFTracker,
    ContinualLearningManager,
    ConceptEraser,
)

router = APIRouter()

_generator = TrainingDataGenerator()
_lm_manager = LMStudioTrainingManager()
_suggestion_tracker = SuggestionTracker()
_feedback_tracker = MicroFeedbackTracker()
_profile_manager = LoRAProfileManager()
_rlhf_tracker = RLHFTracker()
_continual_manager = ContinualLearningManager()
_concept_eraser = ConceptEraser()


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
    active_profile: Optional[str] = None
    enable_dpo: Optional[bool] = None
    dpo_beta: Optional[float] = None
    quality_threshold: Optional[float] = None
    enable_rag: Optional[bool] = None


class SuggestionFeedback(BaseModel):
    suggestion_id: str
    status: str  # "accepted" or "rejected"
    user_replacement: Optional[str] = None
    feedback_type: Optional[str] = None


class MicroFeedbackRequest(BaseModel):
    suggestion_id: str
    feedback_type: str  # more_complex, change_rhyme, etc.
    original_text: str
    context: Optional[str] = ""


class LoRAProfileCreate(BaseModel):
    id: str
    name: str
    mood_tags: List[str]
    bpm_range: List[int]
    description: Optional[str] = ""


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


@router.get("/preview/dpo")
async def preview_dpo_dataset(n: int = 10):
    """Preview first N DPO preference pairs."""
    pairs = _generator.preview_dpo(n)
    return {"success": True, "pairs": pairs, "total": len(pairs)}


@router.get("/formats")
async def get_formats():
    """List available export formats."""
    return {"success": True, "formats": _generator.get_available_formats()}


@router.post("/generate")
async def generate_dataset(
    db: AsyncSession = Depends(get_db),
    quality_threshold: float = 0.0,
    enable_rag: bool = True,
):
    """Regenerate the full training dataset with quality controls."""
    try:
        # Fetch sessions
        result = await db.execute(select(LyricSession))
        sessions = [s.to_dict() for s in result.scalars().all()]

        # Fetch lines (to_dict already includes rhyme_end, has_internal_rhyme, complexity_score)
        result = await db.execute(select(LyricLine))
        lines = [l.to_dict() for l in result.scalars().all()]

        # Fetch versions
        result = await db.execute(select(LineVersion))
        versions = [v.to_dict() for v in result.scalars().all()]

        # Use config threshold if not specified
        if quality_threshold == 0.0:
            quality_threshold = _lm_manager.get_config().get("quality_threshold", 0.0)
        if enable_rag:
            enable_rag = _lm_manager.get_config().get("enable_rag", True)

        metadata = _generator.generate(
            sessions, lines, versions,
            quality_threshold=quality_threshold,
            enable_rag=enable_rag,
        )
        return {"success": True, **metadata}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_dataset(format: str = "zip"):
    """Download training dataset in the specified format."""
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
        elif format == "dpo":
            dpo = _generator.get_dpo_json()
            content = json.dumps(dpo, indent=2)
            return StreamingResponse(
                io.BytesIO(content.encode()),
                media_type="application/json",
                headers={
                    "Content-Disposition": "attachment; filename=dpo_pairs.json"
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

        if file.filename and file.filename.endswith(".jsonl"):
            entries = [json.loads(line) for line in text.strip().split("\n") if line.strip()]
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


# ── Suggestion & Micro-Feedback ────────────────────────────────────

@router.post("/suggestion-feedback")
async def suggestion_feedback(data: SuggestionFeedback):
    """Mark an AI suggestion as accepted or rejected (with optional DPO replacement)."""
    if data.status not in ("accepted", "rejected"):
        raise HTTPException(status_code=400, detail="Status must be 'accepted' or 'rejected'")
    _suggestion_tracker.update_status(
        data.suggestion_id,
        data.status,
        user_replacement=data.user_replacement,
        feedback_type=data.feedback_type,
    )
    return {"success": True, "id": data.suggestion_id, "status": data.status}


@router.post("/micro-feedback")
async def submit_micro_feedback(data: MicroFeedbackRequest):
    """Submit granular micro-feedback on a suggestion."""
    valid_types = [
        "more_complex", "change_rhyme", "more_aggressive",
        "fix_syllables", "too_generic", "off_topic", "better_wordplay",
    ]
    if data.feedback_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid feedback_type. Valid: {valid_types}"
        )
    fb_id = _feedback_tracker.log_feedback(
        data.suggestion_id, data.feedback_type,
        data.original_text, data.context or "",
    )
    # Also update the suggestion's feedback type
    _suggestion_tracker.update_status(
        data.suggestion_id, "rejected",
        feedback_type=data.feedback_type,
    )
    return {"success": True, "feedback_id": fb_id}


@router.get("/feedback-stats")
async def get_feedback_stats():
    """Get micro-feedback distribution stats."""
    return {
        "success": True,
        "suggestion_feedback": _suggestion_tracker.get_feedback_stats(),
        "total_suggestions": len(_suggestion_tracker.get_all()),
        "accepted": len(_suggestion_tracker.get_accepted()),
        "rejected": len(_suggestion_tracker.get_rejected()),
        "dpo_pairs": len(_suggestion_tracker.get_dpo_pairs()),
    }


# ── LoRA Profiles ─────────────────────────────────────────────────

@router.get("/profiles")
async def get_lora_profiles():
    """Get all LoRA training profiles."""
    return {"success": True, "profiles": _profile_manager.get_profiles()}


@router.post("/profiles")
async def create_lora_profile(data: LoRAProfileCreate):
    """Create a new LoRA training profile."""
    profile = _profile_manager.add_profile(data.model_dump())
    return {"success": True, "profile": profile}


@router.post("/profiles/{profile_id}/generate")
async def generate_profile_dataset(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Generate a filtered dataset for a specific LoRA profile."""
    profile = _profile_manager.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")

    try:
        # First generate the full dataset
        result = await db.execute(select(LyricSession))
        sessions = [s.to_dict() for s in result.scalars().all()]
        result = await db.execute(select(LyricLine))
        lines = [l.to_dict() for l in result.scalars().all()]
        result = await db.execute(select(LineVersion))
        versions = [v.to_dict() for v in result.scalars().all()]

        _generator.generate(sessions, lines, versions)
        full_dataset = _generator._dataset

        # Filter for this profile
        filtered = _profile_manager.filter_dataset_for_profile(
            full_dataset, sessions, profile_id
        )

        # Save profile-specific dataset
        import os
        profile_dir = os.path.join("data/training/profiles", profile_id)
        os.makedirs(profile_dir, exist_ok=True)
        profile_path = os.path.join(profile_dir, "alpaca.json")
        alpaca = [
            {"instruction": p["instruction"], "input": p.get("input", ""), "output": p["output"]}
            for p in filtered
        ]
        with open(profile_path, "w") as f:
            json.dump(alpaca, f, indent=2)

        return {
            "success": True,
            "profile": profile_id,
            "total_pairs": len(filtered),
            "dataset_path": profile_path,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
async def start_training(auto_run: bool = False):
    """Generate training script and optionally auto-run it."""
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

    profile = _lm_manager.get_config().get("active_profile") or "default"
    alpaca_path = os.path.join("data", "training", f"alpaca_{profile}.json")
    os.makedirs(os.path.dirname(alpaca_path), exist_ok=True)
    with open(alpaca_path, "w") as f:
        json.dump(alpaca, f, indent=2)

    result = _lm_manager.start_training(alpaca_path, auto_run=auto_run)
    return {"success": True, **result}


@router.get("/lmstudio/status")
async def get_pipeline_status():
    """Check training pipeline status."""
    return {"success": True, **_lm_manager.get_status()}


# ═══════════════════════════════════════════════════════════════════
#  Phase 8: RLHF Arena, Continual Learning, Concept Erasure
# ═══════════════════════════════════════════════════════════════════


# ── RLHF Arena ──

class RLHFVoteRequest(BaseModel):
    prompt: str
    variants: List[str]
    chosen_index: int
    session_id: int = 0


@router.post("/rlhf/vote")
async def submit_rlhf_vote(data: RLHFVoteRequest):
    """Submit an AI Arena vote — chosen variant + rejected variants become DPO pairs."""
    if data.chosen_index < 0 or data.chosen_index >= len(data.variants):
        raise HTTPException(status_code=400, detail="chosen_index out of range")
    match_id = _rlhf_tracker.log_vote(
        prompt=data.prompt,
        variants=data.variants,
        chosen_index=data.chosen_index,
        session_id=data.session_id,
    )
    return {
        "success": True,
        "match_id": match_id,
        "dpo_pairs_created": len(data.variants) - 1,
    }


@router.get("/rlhf/stats")
async def get_rlhf_stats():
    """Get RLHF arena statistics."""
    return {"success": True, **_rlhf_tracker.get_stats()}


@router.get("/rlhf/history")
async def get_rlhf_history():
    """Get recent RLHF arena match history."""
    matches = _rlhf_tracker.get_all()
    return {"success": True, "matches": matches[-20:], "total": len(matches)}


# ── Continual Learning ──

class ContinualConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    min_complexity: Optional[int] = None
    batch_size: Optional[int] = None
    auto_retrain: Optional[bool] = None


@router.get("/continual/config")
async def get_continual_config():
    """Get continual learning configuration."""
    return {"success": True, **_continual_manager.get_config()}


@router.post("/continual/config")
async def update_continual_config(data: ContinualConfigUpdate):
    """Update continual learning configuration."""
    update = {k: v for k, v in data.model_dump().items() if v is not None}
    config = _continual_manager.update_config(update)
    return {"success": True, "config": config}


@router.get("/continual/status")
async def get_continual_status():
    """Get continual learning buffer status and progress."""
    return {"success": True, **_continual_manager.get_buffer_status()}


@router.post("/continual/flush")
async def flush_continual_buffer():
    """Flush the continual learning buffer and return its contents."""
    flushed = _continual_manager.flush_buffer()
    return {"success": True, "flushed_count": len(flushed), "items": flushed[:10]}


# ── Concept Erasure ──

class ErasurePreviewRequest(BaseModel):
    banned_words: List[str]


@router.post("/erasure/preview")
async def preview_erasure(data: ErasurePreviewRequest, db: AsyncSession = Depends(get_db)):
    """Preview how many synthetic DPO pairs concept erasure would generate."""
    # Get high-quality lines to use as source material
    result = await db.execute(
        select(LyricLine).where(LyricLine.complexity_score >= 30)
    )
    lines = result.scalars().all()
    high_q = [{"text": l.final_version or l.user_input} for l in lines if l.final_version or l.user_input]

    stats = _concept_eraser.get_erasure_stats(data.banned_words, high_q)
    return {"success": True, **stats}


@router.post("/erasure/generate")
async def generate_erasure_pairs(data: ErasurePreviewRequest, db: AsyncSession = Depends(get_db)):
    """Generate and return concept erasure DPO pairs for the given banned words."""
    result = await db.execute(
        select(LyricLine).where(LyricLine.complexity_score >= 30)
    )
    lines = result.scalars().all()
    high_q = [{"text": l.final_version or l.user_input} for l in lines if l.final_version or l.user_input]

    pairs = _concept_eraser.generate_erasure_pairs(data.banned_words, high_q)
    return {"success": True, "pairs": pairs[:20], "total": len(pairs)}


"""
Training Data Service
- Generate fine-tuning datasets from VibeLyrics learned data
- Export in Alpaca JSON, conversational JSONL, and plain-text corpus formats
- Import external datasets for merging
- LM Studio model discovery and training pipeline management
"""
import json
import os
import io
import zipfile
import time
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path


TRAINING_DIR = "data/training"
SUGGESTION_LOG = "data/suggestion_log.json"


class SuggestionTracker:
    """Track AI suggestion acceptance/rejection for training signal."""

    DATA_FILE = SUGGESTION_LOG

    def __init__(self):
        self.suggestions: List[Dict] = []
        self._load()

    def _load(self):
        if os.path.exists(self.DATA_FILE):
            try:
                with open(self.DATA_FILE, "r") as f:
                    self.suggestions = json.load(f)
            except Exception:
                self.suggestions = []

    def _save(self):
        os.makedirs(os.path.dirname(self.DATA_FILE), exist_ok=True)
        with open(self.DATA_FILE, "w") as f:
            json.dump(self.suggestions[-500:], f, indent=2)

    def log_suggestion(
        self,
        session_id: int,
        prompt: str,
        suggestion: str,
        action: str = "continue",
    ) -> str:
        """Log an AI suggestion with pending status. Returns suggestion_id."""
        suggestion_id = f"sug_{int(time.time() * 1000)}"
        self.suggestions.append(
            {
                "id": suggestion_id,
                "session_id": session_id,
                "prompt": prompt,
                "suggestion": suggestion,
                "action": action,
                "status": "pending",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._save()
        return suggestion_id

    def update_status(self, suggestion_id: str, status: str):
        """Mark a suggestion as 'accepted' or 'rejected'."""
        for s in self.suggestions:
            if s["id"] == suggestion_id:
                s["status"] = status
                break
        self._save()

    def get_accepted(self) -> List[Dict]:
        return [s for s in self.suggestions if s.get("status") == "accepted"]

    def get_all(self) -> List[Dict]:
        return self.suggestions

    def reset(self):
        self.suggestions = []
        if os.path.exists(self.DATA_FILE):
            os.remove(self.DATA_FILE)


class TrainingDataGenerator:
    """
    Generate fine-tuning datasets from all VibeLyrics learning sources.

    Sources:
    1. Session lines (consecutive line pairs)
    2. Line versions  (rewrite pairs)
    3. Corrections    (improve pairs from CorrectionTracker)
    4. Suggestion log (accepted AI suggestions)
    5. Imported datasets (user-supplied)
    """

    DATASET_FILE = os.path.join(TRAINING_DIR, "dataset.json")
    METADATA_FILE = os.path.join(TRAINING_DIR, "metadata.json")
    IMPORTED_FILE = os.path.join(TRAINING_DIR, "imported.json")

    def __init__(self):
        self._dataset: List[Dict] = []
        self._metadata: Dict = {}
        self._load()

    # ── persistence ────────────────────────────────────────────────

    def _load(self):
        if os.path.exists(self.DATASET_FILE):
            try:
                with open(self.DATASET_FILE, "r") as f:
                    self._dataset = json.load(f)
            except Exception:
                self._dataset = []
        if os.path.exists(self.METADATA_FILE):
            try:
                with open(self.METADATA_FILE, "r") as f:
                    self._metadata = json.load(f)
            except Exception:
                self._metadata = {}

    def _save(self):
        os.makedirs(TRAINING_DIR, exist_ok=True)
        with open(self.DATASET_FILE, "w") as f:
            json.dump(self._dataset, f, indent=2)
        with open(self.METADATA_FILE, "w") as f:
            json.dump(self._metadata, f, indent=2)

    # ── dataset generation ─────────────────────────────────────────

    def generate(self, db_sessions: List[Dict], db_lines: List[Dict],
                 db_versions: List[Dict]) -> Dict:
        """
        Rebuild the entire training dataset from current DB + JSON data.

        Parameters:
            db_sessions - list of session dicts from SQLite
            db_lines    - list of line dicts from SQLite
            db_versions - list of version dicts from SQLite
        """
        pairs: List[Dict] = []

        # ── 1. Consecutive session lines ──
        sessions_map: Dict[int, List[str]] = {}
        for line in db_lines:
            sid = line.get("session_id")
            text = line.get("final_version") or line.get("user_input", "")
            if sid and text.strip():
                sessions_map.setdefault(sid, []).append(text.strip())

        session_meta: Dict[int, Dict] = {}
        for s in db_sessions:
            session_meta[s["id"]] = s

        for sid, lines in sessions_map.items():
            meta = session_meta.get(sid, {})
            mood = meta.get("mood", "")
            theme = meta.get("theme", "")
            bpm = meta.get("bpm", 140)

            context_parts = []
            if theme:
                context_parts.append(f"theme: {theme}")
            if mood:
                context_parts.append(f"mood: {mood}")
            if bpm:
                context_parts.append(f"BPM: {bpm}")
            context = ", ".join(context_parts) if context_parts else "freestyle"

            for i in range(len(lines) - 1):
                pairs.append({
                    "instruction": f"Continue this rap verse ({context}). "
                                   "Output only the next lyric line.",
                    "input": lines[i],
                    "output": lines[i + 1],
                    "source": "session_lines",
                    "session_id": sid,
                })

        # ── 2. Line versions (rewrite pairs) ──
        # Group versions by line_id
        version_map: Dict[int, List[Dict]] = {}
        for v in db_versions:
            lid = v.get("line_id")
            if lid:
                version_map.setdefault(lid, []).append(v)

        for lid, versions in version_map.items():
            sorted_v = sorted(versions, key=lambda x: x.get("version_number", 0))
            for i in range(len(sorted_v) - 1):
                old_text = sorted_v[i].get("content", "").strip()
                new_text = sorted_v[i + 1].get("content", "").strip()
                if old_text and new_text and old_text != new_text:
                    pairs.append({
                        "instruction": "Rewrite this lyric line to improve it. "
                                       "Output only the improved line.",
                        "input": old_text,
                        "output": new_text,
                        "source": "line_versions",
                    })

        # ── 3. Corrections (from CorrectionTracker) ──
        corrections_file = "data/corrections.json"
        if os.path.exists(corrections_file):
            try:
                with open(corrections_file, "r") as f:
                    corrections = json.load(f)
                for c in corrections:
                    orig = c.get("original", "").strip()
                    corrected = c.get("corrected", "").strip()
                    if orig and corrected and orig != corrected:
                        pairs.append({
                            "instruction": "Improve this lyric line. "
                                           "Output only the improved version.",
                            "input": orig,
                            "output": corrected,
                            "source": "corrections",
                        })
            except Exception:
                pass

        # ── 4. Accepted AI suggestions ──
        if os.path.exists(SUGGESTION_LOG):
            try:
                with open(SUGGESTION_LOG, "r") as f:
                    suggestions = json.load(f)
                for s in suggestions:
                    if s.get("status") == "accepted":
                        prompt = s.get("prompt", "").strip()
                        suggestion = s.get("suggestion", "").strip()
                        action = s.get("action", "continue")
                        if prompt and suggestion:
                            pairs.append({
                                "instruction": f"As a ghostwriter, {action} this lyric. "
                                               "Output only the lyric line.",
                                "input": prompt,
                                "output": suggestion,
                                "source": "accepted_suggestions",
                            })
            except Exception:
                pass

        # ── 5. Imported datasets ──
        if os.path.exists(self.IMPORTED_FILE):
            try:
                with open(self.IMPORTED_FILE, "r") as f:
                    imported = json.load(f)
                for entry in imported:
                    entry["source"] = "imported"
                    pairs.append(entry)
            except Exception:
                pass

        self._dataset = pairs
        self._metadata = {
            "total_pairs": len(pairs),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sources": self._count_sources(pairs),
        }
        self._save()
        return self._metadata

    def _count_sources(self, pairs: List[Dict]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for p in pairs:
            src = p.get("source", "unknown")
            counts[src] = counts.get(src, 0) + 1
        return counts

    # ── export formats ─────────────────────────────────────────────

    def get_alpaca_json(self) -> List[Dict]:
        """Return dataset in Alpaca instruction-tuning format."""
        return [
            {
                "instruction": p["instruction"],
                "input": p.get("input", ""),
                "output": p["output"],
            }
            for p in self._dataset
        ]

    def get_jsonl_conversations(self) -> List[Dict]:
        """Return dataset as ChatML / conversational JSONL entries."""
        # Load user style for system prompt
        style_context = self._load_style_context()
        system_msg = (
            "You are VibeLyrics, an elite rap ghostwriter AI. "
            "You have been trained on the user's personal writing style. "
            f"{style_context}"
            "Respond with only the lyric line — no explanations or labels."
        )

        entries = []
        for p in self._dataset:
            messages = [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": f"{p['instruction']}\n\n{p.get('input', '')}".strip()},
                {"role": "assistant", "content": p["output"]},
            ]
            entries.append({"messages": messages})
        return entries

    def get_text_corpus(self) -> str:
        """Return all lyrics as a plain-text corpus for continued pretraining."""
        lines = []
        seen = set()
        for p in self._dataset:
            for text in [p.get("input", ""), p.get("output", "")]:
                text = text.strip()
                if text and text not in seen:
                    seen.add(text)
                    lines.append(text)
        return "\n".join(lines)

    def _load_style_context(self) -> str:
        style_file = "data/user_style.json"
        if not os.path.exists(style_file):
            return ""
        try:
            with open(style_file, "r") as f:
                style = json.load(f)
            themes = style.get("themes", {}).get("preferred_themes", [])
            flow = style.get("learned_patterns", {}).get("flow_patterns", [])
            parts = []
            if themes:
                parts.append(f"Preferred themes: {', '.join(themes[:5])}.")
            if flow:
                parts.append(f"Flow styles: {', '.join(flow[:3])}.")
            return " ".join(parts) + " " if parts else ""
        except Exception:
            return ""

    # ── export ZIP ─────────────────────────────────────────────────

    def export_zip(self) -> bytes:
        """Create an in-memory ZIP file with all 3 export formats + metadata."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            # Alpaca JSON
            alpaca = self.get_alpaca_json()
            zf.writestr("alpaca.json", json.dumps(alpaca, indent=2))

            # JSONL
            jsonl_entries = self.get_jsonl_conversations()
            jsonl_text = "\n".join(json.dumps(e) for e in jsonl_entries)
            zf.writestr("conversations.jsonl", jsonl_text)

            # Text corpus
            corpus = self.get_text_corpus()
            zf.writestr("corpus.txt", corpus)

            # Metadata
            zf.writestr("metadata.json", json.dumps(self._metadata, indent=2))

        return buf.getvalue()

    # ── import ─────────────────────────────────────────────────────

    def import_dataset(self, data: List[Dict]) -> Dict:
        """
        Import an external dataset (Alpaca format).
        Merges with imported.json, does NOT overwrite generated data.
        """
        os.makedirs(TRAINING_DIR, exist_ok=True)

        existing: List[Dict] = []
        if os.path.exists(self.IMPORTED_FILE):
            try:
                with open(self.IMPORTED_FILE, "r") as f:
                    existing = json.load(f)
            except Exception:
                existing = []

        # Validate and normalize entries
        added = 0
        for entry in data:
            if "instruction" in entry and "output" in entry:
                existing.append({
                    "instruction": entry["instruction"],
                    "input": entry.get("input", ""),
                    "output": entry["output"],
                    "source": "imported",
                })
                added += 1

        with open(self.IMPORTED_FILE, "w") as f:
            json.dump(existing, f, indent=2)

        return {"imported": added, "total_imported": len(existing)}

    # ── query & preview ────────────────────────────────────────────

    def get_stats(self) -> Dict:
        """Return dataset statistics."""
        if not self._metadata:
            return {
                "total_pairs": 0,
                "generated_at": None,
                "sources": {},
            }
        return self._metadata

    def preview(self, n: int = 10) -> List[Dict]:
        """Return the first N training pairs."""
        return self._dataset[:n]

    def get_available_formats(self) -> List[Dict]:
        return [
            {
                "id": "alpaca",
                "name": "Alpaca JSON",
                "description": "Instruction-tuning format (instruction/input/output). "
                               "Compatible with Unsloth, axolotl, LLaMA-Factory.",
                "extension": ".json",
            },
            {
                "id": "jsonl",
                "name": "ChatML JSONL",
                "description": "Conversational format with system/user/assistant messages. "
                               "Compatible with OpenAI fine-tuning, Unsloth chat.",
                "extension": ".jsonl",
            },
            {
                "id": "text",
                "name": "Plain Text Corpus",
                "description": "Raw lyrics text for continued pretraining or "
                               "domain adaptation. One line per lyric.",
                "extension": ".txt",
            },
            {
                "id": "zip",
                "name": "Complete ZIP Bundle",
                "description": "All formats bundled together with metadata.",
                "extension": ".zip",
            },
        ]


class LMStudioTrainingManager:
    """
    Manage LM Studio model discovery and training pipeline.

    Training flow:
    1. Export data from VibeLyrics as Alpaca JSON
    2. Fine-tune with Unsloth / axolotl (external process)
    3. Convert to GGUF
    4. Load into LM Studio
    """

    CONFIG_FILE = os.path.join(TRAINING_DIR, "training_config.json")
    STATUS_FILE = os.path.join(TRAINING_DIR, "training_status.json")

    def __init__(self):
        self.config = self._load_config()
        self.status = self._load_status()

    def _load_config(self) -> Dict:
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return self._default_config()

    def _default_config(self) -> Dict:
        return {
            "base_model": "unsloth/Mistral-7B-Instruct-v0.3-bnb-4bit",
            "output_dir": "data/training/output",
            "lora_rank": 16,
            "lora_alpha": 16,
            "epochs": 3,
            "learning_rate": 2e-4,
            "batch_size": 4,
            "max_seq_length": 512,
            "warmup_steps": 10,
            "weight_decay": 0.01,
            "gradient_accumulation_steps": 4,
            "quantization": "4bit",
            "dataset_format": "alpaca",
        }

    def _load_status(self) -> Dict:
        if os.path.exists(self.STATUS_FILE):
            try:
                with open(self.STATUS_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"state": "idle", "progress": 0, "message": "", "started_at": None}

    def save_config(self, config: Dict):
        os.makedirs(TRAINING_DIR, exist_ok=True)
        self.config = {**self._default_config(), **config}
        with open(self.CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=2)

    def _save_status(self):
        os.makedirs(TRAINING_DIR, exist_ok=True)
        with open(self.STATUS_FILE, "w") as f:
            json.dump(self.status, f, indent=2)

    def get_config(self) -> Dict:
        return self.config

    def get_status(self) -> Dict:
        return self.status

    def discover_lmstudio_models(self) -> List[Dict]:
        """Query LM Studio's local API for loaded models."""
        lm_url = os.getenv("LM_STUDIO_BASE_URL", "http://127.0.0.1:1234")
        if not lm_url.endswith("/v1"):
            lm_url = f"{lm_url.rstrip('/')}/v1"

        try:
            import httpx
            check_url = lm_url.rstrip("/").replace("/v1", "")
            r = httpx.get(f"{check_url}/v1/models", timeout=3)
            if r.status_code == 200:
                models = r.json().get("data", [])
                return [
                    {
                        "id": m.get("id", "unknown"),
                        "object": m.get("object", "model"),
                        "owned_by": m.get("owned_by", "local"),
                    }
                    for m in models
                ]
        except Exception:
            pass
        return []

    def start_training(self, dataset_path: str) -> Dict:
        """
        Kick off a fine-tuning job.
        This creates a training script and runs it as a subprocess.
        The actual training uses Unsloth for QLoRA fine-tuning.
        """
        self.status = {
            "state": "preparing",
            "progress": 5,
            "message": "Generating training script...",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "dataset_path": dataset_path,
        }
        self._save_status()

        # Generate the training script
        script_path = os.path.join(TRAINING_DIR, "train.py")
        self._generate_training_script(script_path, dataset_path)

        self.status["state"] = "ready"
        self.status["progress"] = 10
        self.status["message"] = (
            f"Training script generated at {script_path}. "
            "Run it manually or use the auto-train feature. "
            "See docs/TRAINING_SETUP.md for instructions."
        )
        self.status["script_path"] = script_path
        self._save_status()

        return self.status

    def _generate_training_script(self, script_path: str, dataset_path: str):
        """Generate a Python training script using Unsloth."""
        os.makedirs(os.path.dirname(script_path), exist_ok=True)
        config = self.config
        script = f'''#!/usr/bin/env python3
"""
VibeLyrics Fine-Tuning Script
Auto-generated by VibeLyrics Training Hub
Uses Unsloth for QLoRA fine-tuning.
"""
import json, os

# ── Configuration ──
BASE_MODEL     = "{config['base_model']}"
DATASET_PATH   = r"{os.path.abspath(dataset_path)}"
OUTPUT_DIR     = r"{os.path.abspath(config['output_dir'])}"
LORA_RANK      = {config['lora_rank']}
LORA_ALPHA     = {config['lora_alpha']}
EPOCHS         = {config['epochs']}
LEARNING_RATE  = {config['learning_rate']}
BATCH_SIZE     = {config['batch_size']}
MAX_SEQ_LEN    = {config['max_seq_length']}
WARMUP_STEPS   = {config['warmup_steps']}
WEIGHT_DECAY   = {config['weight_decay']}
GRAD_ACCUM     = {config['gradient_accumulation_steps']}

def main():
    print("=" * 60)
    print("VibeLyrics Fine-Tuning Pipeline")
    print("=" * 60)

    # Step 1: Load model with Unsloth
    print("\\n[1/5] Loading base model with Unsloth 4-bit quantization...")
    from unsloth import FastLanguageModel

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=MAX_SEQ_LEN,
        dtype=None,
        load_in_4bit=True,
    )

    # Step 2: Add LoRA adapters
    print("[2/5] Attaching LoRA adapters...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_RANK,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                         "gate_proj", "up_proj", "down_proj"],
        lora_alpha=LORA_ALPHA,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
    )

    # Step 3: Load dataset
    print("[3/5] Loading VibeLyrics training dataset...")
    from datasets import Dataset

    with open(DATASET_PATH, "r") as f:
        raw_data = json.load(f)

    # Format as Alpaca prompt template
    TEMPLATE = """Below is an instruction that describes a task, paired with an input. Write a response.

### Instruction:
{{instruction}}

### Input:
{{input}}

### Response:
{{output}}"""

    def format_sample(sample):
        text = TEMPLATE.replace("{{instruction}}", sample["instruction"])
        text = text.replace("{{input}}", sample.get("input", ""))
        text = text.replace("{{output}}", sample["output"])
        return {{"text": text + tokenizer.eos_token}}

    dataset = Dataset.from_list(raw_data).map(format_sample)
    print(f"    Loaded {{len(dataset)}} training samples")

    # Step 4: Train
    print("[4/5] Starting fine-tuning...")
    from trl import SFTTrainer
    from transformers import TrainingArguments

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LEN,
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=BATCH_SIZE,
            gradient_accumulation_steps=GRAD_ACCUM,
            warmup_steps=WARMUP_STEPS,
            num_train_epochs=EPOCHS,
            learning_rate=LEARNING_RATE,
            fp16=True,
            logging_steps=5,
            optim="adamw_8bit",
            weight_decay=WEIGHT_DECAY,
            lr_scheduler_type="linear",
            output_dir=OUTPUT_DIR,
            save_strategy="epoch",
        ),
    )

    trainer.train()
    print("    Training complete!")

    # Step 5: Save and convert
    print("[5/5] Saving model...")
    lora_dir = os.path.join(OUTPUT_DIR, "lora_adapter")
    model.save_pretrained(lora_dir)
    tokenizer.save_pretrained(lora_dir)
    print(f"    LoRA adapter saved to: {{lora_dir}}")

    # Merge and save in float16 for GGUF conversion
    merged_dir = os.path.join(OUTPUT_DIR, "merged_model")
    model.save_pretrained_merged(merged_dir, tokenizer, save_method="merged_16bit")
    print(f"    Merged model saved to: {{merged_dir}}")

    # GGUF conversion
    gguf_path = os.path.join(OUTPUT_DIR, "vibelyrics-model.gguf")
    print(f"    Converting to GGUF (Q4_K_M)...")
    model.save_pretrained_gguf(
        gguf_path.replace(".gguf", ""),
        tokenizer,
        quantization_method="q4_k_m",
    )
    print(f"    GGUF saved to: {{gguf_path}}")

    print()
    print("=" * 60)
    print("DONE! Next steps:")
    print(f"  1. Copy the GGUF file to your LM Studio models folder")
    print(f"  2. Load it in LM Studio")
    print(f"  3. Set VibeLyrics provider to 'lmstudio'")
    print("=" * 60)

if __name__ == "__main__":
    main()
'''
        with open(script_path, "w") as f:
            f.write(script)

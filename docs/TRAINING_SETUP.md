# VibeLyrics Training Setup — Advanced Guide

Complete guide to fine-tuning a local AI model on your VibeLyrics writing style.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Quality-Gated Data Export](#quality-gated-data-export)
3. [DPO Preference Training](#dpo-preference-training)
4. [Multi-LoRA Profiles](#multi-lora-profiles)
5. [RAG-Augmented Training](#rag-augmented-training)
6. [Unsloth Fine-Tuning](#unsloth-fine-tuning)
7. [GGUF Conversion & LM Studio](#gguf-conversion--lm-studio)
8. [Micro-Feedback System](#micro-feedback-system)
9. [Auto-Train Pipeline](#auto-train-pipeline)
10. [Importing Datasets](#importing-datasets)
11. [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# 1. Open VibeLyrics → Learning Center → 🔬 Training Hub
# 2. Click "Generate Dataset" on the Overview tab
# 3. Go to Export tab → Download ZIP bundle
# 4. Follow Unsloth instructions below to fine-tune
```

---

## How Custom Models Work

When you want to train VibeLyrics on your unique style, here is the exact lifecycle:

### Phase 1: Training (Teaching your style)
1. **The Base Model:** You start with a raw, un-styled model (like `llama-3-8b`) downloaded from Hugging Face or via LM Studio.
2. **Generate Your Data:** In VibeLyrics' **Training Hub**, you click "Generate Dataset". This packages all your written lyrics, punchlines, and DPO rejected/chosen pairs into an Alpaca JSON format.
3. **Configure & Train:** In the **LM Studio tab** of the Training Hub, you select your base model and click **🚀 Auto-Train** (or run the generated python script manually). 
4. **What the script does:** 
   - It feeds the base model your lyrics dataset (the "SFT" phase) to learn your vocabulary and flow.
   - It feeds it your rejected lines (the "DPO" phase) to learn what clichés to avoid.
   - It packages this newly trained "brain" into a single file called a **GGUF** (e.g., `vibelyrics-aggressive.gguf`).

### Phase 2: Using Your Custom Model (Writing)
1. **Load it:** You open the LM Studio application, take your newly created `vibelyrics.gguf` file, and load it.
2. **Start the Server:** Inside LM Studio, start the "Local Server" (running on port `1234`).
3. **Connect VibeLyrics:** Open VibeLyrics, go to **Settings ⚙️ -> AI Provider**, and select **LM Studio (Local)**.

**The Result:** The ghost-text suggestions streaming into your editor are now coming directly from your custom model running locally on your PC. It will naturally use your favorite words, match your syllable counts, and write in the specific mood/genre you trained it on!

---

## Quality-Gated Data Export

VibeLyrics scores each line with a **complexity score** (0-100). Set a quality threshold to only train on your best work:

| Threshold | Effect |
|-----------|--------|
| 0 | No filter (all lines included) |
| 30 | Good quality lines only |
| 60 | High quality — advanced wordplay only |

**Set threshold:** LM Studio tab → Training Configuration → "Quality Threshold" field.

When generating a dataset, lines with `complexity_score < threshold` are excluded. The Overview tab shows how many lines were filtered.

### Syllable & Metre Tagging

Training instructions automatically include syllable targets and rhyme hints:
```
"Continue this rap verse (theme: struggle, mood: aggressive, BPM: 140).
 Target: ~12 syllables. Rhyme with 'pain'. Output only the next lyric line. [HIGH QUALITY]"
```

---

## DPO Preference Training

DPO (Direct Preference Optimization) teaches the model what *not* to write.

### How It Works

1. **AI suggests a line** → You reject it and write your own
2. VibeLyrics saves: `{chosen: your_line, rejected: ai_suggestion}`
3. During training, the model is penalized for the rejected style

### Providing DPO Data

When rejecting an AI suggestion via the API:
```json
POST /api/training/suggestion-feedback
{
    "suggestion_id": "sug_17098234...",
    "status": "rejected",
    "user_replacement": "My better version of the line",
    "feedback_type": "too_generic"
}
```

### Feedback Types
- `more_complex` — Needs advanced wordplay
- `change_rhyme` — Different rhyme scheme wanted
- `more_aggressive` — Harder delivery needed
- `fix_syllables` — Syllable count was off
- `too_generic` — Too cliché
- `off_topic` — Didn't match the theme
- `better_wordplay` — Needs cleverer punchlines

### Exporting DPO Data
- **DPO tab** in Training Hub shows pair counts
- Export → Download "DPO Preference Pairs" format
- ZIP bundle includes `dpo_pairs.json` automatically

---

## Multi-LoRA Profiles

Train specialized LoRA adapters for different moods/genres:

| Profile | Mood Tags | BPM Range |
|---------|-----------|-----------|
| Aggressive / Diss | aggressive, angry, intense | 120-180 |
| Melodic / R&B | melodic, emotional, romantic | 70-110 |
| Trap / Hype | hype, confident, energetic | 130-160 |
| Conscious / Lyrical | conscious, thoughtful, deep | 80-120 |

### Using Profiles

1. **🎭 LoRA Profiles tab** → Click profile card → "Generate" to create filtered dataset
2. **Select** a profile to make it active
3. **LM Studio tab** → "Generate Script" creates a profile-specific training script
4. Output: `vibelyrics-aggressive.gguf`, `vibelyrics-melodic.gguf`, etc.

---

## RAG-Augmented Training

When enabled (default), the dataset generator finds similar lines across different sessions and creates **callback** training pairs:

```
"Write a callback line that references this past lyric.
 Shared themes: grind, hustle. Output only the new callback line."
```

This teaches the model to make self-referential lyrics — a hallmark of great rappers.

Toggle: **LM Studio tab → Enable RAG Callbacks** checkbox.

---

## Unsloth Fine-Tuning

### Prerequisites

```bash
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
pip install --no-deps "trl<0.9.0" peft accelerate bitsandbytes xformers
```

### Running the Generated Script

```bash
# After clicking "Generate Script" in Training Hub:
cd data/training
python train_default.py        # or train_aggressive.py, etc.
```

The script handles:
1. Loading base model (4-bit quantized)
2. Attaching LoRA adapters
3. **SFT phase** — main instruction fine-tuning
4. **DPO phase** (if enabled) — preference optimization
5. Saving LoRA adapter + merged model
6. GGUF conversion (Q4_K_M)

---

## GGUF Conversion & LM Studio

After training completes:

1. Copy `data/training/output/vibelyrics-{profile}.gguf` to LM Studio's models folder
2. Open LM Studio → Load the model
3. In VibeLyrics, set provider to `lmstudio`

LM Studio models folder default locations:
- **Windows:** `C:\Users\<you>\.cache\lm-studio\models\`
- **macOS:** `~/.cache/lm-studio/models/`
- **Linux:** `~/.cache/lm-studio/models/`

---

## Micro-Feedback System

Beyond accept/reject, VibeLyrics captures granular feedback to refine training:

Each feedback type generates a targeted training instruction. For example, clicking "Too Generic" creates:
```
"Rewrite this rap line. Avoid clichés. Be more specific, personal, and original."
```

These micro-instructions are mixed into the training data to teach the model your specific preferences.

---

## Auto-Train Pipeline

Two options for running training:

| Mode | Button | Description |
|------|--------|-------------|
| Script Only | 📝 Generate Script | Creates `train_{profile}.py` for manual execution |
| Auto-Train | 🚀 Auto-Train | Runs training as background subprocess |

Auto-Train requirements:
- Python environment with Unsloth installed
- CUDA-compatible GPU (8GB+ VRAM recommended)
- Dataset must be generated first

Pipeline status shows in real-time on the LM Studio tab.

---

## Importing Datasets

Import external rap datasets to augment your training data:

**Supported formats:**
- Alpaca JSON: `[{"instruction": "...", "input": "...", "output": "..."}]`
- ChatML JSONL: `{"messages": [{"role": "user", ...}, {"role": "assistant", ...}]}`

Import via: **📥 Import tab** → drag & drop or file picker

---

## How to Build a Dataset from Scratch

If you're starting with zero (or very little) existing data but want to train a highly capable model, use these strategies:

### 1. The "Synthetic Data" Strategy (Scrape)
Use the built-in Lyrics Scraper in the Learning Center to pull albums from your favorite artists (e.g., Kendrick, Cole). When you click "Generate Dataset" in the Training Hub, the system converts those scraped songs into thousands of SFT pairs. Your model instantly learns complex rhyme structures from the greats without you typing a single line.

### 2. The "Style Cloning" Strategy (Import)
Find open-source hip-hop datasets on HuggingFace (e.g., Rap Genius datasets). Go to the **📥 Import tab** and upload them. You instantly bootstrap your model with thousands of examples of formatting and song structure.

### 3. The "Seed & Iterate" Strategy (AI Generation)
Instead of writing 1,000 lines manually, write 10 great lines. Set up an aggressive beat, write a few punchlines, and use the VibeLyrics "Ghost text" and "⚡ Improve" tools. Accept the great suggestions. Reject the bad ones (which automatically creates ⚖️ DPO preference pairs). You can generate a 500-pair dataset in an hour just by actively curating the AI's outputs.

### 4. Leverage the "Score-Gate" (Quality Control)
If you generate data automatically, much of it might be "filler" lines ("Yeah", "Uh"). When generating your dataset, set the **Quality Threshold to 40 or 50**. VibeLyrics will discard simple lines and *only* train your model on lines with complex internal rhymes, multi-syllabic setups, and high vocabulary scores. A model trained on 500 elite lines is much better than one trained on 5,000 basic lines.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| CUDA out of memory | Reduce batch_size to 2, max_seq_length to 256 |
| Training loss not decreasing | Increase dataset size, reduce learning_rate |
| DPO makes model worse | Reduce dpo_beta (try 0.05), ensure enough DPO pairs (50+) |
| GGUF loading fails | Re-run conversion, try Q5_K_M instead of Q4_K_M |
| Profile dataset empty | Check that sessions have matching mood tags |
| RAG pairs too noisy | Increase quality_threshold to filter low-quality source lines |

### Recommended Hyperparameters by Dataset Size

| Dataset Size | Epochs | Learning Rate | Quality Threshold |
|-------------|--------|---------------|-------------------|
| < 100 pairs | 5-10 | 1e-4 | 0 (use all data) |
| 100-500 pairs | 3-5 | 2e-4 | 20 |
| 500-2000 pairs | 2-3 | 2e-4 | 30 |
| 2000+ pairs | 1-2 | 3e-4 | 40+ |

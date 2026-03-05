# VibeLyrics Training Setup Guide

Complete guide for exporting training data, fine-tuning a custom model with Unsloth, converting to GGUF, and loading into LM Studio.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | Must have CUDA support for GPU training |
| CUDA Toolkit | 11.8+ or 12.x | Required for Unsloth |
| LM Studio | Latest | [Download](https://lmstudio.ai/) |
| VRAM | 8 GB+ | 16 GB recommended for 7B models |
| Disk Space | ~30 GB | For base model + fine-tuned output |

---

## Step 1: Export Training Data from VibeLyrics

### Via Training Hub UI

1. Open VibeLyrics and navigate to **AI Learning Center** → **🔬 Training Hub**
2. Click **🔄 Generate Dataset** to build training pairs from all your learned data
3. Review the source breakdown and preview
4. Click **Download** on the **Complete ZIP Bundle** format

### Via API

```bash
# Generate dataset from all sources
curl -X POST http://localhost:8000/api/training/generate

# Download as ZIP
curl http://localhost:8000/api/training/export?format=zip -o training_data.zip

# Or specific formats
curl http://localhost:8000/api/training/export?format=alpaca -o alpaca.json
curl http://localhost:8000/api/training/export?format=jsonl -o conversations.jsonl
curl http://localhost:8000/api/training/export?format=text -o corpus.txt
```

The ZIP includes:
- `alpaca.json` — Instruction-tuning format
- `conversations.jsonl` — ChatML conversational format
- `corpus.txt` — Plain text corpus
- `metadata.json` — Dataset statistics

---

## Step 2: Install Unsloth

```bash
# Create a dedicated venv
python -m venv training_venv
# Windows
training_venv\Scripts\activate
# Linux/Mac
source training_venv/bin/activate

# Install Unsloth (CUDA 12.x)
pip install unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git
pip install xformers trl datasets peft accelerate bitsandbytes

# For CUDA 11.8, use:
# pip install unsloth[cu118] @ git+https://github.com/unslothai/unsloth.git
```

---

## Step 3: Run Fine-Tuning

### Option A: Use the Auto-Generated Script

1. In the Training Hub, go to **🧪 LM Studio** tab
2. Configure hyperparameters (defaults are good to start)
3. Click **🚀 Generate Training Script**
4. Run the generated script:

```bash
cd path/to/VibeLyrics
python data/training/train.py
```

### Option B: Manual Training

```python
from unsloth import FastLanguageModel
from datasets import Dataset
import json

# 1. Load model
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Mistral-7B-Instruct-v0.3-bnb-4bit",
    max_seq_length=512,
    load_in_4bit=True,
)

# 2. Add LoRA
model = FastLanguageModel.get_peft_model(
    model, r=16, lora_alpha=16,
    target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
    lora_dropout=0, bias="none",
    use_gradient_checkpointing="unsloth",
)

# 3. Load your exported data
with open("alpaca.json") as f:
    data = json.load(f)

TEMPLATE = """Below is an instruction that describes a task, paired with an input. Write a response.

### Instruction:
{instruction}

### Input:
{input}

### Response:
{output}"""

def format_sample(s):
    return {"text": TEMPLATE.format(**s) + tokenizer.eos_token}

dataset = Dataset.from_list(data).map(format_sample)

# 4. Train
from trl import SFTTrainer
from transformers import TrainingArguments

SFTTrainer(
    model=model, tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=512,
    args=TrainingArguments(
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        warmup_steps=10,
        num_train_epochs=3,
        learning_rate=2e-4,
        fp16=True, logging_steps=5,
        optim="adamw_8bit",
        output_dir="./output",
    ),
).train()

# 5. Save
model.save_pretrained_merged("./merged_model", tokenizer, save_method="merged_16bit")
model.save_pretrained_gguf("./gguf_model", tokenizer, quantization_method="q4_k_m")
```

---

## Step 4: Load into LM Studio

1. Find the generated `.gguf` file in `data/training/output/` (or your output dir)
2. Copy it to your LM Studio models directory:
   - **Windows:** `C:\Users\<you>\.lmstudio\models\`
   - **Mac:** `~/.lmstudio/models/`
   - **Linux:** `~/.lmstudio/models/`
3. Open LM Studio → **Local Models** → Your model should appear
4. Load it and test with a prompt

---

## Step 5: Configure VibeLyrics

1. In VibeLyrics, go to **Settings**
2. Switch AI Provider to **LM Studio**
3. Ensure LM Studio is running with your fine-tuned model loaded
4. Test by going to a session and requesting a suggestion

---

## Importing External Datasets

You can import additional training data into VibeLyrics:

### Via UI
1. Go to **Training Hub** → **📥 Import**
2. Drag and drop a `.json` (Alpaca) or `.jsonl` (ChatML) file

### Via API
```bash
curl -X POST http://localhost:8000/api/training/import \
  -F "file=@external_dataset.json"
```

Imported data is stored separately in `data/training/imported.json` and merged when generating datasets.

---

## Hyperparameter Guide

| Parameter | Default | Description |
|---|---|---|
| `base_model` | `unsloth/Mistral-7B-Instruct-v0.3-bnb-4bit` | HuggingFace model name |
| `lora_rank` | 16 | LoRA rank (higher = more capacity, more VRAM) |
| `lora_alpha` | 16 | LoRA scaling factor |
| `epochs` | 3 | Training passes over data |
| `learning_rate` | 2e-4 | Learning rate |
| `batch_size` | 4 | Per-device batch size |
| `max_seq_length` | 512 | Maximum token length per sample |
| `quantization` | 4bit | QLoRA quantization level |

### Tips
- **Small dataset (<100 pairs):** Use 5-10 epochs, lr=5e-5
- **Medium dataset (100-1000):** Use 3 epochs, lr=2e-4 (default)
- **Large dataset (1000+):** Use 1-2 epochs, lr=1e-4
- **Overfitting signs:** Loss goes very low → model repeats training data verbatim

---

## Recommended Base Models

| Model | VRAM | Quality | Speed |
|---|---|---|---|
| `unsloth/Mistral-7B-Instruct-v0.3-bnb-4bit` | ~6 GB | ⭐⭐⭐⭐ | Fast |
| `unsloth/Llama-3.1-8B-Instruct-bnb-4bit` | ~6 GB | ⭐⭐⭐⭐⭐ | Fast |
| `unsloth/Qwen2.5-7B-Instruct-bnb-4bit` | ~6 GB | ⭐⭐⭐⭐ | Fast |
| `unsloth/Phi-3.5-mini-instruct-bnb-4bit` | ~4 GB | ⭐⭐⭐ | Very Fast |

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `CUDA out of memory` | Reduce `batch_size` to 2, or `max_seq_length` to 256 |
| `No module named 'unsloth'` | Activate the training venv: `training_venv\Scripts\activate` |
| Model outputs gibberish | More training data needed, or reduce epochs (overfitting) |
| LM Studio doesn't show model | Ensure GGUF is in `~/.lmstudio/models/` and restart LM Studio |
| Training loss doesn't decrease | Increase learning rate or check data quality |
| Empty dataset | Run "Generate Dataset" first — need sessions/lines in VibeLyrics |

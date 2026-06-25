# Spec: Model Fine-Tuning Pipeline

## 🎯 Goal
Train a local Large Language Model (e.g., Mistral-7B-Instruct-v0.3) to act as a custom ghostwriter for VibeLyrics. The model must learn:
1. **Romanized Kannada (Kanglish) vocabulary, stress patterns, and mappings**: Derived from a dictionary PDF.
2. **The user's rap writing style**: Derived from the user's historical writing sessions.
3. **Preference alignment (what NOT to write)**: Derived from rejected AI lines, micro-feedback, and AI Arena votes.

---

## 📦 Existing Resources

### 1. Kannada Dictionary Dataset
*   **Path:** [kannada_dictionary_sft.json](file:///d:/GitHub/VibeLyrics/data/training/kannada_dictionary_sft.json)
*   **Size:** 31,020 instruction-tuning pairs.
*   **Format:** Alpaca instruction-response format:
    ```json
    {
      "instruction": "Define and translate the Romanized Kannada word to English.",
      "input": "Word: pacagavya",
      "output": "The Romanized Kannada word 'pacagavya' means: five things derived from the cow, i.e., milk, curds, ghee, urine and dung [Sk.] (n.) [Category: zoo.]."
    }
    ```
*   **Status:** Already generated and stored.

### 2. User Style SFT & DPO Dataset
*   **Manager:** [TrainingDataGenerator](file:///d:/GitHub/VibeLyrics/backend/services/training_data.py#L607)
*   **SFT Pairs:** Generated from SQLite tables `LyricSession`, `LyricLine`, and `LineVersion`:
    *   `session_lines`: Consecutive lines within a writing session with mood/BPM/theme context.
    *   `line_versions`: Rewrite history of individual lines.
    *   `corrections`: Inline improvements made by the user.
    *   `accepted_suggestions`: Positive ghostwriter suggestions.
    *   `rag_callbacks`: RAG-augmented thematic callback pairs across sessions.
    *   `micro_feedback`: Instructions generated from user complaints (e.g., "make it more aggressive", "too generic").
*   **DPO Pairs:** Preference alignment pairs:
    *   `SuggestionTracker.get_dpo_pairs()`: Rejected AI suggestions paired with the user's manual replacement.
    *   `RLHFTracker.get_dpo_pairs()`: Direct votes from the 4-way AI Arena.
    *   `ConceptEraser.generate_erasure_pairs()`: Synthetic negative pairs constructed around banned words.

### 3. Local Training Management
*   **Manager:** [LMStudioTrainingManager](file:///d:/GitHub/VibeLyrics/backend/services/training_data.py#L1142)
*   **Pipeline Router:** [training.py](file:///d:/GitHub/VibeLyrics/backend/routers/training.py)
*   **Mechanism:** Generates a python fine-tuning script (`data/training/train_{profile}.py`) leveraging `Unsloth` for 4-bit PEFT (LoRA) fine-tuning of `unsloth/Mistral-7B-Instruct-v0.3-bnb-4bit` (or similar base model).

---

## 🛠️ Architecture & Quantization
*   **Quantization:** 4-bit quantization (via `bitsandbytes` + Unsloth) is used to load the base model to allow training on standard consumer GPUs (8-16GB VRAM).
*   **Adapters:** PEFT/LoRA adapters targeting attention and projection layers (`q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`).
*   **Export Format:** LoRA weights are merged back into the base model (16-bit method) and exported as a `.gguf` file using `Q4_K_M` quantization.
*   **Integration:** The generated GGUF model is loaded into LM Studio and queried via the `/v1/chat/completions` API by VibeLyrics.

---

## ⚠️ Constraints & Risks

1. **VRAM Limitation:** Running Unsloth requires a local NVIDIA GPU with at least 8GB-12GB VRAM. If the system does not have this, the training script must be offloaded to a cloud service (e.g., Google Colab) using the exported `.zip` bundle.
2. **Dataset Imbalance:** The Kannada Dictionary dataset contains ~31k pairs, while the user's rap style dataset is likely much smaller (hundreds of lines). Simply training them jointly might drown out the user's style, while training them sequentially can lead to *catastrophic forgetting* of the vocabulary.
3. **Unsloth Installation:** `unsloth` requires specific CUDA/PyTorch versions which can be tricky to compile/install on Windows. The plan must account for this.

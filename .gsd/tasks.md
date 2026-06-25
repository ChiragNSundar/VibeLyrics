# Tasks: Model Fine-Tuning Pipeline

## 📋 Task Checklist

- [ ] **Milestone 1: Environment & Hardware Setup Validation**
  - [ ] **Task 1.1: local GPU check**
    - Run Python script to check CUDA status and VRAM capacity.
    - *Acceptance Criteria:* PyTorch is CUDA-capable, and GPU has 8GB+ VRAM.
  - [ ] **Task 1.2: Unsloth installation**
    - Install `unsloth` globally or in a local virtual environment.
    - *Acceptance Criteria:* `from unsloth import FastLanguageModel` imports without error.
  - [ ] **Task 1.3: Google Colab template preparation**
    - Verify that a cloud-based notebook script is configured to download dataset ZIP and run Unsloth.
    - *Acceptance Criteria:* Colab script runs and loads base model on a free T4 GPU.

- [ ] **Milestone 2: Dataset Preparation**
  - [ ] **Task 2.1: Kannada dictionary dataset verification**
    - Verify the existence and size of `kannada_dictionary_sft.json`.
    - Run script `python scripts/ingest_kannada_dictionary.py` if index is missing.
    - *Acceptance Criteria:* `data/training/kannada_dictionary_sft.json` exists with ~31,000 items.
  - [ ] **Task 2.2: Compile user style datasets**
    - Start VibeLyrics backend server: `python run.py --skip-install`.
    - Send a POST request to `/api/training/generate` to generate the style SFT dataset.
    - *Acceptance Criteria:* `data/training/dataset.json` and `data/training/dpo_dataset.json` are created.
  - [ ] **Task 2.3: Dataset mixing**
    - Merge `kannada_dictionary_sft.json` with user style dataset `dataset.json` at a controlled ratio (e.g. 5:1 dictionary to lyrics ratio, capped at a manageable total token count for rapid fine-tuning).
    - *Acceptance Criteria:* A combined SFT dataset `combined_sft.json` is saved.

- [ ] **Milestone 3: Fine-Tuning Execution**
  - [ ] **Task 3.1: Generate training script**
    - Save or configure `LMStudioTrainingManager` config via POST `/api/training/lmstudio/config` with base model and hyper-parameters.
    - Send POST `/api/training/lmstudio/start` (with `auto_run=False`) to generate `data/training/train_{profile}.py`.
    - *Acceptance Criteria:* `train_{profile}.py` is written to disk.
  - [ ] **Task 3.2: Execute training script**
    - Run the generated training script locally: `python data/training/train_{profile}.py`.
    - *Acceptance Criteria:* The script completes, saving the PEFT/LoRA adapters and the merged 16-bit model in `data/training/output`.
  - [ ] **Task 3.3: GGUF conversion**
    - Verify that Unsloth successfully converts the merged model to GGUF `q4_k_m`.
    - *Acceptance Criteria:* File `data/training/output/vibelyrics-{profile}.gguf` exists.

- [ ] **Milestone 4: Deployment & Integration**
  - [ ] **Task 4.1: Deploy GGUF in LM Studio**
    - Copy the `.gguf` file to LM Studio's model repository (typically `C:\Users\<user>\.cache\lm-studio\models\<publisher>\<model-name>\`).
    - *Acceptance Criteria:* Model appears in LM Studio and can be loaded.
  - [ ] **Task 4.2: Backend provider configuration**
    - Update `VibeLyrics` provider in UI Settings or backend settings to use `lmstudio` with endpoint `http://127.0.0.1:1234/v1`.
    - *Acceptance Criteria:* Connection badge shows active connected status.
  - [ ] **Task 4.3: Ghostwriter capability test**
    - Input a couple of prompt lines using Romanized Kannada vocabulary (e.g., "dobarāṭa") and verify that suggestions align with both Kannada meanings and the user's rap style.
    - *Acceptance Criteria:* Suggested lines rhyme, maintain the correct cadence, and make sense.

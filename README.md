# AI-Driven Autonomous Memory Leak Detection Utility

An autonomous, local AI tool designed to detect memory leaks and dangling pointers in game engine environments using semantic event lifecycle analysis.

## Overview
In large-scale game engines (AAA environments), manual memory profiling is heavily time-consuming. This utility leverages a fine-tuned Large Language Model (Llama 3 / DeepSeek Coder via Unsloth) to autonomously analyze C++ allocation/destruction logs and identify orphaned objects (where the parent is destroyed, but the child memory is not freed).

## Architecture
1. **Synthetic Data Generator (`dataset_generator.py`)**: Simulates a game engine's tick system and object hierarchy (Parent-Child). Injects intentional dangling pointer scenarios to create a high-quality training dataset (`.jsonl`).
2. **LoRA Fine-Tuning (`training_notebook.ipynb`)**: Uses `Unsloth` to fine-tune a 4-bit quantized LLM specifically for memory leak detection, saving VRAM and drastically reducing training time.
3. **Local Inference (`Modelfile`)**: Packages the fine-tuned model into GGUF format and runs it locally via `Ollama` for zero-latency, offline, and private analysis.

## Repository Structure
* `dataset_generator.py` - Python script to generate synthetic allocation logs.
* `Modelfile` - Ollama configuration file containing the system template and prompts.
* `training_notebook.ipynb` - The notebook used for Unsloth fine-tuning.

*(Note: The trained `.gguf` weights and raw `.jsonl` datasets are excluded from this repository due to size limits. You can generate your own using the scripts provided).*

## Installation & Usage

### 1. Generate Data (Optional)
Run the generator to create synthetic memory logs:
```bash
python dataset_generator.py
```

### 2. Run Inference with Ollama
Make sure you have [Ollama](https://ollama.com/) installed on your machine.
Place your `.gguf` model file in the same directory as the `Modelfile`.

Build the local model:
```bash
ollama create memory_profiler -f Modelfile
```

Run the model:
```bash
ollama run memory_profiler
```

## Example Analysis
**Input Log:**
```json
{"tick": 1, "action": "ALLOCATE", "entity_id": "player_01", "type": "Actor"}
{"tick": 2, "action": "ALLOCATE", "entity_id": "weapon_01", "type": "Weapon", "parent_id": "player_01"}
{"tick": 100, "action": "DESTROY", "entity_id": "player_01"}
{"tick": 101, "action": "FREE_MEMORY", "entity_id": "player_01"}
```

**Output:**
```
Memory leak detected. Orphaned entities: [weapon_01]
```

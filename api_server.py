import os
import sys
import json
import time
import uuid
import asyncio
import threading
from typing import List, Optional, Dict, Any

import torch
import torch.distributed as dist
from transformers import AutoTokenizer
from safetensors.torch import load_model

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(current_dir, "../encoding")))

from model import Transformer, ModelArgs
from generate import generate
from encoding import encode_messages

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="DeepSeek-V4.1-Flash OpenAI Compatible API")

# Shared queue for Rank 0
request_queue = None
MODEL_NAME = "deepseek-ai/DeepSeek-V4.1-Flash"

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = MODEL_NAME
    messages: List[Message]
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.6
    thinking_mode: Optional[str] = "chat"

@app.get("/health")
def health():
    return {"status": "healthy", "model": MODEL_NAME}

@app.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL_NAME,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "deepseek",
            },
            {
                "id": "deepseek-v4.1-flash",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "deepseek",
            }
        ]
    }

@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    
    payload = {
        "messages": [m.dict() for m in req.messages],
        "max_tokens": req.max_tokens or 512,
        "temperature": req.temperature or 0.6,
        "thinking_mode": req.thinking_mode or "chat",
        "future": future,
        "loop": loop,
    }
    
    request_queue.put(payload)
    
    try:
        response_text, prompt_len, completion_len = await asyncio.wait_for(future, timeout=300.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Inference timed out")
        
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created_time = int(time.time())
    
    return {
        "id": completion_id,
        "object": "chat.completion",
        "created": created_time,
        "model": req.model or MODEL_NAME,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text,
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": prompt_len,
            "completion_tokens": completion_len,
            "total_tokens": prompt_len + completion_len
        }
    }

def main():
    global request_queue
    world_size = int(os.getenv("WORLD_SIZE", "1"))
    rank = int(os.getenv("RANK", "0"))
    local_rank = int(os.getenv("LOCAL_RANK", "0"))

    if world_size > 1:
        dist.init_process_group("nccl")

    torch.cuda.set_device(local_rank)
    torch.set_default_dtype(torch.bfloat16)
    torch.set_num_threads(8)

    ckpt_path = "/data/models/deepseek-v4.1-flash-tp8"
    config_path = os.path.join(current_dir, "config.json")

    with open(config_path) as f:
        args = ModelArgs(**json.load(f))
    args.max_batch_size = 1
    args.max_seq_len = 64 * 1024

    if rank == 0:
        print(f"Loading tokenizer from {ckpt_path}...")
    tokenizer = AutoTokenizer.from_pretrained(ckpt_path)

    if rank == 0:
        print("Building model...")
    with torch.device("cuda"):
        model = Transformer(args, tokenizer)

    if rank == 0:
        print(f"Loading weights rank {rank}...")
    load_model(model, os.path.join(ckpt_path, f"model{rank}-mp{world_size}.safetensors"))
    torch.set_default_device("cuda")

    if rank == 0:
        print("Model loaded successfully across all ranks!")
        import queue
        request_queue = queue.Queue()

        # Start FastAPI in a background daemon thread
        def run_uvicorn():
            uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

        server_thread = threading.Thread(target=run_uvicorn, daemon=True)
        server_thread.start()
        print("OpenAI-compatible API server started on http://0.0.0.0:8000")

    # Main inference loop across all ranks
    while True:
        if rank == 0:
            item = request_queue.get()
            msgs = item["messages"]
            thinking_mode = item["thinking_mode"]
            max_new_tokens = item["max_tokens"]
            
            prompt_str = encode_messages(msgs, thinking_mode=thinking_mode)
            prompt_tokens = tokenizer.encode(prompt_str)
            
            broadcast_data = [prompt_tokens, max_new_tokens]
            if world_size > 1:
                dist.broadcast_object_list(broadcast_data, src=0)
        else:
            broadcast_data = [None, None]
            dist.broadcast_object_list(broadcast_data, src=0)
            prompt_tokens, max_new_tokens = broadcast_data

        completion_tokens = generate(model, [prompt_tokens], max_new_tokens, tokenizer.eos_token_id)

        if rank == 0:
            completion_text = tokenizer.decode(completion_tokens[0])
            prompt_len = len(prompt_tokens)
            comp_len = len(completion_tokens[0])
            
            loop = item["loop"]
            future = item["future"]
            loop.call_soon_threadsafe(future.set_result, (completion_text, prompt_len, comp_len))

if __name__ == "__main__":
    main()

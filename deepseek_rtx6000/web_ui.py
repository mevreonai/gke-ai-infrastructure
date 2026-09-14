#!/usr/bin/env python3
"""
Gradio Chat Web UI for DeepSeek-V4.1-Flash with Live 8x RTX 6000 Telemetry.

This interface connects directly to:
1. vLLM OpenAI-compatible API at http://localhost:8000/v1 for streaming chat.
2. NVIDIA DCGM Exporter / Prometheus at http://localhost:9400 or :9090 for GPU telemetry.
"""

import os
import sys
import time
import requests
import gradio as gr
from openai import OpenAI

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------
VLLM_API_BASE = os.getenv("VLLM_API_BASE", "http://localhost:8000/v1")
DCGM_METRICS_URL = os.getenv("DCGM_METRICS_URL", "http://localhost:9400/metrics")
MODEL_NAME = os.getenv("MODEL_NAME", "deepseek-ai/DeepSeek-V4.1-Flash")
PORT = int(os.getenv("GRADIO_PORT", "7860"))

# Initialize OpenAI client pointing to the local vLLM server
client = OpenAI(
    base_url=VLLM_API_BASE,
    api_key="none",  # vLLM does not require an API key by default
)


def fetch_gpu_telemetry():
    """
    Scrapes DCGM Prometheus metrics to extract real-time VRAM and utilization
    for all 8 NVIDIA RTX Pro 6000 GPUs.
    """
    gpu_stats = {}
    try:
        resp = requests.get(DCGM_METRICS_URL, timeout=1.5)
        if resp.status_code == 200:
            for line in resp.text.splitlines():
                if line.startswith("#"):
                    continue
                # Parse DCGM_FI_DEV_FB_USED (VRAM used in MB)
                if "DCGM_FI_DEV_FB_USED{" in line:
                    gpu_id = line.split('gpu="')[1].split('"')[0]
                    used_mb = float(line.split()[-1])
                    gpu_stats.setdefault(gpu_id, {})["used_gb"] = round(used_mb / 1024, 1)

                # Parse DCGM_FI_DEV_GPU_UTIL (GPU core utilization %)
                if "DCGM_FI_DEV_GPU_UTIL{" in line:
                    gpu_id = line.split('gpu="')[1].split('"')[0]
                    util_pct = float(line.split()[-1])
                    gpu_stats.setdefault(gpu_id, {})["util_pct"] = int(util_pct)
    except Exception:
        pass

    # Build human-readable markdown table
    if not gpu_stats:
        return "⚠️ *Waiting for DCGM exporter on port 9400...*"

    lines = [
        "| GPU # | Model | VRAM Allocated | Total Capacity | VRAM % | Compute Util |",
        "| :---: | :---: | :---: | :---: | :---: | :---: |"
    ]
    for gpu_id in sorted(gpu_stats.keys(), key=lambda x: int(x) if x.isdigit() else 0):
        data = gpu_stats[gpu_id]
        used = data.get("used_gb", 0.0)
        total = 96.0  # RTX 6000 96GB VRAM
        pct = round((used / total) * 100, 1)
        compute = data.get("util_pct", 0)
        lines.append(f"| **GPU {gpu_id}** | RTX 6000 | {used:.1f} GB | 96.0 GB | **{pct}%** | {compute}% |")

    return "\n".join(lines)


def chat_stream(message, history, system_prompt, temperature, max_tokens):
    """
    Streams tokens from the local vLLM server with live latency and speed tracking.
    """
    if not message.strip():
        return

    # Build chat history
    messages = [{"role": "system", "content": system_prompt}]
    for user_msg, assistant_msg in history:
        messages.append({"role": "user", "content": user_msg})
        if assistant_msg:
            messages.append({"role": "assistant", "content": assistant_msg})
    messages.append({"role": "user", "content": message})

    start_time = time.time()
    first_token_time = None
    token_count = 0
    full_response = ""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content or ""
            if delta:
                if first_token_time is None:
                    first_token_time = time.time()
                token_count += 1
                full_response += delta
                yield full_response

        # Calculate performance stats
        total_time = time.time() - start_time
        ttft = (first_token_time - start_time) if first_token_time else 0.0
        tps = (token_count / (total_time - ttft)) if (total_time - ttft) > 0 else 0.0

        # Append performance footer
        footer = f"\n\n---\n*⚡ {token_count} tokens in {total_time:.2f}s | TTFT: {ttft*1000:.0f}ms | Speed: {tps:.1f} tok/s | 8x RTX 6000 (TP=8)*"
        yield full_response + footer

    except Exception as e:
        yield f"❌ **Error connecting to vLLM on port 8000:**\n```\n{str(e)}\n```\n*Ensure the vLLM container is running and finished loading weights.*"


# ------------------------------------------------------------------------------
# Gradio UI Layout
# ------------------------------------------------------------------------------
custom_theme = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="slate",
    neutral_hue="slate",
)

with gr.Blocks(title="DeepSeek-V4.1-Flash (8x RTX 6000)", theme=custom_theme) as demo:
    gr.Markdown(
        """
        # 🚀 DeepSeek-V4.1-Flash (FP8) on 8× NVIDIA RTX Pro 6000
        ### **Tensor Parallelism: 8** | **Total VRAM: 768 GB** | **Storage: 1,000 GB NVMe Disk**
        """
    )

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(height=520, show_copy_button=True)
            with gr.Row():
                msg_input = gr.Textbox(
                    placeholder="Enter your prompt here (e.g., 'Write a high-performance CUDA kernel for matrix multiplication')...",
                    show_label=False,
                    scale=8,
                )
                submit_btn = gr.Button("Send", variant="primary", scale=1)
                clear_btn = gr.Button("Clear", scale=1)

        with gr.Column(scale=2):
            gr.Markdown("### 📊 Real-Time Hardware Telemetry")
            telemetry_box = gr.Markdown(fetch_gpu_telemetry)
            refresh_btn = gr.Button("🔄 Refresh GPU Stats", size="sm")

            with gr.Accordion("⚙️ Inference Parameters", open=False):
                system_prompt = gr.Textbox(
                    label="System Prompt",
                    value="You are DeepSeek-V4.1-Flash, an advanced AI reasoning assistant running locally with Tensor Parallelism 8.",
                    lines=3,
                )
                temperature = gr.Slider(
                    label="Temperature", minimum=0.0, maximum=1.0, value=0.3, step=0.05
                )
                max_tokens = gr.Slider(
                    label="Max Output Tokens", minimum=128, maximum=8192, value=2048, step=128
                )

    # Event handlers
    def user_turn(user_msg, history):
        return "", history + [[user_msg, ""]]

    submit_btn.click(
        user_turn, [msg_input, chatbot], [msg_input, chatbot]
    ).then(
        chat_stream, [msg_input, chatbot, system_prompt, temperature, max_tokens], chatbot
    ).then(
        fetch_gpu_telemetry, None, telemetry_box
    )

    msg_input.submit(
        user_turn, [msg_input, chatbot], [msg_input, chatbot]
    ).then(
        chat_stream, [msg_input, chatbot, system_prompt, temperature, max_tokens], chatbot
    ).then(
        fetch_gpu_telemetry, None, telemetry_box
    )

    clear_btn.click(lambda: None, None, chatbot)
    refresh_btn.click(fetch_gpu_telemetry, None, telemetry_box)

if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=PORT, share=False)

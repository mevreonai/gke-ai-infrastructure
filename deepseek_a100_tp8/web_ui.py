import argparse
import json
import time
import requests
import gradio as gr

parser = argparse.ArgumentParser(description="DeepSeek-V4.1-Flash (TP=8) Gradio Web UI")
parser.add_argument("--host", default="localhost", help="vLLM host IP or domain")
parser.add_argument("--port", type=int, default=8000, help="vLLM API port")
parser.add_argument("--listen-port", type=int, default=7860, help="Gradio listen port")
parser.add_argument("--share", action="store_true", help="Create a public Gradio link")
args, _ = parser.parse_known_args()

DEFAULT_BASE_URL = f"http://{args.host}:{args.port}"
MODEL_ID = "/models/deepseek-ai/DeepSeek-V4.1-Flash"

def parse_prometheus_metrics(raw_text):
    metrics = {}
    for line in raw_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            key, val = parts[0], parts[1]
            try:
                metrics[key] = float(val)
            except ValueError:
                metrics[key] = val
    return metrics

def fetch_metrics(endpoint_url):
    try:
        resp = requests.get(f"{endpoint_url}/metrics", timeout=3)
        if resp.status_code == 200:
            parsed = parse_prometheus_metrics(resp.text)
            cache_usage = parsed.get("vllm:gpu_cache_usage_factor", 0.0) * 100
            running_reqs = int(parsed.get("vllm:num_requests_running", 0))
            waiting_reqs = int(parsed.get("vllm:num_requests_waiting", 0))
            prompt_tokens = int(parsed.get("vllm:num_prompt_tokens_total", 0))
            gen_tokens = int(parsed.get("vllm:num_generation_tokens_total", 0))

            summary = (
                f"### 📊 Live Prometheus Metrics\n\n"
                f"- **KV Cache Usage:** `{cache_usage:.1f}%`\n"
                f"- **Running Requests:** `{running_reqs}`\n"
                f"- **Waiting Queue:** `{waiting_reqs}`\n"
                f"- **Total Prompt Tokens:** `{prompt_tokens:,}`\n"
                f"- **Total Gen Tokens:** `{gen_tokens:,}`\n"
                f"- **Status:** 🟢 **Engine Healthy (TP=8)**\n"
            )
            return summary
    except Exception as e:
        return f"### 📊 Live Prometheus Metrics\n\n- **Status:** 🔴 Disconnected ({e})\n"
    return "### 📊 Live Prometheus Metrics\n\n- **Status:** ⚪ Awaiting data\n"

def chat_stream(message, history, endpoint_url, temperature, max_tokens):
    if not message.strip():
        yield "Please enter a valid message."
        return

    messages = [{"role": "system", "content": "You are DeepSeek-V4.1-Flash, an advanced AI model running on 8x NVIDIA A100 GPUs with Tensor Parallelism 8."}]
    for user_msg, bot_msg in history:
        if user_msg:
            messages.append({"role": "user", "content": str(user_msg)})
        if bot_msg:
            messages.append({"role": "assistant", "content": str(bot_msg)})
    messages.append({"role": "user", "content": message})

    payload = {
        "model": MODEL_ID,
        "messages": messages,
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
        "stream": True
    }

    url = f"{endpoint_url}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}

    start_time = time.time()
    generated_text = ""

    try:
        response = requests.post(url, headers=headers, json=payload, stream=True, timeout=60)
        response.raise_for_status()

        for chunk in response.iter_lines():
            if not chunk:
                continue
            line = chunk.decode("utf-8")
            if line.startswith("data: "):
                data_str = line[6:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    delta = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if delta:
                        generated_text += delta
                        yield generated_text
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        yield f"⚠️ Inference Error connecting to `{url}`: {str(e)}"

with gr.Blocks(title="DeepSeek-V4.1-Flash (8x A100 TP=8)") as demo:
    gr.Markdown(
        """
        # 🚀 DeepSeek-V4.1-Flash (Native FP8)
        ### 8× NVIDIA A100 (80GB) SXM4 | Tensor Parallelism 8 | 640 GB VRAM Cluster
        """
    )

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(height=520, label="DeepSeek-V4.1-Flash Chat")
            msg = gr.Textbox(placeholder="Ask DeepSeek anything...", label="User Prompt", lines=2)
            with gr.Row():
                submit_btn = gr.Button("Send Prompt", variant="primary")
                clear_btn = gr.ClearButton([msg, chatbot], value="Clear Conversation")

        with gr.Column(scale=1):
            gr.Markdown("### ⚙️ Cluster Configuration")
            endpoint_input = gr.Textbox(value=DEFAULT_BASE_URL, label="vLLM Base URL", interactive=True)
            temp_slider = gr.Slider(minimum=0.0, maximum=1.0, value=0.3, step=0.05, label="Temperature")
            tokens_slider = gr.Slider(minimum=64, maximum=4096, value=512, step=64, label="Max Tokens")

            metrics_box = gr.Markdown(value="### 📊 Live Prometheus Metrics\n\n- Click **Refresh Metrics** to load cluster telemetry.")
            refresh_btn = gr.Button("🔄 Refresh Metrics", size="sm")
            refresh_btn.click(fn=fetch_metrics, inputs=[endpoint_input], outputs=[metrics_box])

    def user_turn(user_message, history):
        return "", history + [[user_message, None]]

    def bot_turn(history, endpoint_url, temperature, max_tokens):
        user_message = history[-1][0]
        bot_message = ""
        for partial in chat_stream(user_message, history[:-1], endpoint_url, temperature, max_tokens):
            history[-1][1] = partial
            yield history

    submit_btn.click(
        fn=user_turn,
        inputs=[msg, chatbot],
        outputs=[msg, chatbot],
        queue=False
    ).then(
        fn=bot_turn,
        inputs=[chatbot, endpoint_input, temp_slider, tokens_slider],
        outputs=[chatbot]
    ).then(
        fn=fetch_metrics,
        inputs=[endpoint_input],
        outputs=[metrics_box]
    )

    msg.submit(
        fn=user_turn,
        inputs=[msg, chatbot],
        outputs=[msg, chatbot],
        queue=False
    ).then(
        fn=bot_turn,
        inputs=[chatbot, endpoint_input, temp_slider, tokens_slider],
        outputs=[chatbot]
    ).then(
        fn=fetch_metrics,
        inputs=[endpoint_input],
        outputs=[metrics_box]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=args.listen_port, share=args.share, theme=gr.themes.Soft(primary_hue="cyan"))


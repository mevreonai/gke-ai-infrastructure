"""
Interactive Gradio Web UI for Multi-Host TPU LLM Demo
Allows demonstrating live streaming chat, real-time latency metrics,
and multi-host TPU architecture details to executive leadership / stakeholders.
"""
import time
import requests
import json
import gradio as gr

DEFAULT_API_URL = "http://localhost:8000/v1"

def check_endpoint_status(api_url):
    try:
        r = requests.get(f"{api_url.rstrip('/')}/models", timeout=3)
        if r.status_code == 200:
            models = [m.get("id") for m in r.json().get("data", [])]
            return f"🟢 Connected | Available Models: {', '.join(models)}"
        return f"🟡 Responded with status {r.status_code}"
    except Exception as e:
        return f"🔴 Disconnected ({str(e)})"

def stream_chat(message, history, system_prompt, temperature, max_tokens, api_url, model_name):
    if not message.strip():
        yield history, "0.0s", "0.0 t/s"
        return

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    for user_msg, bot_msg in history:
        messages.append({"role": "user", "content": user_msg})
        if bot_msg:
            messages.append({"role": "assistant", "content": bot_msg})
            
    messages.append({"role": "user", "content": message})

    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
        "stream": True
    }

    start_time = time.time()
    token_count = 0
    accumulated_text = ""
    history = history + [[message, ""]]

    try:
        response = requests.post(
            f"{api_url.rstrip('/')}/chat/completions",
            json=payload,
            stream=True,
            timeout=60
        )
        
        if response.status_code != 200:
            history[-1][1] = f"Error ({response.status_code}): {response.text}"
            yield history, "Error", "0.0 t/s"
            return

        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("data: "):
                    data_str = decoded[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0]["delta"].get("content", "")
                        if delta:
                            accumulated_text += delta
                            token_count += 1
                            elapsed = time.time() - start_time
                            tps = token_count / elapsed if elapsed > 0 else 0
                            history[-1][1] = accumulated_text
                            yield history, f"{elapsed:.2f}s", f"{tps:.1f} tokens/s"
                    except Exception:
                        continue

        elapsed = time.time() - start_time
        tps = token_count / elapsed if elapsed > 0 else 0
        yield history, f"{elapsed:.2f}s", f"{tps:.1f} tokens/s"

    except Exception as e:
        history[-1][1] = f"Connection Failed: {str(e)}"
        yield history, "Failed", "0.0 t/s"

# Gradio Custom Theme and Layout
custom_css = """
#header {text-align: center; margin-bottom: 20px;}
.metric-box {background: #1e293b; border-radius: 8px; padding: 12px; border: 1px solid #334155;}
"""

with gr.Blocks(title="Google Cloud Multi-Host TPU LLM Demo", css=custom_css, theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🚀 Google Cloud Multi-Host TPU LLM Inference Demo
        ### GKE + KubeRay + vLLM on Cloud TPU v5e (Multi-Host Slice: 2 Hosts x 4 Chips = 8 TPUs)
        """
    )
    
    with gr.Row():
        with gr.Column(scale=3):
            status_box = gr.Textbox(
                label="TPU Service Health Status",
                value=check_endpoint_status(DEFAULT_API_URL),
                interactive=False
            )
        with gr.Column(scale=1):
            refresh_btn = gr.Button("🔄 Refresh Status", variant="secondary")

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(label="Chat with Multi-Host TPU Model", height=450, show_copy_button=True)
            msg = gr.Textbox(
                placeholder="Ask anything (e.g. 'Explain how Multi-Host TPU Inter-Chip Interconnect enables ultra-fast distributed LLM inference')...",
                label="Your Prompt",
                lines=2
            )
            with gr.Row():
                submit_btn = gr.Button("🚀 Send Request", variant="primary")
                clear_btn = gr.Button("🗑️ Clear Chat")

        with gr.Column(scale=1):
            gr.Markdown("### 📊 Performance Telemetry")
            latency_stat = gr.Textbox(label="Latency", value="0.0s", interactive=False)
            throughput_stat = gr.Textbox(label="Generation Throughput", value="0.0 tokens/s", interactive=False)
            
            gr.Markdown("### ⚙️ Serving Parameters")
            api_url = gr.Textbox(label="Ray Serve Base URL", value=DEFAULT_API_URL)
            model_name = gr.Textbox(label="Model ID", value="google/gemma-2-27b-it")
            temperature = gr.Slider(0.0, 1.0, value=0.7, step=0.1, label="Temperature")
            max_tokens = gr.Slider(64, 2048, value=512, step=64, label="Max Generation Tokens")
            system_prompt = gr.Textbox(
                label="System Prompt",
                value="You are an expert AI running on Google Cloud TPU multi-host infrastructure.",
                lines=2
            )
            
            gr.Markdown(
                """
                ### 🏗️ Architecture Stack
                - **Hardware**: Cloud TPU v5e (`2x2x1` topology)
                - **Hosts**: 2x `ct5lp-hightpu-4t` nodes (8 chips)
                - **Network**: TPU ICI (Inter-Chip Interconnect) + DRA
                - **Orchestration**: GKE + KubeRay (`RayService`)
                - **Engine**: vLLM with Pallas / XLA Compiler
                """
            )

    refresh_btn.click(fn=check_endpoint_status, inputs=[api_url], outputs=[status_box])
    submit_btn.click(
        fn=stream_chat,
        inputs=[msg, chatbot, system_prompt, temperature, max_tokens, api_url, model_name],
        outputs=[chatbot, latency_stat, throughput_stat]
    )
    msg.submit(
        fn=stream_chat,
        inputs=[msg, chatbot, system_prompt, temperature, max_tokens, api_url, model_name],
        outputs=[chatbot, latency_stat, throughput_stat]
    )
    clear_btn.click(lambda: [], None, chatbot, queue=False)

if __name__ == "__main__":
    print("Launching Multi-Host TPU Gradio Demo UI on http://localhost:7860...")
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)

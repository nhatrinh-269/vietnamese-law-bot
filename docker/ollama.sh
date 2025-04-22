#!/bin/bash

# Start Ollama in the background.
/bin/ollama serve &
# Record Process ID.
pid=$!

# Pause for Ollama to start.
sleep 5

# Download models here.
echo "🔴 Retrieve Qwen2.5 model..."
ollama pull qwen2.5:latest

echo "🟢 Done!"

# Wait for Ollama process to finish.
wait $pid

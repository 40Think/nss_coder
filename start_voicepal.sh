#!/bin/bash
# start_voicepal.sh - Launch VoicePal v2 with correct CUDA paths
#
# ===============================================================================
# ВАЖНО / IMPORTANT:
# Этот скрипт требует venv с faster-whisper и CUDA зависимостями.
# Эта venv НЕ включена в репозиторий, так как зависит от железа.
# 
# AI-агент должен:
# 1. Определить GPU и версию CUDA на целевой машине
# 2. Создать venv: python3 -m venv venv
# 3. Установить faster-whisper с правильными CUDA библиотеками
# 4. Проверить что LD_LIBRARY_PATH корректно настроен
#
# This script requires a venv with faster-whisper and CUDA dependencies.
# This venv is NOT included in the repository as it's hardware-specific.
#
# The AI agent must:
# 1. Detect GPU and CUDA version on target machine
# 2. Create venv: python3 -m venv venv
# 3. Install faster-whisper with correct CUDA libraries
# 4. Verify LD_LIBRARY_PATH is correctly configured
# ===============================================================================

# Ensure we are in the script's directory
cd "$(dirname "$0")"

# Activate venv if it exists
if [ -d "../venv" ]; then
    echo "Activating venv..."
    source ../venv/bin/activate
elif [ -d "venv" ]; then
    echo "Activating venv..."
    source venv/bin/activate
fi

# Find CUDA libraries in venv
echo "Configuring CUDA paths..."
SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])" 2>/dev/null || echo "./venv/lib/python3.12/site-packages")
CUDNN_PATH="$SITE_PACKAGES/nvidia/cudnn/lib"
CUBLAS_PATH="$SITE_PACKAGES/nvidia/cublas/lib"

if [ -d "$CUDNN_PATH" ]; then
    export LD_LIBRARY_PATH="$CUDNN_PATH:$CUBLAS_PATH:$LD_LIBRARY_PATH"
    echo "LD_LIBRARY_PATH set to include $CUDNN_PATH"
else
    echo "WARNING: Could not find nvidia/cudnn/lib in $SITE_PACKAGES"
    # Fallback search
    export CUDNN_PATH=$(dirname $(find . -name "libcudnn_ops.so.9" | head -n 1))
    export CUBLAS_PATH=$(dirname $(find . -name "libcublas.so.12" | head -n 1))
    export LD_LIBRARY_PATH="$CUDNN_PATH:$CUBLAS_PATH:$LD_LIBRARY_PATH"
fi

# Kill existing instance
pkill -f voice_server.py

# Start Server
echo "Starting Voice Server on port 5000..."
python3 automation/voice_server.py

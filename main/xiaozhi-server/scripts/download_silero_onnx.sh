#!/bin/bash
# 下载 Silero VAD ONNX 模型
# 用于替代 PyTorch 版本，减少 Docker 镜像约 2GB

MODEL_DIR="models"
# HuggingFace 镜像（GitHub 链接已失效）
MODEL_URL="https://huggingface.co/deepghs/silero-vad-onnx/resolve/main/silero_vad.onnx"
MODEL_PATH="${MODEL_DIR}/silero_vad.onnx"

# 创建目录
mkdir -p ${MODEL_DIR}

echo "正在下载 Silero VAD ONNX 模型..."
echo "URL: ${MODEL_URL}"
echo "保存到: ${MODEL_PATH}"

# 下载模型
if command -v wget &> /dev/null; then
    wget -O ${MODEL_PATH} ${MODEL_URL}
elif command -v curl &> /dev/null; then
    curl -L -o ${MODEL_PATH} ${MODEL_URL}
else
    echo "错误: 需要安装 wget 或 curl"
    exit 1
fi

# 验证下载
if [ -f ${MODEL_PATH} ]; then
    SIZE=$(ls -lh ${MODEL_PATH} | awk '{print $5}')
    echo ""
    echo "✅ 下载完成!"
    echo "   模型路径: ${MODEL_PATH}"
    echo "   模型大小: ${SIZE}"
    echo ""
    echo "使用方法:"
    echo "1. 修改 config.yaml 中的 selected_module.VAD 为 SileroONNX"
    echo "2. 安装依赖: pip install onnxruntime (或 onnxruntime-cpu)"
    echo "3. 移除 PyTorch: pip uninstall torch torchaudio torchvision"
else
    echo "❌ 下载失败"
    exit 1
fi

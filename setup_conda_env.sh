#!/bin/bash

# 현재 디렉토리 이름을 환경 이름으로 사용
ENV_NAME=$(basename "$PWD")

# Conda 환경 생성
echo "Creating Conda environment: $ENV_NAME"
conda create --name "$ENV_NAME" python=3.8 -y

# Conda 환경 활성화
echo "Activating Conda environment: $ENV_NAME"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"

# requirements.txt 파일 확인 및 설치
if [ -f "requirements.txt" ]; then
    echo "Installing packages from requirements.txt"
    pip install -r requirements.txt
else
    echo "requirements.txt not found in the current directory."
fi

echo "Setup complete. Activated conda environment: $ENV_NAME"
echo "You can now run your Python scripts in this environment."
echo "To activate this environment in the future, use:"
echo "conda activate $ENV_NAME"
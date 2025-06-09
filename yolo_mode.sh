#!/bin/bash

# 고정된 파일 이름
file_name="config.py"

# 임시 파일을 생성합니다.
temp_file=$(mktemp)

# 파일에서 MODE = 줄을 지우고, 임시 파일에 저장합니다.
grep -v "^MODE =" "$file_name" > "$temp_file"

# 새 MODE = "chromadb" 줄을 임시 파일의 끝에 추가합니다.
echo 'MODE = "yolo"' >> "$temp_file"

# 임시 파일을 원래 파일로 덮어씁니다.
mv "$temp_file" "$file_name"

echo "mode : yolo"

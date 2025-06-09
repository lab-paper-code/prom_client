#!/bin/bash

# 저장소 URL
repo_url="https://github.com/jangscon/prom_client.git"

# 현재 디렉토리 경로 저장
current_dir=$(pwd)

# 임시 디렉토리 생성
temp_dir=$(mktemp -d)

# 저장소를 임시 디렉토리로 클론
git clone "$repo_url" "$temp_dir"

# 현재 디렉토리의 config.py와 scp_config.py 파일을 임시 디렉토리로 이동
mv "$current_dir/config.py" "$temp_dir"
mv "$current_dir/scp_config.py" "$temp_dir"

# 현재 디렉토리의 내용물을 삭제
rm -rf "$current_dir"/*

# 임시 디렉토리의 내용물을 현재 디렉토리로 이동
mv "$temp_dir"/* "$current_dir"

# 임시 디렉토리 삭제
rm -rf "$temp_dir"

echo "repository updated"

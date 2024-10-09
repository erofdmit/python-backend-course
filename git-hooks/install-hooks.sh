#!/bin/bash

COMMIT_MSG_HOOK_PATH="git-hooks/commit-msg"
PRE_RECEIVE_HOOK_PATH="git-hooks/pre-receive"

mkdir -p .git/hooks

cp "$COMMIT_MSG_HOOK_PATH" .git/hooks/commit-msg
cp "$PRE_RECEIVE_HOOK_PATH" .git/hooks/pre-receive

# Установка прав на выполнение для pre-commit хука
chmod +x .git/hooks/commit-msg
chmod +x .git/hooks/pre-receive

echo "git hooks установлены успешно!"
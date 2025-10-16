#!/usr/bin/env bash
set -euo pipefail

REPO_URL=${OPENWEBUI_REPO_URL:-https://github.com/open-webui/open-webui.git}
BRANCH=${OPENWEBUI_BRANCH:-main}
TARGET_DIR=${OPENWEBUI_DIR:-open-webui}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "${script_dir}/.." && pwd)"
cd "${project_root}"

if [[ -d "${TARGET_DIR}/.git" ]]; then
  echo "[openwebui] Repo exists at '${TARGET_DIR}' - updating..."
  git -C "${TARGET_DIR}" fetch --all --tags
  git -C "${TARGET_DIR}" checkout "${BRANCH}"
  git -C "${TARGET_DIR}" pull --ff-only origin "${BRANCH}" || true
  git -C "${TARGET_DIR}" submodule update --init --recursive || true
else
  echo "[openwebui] Cloning '${REPO_URL}' (branch: ${BRANCH}) into '${TARGET_DIR}' ..."
  git clone --depth 1 --branch "${BRANCH}" "${REPO_URL}" "${TARGET_DIR}"
  git -C "${TARGET_DIR}" submodule update --init --recursive || true
fi

echo "[openwebui] Current HEAD:"
GIT_PAGER=cat git -C "${TARGET_DIR}" log -1 --oneline || true

echo "[openwebui] Done. You can now run 'make up' to build and start."

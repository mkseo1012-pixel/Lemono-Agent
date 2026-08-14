#!/usr/bin/env bash
set -Eeuo pipefail

REPOSITORY_URL="${LEMONO_REPOSITORY_URL:-https://github.com/mkseo1012-pixel/Lemono-Agent.git}"
INSTALL_ROOT="${LEMONO_INSTALL_DIR:-${HOME}/.local/share/lemono-agent}"
BIN_DIR="${LEMONO_BIN_DIR:-${HOME}/.local/bin}"
REF="${LEMONO_REF:-main}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

fail() {
  printf 'Lemono install error: %s\n' "$1" >&2
  exit 1
}

command -v git >/dev/null 2>&1 || fail "git is required"
command -v "${PYTHON_BIN}" >/dev/null 2>&1 || fail "Python 3.11+ is required"
"${PYTHON_BIN}" - <<'PY' || fail "Python 3.11+ is required"
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY

umask 077
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf -- "${TEMP_DIR}"' EXIT

printf 'Downloading Lemono Agent (%s)...\n' "${REF}"
git init --quiet "${TEMP_DIR}/source"
git -C "${TEMP_DIR}/source" remote add origin "${REPOSITORY_URL}"
git -C "${TEMP_DIR}/source" fetch --quiet --depth 1 origin "${REF}"
git -C "${TEMP_DIR}/source" checkout --quiet --detach FETCH_HEAD
COMMIT="$({ git -C "${TEMP_DIR}/source" rev-parse HEAD; } 2>/dev/null)"
[[ "${COMMIT}" =~ ^[0-9a-f]{40}$ ]] || fail "could not verify downloaded revision"

RELEASE_DIR="${INSTALL_ROOT}/releases/${COMMIT}"
mkdir -p -- "${INSTALL_ROOT}/releases" "${BIN_DIR}"
if [[ ! -d "${RELEASE_DIR}" ]]; then
  mv -- "${TEMP_DIR}/source" "${RELEASE_DIR}"
fi

if [[ ! -x "${RELEASE_DIR}/.venv/bin/python" ]]; then
  "${PYTHON_BIN}" -m venv "${RELEASE_DIR}/.venv"
fi
"${RELEASE_DIR}/.venv/bin/python" -m pip install --quiet --upgrade pip
"${RELEASE_DIR}/.venv/bin/python" -m pip install --quiet --upgrade "${RELEASE_DIR}"

ln -sfn -- "${RELEASE_DIR}" "${INSTALL_ROOT}/current"
ln -sfn -- "${RELEASE_DIR}/.venv/bin/lemono" "${BIN_DIR}/lemono"

printf '\nLemono Agent installed successfully.\n'
printf 'Command: %s/lemono\n' "${BIN_DIR}"
case ":${PATH}:" in
  *":${BIN_DIR}:"*) ;;
  *) printf 'Add this to your shell profile: export PATH="%s:$PATH"\n' "${BIN_DIR}" ;;
esac

if [[ "${LEMONO_NO_SETUP:-0}" != "1" && -r /dev/tty ]]; then
  printf 'Configure an AI provider now? [Y/n] ' >/dev/tty
  read -r ANSWER </dev/tty || ANSWER="n"
  case "${ANSWER}" in
    n|N|no|NO) printf 'Run `lemono setup` whenever you are ready.\n' ;;
    *) "${BIN_DIR}/lemono" setup </dev/tty ;;
  esac
else
  printf 'Run `lemono setup` to configure a provider.\n'
fi

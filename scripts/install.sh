#!/usr/bin/env bash
set -Eeuo pipefail

REPOSITORY_URL="${LEMONO_REPOSITORY_URL:-https://github.com/mkseo1012-pixel/Lemono-Agent.git}"
INSTALL_ROOT="${LEMONO_INSTALL_DIR:-${HOME}/.local/share/lemono-agent}"
BIN_DIR="${LEMONO_BIN_DIR:-${HOME}/.local/bin}"
REF="${LEMONO_REF:-main}"
PYTHON_BIN="${PYTHON_BIN:-}"

fail() {
  printf 'Lemono install error: %s\n' "$1" >&2
  exit 1
}

python_is_supported() {
  command -v "$1" >/dev/null 2>&1 && "$1" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
}

find_python() {
  local candidate
  if [[ -n "${PYTHON_BIN}" ]]; then
    python_is_supported "${PYTHON_BIN}" || fail "PYTHON_BIN must point to Python 3.11+"
    return
  fi
  for candidate in python3.13 python3.12 python3.11 python3; do
    if python_is_supported "${candidate}"; then
      PYTHON_BIN="${candidate}"
      return
    fi
  done
  return 1
}

as_root() {
  if [[ "$(id -u)" -eq 0 ]]; then
    "$@"
  elif command -v sudo >/dev/null 2>&1; then
    sudo "$@"
  else
    fail "administrator access is required to install prerequisites"
  fi
}

install_prerequisites() {
  printf 'Installing required Git, Python 3.11+, and venv support...\n'
  if command -v apt-get >/dev/null 2>&1; then
    as_root apt-get update
    as_root apt-get install -y git python3 python3-venv
    if ! find_python; then
      local version
      for version in 3.13 3.12 3.11; do
        if apt-cache show "python${version}" >/dev/null 2>&1; then
          as_root apt-get install -y "python${version}" "python${version}-venv"
          break
        fi
      done
    fi
  elif command -v dnf >/dev/null 2>&1; then
    as_root dnf install -y git python3
  elif command -v yum >/dev/null 2>&1; then
    as_root yum install -y git python3
  elif command -v pacman >/dev/null 2>&1; then
    as_root pacman -Sy --needed --noconfirm git python
  elif command -v apk >/dev/null 2>&1; then
    as_root apk add git python3 py3-pip
  elif command -v brew >/dev/null 2>&1; then
    brew install git python@3.12
  else
    fail "no supported package manager found; install Git and Python 3.11+ manually"
  fi
}

if ! command -v git >/dev/null 2>&1 || ! find_python; then
  install_prerequisites
fi
command -v git >/dev/null 2>&1 || fail "Git installation did not complete"
find_python || fail "Python 3.11+ is unavailable from this system package manager"

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
  "${PYTHON_BIN}" -m venv "${RELEASE_DIR}/.venv" || fail "Python venv support is unavailable"
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

# Lemono Agent 🍋

Lemono is a local-first personal AI agent that remembers, checks its own health, and adapts to each user without silently rewriting its code or expanding its permissions.

## One-line install / 원라이너 설치

Windows PowerShell — WSL이 필요하지 않으며 Python이 없으면 WinGet으로 자동 설치합니다. No WSL required; missing Python is installed automatically with WinGet:

```powershell
irm https://raw.githubusercontent.com/mkseo1012-pixel/Lemono-Agent/main/scripts/install.ps1 | iex
```

macOS, Linux, WSL — Git, Python, venv가 없으면 지원되는 패키지 관리자로 자동 설치합니다. Missing Git, Python, and venv support are installed with a supported package manager:

```bash
curl -fsSL https://raw.githubusercontent.com/mkseo1012-pixel/Lemono-Agent/main/scripts/install.sh | bash
```

설정을 다시 변경하려면 `lemono setup`을 실행하세요. Run `lemono setup` whenever you want to change providers, models, or API keys.

## MVP features

- **Multi-model routing:** OpenAI/Codex, xAI Grok, Anthropic Claude, and Google Gemini behind one interface
- **Durable memory:** local SQLite + FTS5 retrieval with user isolation, provenance, confidence, and complete deletion
- **Safe personal evolution:** learns only explicit preferences and injects the user profile on future turns
- **Self-diagnostics:** database, provider configuration, and disk checks via CLI or API
- **Resilience:** ordered provider fallback with bounded HTTP timeouts
- **Local-first security:** no telemetry, no shell tools, non-root hardened container, restricted CORS

The design takes inspiration from the public ideas behind Hermes Agent—persistent memory, learning loops, self-hosting, skills, gateways, and automation—while remaining an independent implementation. The current milestone deliberately focuses on a small, auditable core.

## 설치 방법 (한국어)

### 요구 사항

- Windows 10/11 PowerShell 또는 지원되는 macOS/Linux/WSL 환경
- Windows 자동 설치에는 WinGet(Microsoft App Installer) 필요
- Linux/macOS 자동 설치에는 `apt`, `dnf`, `yum`, `pacman`, `apk`, Homebrew 중 하나 필요
- OpenAI, xAI, Anthropic, Google 중 하나 이상의 API 키

### 로컬 설치

Windows PowerShell 원라이너(WSL 불필요):

```powershell
irm https://raw.githubusercontent.com/mkseo1012-pixel/Lemono-Agent/main/scripts/install.ps1 | iex
```

macOS, Linux, WSL 원라이너:

```bash
curl -fsSL https://raw.githubusercontent.com/mkseo1012-pixel/Lemono-Agent/main/scripts/install.sh | bash
```

설치기는 필요한 Python 3.11+, Git, venv 지원을 먼저 확인하고 가능한 경우 자동 설치합니다. Windows PowerShell 설치는 WSL을 사용하지 않습니다. 설치 과정에서 바로 모델 공급자와 API 키를 설정할 수 있으며, 나중에 `lemono setup`으로 다시 설정할 수 있습니다. 시스템 패키지 설치에는 관리자 승인이나 `sudo` 암호가 필요할 수 있습니다.

수동 설치:

```bash
git clone https://github.com/mkseo1012-pixel/Lemono-Agent.git
cd Lemono-Agent

python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1

pip install -e .
cp .env.example .env
```

`.env` 파일을 열어 사용할 공급자의 키를 하나 이상 입력하세요.

```dotenv
OPENAI_API_KEY=your_key_here
# XAI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here
# GEMINI_API_KEY=your_key_here
```

설정을 진단하고 CLI를 실행합니다.

```bash
lemono --doctor
lemono --provider openai
# 예: lemono --provider claude --model claude-sonnet-4-5
```

REST API 서버를 실행하려면:

```bash
uvicorn lemono.api:app --host 127.0.0.1 --port 8000
curl http://localhost:8000/v1/diagnostics
curl -X POST http://localhost:8000/v1/chat \
  -H 'content-type: application/json' \
  -d '{"user_id":"local","message":"답변은 간결하게 해줘"}'
```

API 문서는 `http://localhost:8000/docs`에서 볼 수 있습니다. 외부에 공개할 때는 반드시 인증 기능이 있는 리버스 프록시 뒤에 배치하세요.

### Docker로 설치

```bash
git clone https://github.com/mkseo1012-pixel/Lemono-Agent.git
cd Lemono-Agent
cp .env.example .env
# .env에 API 키를 입력한 다음 실행합니다.
docker compose up --build -d
curl http://localhost:8000/v1/diagnostics
```

중지하려면 `docker compose down`을 실행합니다. 기억 데이터는 `lemono-data` Docker 볼륨에 유지됩니다.

## Installation (English)

### Requirements

- Windows 10/11 PowerShell, or a supported macOS/Linux/WSL environment
- WinGet (Microsoft App Installer) for automatic prerequisite installation on Windows
- One of `apt`, `dnf`, `yum`, `pacman`, `apk`, or Homebrew for automatic setup on Unix
- At least one API key from OpenAI, xAI, Anthropic, or Google

### Local installation

Windows PowerShell one-liner (WSL is not required):

```powershell
irm https://raw.githubusercontent.com/mkseo1012-pixel/Lemono-Agent/main/scripts/install.ps1 | iex
```

macOS, Linux, and WSL one-liner:

```bash
curl -fsSL https://raw.githubusercontent.com/mkseo1012-pixel/Lemono-Agent/main/scripts/install.sh | bash
```

The installer checks for Python 3.11+, Git, and venv support and installs missing prerequisites when possible. The native PowerShell installer does not use WSL. It can configure a model provider and API key immediately; run `lemono setup` any time to change them. Installing system packages may request administrator approval or a `sudo` password.

Manual installation:

```bash
git clone https://github.com/mkseo1012-pixel/Lemono-Agent.git
cd Lemono-Agent

python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1

pip install -e .
cp .env.example .env
```

Open `.env` and add at least one provider key:

```dotenv
OPENAI_API_KEY=your_key_here
# XAI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here
# GEMINI_API_KEY=your_key_here
```

Check the installation and start the CLI:

```bash
lemono --doctor
lemono --provider openai
# Example: lemono --provider claude --model claude-sonnet-4-5
```

To run the REST API:

```bash
uvicorn lemono.api:app --host 127.0.0.1 --port 8000
curl http://localhost:8000/v1/diagnostics
curl -X POST http://localhost:8000/v1/chat \
  -H 'content-type: application/json' \
  -d '{"user_id":"local","message":"Keep the answer concise"}'
```

OpenAPI documentation is available at `http://localhost:8000/docs`. If you expose the service publicly, place it behind an authenticated reverse proxy.

### Docker installation

```bash
git clone https://github.com/mkseo1012-pixel/Lemono-Agent.git
cd Lemono-Agent
cp .env.example .env
# Add an API key to .env before starting.
docker compose up --build -d
curl http://localhost:8000/v1/diagnostics
```

Run `docker compose down` to stop the service. Memory remains in the `lemono-data` Docker volume.

## Provider configuration

| Provider | `provider` value | Key | Example default model |
|---|---|---|---|
| OpenAI / Codex | `openai` or `codex` | `OPENAI_API_KEY` | `gpt-5` |
| xAI | `grok` | `XAI_API_KEY` | `grok-4` |
| Anthropic | `claude` | `ANTHROPIC_API_KEY` | `claude-sonnet-4-5` |
| Google | `gemini` | `GEMINI_API_KEY` | `gemini-2.5-pro` |

Model names change over time; override them with `--model`, the chat request `model`, or `LEMONO_DEFAULT_MODEL`. `codex` currently uses OpenAI's standard API adapter; consumer ChatGPT subscriptions are not API credentials.

## Memory and privacy

Memories live at `~/.lemono/lemono.db` by default. Every row records its user, kind, source, confidence, and timestamp. Retrieval always filters by `user_id`. Delete one user's data with:

```bash
curl -X DELETE http://localhost:8000/v1/memories/local
```

The API has no built-in authentication in v0.1. Bind it only to localhost or put it behind an authenticated reverse proxy. Never commit `.env`.

## Architecture

```mermaid
flowchart TD
    C[CLI or REST API] --> A[Agent core]
    A --> M[SQLite memory + profile]
    A --> R[Provider router + fallback]
    R --> P[OpenAI · Grok · Claude · Gemini]
    D[Self-diagnostics] --> M
    D --> R
```

Provider responses, remote content, and recalled memory are untrusted. The effect boundary owns authorization. Future tools must declare capabilities and require confirmation for destructive or external side effects.

## Roadmap

- v0.2: versioned `SKILL.md` registry and permission-gated tools
- v0.3: scheduler, Telegram/Discord gateways, streaming, and session summaries
- v0.4: sandboxed sub-agents, browser/MCP adapters, memory evaluation suite
- v1.0: encrypted secrets, auth/RBAC, migrations, observability, stable plugin SDK

## Development

```bash
pip install -e '.[dev]'
ruff check .
pytest -q
```

Contributions are welcome. Please keep provider-specific behavior behind adapters, add deterministic tests, and never log secrets or raw private memories.

## License

MIT

# Security

Please report vulnerabilities privately through GitHub Security Advisories. Do not open a public issue.

Lemono treats model output and recalled memory as untrusted. API keys are read from the environment, memory is isolated by `user_id`, and the default runtime exposes no shell, filesystem, browser, or account-changing tools. Public deployments must add authentication at a trusted reverse proxy; the MVP API is intended for localhost or a private network.

The setup wizard stores secrets in `~/.lemono/.env` with file mode `0600` and never prints entered keys. The one-line installer uses versioned release directories and verifies the downloaded Git commit before switching the active symlink. Users who do not trust pipe-to-shell installation should download and inspect `scripts/install.sh` before running it.

On Windows, `scripts/install.ps1` uses the GitHub API to resolve an exact 40-character commit, downloads that commit's archive, validates the project manifest, and installs without WSL. If Python is absent it uses the exact WinGet package ID `Python.Python.3.12`; package and source agreements are accepted for unattended installation. Review either installer before execution if your environment requires stricter software-supply-chain controls.

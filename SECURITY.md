# Security

Please report vulnerabilities privately through GitHub Security Advisories. Do not open a public issue.

Lemono treats model output and recalled memory as untrusted. API keys are read from the environment, memory is isolated by `user_id`, and the default runtime exposes no shell, filesystem, browser, or account-changing tools. Public deployments must add authentication at a trusted reverse proxy; the MVP API is intended for localhost or a private network.


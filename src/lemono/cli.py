from __future__ import annotations

import argparse
import asyncio
import json

from .agent import LemonoAgent
from .config import Settings
from .diagnostics import Diagnostics
from .memory import MemoryStore
from .models import ChatRequest
from .providers import build_providers


def main() -> None:
    parser = argparse.ArgumentParser(prog="lemono")
    parser.add_argument("--doctor", action="store_true", help="run self-diagnostics")
    parser.add_argument("--provider")
    parser.add_argument("--model")
    args = parser.parse_args()
    settings = Settings()
    memory = MemoryStore(settings.database_path)
    providers = build_providers(settings.request_timeout_seconds)
    if args.doctor:
        print(json.dumps(Diagnostics(settings, memory, providers).run().model_dump(), indent=2))
        return
    agent = LemonoAgent(settings, memory, providers)
    print("Lemono Agent — /quit to exit")
    while True:
        message = input("you> ").strip()
        if message in {"/quit", "/exit"}:
            break
        result = asyncio.run(agent.chat(ChatRequest(message=message, provider=args.provider, model=args.model)))
        print(f"lemono[{result.provider}]> {result.response}")


if __name__ == "__main__":
    main()


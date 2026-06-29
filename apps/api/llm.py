import os
from dotenv import load_dotenv
load_dotenv()

def call_llm(provider: str, prompt: str):
    if provider.lower() == 'gemini':
        return f'[Gemini] {prompt}에 대한 응답입니다 nyaong~'
    return f'[{provider}] 응답: {prompt}'
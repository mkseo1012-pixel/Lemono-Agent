import os
from dotenv import load_dotenv
load_dotenv()

def call_llm(provider: str, prompt: str):
    if provider == 'gemini':
        # TODO: Google Gemini API
        return f'Gemini response to: {prompt}'
    elif provider == 'grok':
        return f'Grok response to: {prompt}'
    # Add OpenAI, Anthropic etc.
    return 'Default response nyaong~'

if __name__ == '__main__':
    print(call_llm('gemini', 'Hello!'))
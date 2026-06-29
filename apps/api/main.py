from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Lemono Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Lemono Agent is running! nyaong~"}

@app.post("/chat")
def chat(message: dict):
    # TODO: Integrate with Grok/OpenAI etc.
    return {"response": f"Echo: {message.get('message', '')}"}
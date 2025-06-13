import os
import base64
import tempfile
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import asyncio
from maplehack import azure_pattern_opt_triage_agent, image_to_text_gpt4o, thread

app = FastAPI()

# Allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: list[str] = []

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    # Combine history and new message
    messages = req.history + [req.message]
    response = await azure_pattern_opt_triage_agent.get_response(messages=messages, thread=thread)
    return {"response": response.message.content}

@app.post("/image")
async def image_endpoint(file: UploadFile = File(...), message: str = Form("")):
    # Save uploaded image to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        extracted_text = image_to_text_gpt4o(tmp_path)
        # Combine user message and extracted text
        user_input = (message.strip() + "\n[Diagram Analysis]: " + extracted_text).strip()
        response = await azure_pattern_opt_triage_agent.get_response(messages=user_input, thread=thread)
        return {"response": response.message.content, "extracted_text": extracted_text}
    finally:
        os.remove(tmp_path)

if __name__ == "__main__":
    uvicorn.run("frontend.backend:app", host="0.0.0.0", port=8000, reload=True)

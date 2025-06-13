# Maplehack Azure Architecture Conversational Agent

This project is a multi-agent conversational system for analyzing, optimizing, and discussing Azure cloud architectures. It supports both terminal and web-based chat interfaces, image (diagram) analysis, and leverages Azure OpenAI GPT-4o for vision tasks.

## Features
- **Conversational Agent**: Multi-agent orchestration (core, cost, performance, Bing search, triage/orchestrator) for Azure architecture Q&A and optimization.
- **Image Analysis**: Upload architecture diagrams (PNG/JPG/SVG) for automated extraction and analysis using Azure OpenAI GPT-4o Vision.
- **Web Frontend**: Modern chat UI with image upload, conversation history, and AJAX backend integration.
- **Terminal Support**: CLI chat loop for text and image-based queries.
- **Cost & Performance Optimization**: Agents can suggest improvements for Azure cost and performance.
- **Bing Search Integration**: Augments answers with web search when needed.

## Project Structure
```
maplehack.py           # Main backend agent/orchestrator logic
bing_agent.py          # BingSearch agent plugin
service_settings.py    # Service configuration
services.py            # Service utilities
requirements.txt       # Python dependencies
frontend/
  ├── backend.py       # FastAPI backend for web frontend
  ├── index.html       # Web chat UI
  ├── script.js        # Frontend JS (chat, image upload)
  ├── style.css        # Frontend styles
```

## Setup & Usage

### 1. Install Python dependencies
```sh
pip install -r requirements.txt
```

### 2. Run the FastAPI backend
```sh
cd frontend
uvicorn backend:app --reload
```

### 3. Open the Web Frontend
Open `frontend/index.html` in your browser. (If running locally, you may need to allow CORS or use a simple HTTP server.)

### 4. Use the Terminal Chat (optional)
You can also run `maplehack.py` directly for a CLI chat experience:
```sh
python maplehack.py
```

## Configuration
- **Azure OpenAI**: Set your Azure OpenAI endpoint and key in `service_settings.py`.
- **Bing Search**: Configure Bing Search API credentials in `bing_agent.py` if required.

## Development Notes
- The system uses a multi-agent orchestration pattern. All user queries (text or image) are routed through a triage/orchestrator agent.
- The BingSearch agent must return an object with a `.content` attribute (not just a string) for proper orchestration.
- Frontend and backend communicate via AJAX; conversation history is maintained in the browser.

## Troubleshooting
- If you see errors related to BingSearch agent (`'str' object has no attribute 'content'`), ensure the agent returns a response object with a `.content` property.
- For CORS issues, make sure FastAPI backend has CORS enabled (already set in `backend.py`).

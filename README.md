# Talk2Publish

AI-powered ghostwriting partner that helps authors write books through conversation.

## Project Structure

This is a monorepo containing:
- `apps/api/` - Python FastAPI backend service
- `docs/` - Project documentation (PRD, Architecture)
- `.bmad-core/` - BMad development framework

## Quick Start

```bash
cd apps/api
pip install -r requirements.txt
uvicorn src.main:app --reload
```

## Documentation

- [Product Requirements](docs/prd/Talk2Publish%20Product%20Requirements%20Document%20(PRD).md)
- [Architecture](docs/architecture/Talk2Publish%20Architecture%20Document.md)
- [Development Stories](docs/stories/)

## Tech Stack

- Python 3.11+
- FastAPI
- deepagents (LangGraph)
- PostgreSQL (Neon)
- Railway (Deployment)

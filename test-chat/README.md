# Talk2Publish Test Chat

Simple HTML chat interface for testing the Talk2Publish agents API.

## Quick Start

1. **Ensure API is running:**
   ```bash
   cd ../apps/api
   source venv/bin/activate
   uvicorn src.main:app --reload
   ```
   API should be available at http://localhost:8000

2. **Open the test chat:**
   - Simply open `index.html` in your browser
   - Or use a local server:
     ```bash
     # Using Python
     python3 -m http.server 3000
     # Then open http://localhost:3000
     ```

## Features

- ✅ Send messages to orchestration agent
- ✅ View conversation history
- ✅ Thread ID management (maintains context)
- ✅ Streaming indicator during API calls
- ✅ Clear chat / New thread controls
- ✅ Auto-resize input textarea
- ✅ **Keyboard shortcuts**:
  - Enter to send message
  - Shift+Enter for new line
- ✅ **Key Points Sidebar**: Automatically extracts and displays:
  - Bullet points
  - Numbered steps
  - Important highlights
  - Questions from AI responses
- ✅ Full-height ChatGPT-like interface
- ✅ Mobile-responsive design with collapsible sidebar

## Testing Workflow

### 1. Author Profiling
```
You: Hi, I want to write a book
Agent: [Biographer will start profiling process]
```

### 2. Audience Definition
```
You: [Answer profiling questions]
Agent: [Empath will create audience persona]
```

### 3. Book Planning
```
Agent: [Planner will create outline and chapter structure]
```

### 4. Chapter Transcript
```
You: [Provide chapter transcript]
Agent: [Gap analysis will identify missing topics]
```

### 5. HITL Clarifications
```
Agent: [Questions about missing topics]
You: [Provide clarifications]
```

### 6. Chapter Drafting
```
Agent: [Writer will create draft]
```

## API Endpoints Tested

- **POST /chat**: Synchronous chat (used by this interface)
- **GET /health**: Health check (tested on page load)

## Troubleshooting

**Error: Cannot connect to API**
- Ensure the API server is running on http://localhost:8000
- Check `apps/api` terminal for errors
- Verify database connection in API logs

**No response from agent**
- Check API terminal for error logs
- Verify agents are seeded in database
- Check that orchestrator is loading subagents correctly

**Thread context not maintained**
- Thread ID should appear in header after first message
- Click "New Thread" to reset conversation context

## Architecture

- **Frontend**: Pure HTML/CSS/JavaScript (no build step)
- **API**: FastAPI running on port 8000
- **State**: Thread-based conversation persistence via LangGraph checkpointer

## Next Steps

For a full production frontend, use the comprehensive prompt in `AI-Frontend-Generation-Prompt.md` to generate a Next.js application with:
- TypeScript + shadcn/ui components
- Server-Sent Events (SSE) streaming
- Artifact management panel
- Project dashboard
- Mobile-first responsive design

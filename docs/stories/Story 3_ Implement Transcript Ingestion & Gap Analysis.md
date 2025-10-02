# **Story 3: Implement Transcript Ingestion & Gap Analysis**

### **Status**

Draft

### **Story**

As a System,  
I need to ingest a user's text transcript and automatically compare it against the chapter plan,  
so that I can identify any discrepancies for clarification.

### **Acceptance Criteria**

1. A new API endpoint POST /chat/{project\_id}/transcript is created to accept a text transcript.  
2. The Orchestration Agent's state graph is updated with a transcript\_ingestion node and a gap\_analysis node.  
3. When the endpoint is called, the Orchestrator retrieves the correct chapter plan from the database.  
4. The gap analysis logic correctly identifies key topics from the plan that are missing from the transcript.  
5. The gap analysis logic correctly identifies new, unplanned topics that were introduced in the transcript.  
6. The lists of "missing" and "new" topics are stored in the agent's state for the next step.

### **Tasks / Subtasks**

* \[ \] **Task 1: Create Transcript API Endpoint** (AC: 1\)  
  * \[ \] In apps/api/src/routes/chat.py, add the new POST /chat/{project\_id}/transcript endpoint.  
  * \[ \] This endpoint should accept a JSON payload with the transcript text and trigger the Orchestrator's transcript processing flow.  
* \[ \] **Task 2: Update Orchestrator for Gap Analysis** (AC: 2, 3, 4, 5, 6\)  
  * \[ \] In apps/api/src/agents/orchestrator.py, add the transcript\_ingestion and gap\_analysis nodes to the LangGraph state machine.  
  * \[ \] Implement the logic to fetch the chapter plan using the Data Access Layer.  
  * \[ \] Implement the core gap analysis logic (this will likely involve an LLM call comparing two pieces of text).  
  * \[ \] Store the results in the graph's state object.  
* \[ \] **Task 3: Add Integration Tests** (AC: 3, 4, 5, 6\)  
  * \[ \] In apps/api/tests/test\_agents.py, test the gap\_analysis logic with sample plans and transcripts.  
  * \[ \] In apps/api/tests/test\_routes.py, add a test for the new API endpoint.

### **Dev Notes**

File Structure:  
Modify apps/api/src/routes/chat.py for the new endpoint and apps/api/src/agents/orchestrator.py for the new logic.  
Source: docs/architecture.md\#Source Tree  
Gap Analysis Logic:  
The core of this task is an AI-driven comparison. The prompt should instruct an LLM to act as an editor, comparing a structured plan (JSON/Markdown) against a block of prose (the transcript) and outputting two lists: topics mentioned in the plan but not the prose, and topics in the prose not mentioned in the plan.  
Source: docs/prd.md\#FR9  
Data Models:  
The agent will need to read from the Chapter table to retrieve the plan and will write the raw\_transcript to the same record.  
Source: docs/architecture.md\#Data Models

### **Change Log**

| Date | Version | Description | Author |
| :---- | :---- | :---- | :---- |
| 2025-10-01 | 1.0 | Initial story draft created. | Bob (SM) |


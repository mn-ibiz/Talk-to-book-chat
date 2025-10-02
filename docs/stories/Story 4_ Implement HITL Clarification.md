# **Story 4: Implement HITL Clarification**

### **Status**

Draft

### **Story**

As an Author,  
I want the AI to ask me clarifying questions about my recorded content,  
so that it has all the information it needs to write a great draft.

### **Acceptance Criteria**

1. The Orchestration Agent's state graph includes a hitl\_clarification node that is triggered after gap\_analysis.  
2. The agent generates targeted, user-facing questions based on the "missing" and "new" topics identified in the previous step.  
3. The agent enters a conversational loop, asking questions and waiting for user answers via the chat interface.  
4. The user's answers are captured and stored in the agent's state.  
5. The loop concludes when all identified gaps have been addressed.

### **Tasks / Subtasks**

* \[ \] **Task 1: Update Orchestrator for HITL** (AC: 1, 2, 3, 4, 5\)  
  * \[ \] In apps/api/src/agents/orchestrator.py, add the hitl\_clarification node to the LangGraph graph.  
  * \[ \] This node should have logic to generate questions from the gap analysis results.  
  * \[ \] Implement the conversational loop. The graph should wait for the next user input before proceeding.  
  * \[ \] Store the Q\&A pairs in the state.  
* \[ \] **Task 2: Implement Database Interaction** (AC: 4\)  
  * \[ \] In apps/api/src/database/repository.py, add a method update\_chapter\_clarifications(chapter\_id, hitl\_data).  
* \[ \] **Task 3: Add Integration Tests** (AC: 1, 2, 3, 4\)  
  * \[ \] In apps/api/tests/test\_agents.py, test the HITL workflow. Provide a mock gap analysis result and simulate user answers to verify the state is updated correctly.  
  * \[ \] Verify that the repository method is called at the end of the loop.

### **Dev Notes**

File Structure:  
Primary modifications will be in apps/api/src/agents/orchestrator.py. A new method will be added to apps/api/src/database/repository.py.  
Source: docs/architecture.md\#Source Tree  
Conversational Loop:  
This is a key feature of LangGraph. The graph should route back to the hitl\_clarification node as long as there are unanswered questions. The state object should track which questions have been asked and answered.  
Source: LangGraph Documentation  
Data Model:  
The agent will save the collected Q\&A pairs to the hitl\_clarifications (JSONB) field in the Chapter record.  
Source: docs/architecture.md\#Data Models

### **Change Log**

| Date | Version | Description | Author |
| :---- | :---- | :---- | :---- |
| 2025-10-01 | 1.0 | Initial story draft created. | Bob (SM) |


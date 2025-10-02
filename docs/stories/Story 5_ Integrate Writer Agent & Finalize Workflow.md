# **Story 5: Integrate Writer Agent & Finalize Workflow**

### **Status**

Draft

### **Story**

As an Author,  
I want the AI to synthesize our plan and conversations into a well-written first draft of my chapter,  
so that I can move on to editing and refining.

### **Acceptance Criteria**

1. The Orchestration Agent's state graph includes a final generate\_draft node.  
2. The Orchestrator gathers all necessary context: the chapter plan, the raw transcript, and the HITL clarifications.  
3. The Orchestrator successfully calls the "Writer" sub-agent, passing the complete context.  
4. The Writer agent generates the final draft and saves it to the database via the repository.  
5. The final draft is presented to the user via the chat interface, and the workflow for the chapter concludes.

### **Tasks / Subtasks**

* \[ \] **Task 1: Update Orchestrator to Call Writer Agent** (AC: 1, 2, 3, 5\)  
  * \[ \] In apps/api/src/agents/orchestrator.py, add the generate\_draft node to the LangGraph graph, triggered after the HITL step.  
  * \[ \] Implement the logic to compile all artifacts from the state into a single context object.  
  * \[ \] Instantiate and run the WriterAgent, passing the context.  
  * \[ \] Implement the logic to present the final draft to the user.  
* \[ \] **Task 2: Create Final End-to-End Integration Test** (AC: 1, 2, 3, 4, 5\)  
  * \[ \] In apps/api/tests/integration/, create a new test file test\_full\_workflow.py.  
  * \[ \] Write a test that simulates the entire user journey for one chapter, from planning through drafting, mocking only the LLM calls to ensure the state transitions and data persistence work correctly.

### **Dev Notes**

File Structure:  
Primary modifications will be in apps/api/src/agents/orchestrator.py. A new integration test file will be created.  
Source: docs/architecture.md\#Source Tree  
Dependencies:  
This story depends on the completed implementation of the WriterAgent (Story 1-4) and the HITL workflow (Story 4).  
End-to-End Test:  
This test is critical. It will be the primary validation that all components and agents work together as designed. It should be the most comprehensive test in the suite.  
Source: docs/architecture.md\#Test Strategy and Standards

### **Change Log**

| Date | Version | Description | Author |
| :---- | :---- | :---- | :---- |
| 2025-10-01 | 1.0 | Initial story draft created. | Bob (SM) |


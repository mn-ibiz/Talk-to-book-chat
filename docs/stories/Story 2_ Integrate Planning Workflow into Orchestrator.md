# **Story 2: Integrate Planning Workflow into Orchestrator**

### **Status**

Ready

### **Story**

As a System,  
I need the Orchestration Agent to manage the entire book planning phase,  
so that a user is guided sequentially through author profiling, audience definition, and chapter planning.

### **Acceptance Criteria**

1. The Orchestration Agent's LangGraph state machine is updated to include nodes for the Biographer, Empath, and Planner agents.  
2. The Orchestrator correctly calls the Biographer agent first, then the Empath agent, and finally the Planner agent.  
3. The state (e.g., book\_project\_id, collected artifacts) is correctly passed between agent calls.  
4. After the Planner agent completes, the Orchestrator's state transitions to a new planning\_complete stage.  
5. All interactions are logged with appropriate context.

### **Tasks / Subtasks**

* \[ \] **Task 1: Update Orchestrator State Graph** (AC: 1, 2\)  
  * \[ \] In apps/api/src/agents/orchestrator.py, modify the LangGraph definition.  
  * \[ \] Add nodes for run\_biographer, run\_empath, and run\_planner.  
  * \[ \] Define conditional edges to ensure the sequence: start \-\> run\_biographer \-\> run\_empath \-\> run\_planner \-\> planning\_complete.  
* \[ \] **Task 2: Implement Agent Invocation Logic** (AC: 2, 3\)  
  * \[ \] Implement the methods for the new nodes (run\_biographer, etc.).  
  * \[ \] These methods should instantiate and run the respective sub-agents created in Stories 1-1, 1-2, and 1-3.  
  * \[ \] Ensure the book\_project\_id and other necessary context are passed to each sub-agent.  
* \[ \] **Task 3: Add Integration Tests** (AC: 1, 2, 3, 4\)  
  * \[ \] In apps/api/tests/test\_agents.py, create a new integration test for the OrchestrationAgent.  
  * \[ \] Mock the sub-agents to verify they are called in the correct order.  
  * \[ \] Assert that the final state of the graph is planning\_complete.

### **Dev Notes**

File Structure:  
All modifications for this story will be primarily within apps/api/src/agents/orchestrator.py.  
Source: docs/architecture.md\#Source Tree  
Stateful Agent Workflow:  
This story is the primary implementation of the stateful workflow for the planning phase. The LangGraph StateGraph should be the source of truth for the workflow sequence.  
Source: docs/architecture.md\#Architectural and Design Patterns  
Dependencies:  
This story depends on the completed implementation of the BiographerAgent (Story 1-1), EmpathAgent (Story 1-2), and PlannerAgent (Story 1-3).

### **Change Log**

| Date | Version | Description | Author |
| :---- | :---- | :---- | :---- |
| 2025-10-01 | 1.0 | Initial story draft created. | Bob (SM) |


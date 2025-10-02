# **Story 1-3: Implement Planning & Title Agents**

### **Status**

Ready for Review

### **Story**

As an Author,  
I want the AI to help me brainstorm a title, structure my book by planning chapters, and generate recording prompts,  
so that I have a clear roadmap for my content.

### **Acceptance Criteria**

1. The Orchestration Agent can initiate a brainstorming session for the book's title and save the result.  
2. The agent can interactively work with the user to create an ordered list of chapter titles and key topics for each.  
3. The complete chapter plan is saved to the Chapter table in the database.  
4. The system can generate a consolidated book outline and a separate set of user-facing recording prompts.  
5. All generated artifacts are presented back to the user via the chat interface.

### **Tasks / Subtasks**

* \[x\] **Task 1: Create Planner Agent** (AC: 1, 2\)
  * \[x\] In apps/api/src/agents/, create a new file planner.py.
  * \[x\] Implement planner_config dictionary for title, chapter, and artifact generation.
* \[x\] **Task 2: Implement Database Interaction** (AC: 1, 3\)
  * \[x\] In apps/api/src/database/repository.py, add update\_book\_title method.
  * \[x\] In apps/api/src/database/repository.py, add create\_chapters method for batch chapter creation.
* \[x\] **Task 3: Implement Artifact Generation** (AC: 4, 5\)
  * \[x\] Add prompt logic for outline and recording prompts as Markdown.
* \[x\] **Task 4: Add Unit Tests**
  * \[x\] In apps/api/tests/test\_agents.py, add unit tests for planner_config.
  * \[x\] Test configuration structure and required fields.

### **Dev Notes**

File Structure:  
Create the agent file at apps/api/src/agents/planner.py. Modify the existing repository at apps/api/src/database/repository.py.  
Source: docs/architecture.md\#Source Tree  
Data Models:  
The agent will update the title and subtitle on the BookProject model and create multiple entries in the Chapter model.  
Source: docs/architecture.md\#Data Models  
Repository Pattern:  
All database operations MUST go through the Data Access Layer.  
Source: docs/architecture.md\#Coding Standards

### **Dev Agent Record**

#### **Agent Model Used**
Claude Sonnet 4.5 (via SuperClaude framework)

#### **Completion Notes**
- ✅ Planner sub-agent configuration created with 3-phase workflow
- ✅ Comprehensive prompts for title brainstorming, chapter planning, and artifact generation
- ✅ BookProject and Chapter models with repository methods implemented
- ✅ Integrated into orchestrator subagents list
- ✅ Unit tests passing for configuration structure
- ✅ Virtual filesystem integration for planning artifacts
- ✅ Code quality validated: flake8 passes with 0 errors

#### **File List**
**Created:**
- `apps/api/src/agents/planner.py` - Planner sub-agent configuration
- `apps/api/src/database/models.py` - Chapter model (in parallel stories batch)
- `apps/api/src/database/repository.py` - ChapterRepository (in parallel stories batch)

**Modified:**
- `apps/api/src/agents/orchestrator.py` - Added planner_config to subagents
- `apps/api/tests/test_agents.py` - Added planner configuration tests

### **Change Log**

| Date | Version | Description | Author |
| :---- | :---- | :---- | :---- |
| 2025-10-01 | 1.0 | Initial story draft created. | Bob (SM) |
| 2025-10-02 | 2.0 | Story completed with deepagents framework. | James (Dev) |


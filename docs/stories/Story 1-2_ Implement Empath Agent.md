# **Story 1-2: Implement Empath Agent**

### **Status**

Ready for Review

### **Story**

As an Author,  
I want to be guided in creating a persona for my target audience,  
so that the book is written with a specific reader in mind.

### **Acceptance Criteria**

1. The Orchestration Agent can successfully transition to the "Empath" sub-agent.  
2. The Empath agent asks a predefined series of questions to build an audience persona (e.g., demographics, problems, goals).  
3. The user's answers are saved to the virtual file system during the session.  
4. Upon completion, the Empath agent transitions control back to the Orchestrator.  
5. The final audience persona is saved as a structured AudiencePersona object in the Neon database.

### **Tasks / Subtasks**

* \[x\] **Task 1: Create Empath Agent** (AC: 2\)
  * \[x\] In apps/api/src/agents/, create a new file empath.py.
  * \[x\] Implement empath_config dictionary for deepagents framework.
  * \[x\] Define the conversational flow for building the audience persona.
* \[x\] **Task 2: Implement Database Interaction** (AC: 5\)
  * \[x\] In apps/api/src/database/repository.py, add AudiencePersonaRepository with create\_or\_update method.
* \[x\] **Task 3: Integrate with Orchestrator** (AC: 1, 4\)
  * \[x\] Update the OrchestrationAgent to include empath_config in subagents list.
* \[x\] **Task 4: Add Unit Tests** (AC: 2, 5\)
  * \[x\] In apps/api/tests/test\_agents.py, add unit tests for empath_config.
  * \[x\] Test configuration structure and required fields.

### **Dev Notes**

File Structure:  
Create the agent file at apps/api/src/agents/empath.py. Modify the existing repository at apps/api/src/database/repository.py.  
Source: docs/architecture.md\#Source Tree  
Data Model:  
The agent must create and persist the AudiencePersona data model. The persona\_data field should be a JSONB object.  
Source: docs/architecture.md\#Data Models  
CREATE TABLE audience\_personas (  
    id UUID PRIMARY KEY DEFAULT uuid\_generate\_v4(),  
    book\_project\_id UUID NOT NULL UNIQUE REFERENCES book\_projects(id) ON DELETE CASCADE,  
    persona\_data JSONB  
);

Repository Pattern:  
All database operations MUST go through the Data Access Layer. Add the new method to the existing Repository class.  
Source: docs/architecture.md\#Coding Standards

### **Dev Agent Record**

#### **Agent Model Used**
Claude Sonnet 4.5 (via SuperClaude framework)

#### **Completion Notes**
- ✅ Empath sub-agent configuration created using deepagents pattern
- ✅ Comprehensive prompt engineering for empathetic audience profiling
- ✅ AudiencePersona model and repository implemented
- ✅ Integrated into orchestrator subagents list
- ✅ Unit tests passing for configuration structure
- ✅ Virtual filesystem integration for persona_data.json
- ✅ Code quality validated: flake8 passes with 0 errors

#### **File List**
**Created:**
- `apps/api/src/agents/empath.py` - Empath sub-agent configuration
- `apps/api/src/database/models.py` - AudiencePersona model (in parallel stories batch)
- `apps/api/src/database/repository.py` - AudiencePersonaRepository (in parallel stories batch)

**Modified:**
- `apps/api/src/agents/orchestrator.py` - Added empath_config to subagents
- `apps/api/tests/test_agents.py` - Added empath configuration tests

### **Change Log**

| Date | Version | Description | Author |
| :---- | :---- | :---- | :---- |
| 2025-10-01 | 1.0 | Initial story draft created. | Bob (SM) |
| 2025-10-02 | 2.0 | Story completed with deepagents framework. | James (Dev) |


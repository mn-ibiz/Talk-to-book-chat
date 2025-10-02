# **Talk2Publish Parallel Development Plan**

This plan organizes the stories from the PRD into a sequence that allows for maximum parallel development using Git worktrees.

### **Foundational Story (Must be completed first)**

* **Story 1: Project Foundation & Deep Agent Setup**
  * **Description:** Implements the foundational project structure, including the monorepo setup, core dependencies (deepagents, LangGraph, FastAPI), CI/CD pipeline, a health check endpoint, and the basic deep agent created with `create_deep_agent()`. Includes checkpointer setup for state persistence. (Corresponds to PRD Story 1.1)
  * **Worktree Branch:** feature/story-1-foundation
  * **Dependencies:** None
  * **Parallel-safe:** false (This is the prerequisite for all other work)
  * **Module Affected:** Root project structure, .github/workflows/, apps/api/src/, apps/api/main.py
  * **Key Implementation:** Install `deepagents` package, create base orchestrator with `create_deep_agent()`, configure checkpointer (MemorySaver for dev)

### **Parallel Development Set 1 (Can run simultaneously after Story 1\)**

These stories focus on creating the individual, isolated sub-agents and their database interactions. Since they operate on different files within the src/agents/ and src/database/ directories, they can be developed in parallel without causing merge conflicts.

* **Story 1-1: Implement Biographer Sub-Agent**
  * **Description:** Creates the "Biographer" sub-agent configuration dict with name, description, and prompt. Implements database persistence logic for author profile artifacts from virtual filesystem. (Corresponds to PRD Story 1.2)
  * **Worktree Branch:** feature/story-1-1-biographer
  * **Dependencies:** Story 1
  * **Parallel-safe:** true
  * **Module Affected:** apps/api/src/agents/biographer.py (sub-agent config), apps/api/src/database/repository.py
  * **Key Implementation:** Define sub-agent dict with prompt, add to main agent's `subagents` list, extract profile from `result["files"]`
* **Story 1-2: Implement Empath Sub-Agent**
  * **Description:** Creates the "Empath" sub-agent configuration dict for defining target audience persona. Implements database persistence for persona artifacts. (Corresponds to PRD Story 1.3)
  * **Worktree Branch:** feature/story-1-2-empath
  * **Dependencies:** Story 1
  * **Parallel-safe:** true
  * **Module Affected:** apps/api/src/agents/empath.py (sub-agent config), apps/api/src/database/repository.py
  * **Key Implementation:** Define sub-agent dict with prompt, add to `subagents` list, extract persona from `result["files"]`
* **Story 1-3: Implement Planning & Title Sub-Agents**
  * **Description:** Creates sub-agent configuration for book planning: title brainstorming, chapter outlining, and recording prompt generation. Leverages built-in `write_file` tool for artifacts. (Corresponds to PRD Stories 1.4, 1.5, 1.6)
  * **Worktree Branch:** feature/story-1-3-planning
  * **Dependencies:** Story 1
  * **Parallel-safe:** true
  * **Module Affected:** apps/api/src/agents/planner.py (sub-agent config), apps/api/src/database/repository.py
  * **Key Implementation:** Define planner sub-agent dict, use virtual filesystem for outline/prompts, persist to DB from `result["files"]`
* **Story 1-4: Implement Writer Sub-Agent**
  * **Description:** Creates the "Writer" sub-agent configuration for synthesizing all information into chapter drafts. Uses virtual filesystem to access all planning artifacts. (Corresponds to PRD Story 1.9)
  * **Worktree Branch:** feature/story-1-4-writer
  * **Dependencies:** Story 1
  * **Parallel-safe:** true
  * **Module Affected:** apps/api/src/agents/writer.py (sub-agent config), apps/api/src/database/repository.py
  * **Key Implementation:** Define writer sub-agent dict, read from virtual filesystem (plan, transcript, HITL), generate draft, persist to DB

### **Sequential Stories (Must be completed after Parallel Set 1\)**

These stories are sequential because they primarily modify the same core component—the **Orchestration Agent**—integrating the sub-agents and building the complex, stateful workflow logic.

* **Story 2: Configure Planning Workflow in Main Agent**
  * **Description:** Configures the main deep agent's `instructions` to manage sequential planning execution using built-in `task` tool to call sub-agents: Biographer → Empath → Planner. No custom orchestration logic needed - deepagents handles delegation.
  * **Worktree Branch:** feature/story-2-orchestrate-planning
  * **Dependencies:** Stories 1-1, 1-2, 1-3
  * **Parallel-safe:** false
  * **Module Affected:** apps/api/src/agents/orchestrator.py (main agent instructions)
  * **Key Implementation:** Update main agent's `instructions` parameter to guide workflow, leverage `task` tool for sub-agent calls
* **Story 3: Implement Transcript Ingestion & Gap Analysis Tool**
  * **Description:** Creates custom tool for transcript ingestion and gap analysis. Configures tool with HITL via `tool_configs` parameter. (Corresponds to PRD Story 1.7)
  * **Worktree Branch:** feature/story-3-gap-analysis
  * **Dependencies:** Story 2
  * **Parallel-safe:** false
  * **Module Affected:** apps/api/src/tools/gap_analysis.py, apps/api/src/agents/orchestrator.py (add tool + HITL config)
  * **Key Implementation:** Create gap_analysis tool, add to main agent's `tools` list, configure `tool_configs={"gap_analysis": True}`
* **Story 4: Configure HITL Flow with Checkpointer**
  * **Description:** Implements HITL conversation flow using deepagents built-in interrupt/resume pattern via `Command(resume=...)`. Ensures checkpointer is properly configured. (Corresponds to PRD Story 1.8)
  * **Worktree Branch:** feature/story-4-hitl
  * **Dependencies:** Story 3
  * **Parallel-safe:** false
  * **Module Affected:** apps/api/src/routes/chat.py (streaming + resume logic), apps/api/src/agents/orchestrator.py
  * **Key Implementation:** Implement streaming with interrupt detection, handle `Command(resume=[...])` for accept/respond/edit
* **Story 5: Integrate Writer Sub-Agent & Finalize Workflow**
  * **Description:** Updates main agent instructions to call Writer sub-agent via `task` tool with full context from virtual filesystem. Implements final draft persistence from `result["files"]`. (Corresponds to PRD Story 1.9)
  * **Worktree Branch:** feature/story-5-finalize-workflow
  * **Dependencies:** Story 1-4, Story 4
  * **Parallel-safe:** false
  * **Module Affected:** apps/api/src/agents/orchestrator.py (instructions update), apps/api/src/routes/chat.py (draft persistence)
  * **Key Implementation:** Update instructions to invoke writer via `task` tool, extract draft from `result["files"]["chapter_draft.md"]`
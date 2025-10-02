# Agent Transition Analysis - Talk2Publish

**Analysis Date**: 2025-10-03
**Scope**: Orchestrator workflow management and agent transition logic

---

## Executive Summary

**Status**: ⚠️ **Partially Implemented**

The Talk2Publish orchestrator has **clear workflow instructions** but **lacks explicit state tracking** for workflow stages. Agent transitions rely on implicit inference from virtual filesystem contents rather than explicit state management.

**Key Findings**:
- ✅ Well-defined 6-stage workflow with clear instructions
- ✅ Sub-agent delegation mechanism via `task` tool
- ✅ Virtual filesystem for artifact management
- ❌ **No explicit workflow stage tracking in state**
- ❌ **No completion criteria for stages**
- ❌ **No resume capability for interrupted workflows**

---

## Current Architecture

### 1. Workflow Definition (Orchestrator Instructions)

The orchestrator defines 6 sequential stages:

```
1. Author Profiling (Biographer)
   → Output: author_profile.json

2. Audience Definition (Empath)
   → Output: audience_persona.json

3. Book Planning (Planner)
   → Output: book_title.json, chapter_X_plan.json

4. Transcript Ingestion & Gap Analysis
   → Output: chapter_X_transcript.txt, chapter_X_gaps.json

5. HITL Clarification
   → Output: chapter_X_clarifications.json

6. Chapter Drafting (Writer)
   → Output: chapter_X_draft.md (saved to database)
```

### 2. Agent Delegation Mechanism

**How Sub-agents are Invoked**:

```python
# Orchestrator uses the `task` tool provided by SubAgentMiddleware
# Example from instructions:
"Use `task` tool to call the biographer sub-agent"
```

**Task Tool Format**:
```typescript
task(
  description: "Detailed task description for sub-agent",
  subagent_type: "biographer" | "empath" | "planner" | "writer"
)
```

**Available Sub-agents** (loaded from database):
- `biographer` - Captures author profile and writing style
- `empath` - Creates target audience persona
- `planner` - Brainstorms titles, structures chapters
- `writer` - Synthesizes transcripts into polished drafts

### 3. State Management

**Current State Schema** (from deepagents):
```python
class DeepAgentState(AgentState):
    todos: NotRequired[list[Todo]]  # Task tracking
    files: NotRequired[dict[str, str]]  # Virtual filesystem
    # ❌ Missing: current_stage, workflow_progress
```

**What's Tracked**:
- ✅ Messages (via LangGraph checkpointer)
- ✅ Todos (via `write_todos` tool)
- ✅ Files (via virtual filesystem)

**What's NOT Tracked**:
- ❌ Current workflow stage (profiling, audience, planning, etc.)
- ❌ Completed stages
- ❌ Active chapter number
- ❌ Overall workflow progress

### 4. Transition Logic Analysis

**How Transitions Currently Work**:

```yaml
Implicit Inference from Filesystem:
  - Orchestrator checks if author_profile.json exists
  - If yes → assumes profiling complete → moves to audience
  - If audience_persona.json exists → moves to planning
  - etc.

Problem: No explicit state, just file existence checks
```

**Example Transition Flow**:
```
User: "Hi, I want to write a book"

Orchestrator thinks:
1. Check files: author_profile.json exists? NO
2. Conclusion: Must be stage 1 (profiling)
3. Action: Call task(subagent_type="biographer")
4. Biographer creates author_profile.json
5. Orchestrator sees file → infers profiling complete
6. Moves to stage 2 (audience)
```

---

## Identified Issues

### Issue 1: No Explicit Stage Tracking

**Problem**: Workflow stage is inferred from filesystem contents, not explicitly tracked.

**Impact**:
- Difficulty resuming conversations after interruption
- No way to show user "You are at step 3 of 6"
- Potential for confusion if files are missing
- Hard to implement "skip to stage X" functionality

**Example Scenario**:
```
1. User completes profiling and audience definition
2. Browser crashes or session times out
3. User returns: "Where were we?"
4. Orchestrator has to scan files to figure out current stage
5. Risk of repeating stages or missing steps
```

### Issue 2: No Completion Criteria

**Problem**: No explicit validation that a stage is complete.

**Impact**:
- Stage might be marked complete even if output is invalid
- No quality gates between stages
- Difficult to implement "redo stage X" functionality

**Example**:
```python
# Current approach:
if "author_profile.json" in files:
    # Assume profiling complete, but:
    # - Is the profile comprehensive?
    # - Did user approve it?
    # - Does it have all required fields?
```

### Issue 3: No Multi-Chapter Management

**Problem**: Instructions mention "for each chapter" but no state tracks which chapters are complete.

**Impact**:
- Hard to know which chapters need transcripts
- No chapter-level progress tracking
- Difficult to work on multiple chapters in parallel

### Issue 4: Limited Resume Capability

**Problem**: If conversation is interrupted mid-stage, hard to resume intelligently.

**Current Behavior**:
```
User: "I want to continue working on Chapter 3"
Orchestrator: *Scans files, guesses we're at transcript stage*
Risk: Might repeat gap analysis or skip clarifications
```

**Desired Behavior**:
```
User: "I want to continue working on Chapter 3"
Orchestrator: "I see you've completed gap analysis for Chapter 3.
You still need to provide clarifications for these topics: [list]"
```

---

## Transition Decision Tree (Current Implementation)

```
Start
  │
  ├─ author_profile.json exists?
  │   ├─ NO → Stage 1: Call biographer
  │   └─ YES ┐
  │          │
  ├─ audience_persona.json exists?
  │   ├─ NO → Stage 2: Call empath
  │   └─ YES ┐
  │          │
  ├─ book_title.json exists?
  │   ├─ NO → Stage 3: Call planner
  │   └─ YES ┐
  │          │
  ├─ User provides transcript?
  │   ├─ YES → Stage 4: Run gap_analysis
  │   └─ NO → Wait for user input
  │          │
  ├─ Missing topics exist?
  │   ├─ YES → Stage 5: Ask clarifications
  │   └─ NO ┐
  │         │
  └─ All clarified?
      └─ YES → Stage 6: Call writer → Save to database
```

**Analysis**: Decision tree relies on **file existence**, not explicit state.

---

## Recommendations

### 🔴 Critical: Add Workflow State Tracking

**Extend State Schema**:
```python
class Talk2PublishState(DeepAgentState):
    """Extended state for Talk2Publish workflow."""

    # Workflow tracking
    current_stage: Literal[
        "welcome",
        "profiling",
        "audience",
        "planning",
        "transcript",
        "clarification",
        "drafting",
        "complete"
    ]

    completed_stages: list[str]

    # Chapter tracking
    current_chapter: Optional[int]
    total_chapters: Optional[int]
    chapter_status: dict[int, Literal[
        "planned",
        "transcript_uploaded",
        "gaps_analyzed",
        "clarified",
        "drafted",
        "complete"
    ]]

    # Project metadata
    project_id: Optional[str]
    book_title: Optional[str]
```

**Usage Example**:
```python
# In orchestrator logic
if state["current_stage"] == "profiling":
    # Call biographer
    # On completion:
    state["current_stage"] = "audience"
    state["completed_stages"].append("profiling")
```

### 🟡 Important: Add Stage Completion Validation

**Create Validation Tools**:
```python
@tool
def validate_stage_completion(
    stage: str,
    state: Annotated[FilesystemState, InjectedState]
) -> dict:
    """Validate that a workflow stage is complete."""

    validators = {
        "profiling": check_author_profile_complete,
        "audience": check_audience_persona_complete,
        "planning": check_book_plan_complete,
        # ...
    }

    is_valid = validators[stage](state["files"])

    return {
        "stage": stage,
        "complete": is_valid,
        "issues": [] if is_valid else ["Missing X", "Invalid Y"]
    }
```

### 🟡 Important: Implement Resume Logic

**Add to Orchestrator Instructions**:
```
**Resuming Conversations:**
When a user returns to an existing thread:
1. Check `current_stage` in state
2. Check `completed_stages` to show progress
3. Validate current stage completion
4. Offer to continue or review previous work
5. Show clear next steps
```

**Example User Experience**:
```
User: "Hi, I'm back"

Orchestrator: "Welcome back! You've completed:
✅ Author Profiling
✅ Audience Definition
✅ Book Planning (5 chapters outlined)

📍 Current Status: Chapter 1 - Waiting for transcript
Next: Upload your recording transcript for Chapter 1, and I'll analyze it."
```

### 🟢 Enhancement: Add Progress Indicators

**Tool for Progress Display**:
```python
@tool
def get_workflow_progress(
    state: Annotated[Talk2PublishState, InjectedState]
) -> dict:
    """Get current workflow progress for display."""

    return {
        "current_stage": state["current_stage"],
        "progress_percentage": calculate_progress(state),
        "completed_stages": state["completed_stages"],
        "next_action": get_next_action(state),
        "chapter_progress": {
            "current": state["current_chapter"],
            "total": state["total_chapters"],
            "statuses": state["chapter_status"]
        }
    }
```

### 🟢 Enhancement: Add Explicit Transition Guards

**Pattern**:
```python
def can_transition_to(target_stage: str, state: Talk2PublishState) -> bool:
    """Check if transition to target stage is allowed."""

    prerequisites = {
        "audience": ["profiling"],
        "planning": ["profiling", "audience"],
        "transcript": ["planning"],
        "clarification": ["transcript"],
        "drafting": ["clarification"],
    }

    required = prerequisites.get(target_stage, [])
    return all(stage in state["completed_stages"] for stage in required)
```

---

## Testing Recommendations

### Test Scenario 1: Sequential Happy Path
```
1. Start new conversation
2. Complete profiling → verify transition to audience
3. Complete audience → verify transition to planning
4. Complete planning → verify transition to transcript
5. Upload transcript → verify gap analysis runs
6. Provide clarifications → verify drafting starts
7. Verify chapter saved to database
```

### Test Scenario 2: Interrupted Workflow
```
1. Complete profiling and audience
2. Start planning
3. Disconnect mid-planning
4. Reconnect → verify orchestrator knows we're at planning stage
5. Complete planning → verify no stages are repeated
```

### Test Scenario 3: Multi-Chapter Management
```
1. Create plan with 3 chapters
2. Upload transcript for Chapter 1
3. While Chapter 1 is being clarified, upload transcript for Chapter 2
4. Verify orchestrator can track both chapters independently
5. Complete Chapter 1 drafting
6. Verify Chapter 2 can proceed in parallel
```

### Test Scenario 4: Error Recovery
```
1. Complete profiling with incomplete data
2. Move to audience stage
3. User realizes profile is wrong
4. Request to redo profiling
5. Verify orchestrator can rollback to profiling stage
6. Verify new profile replaces old one
```

---

## Implementation Priority

### Phase 1: Critical (Before Production)
- [ ] Add `current_stage` to state
- [ ] Add `completed_stages` tracking
- [ ] Update orchestrator instructions to set stage on transitions
- [ ] Add resume logic to handle returning users

### Phase 2: Important (Before Beta)
- [ ] Add chapter-level status tracking
- [ ] Implement stage validation tools
- [ ] Add progress display tool
- [ ] Update frontend to show progress

### Phase 3: Enhancement (Post-Launch)
- [ ] Add rollback/redo functionality
- [ ] Implement parallel chapter processing
- [ ] Add workflow analytics and insights
- [ ] Support custom workflow paths

---

## Code Examples

### Implementation: Extended State

**File**: `apps/api/src/agents/state.py`
```python
"""Extended state schema for Talk2Publish workflow."""

from typing import Literal, Optional, NotRequired
from typing_extensions import TypedDict
from deepagents.state import DeepAgentState

WorkflowStage = Literal[
    "welcome",
    "profiling",
    "audience",
    "planning",
    "transcript",
    "clarification",
    "drafting",
    "complete"
]

ChapterStatus = Literal[
    "planned",
    "transcript_uploaded",
    "gaps_analyzed",
    "clarified",
    "drafted",
    "complete"
]

class Talk2PublishState(DeepAgentState):
    """State schema for Talk2Publish orchestrator."""

    # Workflow tracking
    current_stage: NotRequired[WorkflowStage]
    completed_stages: NotRequired[list[str]]

    # Chapter tracking
    current_chapter: NotRequired[Optional[int]]
    total_chapters: NotRequired[Optional[int]]
    chapter_status: NotRequired[dict[str, ChapterStatus]]

    # Project metadata
    project_id: NotRequired[Optional[str]]
    book_title: NotRequired[Optional[str]]
```

### Implementation: State Transition Tool

**File**: `apps/api/src/tools/workflow.py`
```python
"""Workflow management tools."""

from typing import Annotated
from langchain_core.tools import tool
from langchain.tools.tool_node import InjectedState
from ..agents.state import Talk2PublishState, WorkflowStage

@tool
def transition_to_stage(
    target_stage: WorkflowStage,
    state: Annotated[Talk2PublishState, InjectedState]
) -> dict:
    """Transition workflow to a new stage.

    Args:
        target_stage: The stage to transition to
        state: Injected state

    Returns:
        dict with success status and updated stage info
    """
    current = state.get("current_stage", "welcome")
    completed = state.get("completed_stages", [])

    # Validate transition
    prerequisites = {
        "audience": ["profiling"],
        "planning": ["profiling", "audience"],
        "transcript": ["planning"],
        "clarification": ["transcript"],
        "drafting": ["clarification"],
    }

    required = prerequisites.get(target_stage, [])
    can_transition = all(s in completed for s in required)

    if not can_transition:
        return {
            "success": False,
            "error": f"Cannot transition to {target_stage}. Required: {required}",
            "current_stage": current
        }

    # Mark previous stage as complete
    if current != "welcome" and current not in completed:
        completed.append(current)

    # Update state
    state["current_stage"] = target_stage
    state["completed_stages"] = completed

    return {
        "success": True,
        "previous_stage": current,
        "current_stage": target_stage,
        "completed_stages": completed,
        "progress": f"{len(completed)}/6 stages complete"
    }
```

---

## Conclusion

**Current State**: The orchestrator has well-designed workflow instructions but lacks explicit state management for stage tracking. Transitions work via implicit inference from filesystem contents.

**Risk Level**: 🟡 **Medium** - Works for simple happy-path scenarios but will have issues with:
- Interrupted workflows
- Multi-chapter management
- User needing to redo stages
- Showing progress to users

**Recommendation**: Implement Phase 1 changes before production deployment to ensure robust workflow management and better user experience.

**Estimated Effort**:
- Phase 1 (Critical): 4-6 hours development + 2 hours testing
- Phase 2 (Important): 6-8 hours development + 3 hours testing
- Phase 3 (Enhancement): 8-12 hours development + 4 hours testing

---

**Analyzed by**: Claude (Sonnet 4.5)
**Review Status**: Ready for implementation planning

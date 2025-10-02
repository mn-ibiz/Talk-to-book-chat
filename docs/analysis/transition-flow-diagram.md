# Agent Transition Flow Diagrams

## Current Implementation (Implicit State Tracking)

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR START                            │
│                                                                  │
│  State: { messages, todos, files }                              │
│  ❌ No current_stage tracking                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │   Check Virtual Filesystem         │
        │   author_profile.json exists?      │
        └────────┬───────────────────┬────────┘
                NO                  YES
                 │                   │
                 ▼                   ▼
        ┌─────────────────┐   ┌─────────────────────┐
        │  STAGE 1        │   │  Check Next File    │
        │  Profiling      │   │  audience_persona   │
        │  (Biographer)   │   │  .json exists?      │
        └────────┬────────┘   └──┬──────────────┬───┘
                 │              NO             YES
                 │               │              │
                 ▼               ▼              ▼
        ┌─────────────────┐  ┌──────────┐  ┌──────────┐
        │ Call task() →   │  │ STAGE 2  │  │ Check    │
        │ biographer      │  │ Audience │  │ Next...  │
        │                 │  │ (Empath) │  │          │
        └────────┬────────┘  └────┬─────┘  └────┬─────┘
                 │                │              │
                 ▼                ▼              ▼
        ┌─────────────────┐  ┌──────────┐       ...
        │ Biographer      │  │ Call     │
        │ saves           │  │ empath   │
        │ author_profile  │  │          │
        │ .json to files  │  └──────────┘
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────────────────────┐
        │ ❌ PROBLEM:                      │
        │ No explicit stage transition    │
        │ Just inferred from file system  │
        │ On reconnect: must re-scan      │
        └─────────────────────────────────┘
```

## Issues with Current Flow

### Problem 1: File-Based Inference
```
Scenario: User Profile Incomplete

Current Flow:
  User completes profiling (partial data)
  → author_profile.json created
  → Orchestrator sees file exists
  → Assumes profiling complete ✅
  → Moves to audience stage
  → ❌ Profile was actually incomplete!

Better Flow (with validation):
  User completes profiling
  → author_profile.json created
  → Orchestrator validates profile
  → ❌ Missing expertise field
  → Stay in profiling stage
  → Request missing information
```

### Problem 2: Resume Confusion
```
Scenario: Browser Crash Mid-Planning

Current Flow:
  Session State:
    files: {
      "author_profile.json": "...",
      "audience_persona.json": "...",
      // Planning was interrupted!
    }

  User reconnects: "Where were we?"

  Orchestrator scans files:
    ✅ author_profile.json exists
    ✅ audience_persona.json exists
    ❌ book_title.json missing

  Conclusion: "We're at planning stage"
  ❌ But was planning started or not?
  ❌ Were chapters partially planned?
  ❌ What was the last user message?

Better Flow (with explicit state):
  Session State:
    current_stage: "planning"
    completed_stages: ["profiling", "audience"]
    planning_progress: {
      titles_generated: true,
      chapters_outlined: false,
      prompts_created: false
    }

  Orchestrator knows exactly where we are!
  ✅ "You were outlining chapters. Want to continue?"
```

### Problem 3: Multi-Chapter Chaos
```
Scenario: Working on Multiple Chapters

Current Flow:
  files: {
    "chapter_1_transcript.txt": "...",
    "chapter_1_gaps.json": "...",
    "chapter_2_transcript.txt": "...",
    // What about chapter_2_gaps.json?
  }

  ❌ Which chapter are we working on?
  ❌ Which chapters need clarifications?
  ❌ Can we draft Chapter 1 while Chapter 2 is in gap analysis?

Better Flow (with chapter tracking):
  chapter_status: {
    1: "clarified",     // Ready for drafting
    2: "gaps_analyzed", // Needs clarification
    3: "planned"        // Waiting for transcript
  }
  current_chapter: 1

  ✅ Crystal clear what to do next
```

---

## Proposed Implementation (Explicit State Tracking)

```
┌──────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR START                             │
│                                                                   │
│  State: {                                                         │
│    current_stage: "welcome",                                      │
│    completed_stages: [],                                          │
│    chapter_status: {},                                            │
│    files: {}                                                      │
│  }                                                                │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
        ┌─────────────────────────────────────┐
        │   Read current_stage from state     │
        │   (Not inferred from files!)        │
        └────────┬────────────────────────────┘
                 │
                 ▼
        ┌─────────────────────┐
        │ current_stage ==    │
        │ "profiling" ?       │
        └──┬──────────────┬───┘
          YES             NO
           │              │
           ▼              ▼
    ┌──────────────┐   ┌────────────────┐
    │ STAGE 1      │   │ Check other    │
    │ Profiling    │   │ stages...      │
    └──────┬───────┘   └────────────────┘
           │
           ▼
    ┌──────────────────────────┐
    │ Call task(biographer)    │
    └──────┬───────────────────┘
           │
           ▼
    ┌──────────────────────────┐
    │ Biographer completes     │
    │ Saves author_profile.json│
    └──────┬───────────────────┘
           │
           ▼
    ┌──────────────────────────────────┐
    │ ✅ Validate Completion:          │
    │ - Check required fields          │
    │ - Verify data quality            │
    │ - User confirmation (optional)   │
    └──────┬────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────┐
    │ ✅ Explicit State Transition:    │
    │ state["current_stage"] = "audience"│
    │ state["completed_stages"].append(│
    │   "profiling"                     │
    │ )                                 │
    └──────┬────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────┐
    │ Next conversation turn:          │
    │ Orchestrator reads state         │
    │ Sees current_stage = "audience"  │
    │ → Calls empath automatically     │
    └──────────────────────────────────┘
```

---

## State Transition Flow with Validation

```
┌─────────────┐
│   STAGE N   │
│  (Current)  │
└──────┬──────┘
       │
       ▼
┌──────────────────────┐
│ Execute Stage Logic  │
│ (Call sub-agent)     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Validate Stage Completion    │
│ - Required artifacts present?│
│ - Data quality checks pass?  │
│ - User approval (if needed)? │
└──────┬───────────────────────┘
       │
       ├─────────────┐
       NO           YES
       │             │
       ▼             ▼
┌──────────────┐  ┌────────────────────────┐
│ Request      │  │ Update State:          │
│ Additional   │  │ 1. completed_stages.   │
│ Info or      │  │    append(current)     │
│ Corrections  │  │ 2. current_stage =     │
│              │  │    next_stage          │
└──────────────┘  └────────┬───────────────┘
                           │
                           ▼
                  ┌────────────────────┐
                  │  STAGE N+1         │
                  │  (Next)            │
                  └────────────────────┘
```

---

## Chapter-Level State Machine

```
                    ┌─────────────┐
                    │  "planned"  │
                    │ (Chapter in │
                    │  outline)   │
                    └──────┬──────┘
                           │
                    User uploads transcript
                           │
                           ▼
              ┌────────────────────────┐
              │ "transcript_uploaded"  │
              └──────┬─────────────────┘
                     │
              Run gap_analysis tool
                     │
                     ▼
              ┌──────────────────┐
              │ "gaps_analyzed"  │
              └──────┬───────────┘
                     │
              User provides clarifications
                     │
                     ▼
              ┌──────────────┐
              │ "clarified"  │
              └──────┬───────┘
                     │
              Call writer sub-agent
                     │
                     ▼
              ┌──────────────┐
              │  "drafted"   │
              └──────┬───────┘
                     │
              Save to database
                     │
                     ▼
              ┌──────────────┐
              │  "complete"  │
              └──────────────┘
```

**Key Benefit**: Each chapter has independent state, allowing:
- Parallel processing of multiple chapters
- Clear progress tracking per chapter
- Resume capability at chapter level

---

## Comparison Table

| Feature | Current (Implicit) | Proposed (Explicit) |
|---------|-------------------|---------------------|
| **Stage Tracking** | Inferred from files ❌ | Stored in state ✅ |
| **Completion Validation** | File exists check ❌ | Validation tools ✅ |
| **Resume Capability** | Must re-scan files ❌ | Read from state ✅ |
| **Progress Display** | Not available ❌ | Built-in ✅ |
| **Multi-Chapter** | Unclear ❌ | Explicit status ✅ |
| **Rollback Support** | Very difficult ❌ | Straightforward ✅ |
| **Parallel Processing** | Not possible ❌ | Supported ✅ |

---

## Example State Evolution

### Scenario: Complete Workflow for 2 Chapters

```python
# Initial state
{
  "current_stage": "welcome",
  "completed_stages": [],
  "chapter_status": {}
}

# After profiling
{
  "current_stage": "audience",
  "completed_stages": ["profiling"],
  "files": {"author_profile.json": "..."}
}

# After planning (2 chapters outlined)
{
  "current_stage": "transcript",
  "completed_stages": ["profiling", "audience", "planning"],
  "total_chapters": 2,
  "current_chapter": 1,
  "chapter_status": {
    "1": "planned",
    "2": "planned"
  },
  "files": {
    "author_profile.json": "...",
    "audience_persona.json": "...",
    "book_title.json": "...",
    "chapter_1_plan.json": "...",
    "chapter_2_plan.json": "..."
  }
}

# After uploading Chapter 1 transcript
{
  "current_stage": "transcript",
  "current_chapter": 1,
  "chapter_status": {
    "1": "transcript_uploaded",  # ← Changed
    "2": "planned"
  },
  "files": {
    ...,
    "chapter_1_transcript.txt": "..."
  }
}

# After gap analysis for Chapter 1
{
  "current_stage": "clarification",  # ← Stage changed
  "current_chapter": 1,
  "chapter_status": {
    "1": "gaps_analyzed",  # ← Changed
    "2": "planned"
  },
  "files": {
    ...,
    "chapter_1_gaps.json": "..."
  }
}

# User provides clarifications
{
  "current_stage": "drafting",
  "current_chapter": 1,
  "chapter_status": {
    "1": "clarified",  # ← Ready for drafting
    "2": "planned"
  },
  "files": {
    ...,
    "chapter_1_clarifications.json": "..."
  }
}

# After drafting Chapter 1
{
  "current_stage": "transcript",  # Back to transcript stage
  "current_chapter": 2,  # Now working on Chapter 2
  "chapter_status": {
    "1": "complete",  # ✅
    "2": "planned"    # Next up
  }
}
```

---

## Visual: Current vs Proposed Decision Making

### Current (File-Based)
```
Question: "What stage are we at?"

Orchestrator thinks:
1. Scan virtual filesystem
2. Check file existence
3. Guess stage based on files
4. Might be wrong if files deleted/corrupted
5. No confidence level
```

### Proposed (State-Based)
```
Question: "What stage are we at?"

Orchestrator thinks:
1. Read state["current_stage"]
2. Immediate answer: "clarification"
3. 100% confidence
4. Also knows: completed_stages, chapter_status
5. Can show progress: "3/6 stages complete, Chapter 1 of 3"
```

---

**Key Takeaway**: Explicit state tracking transforms workflow management from **guesswork** to **certainty**.

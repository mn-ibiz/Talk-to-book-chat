# **Talk2Publish Product Requirements Document (PRD)**

### **Goals and Background Context**

#### **Goals**

* Successfully execute the full planning workflow, including author profiling, audience definition, title brainstorming, and chapter planning, to produce a structured book outline.  
* Successfully execute the drafting workflow for a single chapter by ingesting a transcript, performing a human-in-the-loop (HITL) gap analysis, and generating a coherent first draft.  
* Build the entire workflow on the "Deep Agent" LangGraph framework, demonstrating successful orchestration of sub-agents and artifact management.

#### **Background Context**

Many knowledgeable professionals aspire to write a book but are paralyzed by the "blank page," struggling to translate their spoken expertise into written form. Existing solutions are often too difficult, requiring non-writers to become writers, or too automated, producing generic content that lacks the author's authentic voice.

This project addresses that gap by creating an AI-powered ghostwriting partner. It leverages a collaborative process where the user first plans their book with an AI agent team and then provides their knowledge for each chapter by simply talking. The AI then intelligently processes this information to produce a high-quality first draft that captures the author's unique insights and style.

#### **Change Log**

| Date | Version | Description | Author |
| :---- | :---- | :---- | :---- |
| 2025-10-01 | 1.0 | Initial PRD draft created from Project Brief. | John (PM) |
| 2025-10-01 | 1.1 | Added NFRs for version control and parallel development. | John (PM) |
| 2025-10-01 | 1.2 | Added User Interface Design Goals section. | John (PM) |
| 2025-10-01 | 1.3 | Added Post-MVP Vision section. | John (PM) |
| 2025-10-01 | 1.4 | Added Technical Assumptions section. | John (PM) |
| 2025-10-01 | 1.5 | Added detailed Epic and Story breakdown. | John (PM) |
| 2025-10-01 | 1.6 | Appended PM Checklist validation and Next Steps. | John (PM) |
| 2025-10-02 | 1.7 | Updated with deepagents framework implementation details. | John (PM) |

### **Requirements**

#### **Functional**

1. **FR1:** The system shall be managed by a central Orchestration Agent responsible for the end-to-end user workflow.  
2. **FR2:** The Orchestration Agent must enforce a strict initial sequence, completing Author Profiling (FR3) before Audience Definition (FR4).  
3. **FR3:** The system shall provide a "Biographer" sub-agent to interactively capture the user's author profile and preferred writing style.  
4. **FR4:** The system shall provide an "Empath" sub-agent to guide the user in defining a persona for their target audience.  
5. **FR5:** The system shall facilitate an interactive brainstorming session to generate and select a book title and subtitle.  
6. **FR6:** The system shall guide the user through planning the book's chapters and the key topics to be covered in each.  
7. **FR7:** The system must generate two distinct artifacts upon completion of the planning phase: a structured book outline and a set of chapter-specific recording prompts for the user.  
8. **FR8:** The system must provide a mechanism to ingest a plain text transcript for a single chapter.  
9. **FR9:** The system shall perform an automated gap analysis by comparing the ingested transcript against the pre-defined chapter plan.  
10. **FR10:** The system shall conduct a human-in-the-loop (HITL) clarification session via a chat interface to resolve discrepancies found during the gap analysis.  
11. **FR11:** The system shall generate a coherent, well-structured first draft of a chapter by synthesizing the plan, transcript, and HITL responses.

#### **Non Functional**

1. **NFR1:** The entire backend, including all agent logic, must be developed in Python.
2. **NFR2:** The agent architecture must be built using the `deepagents` Python package, which is built on LangGraph and provides deep agent orchestration patterns.
3. **NFR3:** All persistent data must be stored in a Neon PostgreSQL database.
4. **NFR4:** The final application must be deployable on the Railway platform.
5. **NFR5:** The agent system must manage all session artifacts (user answers, generated content, etc.) within a virtual file system using the deepagents built-in filesystem middleware. Files are stored in state as `dict[str, str]` and passed/retrieved via the `files` key.
6. **NFR6:** For the MVP, the system does not need to handle excessively long transcripts; performance and processing limits for large inputs are out of scope.
7. **NFR7:** The project's source code must be managed in a GitHub repository.
8. **NFR8:** The architecture should support parallel development of different sections or features, potentially using a tool like Sitetrees to manage the structure.
9. **NFR9:** The system must use a LangGraph checkpointer (MemorySaver for development, persistent storage for production) to enable state persistence across conversation turns and human-in-the-loop interactions.
10. **NFR10:** The default language model must be Claude Sonnet 4 (`claude-sonnet-4-20250514`) as specified by the deepagents framework, with support for per-subagent model overrides.
11. **NFR11:** Built-in tools from deepagents (`write_todos`, `ls`, `read_file`, `write_file`, `edit_file`, `task`) must be available to all agents automatically via the framework's middleware stack.

### **User Interface Design Goals**

#### **Overall UX Vision**

The user experience will be purely conversational, presented within a chat interface similar to ChatGPT, Claude, or the one we are using now. The UX vision is to make the complex process of writing a book feel like a guided, collaborative conversation with a friendly and expert team. The user should feel empowered and supported, never overwhelmed.

#### **Key Interaction Paradigms**

The primary interaction model is a turn-based chat. The Orchestration Agent will guide the user through the workflow, asking questions, presenting information, and requesting input at each stage. Human-in-the-loop (HITL) clarifications will also occur within this same chat interface, maintaining a seamless conversational flow.

#### **Core Screens and Views**

As an API, the "screens" are conceptual states within the single chat interface, managed by the Orchestration Agent. These states include:

* Welcome & Onboarding  
* Author Profiling ("Biographer" active)  
* Audience Definition ("Empath" active)  
* Title Brainstorming  
* Chapter Planning  
* Gap Analysis & HITL Clarification  
* Draft Review

#### **Accessibility**

*Assumption:* The chat interface provided by the parent SaaS application should adhere to **WCAG 2.1 AA** standards to ensure the experience is accessible to all users. The API's responses will be text-based and inherently accessible.

#### **Branding**

*Assumption:* All branding, including colors, fonts, and agent personas, will be determined and implemented by the parent SaaS application that consumes this API.

#### **Target Device and Platforms**

The API itself is platform-agnostic. *Assumption:* It will be consumed by a responsive web application, making the user experience accessible across desktop, tablet, and mobile devices.

### **Post-MVP Vision**

#### **Phase II: Enhanced User Interface and Knowledge Consistency**

* **Generative UI Integration:** In Phase II, the user experience will be enhanced by integrating the **Copilot Kit Generative UI** system. This will introduce a "note panel" alongside the chat interface. This panel will display the artifacts of the conversation (e.g., the outline, character notes) in real-time.  
* **Real-Time State Sharing:** The Copilot Kit will enable two-way state sharing. Updates made by the AI agent in the chat will instantly reflect in the note panel, and any user edits in the panel's editable fields will be immediately known by the agent, creating a seamless, interactive workspace.  
* **Book-Wide Knowledge Base:** To ensure cross-chapter consistency, a Retrieval-Augmented Generation (RAG) database and/or a knowledge graph will be implemented. This will allow agents to access the content of all previously written chapters to avoid repetition and maintain a consistent voice and narrative.

### **Technical Assumptions**

#### **Repository Structure: Monorepo**

A **Monorepo** structure is recommended. This approach will house the Talk2Publish API and the parent SaaS application in a single repository. This is advantageous for managing shared code, types, and potentially the Copilot Kit UI components in the future, simplifying dependencies and ensuring consistency.

#### **Service Architecture**

The architecture will be a **Monolithic Service with an Agent-based internal design**. The Python application will act as a single deployable unit. Internally, it will be highly modular, with the LangGraph framework orchestrating the various sub-agents (Biographer, Empath, etc.) to perform their specialized tasks.

#### **Testing Requirements: Unit \+ Integration**

The testing strategy will focus on a combination of **Unit and Integration tests**. Unit tests will verify the logic within individual agents and functions. Integration tests will validate the handoffs and communication between agents within the LangGraph framework and ensure correct database interactions.

#### **Additional Technical Assumptions and Requests**

* **Backend Language:** Python
* **Agent Framework:** `deepagents` Python package (built on LangGraph)
* **Database:** Neon PostgreSQL (with pgvector for Phase II)
* **Deployment Platform:** Railway
* **Version Control:** GitHub
* **Data Flow (MVP):** The Python API will handle all read and write operations to the database.
* **Dynamic Prompts:** Agent system prompts will be designed to be stored in the Neon database, allowing for easy updates and modifications without requiring a full application redeployment.
* **State Management:** LangGraph checkpointer for conversation persistence and HITL support
* **Built-in Tools:** `write_todos`, `ls`, `read_file`, `write_file`, `edit_file`, `task` (provided by deepagents middleware)
* **Virtual Filesystem:** In-state file storage via deepagents (`files` dict in state)

### **Epic 1: MVP End-to-End Workflow**

**Epic Goal:** To establish the complete, end-to-end agent-driven workflow, from initial project setup and user planning to the successful generation of a single, high-quality chapter draft. This epic will deliver a functional proof-of-concept of the core Talk2Publish engine.

#### **Story 1.1: Project Foundation & Orchestrator Setup**

As a Developer,  
I want a foundational project structure set up with the core Orchestration Agent,  
so that I have a stable, testable starting point for building the agent workflow.  
**Acceptance Criteria:**

1. The project repository is initialized on GitHub according to the Monorepo structure.  
2. A basic Python project is created, including dependency management and configuration files.  
3. LangGraph, the Neon DB connector, and other core dependencies are installed.  
4. A "health check" API endpoint is created and successfully deployed to Railway to validate the CI/CD pipeline.  
5. The foundational Orchestration Agent is implemented, capable of starting the workflow, maintaining state, and transitioning between at least two placeholder sub-agents.  
6. The test suite (Unit \+ Integration) is set up, with a basic passing test for the Orchestrator's initial state.

#### **Story 1.2: Implement Author Profiling ("Biographer") Agent**

As an Author,  
I want to be guided through a conversation to define my author profile,  
so that the AI understands my background and preferred writing style.  
**Acceptance Criteria:**

1. The Orchestration Agent can successfully call and transition to a "Biographer" sub-agent.  
2. The Biographer agent asks a predefined series of questions to capture the author's expertise, desired tone of voice, and writing style.  
3. The user's answers are successfully saved to the agent's virtual file system during the session.  
4. Upon completion, the Biographer agent transitions control back to the Orchestrator.  
5. The final, consolidated author profile is saved as a structured object or document in the Neon database.

#### **Story 1.3: Implement Audience Definition ("Empath") Agent**

As an Author,  
I want to be guided in creating a persona for my target audience,  
so that the book is written with a specific reader in mind.  
**Acceptance Criteria:**

1. The Orchestration Agent can successfully transition to the "Empath" sub-agent after the Author Profiling step is complete.  
2. The Empath agent asks a predefined series of questions to build an audience persona (e.g., demographics, problems, goals).  
3. The user's answers are saved to the virtual file system.  
4. Upon completion, the Empath agent transitions control back to the Orchestrator.  
5. The final audience persona is saved as a structured object in the Neon database.

#### **Story 1.4: Implement Title Brainstorming & Selection**

As an Author,  
I want to collaborate with the AI to brainstorm and select a compelling title and subtitle,  
so that my book effectively captures its core message.  
**Acceptance Criteria:**

1. The Orchestration Agent can initiate a brainstorming session for the book's title.  
2. The agent generates at least five distinct title and subtitle options based on the previously captured author profile and audience persona.  
3. The user can select one of the provided options or request a new set of suggestions.  
4. The final selected title and subtitle are saved to the Neon database.

#### **Story 1.5: Implement Chapter & Content Planning**

As an Author,  
I want the AI to help me structure my book by planning out the chapters and their key talking points,  
so that I have a clear roadmap for my content.  
**Acceptance Criteria:**

1. The Orchestration Agent can initiate a chapter planning session.  
2. The agent interactively works with the user to create an ordered list of chapter titles.  
3. For each chapter, the agent guides the user to define 3-5 key topics or questions that should be covered.  
4. The complete chapter plan (titles and key topics) is saved as a structured object in the Neon database.

#### **Story 1.6: Implement Outline & Recording Prompt Generation**

As an Author,  
I want to receive a consolidated book outline and a clear set of recording prompts,  
so that I know exactly what to talk about for each chapter.  
**Acceptance Criteria:**

1. The Orchestration Agent can trigger the generation of the final planning artifacts after the planning phase is complete.  
2. The system generates a clean, well-formatted book outline in Markdown based on the saved chapter plan.  
3. The system generates a separate, user-friendly set of recording prompts, instructing the user on what to discuss for each chapter.  
4. Both artifacts are saved to the agent's virtual file system and presented back to the user via the chat interface.

#### **Story 1.7: Implement Transcript Ingestion & Gap Analysis**

As a System,  
I need to ingest a user's text transcript and automatically compare it against the chapter plan,  
so that I can identify any discrepancies for clarification.  
**Acceptance Criteria:**

1. An API endpoint is available that accepts a plain text payload and a chapter identifier.  
2. On receiving a transcript, the Orchestration Agent retrieves the correct chapter plan from the Neon database.  
3. The agent performs a gap analysis, identifying key topics from the plan that are missing from the transcript.  
4. The agent also identifies new, unplanned topics that were introduced by the user in the transcript.  
5. The list of missing topics and new topics is stored in the virtual file system, ready for the HITL step.

#### **Story 1.8: Implement Human-in-the-Loop (HITL) Clarification**

As an Author,  
I want the AI to ask me clarifying questions about my recorded content,  
so that it has all the information it needs to write a great draft.  
**Acceptance Criteria:**

1. Following the gap analysis, the Orchestration Agent initiates a HITL conversational session.  
2. The agent asks the user targeted questions about the topics that were identified as missing or unclear.  
3. The agent asks for the user's decision on whether to incorporate the new, unplanned topics into the chapter.  
4. The user's answers are captured and stored in the virtual file system.  
5. Upon completion, the agent has a complete and verified set of information for the chapter.

#### **Story 1.9: Implement First Draft Generation**

As an Author,  
I want the AI to synthesize our plan and conversations into a well-written first draft of my chapter,  
so that I can move on to editing and refining.  
**Acceptance Criteria:**

1. The Orchestration Agent can trigger the final draft generation process for a completed chapter.  
2. A "Writer" sub-agent is invoked, which synthesizes all available artifacts: the original plan, the transcript, and the HITL clarifications.  
3. The agent generates a coherent, well-structured chapter draft in Markdown format.  
4. The generated draft meets the quality standard of requiring only stylistic edits, not major structural rewrites.  
5. The final draft is saved to the Neon database, stored in the virtual file system, and presented to the user.

### **Checklist Results Report**

#### **PRD & EPIC VALIDATION SUMMARY**

**Executive Summary**

* **Overall PRD completeness:** 100%  
* **MVP scope appropriateness:** Just Right  
* **Readiness for architecture phase:** Ready  
* **Most critical gaps or concerns:** None. The PRD is exceptionally detailed and well-structured.

**Category Analysis Table**

| Category | Status | Critical Issues |
| :---- | :---- | :---- |
| 1\. Problem Definition & Context | PASS | None |
| 2\. MVP Scope Definition | PASS | None |
| 3\. User Experience Requirements | PASS | None |
| 4\. Functional Requirements | PASS | None |
| 5\. Non-Functional Requirements | PASS | None |
| 6\. Epic & Story Structure | PASS | None |
| 7\. Technical Guidance | PASS | None |
| 8\. Cross-Functional Requirements | PASS | None |
| 9\. Clarity & Communication | PASS | None |

**Final Decision:** **READY FOR ARCHITECT**

The PRD and its single epic are comprehensive, properly structured, and provide a clear, actionable plan. The document is ready for the architecture design phase.

### **Next Steps**

#### **Architect Prompt**

"The Product Requirements Document for the Talk2Publish API is complete and located at docs/prd.md. Please use this document as the single source of truth to create the architecture.md document. Pay close attention to the Technical Assumptions and the sequential nature of the stories in Epic 1 to ensure your architecture supports the required workflow and technology stack."
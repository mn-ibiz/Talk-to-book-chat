# Talk2Publish Frontend - AI Generation Prompt

## FOUNDATIONAL CONTEXT

You are building the **frontend chat interface** for **Talk2Publish**, an AI-powered book-writing platform that transforms spoken expertise into written chapters through a conversational workflow.

### Project Purpose
Talk2Publish helps knowledgeable professionals write books without facing the "blank page" paralysis. Users speak their knowledge, and the AI transforms it into well-structured chapter drafts while maintaining their authentic voice.

### Tech Stack
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS with shadcn/ui components
- **State Management**: React hooks + Context API
- **API Communication**: Server-Sent Events (SSE) for streaming
- **Deployment**: Vercel (recommended)

### UI Component Library
- **Primary**: shadcn/ui (https://ui.shadcn.com)
- **Icons**: Lucide React
- **Animations**: Framer Motion (optional)
- **Forms**: React Hook Form + Zod validation

### Visual Style & Branding
- **Aesthetic**: Clean, professional, conversational (ChatGPT-like)
- **Color Palette**:
  - Primary: Indigo/Blue (trust, intelligence)
  - Secondary: Emerald/Green (growth, creativity)
  - Neutral: Slate grays for text and borders
  - Background: White (light mode), Dark slate (dark mode)
- **Typography**:
  - Headings: Inter (700-800 weight)
  - Body: Inter (400-500 weight)
  - Code/Monospace: JetBrains Mono
- **Spacing**: 8px base unit (Tailwind default)
- **Accessibility**: WCAG 2.1 AA compliant

---

## HIGH-LEVEL GOAL

Create a **responsive, mobile-first chat interface** that enables authors to:
1. Start a new book project via conversation
2. Complete guided workflows (profiling, audience, planning, transcript, drafting)
3. View and manage session artifacts (outlines, drafts, transcripts)
4. Experience seamless real-time streaming responses
5. Handle Human-in-the-Loop (HITL) interactions for gap analysis

The interface must feel like ChatGPT/Claude - familiar, conversational, and unintimidating.

---

## DETAILED, STEP-BY-STEP INSTRUCTIONS

### Part 1: Project Setup & Structure

1. **Initialize Next.js Project**
   ```bash
   npx create-next-app@latest talk2publish-frontend --typescript --tailwind --app
   cd talk2publish-frontend
   ```

2. **Install Required Dependencies**
   ```bash
   # UI Components (shadcn/ui)
   npx shadcn-ui@latest init
   npx shadcn-ui@latest add button input textarea card scroll-area separator avatar badge alert

   # Additional Libraries
   npm install lucide-react
   npm install react-markdown remark-gfm
   npm install date-fns
   npm install @tanstack/react-query
   npm install eventsource-parser
   ```

3. **Configure Environment Variables**
   Create `.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_APP_NAME=Talk2Publish
   ```

4. **Setup Directory Structure**
   ```
   app/
   ├── (auth)/
   │   └── login/
   ├── (dashboard)/
   │   ├── chat/[threadId]/
   │   ├── projects/
   │   └── layout.tsx
   ├── api/
   │   └── chat/
   ├── layout.tsx
   └── page.tsx
   components/
   ├── chat/
   │   ├── ChatInterface.tsx
   │   ├── MessageList.tsx
   │   ├── MessageBubble.tsx
   │   ├── ChatInput.tsx
   │   └── StreamingIndicator.tsx
   ├── artifacts/
   │   ├── ArtifactPanel.tsx
   │   └── OutlineView.tsx
   ├── layout/
   │   ├── Sidebar.tsx
   │   └── Header.tsx
   └── ui/ (shadcn components)
   lib/
   ├── api.ts
   ├── sse-client.ts
   └── types.ts
   hooks/
   ├── useChat.ts
   ├── useSSE.ts
   └── useProjects.ts
   ```

### Part 2: Core Chat Interface Components

5. **Create `types.ts` for TypeScript Definitions**
   ```typescript
   // lib/types.ts
   export interface Message {
     id: string;
     role: 'user' | 'assistant' | 'system';
     content: string;
     timestamp: Date;
     metadata?: {
       agent?: string; // biographer, empath, planner, writer
       type?: 'question' | 'response' | 'artifact';
     };
   }

   export interface Thread {
     id: string;
     projectId?: string;
     title: string;
     updatedAt: Date;
     currentStage: 'profiling' | 'audience' | 'planning' | 'transcript' | 'drafting';
   }

   export interface ChatState {
     messages: Message[];
     isStreaming: boolean;
     currentAgent?: string;
     threadId?: string;
   }
   ```

6. **Build `ChatInterface.tsx` - Main Chat Container**
   - Create a flex column layout (h-screen)
   - Top: Header with project title and stage indicator
   - Middle: Scrollable message list (flex-1, overflow-auto)
   - Bottom: Fixed input area
   - Mobile-first: Full screen on mobile, max-w-4xl centered on desktop

7. **Build `MessageList.tsx` - Scrollable Message Container**
   - Use shadcn ScrollArea component
   - Auto-scroll to bottom on new messages
   - Group messages by date with separators
   - Loading skeleton for streaming
   - Accessibility: role="log", aria-live="polite"

8. **Build `MessageBubble.tsx` - Individual Message Component**
   - User messages: Right-aligned, primary color background
   - Assistant messages: Left-aligned, secondary/muted background
   - Show agent name badge for sub-agent messages (biographer, empath, etc.)
   - Support markdown rendering via react-markdown
   - Timestamp tooltip on hover
   - Copy button for assistant responses

9. **Build `ChatInput.tsx` - Message Input Component**
   - Textarea with auto-resize (max 5 rows)
   - Send button (Ctrl/Cmd+Enter to send)
   - Disabled state during streaming
   - Character count (optional)
   - Mobile: Adjust keyboard handling

10. **Build `StreamingIndicator.tsx` - Typing Animation**
    - Animated dots or pulse effect
    - Shows current agent name if available
    - Example: "Biographer is typing..."

### Part 3: API Integration & SSE Streaming

11. **Create `api.ts` - API Client**
    ```typescript
    // lib/api.ts
    const API_BASE = process.env.NEXT_PUBLIC_API_URL;

    export async function sendMessage(messages: Message[], threadId?: string) {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: messages.map(m => ({ role: m.role, content: m.content })),
          thread_id: threadId
        })
      });
      return response.json();
    }

    // SSE streaming not needed for initial implementation
    // Can use regular POST /chat endpoint
    ```

12. **Create `useChat.ts` Hook - Chat State Management**
    - Manages messages array
    - Handles sending messages
    - Tracks streaming state
    - Manages thread persistence
    - Returns: { messages, sendMessage, isStreaming, threadId }

13. **Setup SSE Streaming (Optional Phase 2)**
    - Create `sse-client.ts` for Server-Sent Events
    - Parse SSE stream from POST /chat/stream
    - Handle event types: message, done, error
    - Update messages in real-time
    - Handle HITL interrupts

### Part 4: Project & Session Management

14. **Create `Sidebar.tsx` - Project Navigation**
    - List of recent projects/threads
    - New project button
    - Search/filter threads
    - Show current stage badges
    - Mobile: Slide-out drawer
    - Desktop: Fixed left sidebar (w-64)

15. **Create `Header.tsx` - Top Navigation**
    - App logo/name
    - Current project title
    - Stage indicator (pills/badges)
    - User menu dropdown
    - Mobile: Hamburger menu for sidebar

16. **Build Project List Page** (`app/(dashboard)/projects/page.tsx`)
    - Grid of project cards
    - Show: title, stage, last updated
    - Click to open chat
    - Create new project button
    - Empty state for no projects

### Part 5: Artifact Management (Phase 2 Enhancement)

17. **Create `ArtifactPanel.tsx` - Side Panel for Artifacts**
    - Collapsible panel (right side on desktop)
    - Tabs: Outline, Profile, Persona, Drafts
    - Real-time updates from chat
    - Download/export buttons
    - Mobile: Full-screen modal

18. **Create `OutlineView.tsx` - Book Outline Display**
    - Expandable chapter list
    - Show key topics per chapter
    - Edit mode (optional)
    - Markdown rendering

### Part 6: Mobile-First Responsive Design

19. **Mobile Layout (< 768px)**
    - Full-screen chat interface
    - Sidebar as slide-out drawer
    - Artifacts as bottom sheet or modal
    - Larger touch targets (min 44x44px)
    - Simplified header

20. **Tablet Layout (768px - 1024px)**
    - Chat takes 60% width
    - Collapsible sidebar (20%)
    - Optional artifact panel (20%)

21. **Desktop Layout (> 1024px)**
    - Fixed sidebar (256px)
    - Chat centered (max 896px)
    - Artifact panel (320px)
    - Max width constraint for readability

---

## CODE EXAMPLES, DATA STRUCTURES & CONSTRAINTS

### API Endpoint Contracts

```typescript
// POST /chat
Request: {
  messages: Array<{ role: string, content: string }>,
  thread_id?: string
}

Response: {
  messages: Array<{ role: string, content: string }>,
  thread_id: string
}

// POST /chat/stream (SSE)
Request: Same as above
Response: Server-Sent Events
  data: {"type": "message", "role": "assistant", "content": "...", "thread_id": "..."}
  data: {"type": "done", "thread_id": "..."}
  data: {"type": "error", "error": "..."}
```

### Message Component Example

```tsx
// components/chat/MessageBubble.tsx
import { Message } from '@/lib/types';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';

  return (
    <div className={cn(
      "flex w-full mb-4",
      isUser ? "justify-end" : "justify-start"
    )}>
      <div className={cn(
        "max-w-[85%] md:max-w-[70%] rounded-2xl px-4 py-3",
        isUser
          ? "bg-primary text-primary-foreground"
          : "bg-muted"
      )}>
        {message.metadata?.agent && (
          <div className="text-xs font-medium mb-1 opacity-70">
            {message.metadata.agent}
          </div>
        )}
        <ReactMarkdown className="prose prose-sm dark:prose-invert">
          {message.content}
        </ReactMarkdown>
        <div className="text-xs opacity-50 mt-1">
          {format(message.timestamp, 'HH:mm')}
        </div>
      </div>
    </div>
  );
}
```

### Chat Hook Example

```typescript
// hooks/useChat.ts
import { useState, useCallback } from 'react';
import { Message } from '@/lib/types';
import { sendMessage as apiSendMessage } from '@/lib/api';
import { v4 as uuidv4 } from 'uuid';

export function useChat(initialThreadId?: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [threadId, setThreadId] = useState(initialThreadId);

  const sendMessage = useCallback(async (content: string) => {
    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsStreaming(true);

    try {
      const response = await apiSendMessage([...messages, userMessage], threadId);

      setThreadId(response.thread_id);

      const assistantMessages = response.messages
        .filter((m: any) => m.role === 'assistant')
        .map((m: any) => ({
          id: uuidv4(),
          role: 'assistant',
          content: m.content,
          timestamp: new Date()
        }));

      setMessages(prev => [...prev, ...assistantMessages]);
    } catch (error) {
      console.error('Failed to send message:', error);
      // Handle error state
    } finally {
      setIsStreaming(false);
    }
  }, [messages, threadId]);

  return { messages, sendMessage, isStreaming, threadId };
}
```

### Constraints & Guidelines

**DO:**
- Use TypeScript strict mode for all files
- Follow shadcn/ui theming conventions
- Implement keyboard shortcuts (Cmd/Ctrl+Enter to send)
- Add loading states for all async operations
- Use semantic HTML (main, nav, article, section)
- Implement proper ARIA labels and roles
- Support dark mode via Tailwind classes
- Cache API responses with React Query
- Use proper error boundaries
- Optimize images with Next.js Image component

**DO NOT:**
- Create custom UI components when shadcn/ui has equivalents
- Use inline styles - only Tailwind classes
- Hardcode API URLs - use environment variables
- Skip accessibility attributes
- Ignore mobile touch targets (<44px)
- Create tight coupling between components
- Store sensitive data in localStorage
- Skip error handling on API calls
- Use any type in TypeScript
- Modify files outside the scope defined below

---

## DEFINE STRICT SCOPE

### Files You SHOULD Create/Modify

**Create These New Files:**
- `app/(dashboard)/chat/[threadId]/page.tsx` - Chat page
- `components/chat/ChatInterface.tsx` - Main chat container
- `components/chat/MessageList.tsx` - Message list
- `components/chat/MessageBubble.tsx` - Individual messages
- `components/chat/ChatInput.tsx` - Input component
- `components/chat/StreamingIndicator.tsx` - Loading state
- `components/layout/Sidebar.tsx` - Navigation sidebar
- `components/layout/Header.tsx` - Top header
- `lib/types.ts` - TypeScript types
- `lib/api.ts` - API client
- `hooks/useChat.ts` - Chat state hook
- `app/(dashboard)/layout.tsx` - Dashboard layout

**You May Modify:**
- `app/layout.tsx` - Add global styles, fonts
- `tailwind.config.ts` - Extend theme colors
- `next.config.js` - Add API proxy if needed

### Files You Must NOT Modify

**Leave These Untouched:**
- Any existing authentication files
- Database configuration files
- API route handlers (unless creating new ones)
- Build configuration files (tsconfig, etc)
- Package.json dependencies (except adding specified ones)

### Component Boundaries

- Chat components should be self-contained and reusable
- API logic should stay in `lib/api.ts`
- State management should use hooks in `hooks/`
- No business logic in UI components
- Keep components under 200 lines (split if larger)

---

## WORKFLOW STAGE INDICATORS

The UI should visually indicate the current workflow stage:

1. **Profiling** (Biographer) - Blue badge, notebook icon
2. **Audience** (Empath) - Green badge, users icon
3. **Planning** (Planner) - Purple badge, map icon
4. **Transcript** - Orange badge, mic icon
5. **Drafting** (Writer) - Indigo badge, pen icon

Use shadcn Badge component with appropriate variant colors.

---

## ACCESSIBILITY REQUIREMENTS

- **Keyboard Navigation**: Tab through all interactive elements
- **Screen Readers**: Proper ARIA labels, landmarks, live regions
- **Color Contrast**: Minimum 4.5:1 for text
- **Focus Indicators**: Visible focus rings on all focusable elements
- **Skip Links**: "Skip to main content" link
- **Alt Text**: All images must have descriptive alt text
- **Form Labels**: Explicit labels for all form inputs

---

## PERFORMANCE CONSIDERATIONS

- Use Next.js dynamic imports for heavy components
- Implement virtualization for long message lists (react-window)
- Lazy load artifact panels
- Debounce input for real-time features
- Optimize bundle size (check with `@next/bundle-analyzer`)
- Use React.memo for message components
- Implement proper loading states to avoid layout shift

---

## TESTING GUIDANCE

While this prompt focuses on generation, you should create:
- Unit tests for utility functions (lib/)
- Component tests for chat components (Vitest + Testing Library)
- E2E tests for critical flows (Playwright)
- Accessibility tests (jest-axe)

---

## EXAMPLE COMPONENT HIERARCHY

```
ChatInterface
├── Header
│   ├── ProjectTitle
│   ├── StageBadge
│   └── UserMenu
├── Sidebar (desktop only)
│   ├── ProjectList
│   └── NewProjectButton
├── MessageList
│   ├── DateSeparator
│   ├── MessageBubble (user)
│   ├── MessageBubble (assistant)
│   ├── StreamingIndicator
│   └── ...
└── ChatInput
    ├── Textarea
    └── SendButton
```

---

## ADDITIONAL CONTEXT

### Workflow States to Support

The chat should adapt its UI based on the current workflow stage:

1. **Welcome State**: Show onboarding, suggest starting profiling
2. **Profiling Active**: Highlight Biographer agent, show profile questions
3. **Planning Active**: Show outline preview in artifact panel
4. **Transcript State**: Add file upload UI for transcript
5. **HITL State**: Highlight gap analysis questions, show approve/edit buttons
6. **Draft Complete**: Show draft preview, download options

### Future Enhancements (Don't Implement Yet)

Phase 2 will add:
- CopilotKit Generative UI integration
- Real-time collaborative editing
- Voice-to-text transcript recording
- PDF export functionality
- Multi-project dashboard

---

## FINAL NOTES

**Structure of This Prompt:**
- **Foundational Context**: Establishes tech stack and project purpose
- **Step-by-Step Instructions**: Breaks down implementation into 21 sequential steps
- **Code Examples**: Provides TypeScript examples for key components
- **Strict Scope**: Defines exactly which files to create/modify/avoid

**Why This Information Was Included:**
- Mobile-first design ensures accessibility on all devices
- shadcn/ui reduces custom component development time
- SSE streaming enables real-time conversational UX
- TypeScript prevents runtime errors in complex state management
- Accessibility requirements ensure inclusive design

**IMPORTANT REMINDER**: All AI-generated code requires careful human review, testing, and refinement to be production-ready. This prompt provides a blueprint, but you must:
- Review all generated code for security vulnerabilities
- Test all components across browsers and devices
- Validate accessibility with actual assistive technologies
- Optimize performance with real user data
- Add comprehensive error handling
- Implement proper authentication and authorization
- Add monitoring and analytics
- Write comprehensive tests

Start by generating the foundational structure (Steps 1-4), then build the chat interface components (Steps 5-10), and finally add API integration (Steps 11-13). Test each phase before proceeding to the next.

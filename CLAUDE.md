# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Design-First Development Process

**IMPORTANT**: Before implementing any complex features or architecture changes, follow this process:

### 1. Clarify Requirements
- Ask specific questions about responsibilities: "Should component X do Y or Z?"
- Confirm the data flow: "What calls what, and when?"
- Understand constraints: "What must be preserved from existing code?"
- Identify the problem clearly before proposing solutions

### 2. Propose Architecture
- Draw the system design in text/ASCII before writing code
- Define each component's single responsibility 
- Specify interfaces between components (what data flows where)
- Distinguish between pull servers (provide data) vs push servers (take action)
- Get explicit approval: "Does this design match your mental model?"

### 3. Design Example Format
```
Component A (Pull Server):
- Responsibility: [single clear purpose]
- Tools: [list of tools/functions]
- Interfaces: [what it provides to other components]

Component B (Push Server):  
- Responsibility: [single clear purpose]
- Tools: [list of tools/functions]
- Interfaces: [what it receives from other components]

Data Flow:
User/Cron → Component C → Component A → Component B → Email/Action
```

### 4. Implementation Guidelines
- Implement the agreed design without changing it mid-stream
- If you discover issues during implementation, stop and redesign rather than pivot silently
- Each component should have minimal, focused responsibilities
- Preserve existing working logic unless explicitly asked to replace it

### 5. When Uncertain
- Ask "Is this what you had in mind?" before major changes
- Propose alternatives: "We could do X or Y - which fits your vision?"
- Admit when you're not sure rather than guessing and pivoting later

**Goal**: Align on the mental model first, then implement that model faithfully.


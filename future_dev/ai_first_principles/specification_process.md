# Specification Process and Dynamic Planning

## Dynamic Context

**Key principle:**
> Main model context ≠ Actual context (what goes to LLM)

**Actual context constantly changes:**
- Based on current task
- Based on agent
- Based on stage

**Rotator agents:** Decide which section to move to, their reasoning NOT left in context.

**Result:** User sees sequential dialogue, while models/prompts/contexts rotate in background.

---

## Dynamic Progress Checklists

**Idea:** After each conversation stage, output checklist of what's done, what's next, further plans. Everything changes dynamically.

### Example Checklist

```markdown
## 📊 Conversation Progress

### Done:
✅ Stage 1: Understanding needs
  ✅ User Story
  ✅ 5 Whys
  ✅ Domain analysis
✅ Stage 2: Alternatives analysis
✅ Deep Research (50 questions)

### Pending:
❌ Specification creation
❌ DDD diagrams
❌ Glossary
❌ Test tickets

### Further Plans:
📋 After spec → Documentation
📋 After docs → Tickets
📋 After tickets → Code
📋 After code → Tests

### Possible Branches:
🔀 Need more research → Deep Research v2
🔀 Need requirement clarification → Return to User Story
```

---

## XV. Specification Process (4 Stages)

**Key idea:** Translating NeuroCore's desires, thoughts, goals from idea to specification through smooth flowing reasoning as **stream of thought**.

### 15.0 Process Philosophy: Three Approaches

| Approach | Characteristics | Questions |
|----------|-----------------|-----------|
| **Philosopher** | Doesn't know programming, understands tasks | Why? For whom? What meaning? |
| **Child** | No complex abstractions, expresses simply | IF/ELSE, loops, simple lists |
| **AI** | Amalgam of all expertise, vector thinking | Vector connections, token fields |

**Fusion:**
```
Philosopher → Understanding meaning → Specification
    ↓
Child → Simple implementation → Code
    ↓
AI → Vector connectivity → Hologram
```

---

### 15.1 Stage 1: Understanding Needs

**Goal:** Clear problem formulation (input, output, constraints)

#### Step 1.1: Initial Dialogue
- NeuroCore describes problems
- AI rewrites from their perspective
- Reveals all hidden contexts

#### Step 1.2: User Story
- Global picture of NeuroCore's work
- Where program fits in ecosystem
- Build intent-graph: what user REALLY wants

#### Step 1.3: Place in Ecosystem
- Where will algorithm fit in ecosystem
- What to consider in architecture
- Integration requirements

#### Step 1.4: Edge Cases
- Non-typical situations
- Hardware/software failures
- Non-standard scenarios

**Methods:**
- Event Storming
- Mini-TRIZ (3 steps)
- 5 Whys (Toyota)
- Pre-Mortem Analysis
- Metaphor Elicitation
- Socratic dialogue

**Quality Control:** AI-critic peer-review

---

### 15.2 Stage 2: Creating Specifications

**Principles of Critical Systems:**

| Factor | Manifestation |
|--------|---------------|
| Context | Always included in spec |
| Traceability | Each action traces from goal |
| Formalization | Spec language executable/verifiable |
| Fault tolerance | How system should NOT behave |
| Modularity | Clear boundaries, isolation |
| Feedback | Built into process |

> Best specs are **behavior models** you can execute, verify, recover.

#### Step 2.1: Alternatives Analysis
- NeuroCore shows similar projects
- AI analyzes why they fit/don't fit
- Should we build or use existing?
- Priority: own ecosystem over external solutions

#### Step 2.2: Questions and Meta-Questions
- AI asks questions
- Meta-questions: how to rethink processes
- NeuroCore comments on suitability

#### Step 2.3: Deep Research (50 Questions)
- Generate research query for AI search
- Structure: 1 A4 intro + 50 detailed questions = 7 A4 pages
- Covers programs, algorithms, documentation

#### Step 2.4: Fault Tolerance Requirements
- Hardware/software environment
- Load degree
- Quality requirements
- Security

> Best specs describe not just behavior, but FAILURE.

#### Step 2.5: DDD Diagrams (3 Levels)
- Domain model
- Component architecture
- Integration flows

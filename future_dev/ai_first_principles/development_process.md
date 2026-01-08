# Development Process

## VI. DEVELOPMENT PROCESS

### 6.1 Planning

#### Phase -1: Context Deep Dive

**Before any design** begins, a multi-layered context understanding process occurs.

**Problem of hidden context:**

When people communicate, they have **hundreds of pages of hidden context** that is implied:
- Shared work history
- Previous decisions and their problems
- Implicit expectations and assumptions
- Understanding from half a word

In regular dialogue this works. **But in our dialogue, all this needs to be explicitly stated, emphasized, and expressed.**

---

### Phase 1: Primary Problem and First Understanding

**NeuroCore tells:**
- What problems they have
- How they think to solve them
- What algorithm or program might help
- Their initial thoughts

**AI does:**

Rewrites this, **stepping into NeuroCore's shoes**, seeing situation through their eyes:
- Writes very detailed
- With all hidden contexts
- With what is implied
- Explicitly states what NeuroCore thought when writing this

**Why this matters:**

This is needed so that:
- **You** (AI) clearly and unambiguously understand what is being discussed
- **They** (NeuroCore) are convinced you understood correctly
- **Executors** (other AI agents) who will later write code can understand context

**Example:**

> **NeuroCore**: Need a document processing system. Currently doing this manually, takes a lot of time.

> **AI (bad — without context expansion)**: Understood, will create document processing system.

> **AI (good — with context expansion)**:
>
> Let me retell how I understood your situation to make sure we're on the same page:
>
> **Your current situation (as I see it):**
>
> You regularly work with documents — probably PDF files, possibly Word documents or scanned images. You process them manually, which means:
> - Opening each document
> - Reading the content
> - Extracting needed information
> - Possibly copying it to another system or file
> - Repeating this for each document
>
> This takes a lot of time — probably from several minutes to an hour per document, depending on complexity.
>
> **What you mean by "processing system":**
>
> You want to automate this process so that:
> - System itself opens documents
> - Extracts needed information
> - Structures it
> - Saves in convenient format
>
> **Hidden expectations I assume:**
> - System should work with different document formats
> - Should be smart enough to understand document structure
> - Should be reliable (not lose data)
> - Should save your time
>
> **Clarifying questions:**
> 1. Did I understand your situation correctly?
> 2. What document formats do you process most often?

---

### Phase 2: Global Picture of Work and Life

After reaching understanding, **NeuroCore tells more globally:**
- About all their work
- What problems they have overall
- What their pain is
- Their history, where the problem being solved is just part of the global picture
- Their repeating actions
- Place of the program being created in global work picture

**AI does:**

Again, **through their eyes**, expands and details this into **story of their life and work**:
- Describes typical work day
- Shows where the problem arises
- How it fits into overall workflow
- What dependencies exist from other processes
- What happens before and after this task

**Why this matters:**

This gives understanding of:
- **Usage context** of the program
- **Priorities** (what is truly important)
- **Constraints** (what program must integrate with)
- **Success criteria** (what means "works well")

---

### Phase 3: Place in Program Ecosystem

**NeuroCore tells:**

What place the created algorithm will occupy in the entire **ecosystem of algorithms and external programs** that already exist:
- What programs to integrate with
- What data formats are used
- What APIs are available
- What constraints exist
- What dependencies exist

**AI does:**

Expands **very detailed understanding of this code's place** in global ecosystem:
- Draws integration map
- Describes data flows
- Identifies interaction points
- Determines exchange formats
- Understands constraints and requirements

**Example ecosystem map:**

```
[Client] 
   ↓ (email with PDF attachment)
[Outlook] 
   ↓ (download attachments)
[Folder on disk] 
   ↓ (read PDF)
[OUR PROGRAM] 
   ↓ (write data)
[Excel checklist] 
   ↓ (read results)
[You verify] 
   ↓ (send via CRM)
[CRM system] 
   ↓ (email to client)
[Client]
```

---

### Phase 4: Non-Standard Situations and Failures

**NeuroCore tells:**

About what **non-standard situations** occur during manual work and program use:
- What failures occur
- Non-standard hardware behavior
- Software problems
- Bugs in custom algorithms
- What to consider
- What non-standard work scenarios exist

**AI does:**

Catalogs and details all edge cases and non-standard scenarios:
- Creates list of possible problems
- Describes how to handle them
- Determines recovery strategies
- Plans logging and monitoring
- Provides fallback scenarios

**Why this matters:**

This allows creating a **robust system** that:
- Doesn't crash on unexpected situations
- Correctly handles errors
- Informs user about problems
- Can recover after failure

**Example edge case catalog:**

| Category | Edge Case | Frequency | Auto Solution |
|----------|-----------|-----------|---------------|
| PDF Problems | Corrupted file | Rare | Repair attempt → notify user |
| PDF Problems | Scanned (no text) | 5-10% | OCR via Tesseract |
| PDF Problems | Foreign language | 1-5% | Language detection → translate/notify |
| Structure | Missing required section | 10-15% | Mark "NOT FOUND" → notify |
| Structure | Non-standard format | 5% | Adaptive parsing → confidence check |
| Integration | Outlook hangs | Rare | Retry with timeout → fallback |

**Logging levels by severity:**
- ERROR: Corrupted files, unrecoverable failures
- WARNING: OCR needed, missing sections, low confidence
- INFO: Language detection, non-standard formats

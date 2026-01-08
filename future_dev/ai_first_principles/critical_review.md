# Critical Review and AI Critic

## Adversarial Testing Examples

### Iteration Examples

**Iteration 1:**
```
ATTACKER: Generates None
INPUT: (None, [])
RESULT: 💥 TypeError: argument of type 'NoneType' is not iterable

DEFENDER: Adds validation
FIX: if query is None: return []
```

**Iteration 2:**
```
ATTACKER: Generates huge list
INPUT: ("test", ["doc"] * 1000000)
RESULT: 💥 MemoryError

DEFENDER: Adds limit
FIX: if len(documents) > 10000: raise ValueError("Too many documents")
```

**Iteration 10:**
```
ATTACKER: Tries various edge cases
RESULT: ✅ All pass
CONVERGENCE: Code is robust!
```

---

## Compliance Gates Checklist

### Gate 1: Planning
- [ ] Function designed as standalone library?
- [ ] CLI interface designed?
- [ ] Contract tests defined?

### Gate 2: Testing
- [ ] Unit tests written?
- [ ] Integration tests written?
- [ ] Tests approved by user?
- [ ] Tests failing (Red Phase)?

### Gate 3: Implementation
- [ ] Implemented in standalone library?
- [ ] CLI interface implemented?
- [ ] Tests passing (Green Phase)?
- [ ] Documentation updated?

### Gate 4: Verification
- [ ] All tests passing?
- [ ] CLI works correctly?
- [ ] Library usable independently?
- [ ] Documentation complete?

**Rule**: If ANY checkbox unchecked → gate NOT PASSED.

---

## XIII. Critical Review

**Key idea**: After specification creation, before implementation, **AI-critic** reviews all work from outside.

### 13.1 AI Critic Role

> AI-critic is separate role (or separate AI agent) competent in both problem domain and software development.

**Critic tasks:**
1. Verify problem understanding
2. Check architecture optimality
3. Verify specification completeness
4. Check edge cases coverage
5. Verify test coverage

**Critic views from outside**, not involved in creation process.

---

### 13.2 Specification Peer-Review

**Process:**
1. Create specification (AI + NeuroCore)
2. Pass to critic (full spec + context)
3. Critical analysis (AI-critic reviews)
4. Critic report (problems and recommendations)
5. Correction (AI + NeuroCore fix)
6. Re-review (if needed)

### What Critic Checks

| Area | Sample Questions |
|------|------------------|
| **Problem understanding** | True need identified? XY-problem? Stakeholders? Success criteria? |
| **Architecture** | Optimal? Over-engineering? Constraints? Constitutional compliance? |
| **Spec completeness** | All FRs? All NFRs? Edge cases? Success metrics? |
| **Contradictions** | Conflicting requirements? Ambiguous terms? Missing dependencies? |
| **Testability** | All testable? Pass criteria? Integration tests? Test plan? |

---

### 13.3 Domain Expertise

**Critic must be competent in domain:**

#### Example 1: Search Engine

Critic knows: IR theory, BM25, TF-IDF, embeddings, Precision/Recall/NDCG

**Critic questions:**
- Why RRF for fusion instead of CombSUM?
- How to handle vocabulary mismatch?
- Cold start problem for new documents?
- How to measure search quality?

#### Example 2: Legal Document Processing

Critic knows: Legal tech, GDPR, document specifics, risks

**Critic questions:**
- How is personal data confidentiality ensured?
- Audit trail requirements met?
- What happens on conflict of interest?
- How to guarantee AI doesn't miss critical clause?

---

### 13.4 Correction Process

**After receiving critic report:**

**Step 1: Analyze remarks**
- Do we agree with remark?
- Is it critical for project?
- How to fix?

**Step 2: Prioritization**

| Priority | Action |
|----------|--------|
| 🔴 Critical | Blocks development, must fix |
| 🟡 Important | Should fix before implementation |
| 🟢 Nice-to-have | Can fix later |

**Step 3: Correction**
- Update specification
- Update architecture
- Update tests
- Document changes

# RAG-Aware Prompting Principles

## 7 Principles for Maximum Documentation Attraction

### Principle 1: Use Specific Technologies

❌ **Bad**: Create a search function.

✅ **Good**: 
```
Create hybrid search using:
- BM25 algorithm for keyword matching
- FAISS vector search
- Reciprocal Rank Fusion (RRF) for result combination
- Min-max normalization for scores
```

**Why it works**: Terms "BM25", "FAISS", "RRF" attract documentation on these technologies.

---

### Principle 2: Mention Library Names, Frameworks, APIs

❌ **Bad**: Write database code.

✅ **Good**:
```
Write PostgreSQL code using:
- psycopg2 for connection
- SQLAlchemy ORM for models
- Alembic for migrations
- Connection pooling via SQLAlchemy engine
```

**What attracts**: psycopg2 docs, SQLAlchemy examples, connection pooling best practices.

---

### Principle 3: Specify Design Patterns

❌ **Bad**: Organize data processing code.

✅ **Good**:
```
Organize data processing using:
- Repository pattern for data access
- Factory pattern for handler creation
- Strategy pattern for algorithms
- Dependency Injection
- SOLID principles
```

---

### Principle 4: Mention Specific Edge Cases

❌ **Bad**: Write JSON parsing function.

✅ **Good**:
```
Write JSON parsing handling:
- Malformed JSON format
- Large files (>100MB) via streaming
- Unicode characters and encoding issues
- Nested structures >10 levels
- Missing fields and null values
- JSON Schema validation
```

---

### Principle 5: Use Semantic Anchors (@TAG)

```
Create function for @TAG:HYBRID-SEARCH using @TAG:BM25-INDEX and @TAG:VECTOR-INDEX.
Follow @TAG:SEMANTIC-GLUE and @TAG:HOLOGRAPHIC-TICKET principles.
```

**Attracts**: All documents with these tags, specifications, code examples.

---

### Principle 6: Use Synonyms (Multiple Formulations)

❌ **Bad** (single): Create caching system.

✅ **Good** (multiple):
```
Create caching system (cache) for:
- Temporary storage of results
- Memoization of expensive computations
- Data buffering
- LRU eviction policy for memory management
- TTL (time-to-live) for stale data removal
```

**Why**: "Caching" + "memoization" + "buffering" = more relevant documents.

---

### Principle 7: Provide Project/Domain Context

❌ **Bad**: Create document processing function.

✅ **Good**:
```
Create function for legal document processing:
- Contract review automation
- Compliance checking
- Clause extraction
- Risk assessment
- GDPR compliance for personal data
```

---

## Structured Prompt Template

```markdown
# TASK: [Brief description]

## CONTEXT:
- Project: [name]
- Domain: [application area]
- Technologies: [list of technologies, libraries, frameworks]
- Patterns: [architectural patterns]

## REQUIREMENTS:

### Functional:
- FR1: [requirement with specific technologies]
- FR2: [requirement with algorithms]
- FR3: [requirement with patterns]

### Non-Functional:
- NFR1: Performance - [specific metrics and optimization tech]
- NFR2: Scalability - [scaling approaches]
- NFR3: Security - [security standards]

## TECHNICAL DETAILS:

### Libraries:
- [Library 1] version X.Y for [specific task]
- [Library 2] version X.Y for [specific task]

### Algorithms:
- [Algorithm 1] for [task]
- [Algorithm 2] for [task]

### Design Patterns:
- [Pattern 1] for [architectural decision]
- [Pattern 2] for [architectural decision]

## EDGE CASES:
- [Problem 1] and solution
- [Edge case 1] and handling

## SEMANTIC ANCHORS:
@TAG:[tag1] @TAG:[tag2] @TAG:[tag3]

## EXPECTED RESULT:
[Detailed description of expected output]
```

---

## Pre-Send Checklist

Before sending prompts, verify:

| ✅ | Check |
|----|-------|
| ☐ | Specific technologies mentioned? (libraries, frameworks, APIs) |
| ☐ | Algorithms and patterns specified? |
| ☐ | Edge cases described? |
| ☐ | Project context provided? |
| ☐ | Synonyms used? (multiple formulations) |
| ☐ | Semantic anchors added? (@TAG) |
| ☐ | Metrics and requirements specified? |
| ☐ | Examples and references included? |

---

## Result Comparison

| Without Embedding Awareness | With Embedding Awareness |
|----------------------------|--------------------------|
| AI uses general knowledge | AI gets actual documentation |
| May use outdated APIs | Uses correct API versions |
| Misses best practices | Follows project best practices |
| Ignores project specifics | Accounts for all edge cases |
| Generic code | Code matching project standards |

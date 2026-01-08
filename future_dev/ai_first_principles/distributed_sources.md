# Distributed Systems and Sources

## Auto-Generated API Clients

```python
"""
AUTH CLIENT

CONTEXT:
- Client for auth-service
- Auto-generated from specs/auth-api.yaml
- Handles retries, circuit breaking, timeouts

DEPENDENCIES:
- auth-service (required)
"""

class AuthClient:
    """
    @TAG:CLIENT:auth-service
    @TAG:AUTO-GENERATED:from-openapi-spec
    """
    
    async def login(self, credentials: LoginRequest) -> LoginResponse:
        """
        SPEC:
        - POST /auth/login
        - Retries: 3x exponential backoff
        - Timeout: 5 seconds
        - Circuit breaker: Open after 5 failures
        """
```

---

## Distributed Transactions: Saga Pattern

### Challenges
1. Eventual consistency
2. Network failures
3. Distributed transactions
4. Observability

### Saga Structure

```python
@dataclass
class SagaStep:
    name: str
    action: callable       # Forward action
    compensation: callable # Rollback action

class DistributedOrderSaga:
    """
    STEPS:
    1. Create order
    2. Reserve inventory
    3. Process payment
    
    COMPENSATION:
    - Payment fails → release inventory, cancel order
    - Inventory fails → cancel order
    """
    
    async def execute(self, order_data):
        # Execute steps sequentially
        # On failure → compensate in reverse order
    
    async def _compensate(self):
        # Rollback completed steps
        # Best effort (continue even if compensation fails)
```

---

## Multi-Repo Projects

### NSS Orchestrator Config

```yaml
project: "E-commerce Platform"

repositories:
  - name: "backend"     preset: "full"
  - name: "frontend"    preset: "balanced"
  - name: "mobile-ios"  preset: "minimal"
  - name: "shared-types" preset: "full"

coordination:
  shared_types_changes:
    require_approval_from: [all teams]
  breaking_changes:
    require_migration_plan: true
    deprecation_period: "3 months"
```

### CLI Commands

```bash
nss-orchestrator validate --all
nss-orchestrator report --format=html
nss-orchestrator check-breaking-changes
nss-orchestrator sync-config --dry-run
```

---

## 32.3 When NOT to Use NSS Coder

### ❌ Don't Use If:
- Project < 1000 lines
- 1-2 week prototype (use "prototype" preset)
- One-off script
- Team not ready for AI-First
- No GPT-4 level AI access

### ✅ Use If:
- Long-term project (> 6 months)
- Team > 3 people
- Performance critical
- Scalability needed
- Documentation important

---

## 32.4 Improvement Roadmap

| Quarter | Focus |
|---------|-------|
| Q1 2025 | Tooling spec, VS Code beta, community guidelines |
| Q2 2025 | Testing framework, CI/CD templates, security |
| Q3 2025 | Scalability patterns, multi-repo, enterprise |
| Q4 2025 | Certification, case studies, benchmarks |

---

## XXXIII. Philosophical Lineage

### 1. Anokhin's Hypernets (Neuroscience)

- **Source**: P.K. Anokhin, "Functional Systems Theory" (1935-1974)
- **Influence**: Holographic redundancy, feedback loops, result anticipation
- **Applied**: Holographic tickets, bidirectional storytelling, specs as "result acceptor"

### 2. TLA+ / Formal Methods

- **Source**: Leslie Lamport, "Specifying Systems" (2002)
- **Influence**: Specifications before code, invariants, temporal logic
- **Applied**: File-level specs, invariants in comments

> "Formal mathematics is nature's way of letting you know how sloppy your writing is." — Lamport

### 3. Domain-Driven Design

- **Source**: Eric Evans, "Domain-Driven Design" (2003)
- **Influence**: Ubiquitous language, bounded contexts, entities/aggregates
- **Applied**: Semantic tags, module boundaries, domain-reflecting names

### 4. Test-Driven Development

- **Source**: Kent Beck, "TDD: By Example" (2002)
- **Influence**: Tests before code, red-green-refactor

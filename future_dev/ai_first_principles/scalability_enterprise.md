# Scalability and Enterprise

## Security Pipeline (CI/CD)

```yaml
name: Security Scan
on: [push, pull_request, schedule: weekly]

steps:
  # 1. SAST
  - uses: returntocorp/semgrep-action@v1
    with: p/security-audit, p/owasp-top-ten
  
  # 2. Dependency
  - run: npm audit --audit-level=moderate
  - uses: snyk/actions/node@master
  
  # 3. Secrets
  - uses: gitleaks/gitleaks-action@v2
  
  # 4. Containers
  - uses: aquasecurity/trivy-action@master
  
  # 5. AI Analysis
  - run: python scripts/ai_security_review.py
```

---

## AI Hallucination Detection

### 3 Detection Strategies

1. **Multi-Model Cross-Validation**
   - Generate with GPT-4, Claude-3, Gemini-Pro
   - Compare results, avg similarity < 0.7 → HIGH risk

2. **Fact-Check Against Documentation**
   - Extract function calls from generated code
   - Verify each exists in API docs
   - Missing → possible hallucination

3. **Confidence Scoring**
   - Request AI with logprobs
   - Confidence < 0.7 → MEDIUM risk
   - Flag low-confidence tokens

### Safe Generation Workflow

```
1. Generate code
2. Run hallucination checks
3. Aggregate risks
4. Decision:
   - HIGH → REQUIRES_REVIEW 🔴
   - MEDIUM → REVIEW_RECOMMENDED 🟡
   - LOW → OK ✅
```

---

## 32.2.6 Scalability

### NSS Coder for Large Teams (100+ devs)

#### Challenges
1. Coordination between teams
2. Uniform code style
3. Dependency management
4. Code review bottlenecks

#### Enterprise Configuration

```yaml
organization: "Large Corp"
teams: 15
developers: 150

presets_by_team:
  backend_team: "full"
  frontend_team: "balanced"
  data_team: "full"
  mobile_team: "minimal"
  devops_team: "prototype"

global_standards:
  cognitive_unit_size: 700
  min_comment_ratio: 0.70
  min_token_gravity: 0.75

ai_resources:
  api_quota_per_team:
    backend: 100k tokens/day
    frontend: 80k tokens/day
  monthly_budget: "$50,000"
```

---

## Microservices Architecture

### Principles
1. Each service = separate NSS Coder project
2. Shared libraries = "full" preset
3. API contracts = formal OpenAPI/gRPC specs

### Structure

```
microservices/
├── services/
│   ├── auth-service/     # preset: "full" (critical)
│   ├── user-service/     # preset: "balanced"
│   └── notification/     # preset: "minimal"
├── shared/
│   ├── core-library/     # preset: "full"
│   └── common-types/     # preset: "full"
└── tools/
    └── nss-orchestrator/
```

### Service Example

```python
# auth-service/src/api/auth.py
"""
AUTH SERVICE API

SPEC:
- Provides authentication and authorization
- Used by: user-service, order-service

API CONTRACT: specs/auth-api.yaml
"""

@app.post("/auth/login")
async def login(credentials: LoginRequest) -> LoginResponse:
    """
    @TAG:CRITICAL:security
    
    HARDWARE-AWARE:
    - Bcrypt hashing (CPU-intensive)
    - Constant-time comparison (security)
    """
```

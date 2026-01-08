# Self-Improving Agent and Gravity Monitoring

## Algorithm 4: Self-Learning Agent Through Log Reading

**What**: Agent reads its own logs and extracts insights.

**Why**: Continuous improvement — agent learns from mistakes and successes.

### Implementation

```python
class SelfImprovingAgent:
    """
    Agent that reads its logs and improves.
    """
    
    def __init__(self, llm):
        self.llm = llm
        self.insights = []
    
    def analyze_generation_log(self, candidates_log):
        """
        Analyzes generation log and extracts insights.
        """
        prompt = self._create_analysis_prompt(candidates_log)
        analysis = self.llm.generate(prompt)
        insights = self._extract_insights(analysis)
        self.insights.extend(insights)
        return insights
    
    def _create_analysis_prompt(self, candidates_log):
        """
        Creates prompt for log analysis.
        """
        summary = []
        for i, entry in enumerate(candidates_log):
            summary.append(
                f"Step {i}: Chose '{entry['chosen_token']}' "
                f"(p={entry['chosen_probability']:.2f}, entropy={entry['entropy']:.2f})"
            )
            summary.append(f"  Alternatives: {', '.join([c['token'] for c in entry['candidates'][:3]])}")
        
        prompt = f"""
You are analyzing your own generation log to improve future performance.

GENERATION LOG:
{chr(10).join(summary)}

TASK: Analyze this log and identify:
1. Moments of high uncertainty (high entropy)
2. Missed opportunities (good alternatives not chosen)
3. Patterns in token selection
4. Suggestions for improvement

FORMAT YOUR RESPONSE AS:
INSIGHT 1: [description]
INSIGHT 2: [description]
...
"""
        return prompt
    
    def apply_insights(self, prompt):
        """
        Applies accumulated insights to new prompt.
        """
        if not self.insights:
            return prompt
        
        insights_text = '\n'.join([f"- {ins}" for ins in self.insights[-5:]])  # Last 5
        
        enhanced_prompt = f"""
{prompt}

LEARNED INSIGHTS (from previous generations):
{insights_text}

Apply these insights to improve your response.
"""
        return enhanced_prompt
```

### Example Output

```
Extracted insights:
  - At step 3, high entropy (3.8) suggests uncertainty about next action
  - Alternative "understand" (18.9%) might be better than "analyze" for exploratory tasks
  - Pattern "analyze → the → requirements" appears frequently, consider varying approach
```

---

## Algorithm 5: Token Gravity Real-Time Monitoring

**What**: Track how tokens "attract" each other during generation.

**Why**: Early detection of problems (looping, focus loss).

### Implementation

```python
class TokenGravityMonitor:
    """
    Monitors token gravity in real-time.
    """
    
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.token_history = []
        self.gravity_scores = []
    
    def update(self, chosen_token, candidates):
        """
        Updates monitoring after each step.
        """
        self.token_history.append(chosen_token)
        
        if len(self.token_history) >= self.window_size:
            gravity = self._calculate_gravity(
                self.token_history[-self.window_size:],
                candidates
            )
            self.gravity_scores.append(gravity)
            
            # Check anomalies
            if gravity > 0.8:
                print(f"⚠️  WARNING: High token gravity ({gravity:.2f}) — possible repetition loop")
            elif gravity < 0.2:
                print(f"⚠️  WARNING: Low token gravity ({gravity:.2f}) — possible loss of focus")
    
    def _calculate_gravity(self, recent_tokens, candidates):
        """
        Calculates "gravity" = probability of repeating recent tokens.
        """
        overlap = sum(1 for cand in candidates[:5] if cand['token'] in recent_tokens)
        gravity = overlap / min(5, len(recent_tokens))
        return gravity
    
    def plot_gravity(self):
        """
        Visualizes gravity change over time.
        """
        plt.figure(figsize=(12, 4))
        plt.plot(self.gravity_scores, marker='o')
        plt.axhline(y=0.8, color='r', linestyle='--', label='High gravity threshold')
        plt.axhline(y=0.2, color='b', linestyle='--', label='Low gravity threshold')
        plt.xlabel('Generation Step')
        plt.ylabel('Token Gravity')
        plt.title('Token Gravity Over Time')
        plt.legend()
        plt.savefig('token_gravity_monitor.png')
        plt.show()
```

---

## Practical Use Cases for Agent Systems

### Use Case 1: Debugging Repetition Loops

```python
monitor = TokenGravityMonitor()
# ... generation ...

if monitor.gravity_scores[-1] > 0.8:
    # Repetition loop detected
    print("Detected repetition loop, restarting with temperature=1.2")
```

### Use Case 2: Prompt Quality Analysis

```python
introspector = TokenCandidateIntrospector()
result = introspector.generate_with_candidates(prompt)

avg_entropy = np.mean([e['entropy'] for e in result['candidates_log']])

if avg_entropy > 4.0:
    print("High entropy — prompt is too vague, model is uncertain")
elif avg_entropy < 1.5:
    print("Low entropy — prompt is too constraining, model has no flexibility")
else:
    print("Good entropy — prompt provides clear direction with flexibility")
```

### Use Case 3: Continuous Improvement

```python
agent = SelfImprovingAgent(llm)

for i, task in enumerate(tasks):
    result = introspector.generate_with_candidates(task['prompt'])
    insights = agent.analyze_generation_log(result['candidates_log'])
    
    # Apply to next task
    if i + 1 < len(tasks):
        next_prompt = agent.apply_insights(tasks[i+1]['prompt'])
```

---

## Summary: Token Introspection for Smart Agents

**What we can do:**

| Capability | Tool | Benefit |
|------------|------|---------|
| Extract token candidates | Top-K Sampling | See alternatives, not just chosen path |
| Visualize token clouds | WordCloud | Understand "possibility space" |
| Analyze semantic connections | NetworkX Graph | Find thinking patterns |
| Self-learn through logs | LLM Analysis | Continuous improvement |
| Monitor token gravity | Real-time tracking | Early problem detection |

**Practical applications:**
- Debugging agent loops
- Prompt quality evaluation
- Continuous agent improvement
- Pattern discovery in agent behavior

# Token Introspection for Agent Debugging

## II.9.6-9.8 Practical Applications and Agent Debugging

### Use Case 1: Prompt Quality Evaluation

```python
def evaluate_prompt_quality(prompt):
    """
    Evaluates prompt quality through "gravity" metrics.
    """
    # Metric 1: Attention concentration
    entropy = measure_attention_concentration(prompt)
    
    # Metric 2: Semantic coherence (within prompt)
    sentences = prompt.split('.')
    if len(sentences) > 1:
        coherence = np.mean([
            measure_semantic_gravity(sentences[i], sentences[i+1])
            for i in range(len(sentences)-1)
        ])
    else:
        coherence = 1.0
    
    # Score
    quality_score = (
        (1.0 / (entropy + 1)) * 0.5 +  # Lower entropy = better
        coherence * 0.5                 # Higher coherence = better
    )
    
    return {
        'quality_score': quality_score,
        'attention_entropy': entropy,
        'semantic_coherence': coherence
    }
```

---

### Use Case 2: Code Semantic Density Monitoring

```python
def monitor_code_semantic_density(code_file):
    """
    Checks semantic density of code (comments + docstrings).
    """
    with open(code_file) as f:
        lines = f.readlines()
    
    comments = [line for line in lines if line.strip().startswith('#')]
    
    if len(comments) < 2:
        return {'density': 0, 'message': 'Not enough comments'}
    
    # Measure semantic gravity between adjacent comments
    gravities = [
        measure_semantic_gravity(comments[i], comments[i+1])
        for i in range(len(comments)-1)
    ]
    
    avg_gravity = np.mean(gravities)
    
    return {
        'density': avg_gravity,
        'message': 'Strong' if avg_gravity > 0.6 else 'Weak'
    }
```

---

## II.9.7 Summary: From Metaphors to Science

| Metaphor (Before) | Metric (After) | Measurement Tool |
|-------------------|----------------|------------------|
| Token Gravity | Attention Weight Concentration | Attention maps, entropy |
| Semantic Gravity | Embedding Distance Reduction | Cosine similarity |
| Token Topology | Embedding Space Geometry | t-SNE, UMAP, clustering |
| Thought Signature | Activation Patterns | Layer activations analysis |
| Token Co-occurrence | Co-occurrence Density | Statistical analysis |

**Important**: Metaphors are useful for **understanding**, metrics for **measuring**.

---

## II.9.8 Token Candidate Introspection: Debugging Agent Systems

**Problem**: How can an agent system "see" its thinking and learn from its own logs?

**Solution**: Token candidate introspection, token cloud analysis, connection visualization.

---

### Algorithm 1: Token Candidate Extraction (Top-K Sampling)

**What**: Get not only the chosen token, but ALL candidates with probabilities.

**Why**: Understand what model was "thinking", what alternatives existed.

```python
class TokenCandidateIntrospector:
    """
    Extracts token candidates and their probabilities for analysis.
    
    USE CASE: Agent system debugging
    - See alternative thinking paths
    - Analyze model confidence
    - Find decision points
    """
    
    def __init__(self, model_name="gpt2"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.model.eval()
    
    def generate_with_candidates(self, prompt, max_new_tokens=50, top_k=10):
        """
        Generates text and saves top-K candidates at each step.
        
        Returns:
            dict: {
                'generated_text': str,
                'candidates_log': List[dict]
            }
        """
        inputs = self.tokenizer(prompt, return_tensors="pt")
        input_ids = inputs['input_ids']
        candidates_log = []
        
        with torch.no_grad():
            for step in range(max_new_tokens):
                outputs = self.model(input_ids)
                logits = outputs.logits[:, -1, :]
                probs = torch.softmax(logits, dim=-1)
                
                # Top-K candidates
                top_k_probs, top_k_indices = torch.topk(probs, top_k, dim=-1)
                next_token_id = top_k_indices[0, 0].item()  # Greedy
                
                # Log candidates
                candidates = [{
                    'token': self.tokenizer.decode([top_k_indices[0, i].item()]),
                    'probability': top_k_probs[0, i].item(),
                    'rank': i + 1
                } for i in range(top_k)]
                
                candidates_log.append({
                    'step': step,
                    'chosen_token': self.tokenizer.decode([next_token_id]),
                    'chosen_probability': top_k_probs[0, 0].item(),
                    'candidates': candidates,
                    'entropy': self._calculate_entropy(probs[0])
                })
                
                input_ids = torch.cat([input_ids, torch.tensor([[next_token_id]])], dim=1)
                if next_token_id == self.tokenizer.eos_token_id:
                    break
        
        return {
            'generated_text': self.tokenizer.decode(generated_tokens),
            'candidates_log': candidates_log
        }
```

**Output Example**:

```json
{
  "step": 0,
  "chosen_token": " analyze",
  "chosen_probability": 0.342,
  "candidates": [
    {"token": " analyze", "probability": 0.342, "rank": 1},
    {"token": " understand", "probability": 0.189, "rank": 2},
    {"token": " identify", "probability": 0.156, "rank": 3}
  ],
  "entropy": 2.34
}
```

**Insight**: Model considered multiple approaches, chose "analyze" as most probable.

---

### Algorithm 2: Token Cloud Visualization

**What**: Visualize token candidates as probability "clouds".

**Why**: See model's "possibility space" at each step.

```python
from wordcloud import WordCloud
import matplotlib.pyplot as plt

class TokenCloudVisualizer:
    """
    Visualizes token candidate clouds.
    """
    
    def visualize_step_cloud(self, candidates, step_num):
        """
        Creates word cloud for one generation step.
        """
        word_freq = {
            cand['token'].strip(): cand['probability'] 
            for cand in candidates
        }
        
        wordcloud = WordCloud(
            width=800, height=400,
            background_color='white',
            colormap='viridis'
        ).generate_from_frequencies(word_freq)
        
        plt.figure(figsize=(12, 6))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(f'Token Cloud at Step {step_num}')
        plt.savefig(f'token_cloud_step_{step_num}.png')
        plt.show()
```

**What We See**:
- **Big words** = high probability
- **Small words** = low probability
- **Color** = rank in top-K

---

### Algorithm 3: Semantic Connection Graph Analysis

**What**: Analyze how tokens are connected in agent system logs.

**Why**: Find thinking patterns, recurring errors, improvement points.

```python
import networkx as nx

class SemanticConnectionAnalyzer:
    """
    Analyzes semantic connections between tokens in logs.
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
    
    def analyze_log(self, candidates_log):
        """
        Builds connection graph between tokens.
        """
        for i, log_entry in enumerate(candidates_log[:-1]):
            current_token = log_entry['chosen_token'].strip()
            next_token = candidates_log[i+1]['chosen_token'].strip()
            
            # Add edge with weight = probability
            if self.graph.has_edge(current_token, next_token):
                self.graph[current_token][next_token]['weight'] += 1
            else:
                self.graph.add_edge(current_token, next_token, weight=1)
        
        return self.graph
    
    def visualize_graph(self):
        """
        Visualizes token connection graph.
        """
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(self.graph)
        nx.draw(self.graph, pos, with_labels=True, 
                node_color='lightblue', node_size=1000,
                font_size=8, arrows=True)
        plt.title("Token Connection Graph")
        plt.savefig('token_graph.png')
        plt.show()
```

**Use Cases**:
- Find decision points (high branching factor)
- Detect loops (repeated tokens)
- Identify confident paths (high weight edges)

# Measuring Token Gravity: From Metaphor to Metrics

## II.9 Measuring Token Gravity

**Problem**: "Token Gravity" and "Semantic Gravity" are beautiful metaphors, but how do we measure them?

**Solution**: Operationalization of metaphors into measurable metrics.

---

## II.9.1 From Metaphors to Measurable Concepts

| Metaphor | Measurable Metric | How to Measure |
|----------|-------------------|----------------|
| **Token Gravity** | Attention Weight Concentration | Attention maps from transformer layers |
| **Semantic Gravity** | Embedding Distance Reduction | Cosine similarity between embeddings |
| **Token Topology** | Embedding Space Geometry | t-SNE/UMAP visualization, clustering |
| **Thought Signature** | Prompt-Specific Activation Patterns | Layer activations analysis |

---

## II.9.2 Metric 1: Attention Weight Concentration

**What we measure**: How strongly the model "focuses" on certain tokens.

### Formula

```
Attention Concentration = Entropy(attention_weights)

Where:
- Low entropy → high concentration (strong "gravity")
- High entropy → low concentration (weak "gravity")
```

### Practical Example

```python
import torch
from transformers import AutoModel, AutoTokenizer
import numpy as np

def measure_attention_concentration(text, model_name="gpt2"):
    """
    Measures attention weights concentration.
    
    Returns:
        float: Average attention entropy (lower = stronger gravity)
    """
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name, output_attentions=True)
    
    inputs = tokenizer(text, return_tensors="pt")
    outputs = model(**inputs)
    
    # Get attention weights from all layers
    attentions = outputs.attentions  # Tuple of (batch, heads, seq_len, seq_len)
    
    entropies = []
    for layer_attention in attentions:
        avg_attention = layer_attention.mean(dim=(0, 1))
        
        for token_attention in avg_attention:
            probs = token_attention / token_attention.sum()
            entropy = -(probs * torch.log(probs + 1e-10)).sum().item()
            entropies.append(entropy)
    
    return np.mean(entropies)
```

### Interpretation

| Entropy | Gravity Strength | Meaning |
|---------|------------------|---------|
| < 2.0 | Strong | Model clearly focuses, strong token attraction |
| 2.0-4.0 | Medium | Moderate focus |
| > 4.0 | Weak | Attention scattered, model uncertain |

---

## II.9.3 Metric 2: Embedding Distance Reduction (Semantic Gravity)

**What we measure**: How close related concepts are in embedding space.

### Formula

```
Semantic Gravity = 1 - cosine_distance(embedding_A, embedding_B)

Where:
- 1.0 → maximum "gravity" (identical embeddings)
- 0.0 → no "gravity" (orthogonal embeddings)
- -1.0 → "repulsion" (opposite embeddings)
```

### Practical Example

```python
from sentence_transformers import SentenceTransformer
import numpy as np

def measure_semantic_gravity(text1, text2, model_name="all-MiniLM-L6-v2"):
    """
    Measures semantic "gravity" between two texts.
    
    Returns:
        float: Cosine similarity (0-1, higher = stronger gravity)
    """
    model = SentenceTransformer(model_name)
    embeddings = model.encode([text1, text2])
    
    similarity = np.dot(embeddings[0], embeddings[1]) / (
        np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
    )
    
    return similarity
```

### Interpretation

| Similarity | Connection Strength |
|------------|---------------------|
| > 0.7 | Strong semantic gravity |
| 0.3-0.7 | Moderate connection |
| < 0.3 | Weak or no gravity |

---

## II.9.4 Metric 3: Token Co-occurrence Density

**What we measure**: How often tokens appear together in context.

### Formula

```
Co-occurrence Density = P(token_B | token_A) / P(token_B)

Where:
- > 1.0 → tokens "attract" (together more often than separate)
- = 1.0 → independent
- < 1.0 → tokens "repel"
```

### Practical Example

```python
from collections import Counter
import re

def measure_cooccurrence_density(corpus, token_a, token_b, window=5):
    """
    Measures token co-occurrence density.
    
    Args:
        corpus: List of texts
        token_a, token_b: Tokens to measure
        window: Context window size
    
    Returns:
        float: Co-occurrence density (> 1.0 = attraction)
    """
    all_tokens = []
    for text in corpus:
        tokens = re.findall(r'\w+', text.lower())
        all_tokens.extend(tokens)
    
    total_tokens = len(all_tokens)
    count_a = all_tokens.count(token_a)
    count_b = all_tokens.count(token_b)
    
    p_b = count_b / total_tokens
    
    cooccurrences = 0
    for i, token in enumerate(all_tokens):
        if token == token_a:
            start = max(0, i - window)
            end = min(len(all_tokens), i + window + 1)
            if token_b in all_tokens[start:end]:
                cooccurrences += 1
    
    p_b_given_a = cooccurrences / count_a if count_a > 0 else 0
    density = p_b_given_a / p_b if p_b > 0 else 0
    
    return density
```

### Interpretation

| Density | Meaning |
|---------|---------|
| > 5.0 | Very strong gravity (tokens almost always together) |
| 2.0-5.0 | Strong connection |
| ~1.0 | Independent |
| < 1.0 | Repulsion (tokens avoid each other) |

---

## II.9.5 Token Topology Visualization

**Embedding Space Geometry**: Visualizes embedding space structure.

### Tools

```python
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt

def visualize_token_topology(texts, model_name="all-MiniLM-L6-v2"):
    """
    Visualizes token "topology" in 2D.
    """
    from sentence_transformers import SentenceTransformer
    
    model = SentenceTransformer(model_name)
    embeddings = model.encode(texts)
    
    # Dimensionality reduction: 384D → 2D
    tsne = TSNE(n_components=2, random_state=42)
    embeddings_2d = tsne.fit_transform(embeddings)
    
    # Visualization
    plt.figure(figsize=(12, 8))
    plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], alpha=0.6)
    
    for i, text in enumerate(texts):
        plt.annotate(text[:30], (embeddings_2d[i, 0], embeddings_2d[i, 1]),
                     fontsize=8, alpha=0.7)
    
    plt.title("Token Topology (Embedding Space Geometry)")
    plt.show()
```

### What We See

- **Clusters** — groups of semantically related tokens ("gravitational wells")
- **Distances** — closer = stronger "gravity"
- **Topology** — space structure (manifold)

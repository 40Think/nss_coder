# Configuration Presets and Monitoring

## 28.6 Hardware-Aware Programming Settings

```yaml
hardware_aware:
  enabled: true
  target_architecture: "x86-64"  # x86-64 | ARM | GPU | auto
  
  optimizations:
    cache_locality: true
    simd_vectorization: true
    branch_prediction: true
    memory_alignment: true
    prefetching: true
  
  profiling:
    enabled: true
    tools: ["perf", "valgrind", "nvidia-smi"]
  
  metrics:
    cache_miss_threshold: 0.01      # < 1%
    branch_misprediction_threshold: 0.02  # < 2%
    simd_utilization_threshold: 0.8  # > 80%
  
  auto_fix_cache_issues: false
  suggest_simd_opportunities: true
```

| Profile | Optimizations | Use Case |
|---------|--------------|----------|
| **High-Performance** | All | Critical systems |
| **Moderate** | Cache only | Normal apps |
| **Off** | None | Prototypes, scripts |

---

## 28.7 Holographic Redundancy Settings

```yaml
holographic_redundancy:
  level: "high"  # high | medium | low | minimal
  
  duplicate:
    context_in_tickets: true
    architecture_in_files: true
    business_logic_in_code: true
    dependencies_in_specs: true
  
  ticket_self_sufficiency: true
  include_full_context: true
  target_ticket_size: 200  # lines
  max_ticket_size: 300
```

| Level | Self-Sufficient | Full Context |
|-------|-----------------|--------------|
| **High** | Yes | Yes |
| **Medium** | Yes | No |
| **Low** | No | No |

---

## 28.8 Configuration Presets

### Preset 1: NSS Coder Pure (Full philosophy)

```yaml
preset: "nss-coder-pure"
cognitive_unit_size: 700
code_decomposition: extreme
semantic_glue: 90%
storytelling: all levels
hardware_aware: all optimizations
holographic: high
```

### Preset 2: Balanced (Philosophy + pragmatism)

```yaml
preset: "balanced"
cognitive_unit_size: 700
code_decomposition: moderate (200 lines)
semantic_glue: 70%
storytelling: no microcode
hardware_aware: cache + SIMD
holographic: medium
```

### Preset 3: Gradual Adoption (Step-by-step)

```yaml
preset: "gradual-adoption"
cognitive_unit_size: 1000  # Larger to start
code_decomposition: minimal
semantic_glue: 50%
storytelling: off
hardware_aware: off
holographic: low

migration_plan:
  phase_1: "Increase comments to 70%"
  phase_2: "Enable bidirectional storytelling"
  phase_3: "Reduce cognitive_unit to 700"
  phase_4: "Enable extreme decomposition"
```

### Preset 4: Legacy Project

```yaml
preset: "legacy-project"
cognitive_unit_size: 1500
code_decomposition: off
semantic_glue: 30%
storytelling: off
hardware_aware: off
holographic: minimal
apply_to_new_files_only: true
```

### Preset 5: Prototype (Fast iteration)

```yaml
preset: "prototype"
cognitive_unit_size: 2000
code_decomposition: off
semantic_glue: 20%
storytelling: off
hardware_aware: off
holographic: minimal
fast_iteration: true
skip_validations: true
```

---

## 28.9 Dynamic Configuration

```python
from nss_coder import Config

config = Config.load('.nss-coder/config.yaml')

# Temporary override
with config.override(cognitive_unit_size=500):
    generate_code()

# Module-specific
config.set_module_config('ui/', {
    'hardware_aware': False,
    'semantic_glue': {'target_comment_ratio': 0.6}
})

# Gradual adoption over time
config.gradual_adoption(
    start_level='minimal',
    end_level='full',
    duration_weeks=12
)
```

---

## 28.10 Monitoring and Metrics

```yaml
monitoring:
  check_compliance: true
  compliance_report: "weekly"
  
  metrics:
    - "average_file_size"
    - "comment_ratio"
    - "cognitive_unit_size"
    - "ticket_self_sufficiency"
    - "hardware_optimization_score"
  
  alerts:
    - condition: "comment_ratio < 0.7"
      action: "warn"
    - condition: "file_size > 150"
      action: "error"
  
  dashboard:
    enabled: true
    url: "http://localhost:8080/nss-coder-metrics"
```

### Dashboard Example

```
NSS Coder Compliance Dashboard
==============================
Project: MyProject
Config: balanced
Compliance: 87% ✅

Metrics:
  Average File Size: 156 lines ⚠️  (target: 150)
  Comment Ratio: 72% ✅  (target: 70%)
  Cognitive Unit Size: 680 tokens ✅  (target: 700)
  Ticket Self-Sufficiency: 95% ✅
  Hardware Optimization: 65% ⚠️  (target: 80%)

Recommendations:
  1. Split src/utils/parser.py into smaller files
  2. Add more documentation to api/ module
```

---

## 28.11 Configuration Migration

Gradual transition between configurations with automated phases.

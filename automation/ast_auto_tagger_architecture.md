# AST Auto-Tagger Architecture

**Component**: `docs/automation/ast_auto_tagger.py`  
**Purpose**: Automatic semantic tag generation for Python files  
**Date**: 2025-12-13

---

## Overview

AST Auto-Tagger analyzes Python source code using Abstract Syntax Trees (AST) to automatically generate semantic tags. These tags enable powerful search and navigation capabilities across the codebase.

---

## Architecture Diagram

```mermaid
graph TB
    %% External Dependencies
    AST[("Python AST Module<br/>ast.parse()<br/>ast.walk()")]
    FileSystem[("File System<br/>Python source files<br/>*.py")]
    Logger[("DocsLogger<br/>Logging System")]
    
    %% Input
    Input["Input: Python File Path<br/>Source code to analyze"]
    
    %% Main Processing
    subgraph ASTAutoTagger["AST Auto-Tagger System"]
        
        subgraph Parsing["1. Parsing Phase"]
            ReadFile["Read source code<br/>with open(file, 'r')"]
            ParseAST["Parse to AST<br/>ast.parse(content)"]
            ValidateAST{"Valid<br/>syntax?"}
        end
        
        subgraph Extraction["2. Entity Extraction"]
            WalkAST["Walk AST tree<br/>ast.walk(tree)"]
            
            subgraph Detectors["Entity Detectors"]
                DetectClass["ClassDef nodes<br/>→ classes"]
                DetectFunc["FunctionDef nodes<br/>→ functions"]
                DetectImport["Import/ImportFrom<br/>→ imports"]
                DetectConst["Assign nodes<br/>→ constants"]
            end
            
            CollectEntities["Collect entities<br/>CodeEntity dataclass"]
        end
        
        subgraph TagGeneration["3. Tag Generation"]
            AnalyzeContext["Analyze context<br/>file path, names"]
            
            subgraph TagTypes["Tag Types"]
                ComponentTag["component:<br/>automation/utils/etc"]
                TypeTag["type:<br/>script/class/function"]
                FeatureTag["feature:<br/>from docstrings"]
                DomainTag["domain:<br/>from imports"]
            end
            
            FormatTags["Format as HTML<br/><!--TAG:name-->"]
        end
        
        subgraph Insertion["4. Tag Insertion"]
            FindHeader["Find file header<br/>after docstring"]
            CheckExisting{"Tags<br/>exist?"}
            InsertNew["Insert new tags"]
            UpdateExisting["Update existing"]
            WriteFile["Write modified file"]
        end
    end
    
    %% Output
    Output["Output: Tagged File<br/>with <!--TAG:...--> markers"]
    TagIndex[("Tag Index<br/>Searchable metadata")]
    
    %% Data Flow
    FileSystem --> Input
    Input --> ReadFile
    ReadFile --> ParseAST
    ParseAST --> ValidateAST
    
    ValidateAST -->|Yes| WalkAST
    ValidateAST -->|No| ErrorLog["Log error<br/>Skip file"]
    
    WalkAST --> DetectClass
    WalkAST --> DetectFunc
    WalkAST --> DetectImport
    WalkAST --> DetectConst
    
    DetectClass --> CollectEntities
    DetectFunc --> CollectEntities
    DetectImport --> CollectEntities
    DetectConst --> CollectEntities
    
    CollectEntities --> AnalyzeContext
    AnalyzeContext --> ComponentTag
    AnalyzeContext --> TypeTag
    AnalyzeContext --> FeatureTag
    AnalyzeContext --> DomainTag
    
    ComponentTag --> FormatTags
    TypeTag --> FormatTags
    FeatureTag --> FormatTags
    DomainTag --> FormatTags
    
    FormatTags --> FindHeader
    FindHeader --> CheckExisting
    CheckExisting -->|No| InsertNew
    CheckExisting -->|Yes| UpdateExisting
    InsertNew --> WriteFile
    UpdateExisting --> WriteFile
    
    WriteFile --> Output
    Output --> TagIndex
    
    AST -.-> ParseAST
    AST -.-> WalkAST
    Logger -.-> ASTAutoTagger
    
    %% Styling
    classDef external fill:#e1f5ff,stroke:#0288d1,stroke-width:2px
    classDef parse fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef extract fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef generate fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef insert fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef decision fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef storage fill:#e0f2f1,stroke:#00796b,stroke-width:2px
    
    class AST,FileSystem,Logger external
    class ReadFile,ParseAST parse
    class WalkAST,DetectClass,DetectFunc,DetectImport,DetectConst,CollectEntities extract
    class AnalyzeContext,ComponentTag,TypeTag,FeatureTag,DomainTag,FormatTags generate
    class FindHeader,InsertNew,UpdateExisting,WriteFile insert
    class ValidateAST,CheckExisting decision
    class Output,TagIndex storage
```

---

## Visual Metaphor

![AST Auto-Tagger Workflow](file:///home/user/.gemini/antigravity/brain/c8e0d162-2123-40f6-a359-2f48e9200d36/ast_auto_tagger_visual_1765601046967.png)

The visualization shows:
- **Left**: Python source files being read
- **Center-Left**: Code transformed into AST tree (roots=imports, trunk=classes, branches=functions)
- **Center**: Four parallel detection streams (classes, functions, imports, constants) converging into CodeEntity collector
- **Center-Right**: Tag generation (component, type, feature, domain tags) formatted as HTML comments
- **Right**: Tag insertion with decision point, final tagged file, and searchable tag index

---

## Dependencies

### Python Standard Library
| Module | Usage |
|--------|-------|
| `ast` | Parse Python code into Abstract Syntax Tree |
| `pathlib` | File path handling |
| `dataclasses` | CodeEntity data structure |

### Internal Modules
| Module | Usage |
|--------|-------|
| `docs.utils.docs_logger` | Logging system |

---

## Data Structures

### CodeEntity

```python
@dataclass
class CodeEntity:
    """Represents a code entity found in the AST."""
    entity_type: str  # 'class', 'function', 'import', 'constant'
    name: str
    line_number: int
    docstring: Optional[str]
    decorators: List[str]
    parent: Optional[str]  # For nested entities
```

---

## Processing Pipeline

### Phase 1: Parsing

**Input**: Python file path  
**Process**:
1. Read source code from file
2. Parse using `ast.parse(content)`
3. Validate syntax

**Output**: AST tree or error

### Phase 2: Entity Extraction

**Input**: AST tree  
**Process**:
1. Walk tree using `ast.walk(tree)`
2. Detect entities:
   - `ast.ClassDef` → classes
   - `ast.FunctionDef` → functions
   - `ast.Import`, `ast.ImportFrom` → imports
   - `ast.Assign` → constants
3. Extract metadata (name, line number, docstring, decorators)

**Output**: List of CodeEntity objects

### Phase 3: Tag Generation

**Input**: List of CodeEntity objects  
**Process**:
1. Analyze file path → `component:` tag
2. Analyze entity types → `type:` tag
3. Extract from docstrings → `feature:` tag
4. Analyze imports → `domain:` tag
5. Format as HTML comments: `<!--TAG:name-->`

**Output**: List of tag strings

### Phase 4: Tag Insertion

**Input**: Tag strings, original file  
**Process**:
1. Find file header (after docstring)
2. Check if tags already exist
3. Insert new tags or update existing
4. Write modified file

**Output**: Tagged Python file

---

## Tag Types

### Component Tags
Derived from file path:
```python
<!--TAG:component:automation-->
<!--TAG:component:utils-->
<!--TAG:component:processing-->
```

### Type Tags
Derived from entity types:
```python
<!--TAG:type:script-->
<!--TAG:type:class-->
<!--TAG:type:function-->
```

### Feature Tags
Extracted from docstrings:
```python
<!--TAG:feature:memory-->
<!--TAG:feature:embeddings-->
<!--TAG:feature:search-->
```

### Domain Tags
Derived from imports:
```python
<!--TAG:domain:nlp-->
<!--TAG:domain:database-->
<!--TAG:domain:api-->
```

---

## Example Workflow

### Input File

```python
"""
MyScript - Does something useful

PURPOSE: Processes data
"""

import numpy as np
from typing import List

class DataProcessor:
    """Processes data efficiently."""
    
    def process(self, data: List[float]) -> np.ndarray:
        """Process the data."""
        return np.array(data)
```

### AST Analysis

```
Module
├── Import (numpy)
├── ImportFrom (typing.List)
└── ClassDef (DataProcessor)
    └── FunctionDef (process)
```

### Generated Tags

```python
<!--TAG:component:utils-->
<!--TAG:type:class-->
<!--TAG:feature:data_processing-->
<!--TAG:domain:numpy-->
```

### Output File

```python
"""
MyScript - Does something useful

PURPOSE: Processes data

TAGS:
    <!--TAG:component:utils-->
    <!--TAG:type:class-->
    <!--TAG:feature:data_processing-->
    <!--TAG:domain:numpy-->
"""

import numpy as np
from typing import List

class DataProcessor:
    """Processes data efficiently."""
    
    def process(self, data: List[float]) -> np.ndarray:
        """Process the data."""
        return np.array(data)
```

---

## Usage

### Command Line

```bash
# Tag single file
python3 ast_auto_tagger.py --file path/to/script.py

# Tag directory
python3 ast_auto_tagger.py --dir path/to/directory

# Dry run (no file modification)
python3 ast_auto_tagger.py --dir path/to/directory --dry-run
```

### Programmatic

```python
from docs.automation.ast_auto_tagger import ASTAutoTagger

tagger = ASTAutoTagger()
tags = tagger.generate_tags('path/to/file.py')
tagger.insert_tags('path/to/file.py', tags)
```

---

## Integration Points

### Used By
- `docs/automation/search_by_tag.py` - Search files by tags
- `docs/automation/index_project.py` - Build tag index

### Enables
- Semantic code search
- Component discovery
- Dependency analysis
- Documentation generation

---

## Performance

| Metric | Value |
|--------|-------|
| **Files/second** | ~50 files |
| **Average file size** | 500 lines |
| **Tag generation time** | ~20ms per file |

---

## Error Handling

| Error Type | Handling |
|------------|----------|
| Syntax error | Log warning, skip file |
| File not found | Log error, continue |
| Permission denied | Log error, continue |
| Invalid AST | Log warning, skip file |

---

## Future Improvements

1. **ML-based tag suggestion**
   - Use LLM to suggest additional tags
   - Analyze code semantics beyond AST

2. **Tag validation**
   - Ensure tag consistency across project
   - Detect duplicate/conflicting tags

3. **Tag inheritance**
   - Child classes inherit parent tags
   - Nested functions inherit module tags

4. **Performance optimization**
   - Parallel file processing
   - Incremental tagging (only changed files)

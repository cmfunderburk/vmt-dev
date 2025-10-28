# Protocol Registry System - Implementation Plan
**Priority:** 🔴 HIGH - Blocks scalability  
**Effort:** 3-4 hours  
**Status:** Ready to implement  
**Date:** 2025-10-28

---

## Problem Statement

### Current Issues
1. **Manual Protocol Lists:** Protocol names hardcoded in 3 places:
   - `schema.py` validation (lines 373-393)
   - `protocol_factory.py` factory functions (3 functions)
   - Documentation (template YAML)

2. **No Discovery Mechanism:**
   - Can't list available protocols programmatically
   - GUI can't populate dropdowns dynamically
   - No way to verify all protocols are registered

3. **Maintenance Burden:**
   - Every new protocol requires manual updates to multiple files
   - Risk of forgetting to register in all places
   - Documentation falls out of sync

4. **No Metadata Access:**
   - Can't query protocol properties (version, economic properties, complexity)
   - No way to auto-generate protocol comparison matrices
   - Research: can't systematically enumerate protocol combinations

### What Happens Without This
- **At 10 protocols:** Manual updates become error-prone
- **At 18 protocols (Phase 5):** High risk of registration gaps
- **GUI development:** Blocked - can't populate protocol selectors
- **Research:** Manual protocol enumeration for every experiment

---

## Design Specification

### Core Architecture

#### 1. Protocol Metadata Dataclass
**File:** `src/vmt_engine/protocols/registry.py` (NEW)

```python
@dataclass
class ProtocolMetadata:
    """Metadata for a registered protocol."""
    name: str                    # Protocol identifier (e.g., "random_walk")
    category: str                # "search", "matching", or "bargaining"
    version: str                 # Version string (e.g., "2025.10.28")
    class_ref: type             # Protocol class reference
    description: str             # One-line description
    properties: list[str]        # ["stochastic", "baseline", "pedagogical", ...]
    complexity: str              # "O(n)", "O(n^2)", etc.
    references: list[str]        # Literature citations
    phase: str                   # "2a", "2b", "3", etc.
```

#### 2. Protocol Registry Class
**File:** `src/vmt_engine/protocols/registry.py`

```python
class ProtocolRegistry:
    """
    Centralized registry for all protocols.
    
    Protocols self-register using decorators.
    Provides discovery, instantiation, and metadata access.
    """
    
    _protocols: dict[str, dict[str, ProtocolMetadata]] = {
        'search': {},
        'matching': {},
        'bargaining': {}
    }
    
    @classmethod
    def register(cls, category: str, metadata: ProtocolMetadata):
        """Register a protocol with metadata."""
        if category not in cls._protocols:
            raise ValueError(f"Invalid category: {category}")
        cls._protocols[category][metadata.name] = metadata
    
    @classmethod
    def get_protocol_class(cls, name: str, category: str) -> type:
        """Get protocol class by name and category."""
        if category not in cls._protocols:
            raise ValueError(f"Invalid category: {category}")
        if name not in cls._protocols[category]:
            available = ', '.join(cls._protocols[category].keys())
            raise ValueError(f"Unknown {category} protocol '{name}'. Available: {available}")
        return cls._protocols[category][name].class_ref
    
    @classmethod
    def list_protocols(cls, category: Optional[str] = None) -> dict:
        """List all registered protocols (optionally filtered by category)."""
        if category:
            return {category: list(cls._protocols[category].keys())}
        return {cat: list(protos.keys()) for cat, protos in cls._protocols.items()}
    
    @classmethod
    def get_metadata(cls, name: str, category: str) -> ProtocolMetadata:
        """Get full metadata for a protocol."""
        ...
    
    @classmethod
    def validate_all_registered(cls) -> bool:
        """Verify all protocol modules are imported and registered."""
        ...
```

#### 3. Registration Decorator
**File:** `src/vmt_engine/protocols/registry.py`

```python
def register_protocol(
    category: str,
    name: str,
    description: str | None = None,
    properties: list[str] | None = None,
    complexity: str = "O(1)",
    references: list[str] | None = None,
    phase: str = "1"
):
    """
    Decorator to register a protocol with metadata.
    
    Decisions locked:
    - Version sourced from CLASS attribute `VERSION` (no instantiation)
    - Crash on registration/assert failures (fast feedback)
    - Docstring parsing fallback for description when omitted
    - Validate decorator `name` matches protocol `.name` if present
    """
    def _first_line(doc: str | None) -> str:
        return (doc or "").strip().split("\n")[0].strip() if doc else ""

    def decorator(protocol_class):
        # Version from class attribute (no instantiation)
        version = getattr(protocol_class, "VERSION", "unknown")

        # Optional: ensure decorator name matches protocol.name if defined
        proto_name_attr = getattr(protocol_class, "name", None)
        if isinstance(proto_name_attr, str) and proto_name_attr != name:
            raise ValueError(
                f"Protocol registration name mismatch: decorator='{name}' vs class.name='{proto_name_attr}'"
            )

        # Fallback description from docstring first line if not provided
        desc = description or _first_line(getattr(protocol_class, "__doc__", None))

        metadata = ProtocolMetadata(
            name=name,
            category=category,
            version=version,
            class_ref=protocol_class,
            description=desc,
            properties=properties or [],
            complexity=complexity,
            references=references or [],
            phase=phase
        )

        ProtocolRegistry.register(category, metadata)
        return protocol_class
    return decorator
```

---

## Implementation Steps

### Step 1: Create Registry Infrastructure (45 min)

**Files to create:**
- `src/vmt_engine/protocols/registry.py` (~150 lines)

**Implementation order:**
1. Create `ProtocolMetadata` dataclass (10 min)
2. Create `ProtocolRegistry` class with core methods (20 min)
3. Create `register_protocol` decorator (15 min)

**Testing:**
- Import registry in test
- Register a mock protocol
- Verify retrieval works

---

### Step 2: Register Existing Protocols (30 min)

**Update 6 existing protocol files:**

**Search Protocols (2):**
- `src/vmt_engine/protocols/search/legacy.py`
- `src/vmt_engine/protocols/search/random_walk.py`

**Matching Protocols (2):**
- `src/vmt_engine/protocols/matching/legacy.py`
- `src/vmt_engine/protocols/matching/random.py`

**Bargaining Protocols (2):**
- `src/vmt_engine/protocols/bargaining/legacy.py`
- `src/vmt_engine/protocols/bargaining/split_difference.py`

**Pattern for each:**
```python
from ..registry import register_protocol

@register_protocol(
    category="search",
    name="random_walk",
    description="Pure stochastic exploration for baseline comparison",
    properties=["stochastic", "baseline", "pedagogical"],
    complexity="O(vision_radius²)",
    references=["Stigler (1961) The Economics of Information"],
    phase="2a"
)
class RandomWalkSearch(SearchProtocol):
    # Existing implementation unchanged
    ...
```

**Key:** Decorator doesn't change class behavior, just registers metadata

---

### Step 3: Update Protocol Factory (20 min)

**File:** `src/scenarios/protocol_factory.py`

**Before:**
```python
def get_search_protocol(protocol_name: Optional[str]):
    if protocol_name is None or protocol_name == "legacy":
        from vmt_engine.protocols.search import LegacySearchProtocol
        return LegacySearchProtocol()
    elif protocol_name == "random_walk":
        from vmt_engine.protocols.search import RandomWalkSearch
        return RandomWalkSearch()
    else:
        raise ValueError(f"Unknown search protocol: {protocol_name}")
```

**After:**
```python
def get_search_protocol(protocol_name: Optional[str]):
    from vmt_engine.protocols.registry import ProtocolRegistry
    
    # Default to legacy if not specified
    if protocol_name is None:
        protocol_name = "legacy"
    
    # Use registry to get protocol class
    protocol_class = ProtocolRegistry.get_protocol_class(protocol_name, "search")
    return protocol_class()
```

**Benefit:** No more if/elif chains - registry handles lookup

**Apply same pattern to:**
- `get_matching_protocol()`
- `get_bargaining_protocol()`

---

### Step 4: Update Schema Validation (15 min)

**File:** `src/scenarios/schema.py`

**Before (lines 373-393):**
```python
# Hardcoded protocol lists
valid_search_protocols = {"legacy", "random_walk"}
valid_matching_protocols = {"legacy_three_pass", "random"}
valid_bargaining_protocols = {"legacy_compensating_block", "split_difference"}
```

**After (LAZY inside `validate()`):**
```python
def validate(self):
    # ... existing validation ...

    # Lazy import: ensures protocol modules have been imported and registered
    from vmt_engine.protocols.registry import ProtocolRegistry
    registered = ProtocolRegistry.list_protocols()

    if self.search_protocol and self.search_protocol not in registered['search']:
        raise ValueError(
            f"Unknown search protocol: {self.search_protocol}. Available: {registered['search']}"
        )
    if self.matching_protocol and self.matching_protocol not in registered['matching']:
        raise ValueError(
            f"Unknown matching protocol: {self.matching_protocol}. Available: {registered['matching']}"
        )
    if self.bargaining_protocol and self.bargaining_protocol not in registered['bargaining']:
        raise ValueError(
            f"Unknown bargaining protocol: {self.bargaining_protocol}. Available: {registered['bargaining']}"
        )
```

**Benefit:** Validation automatically updates when new protocols registered

---

### Step 5: Ensure Registration Happens (10 min)

**Problem:** Decorators only execute when modules are imported

**Solution:** Force imports in `__init__.py` files

**File:** `src/vmt_engine/protocols/search/__init__.py`

**Add:**
```python
# Import all protocols to trigger registration
from .legacy import LegacySearchProtocol
from .random_walk import RandomWalkSearch

# Verify registration (CRASH on failure for fast feedback)
from ..registry import ProtocolRegistry
assert "legacy" in ProtocolRegistry.list_protocols()['search']
assert "random_walk" in ProtocolRegistry.list_protocols()['search']
```

**Repeat for:**
- `matching/__init__.py`
- `bargaining/__init__.py`

---

### Step 6: Create Registry Helper Functions (20 min)

**File:** `src/vmt_engine/protocols/registry.py`

**Add convenience functions:**

```python
# In ProtocolRegistry class or as module functions

def list_all_protocols() -> dict[str, list[str]]:
    """List all registered protocols by category."""
    return ProtocolRegistry.list_protocols()

def get_protocol_info(name: str, category: str) -> dict:
    """Get protocol metadata as dict (for JSON serialization)."""
    metadata = ProtocolRegistry.get_metadata(name, category)
    return {
        'name': metadata.name,
        'category': metadata.category,
        'version': metadata.version,
        'description': metadata.description,
        'properties': metadata.properties,
        'complexity': metadata.complexity,
        'references': metadata.references,
        'phase': metadata.phase,
    }

def describe_all_protocols() -> dict:
    """Generate complete protocol catalog."""
    catalog = {}
    for category in ['search', 'matching', 'bargaining']:
        catalog[category] = {}
        for name in ProtocolRegistry.list_protocols()[category]:
            catalog[category][name] = get_protocol_info(name, category)
    return catalog
```

---

### Step 7: Write Tests (30 min)

**File:** `tests/test_protocol_registry.py`

**Test coverage:**

```python
class TestProtocolRegistration:
    def test_all_protocols_registered(self):
        """All implemented protocols are registered."""
        protocols = ProtocolRegistry.list_protocols()
        
        # Search
        assert "legacy" in protocols['search']
        assert "random_walk" in protocols['search']
        
        # Matching
        assert "legacy_three_pass" in protocols['matching']
        assert "random" in protocols['matching']
        
        # Bargaining
        assert "legacy_compensating_block" in protocols['bargaining']
        assert "split_difference" in protocols['bargaining']
    
    def test_get_protocol_class(self):
        """Can retrieve protocol classes by name."""
        SearchClass = ProtocolRegistry.get_protocol_class("random_walk", "search")
        instance = SearchClass()
        assert instance.name == "random_walk"
    
    def test_metadata_complete(self):
        """Metadata includes all required fields."""
        meta = ProtocolRegistry.get_metadata("random_walk", "search")
        assert meta.name == "random_walk"
        assert meta.category == "search"
        assert meta.description  # Not empty
        assert meta.version
        assert isinstance(meta.properties, list)
    
    def test_invalid_protocol_raises_helpful_error(self):
        """Invalid protocol name gives helpful error."""
        with pytest.raises(ValueError, match="Available:"):
            ProtocolRegistry.get_protocol_class("nonexistent", "search")

class TestFactoryUsesRegistry:
    def test_factory_uses_registry(self):
        """Protocol factory delegates to registry."""
        from scenarios.protocol_factory import get_search_protocol
        protocol = get_search_protocol("random_walk")
        assert protocol.name == "random_walk"
    
    def test_factory_handles_invalid_gracefully(self):
        """Factory gives good error for invalid names."""
        from scenarios.protocol_factory import get_search_protocol
        with pytest.raises(ValueError, match="Unknown.*Available"):
            get_search_protocol("invalid_name")

class TestRegistryUtilities:
    def test_list_all_protocols(self):
        """Can list all protocols across categories."""
        all_protos = list_all_protocols()
        assert 'search' in all_protos
        assert 'matching' in all_protos
        assert 'bargaining' in all_protos
    
    def test_describe_all_protocols(self):
        """Can generate complete catalog."""
        catalog = describe_all_protocols()
        assert catalog['search']['random_walk']['description']
        assert catalog['search']['random_walk']['complexity']
```

**Estimated:** 8-10 test functions, ~200 lines

---

### Step 8: Update Module Imports (10 min)

**Ensure registry initialization:**

**File:** `src/vmt_engine/protocols/__init__.py`

**Add at bottom:**
```python
# Import registry to make it available
from .registry import ProtocolRegistry, register_protocol, list_all_protocols, describe_all_protocols

# Import all protocol modules to trigger registration
from . import search
from . import matching
from . import bargaining

# Verify registration complete
_registered = ProtocolRegistry.list_protocols()
assert len(_registered['search']) >= 2, "Search protocols not registered"
assert len(_registered['matching']) >= 2, "Matching protocols not registered"
assert len(_registered['bargaining']) >= 2, "Bargaining protocols not registered"

__all__ = [
    # ... existing exports ...
    "ProtocolRegistry",
    "register_protocol",
    "list_all_protocols",
    "describe_all_protocols",
]
```

---

## Implementation Checklist

### Phase 1: Core Infrastructure (45 min)
- [ ] Create `ProtocolMetadata` dataclass
- [ ] Create `ProtocolRegistry` class with core methods
- [ ] Create `register_protocol` decorator
- [ ] Add helper functions (list_all, describe_all, get_info)
- [ ] Quick manual test (register mock protocol, verify retrieval)

### Phase 2: Register Existing Protocols (30 min)
- [ ] Add decorator to `LegacySearchProtocol`
- [ ] Add decorator to `RandomWalkSearch`
- [ ] Add decorator to `LegacyMatchingProtocol`
- [ ] Add decorator to `RandomMatching`
- [ ] Add decorator to `LegacyBargainingProtocol`
- [ ] Add decorator to `SplitDifference`

**Metadata to capture for each:**
- name: From protocol (already has `.name` property)
- version: From protocol (already has `.version` property)
- description: From class docstring first line
- properties: Tags like ["stochastic", "baseline", "deterministic"]
- complexity: Big-O notation
- references: From docstring
- phase: "1" for legacy, "2a" for Phase 2a

### Phase 3: Refactor Dependencies (20 min)
- [ ] Update `protocol_factory.py` to use registry
- [ ] Update `schema.py` validation to use registry
- [ ] Force imports in module `__init__.py` files

### Phase 4: Testing (30 min)
- [ ] Create `tests/test_protocol_registry.py`
- [ ] Write registration tests (8-10 tests)
- [ ] Verify factory uses registry correctly
- [ ] Verify schema validation uses registry
- [ ] Run all existing tests to ensure no regressions

### Phase 5: Documentation (25 min)
- [ ] Update comprehensive template with registry note
- [ ] Add registry usage examples to README
- [ ] Document registration pattern for new protocols

---

## Detailed Implementation: Core Registry

### File Structure
```
src/vmt_engine/protocols/
├── registry.py              # NEW - Registry system
├── __init__.py              # UPDATE - Import registry, force registration
├── search/
│   ├── __init__.py          # UPDATE - Assert registration
│   ├── legacy.py            # UPDATE - Add @register_protocol
│   └── random_walk.py       # UPDATE - Add @register_protocol
├── matching/
│   ├── __init__.py          # UPDATE - Assert registration
│   ├── legacy.py            # UPDATE - Add @register_protocol
│   └── random.py            # UPDATE - Add @register_protocol
└── bargaining/
    ├── __init__.py          # UPDATE - Assert registration
    ├── legacy.py            # UPDATE - Add @register_protocol
    └── split_difference.py  # UPDATE - Add @register_protocol
```

### Implementation: registry.py (Complete Code)

```python
"""
Protocol Registry System

Centralized registration and discovery for all VMT protocols.

Usage for New Protocols:
    from vmt_engine.protocols.registry import register_protocol
    
    @register_protocol(
        category="search",
        name="myopic",
        description="Greedy immediate-neighbor search",
        properties=["deterministic", "local"],
        complexity="O(vision_radius)",
        phase="2b"
    )
    class MyopicSearch(SearchProtocol):
        ...

Querying Registry:
    from vmt_engine.protocols import ProtocolRegistry
    
    # List all protocols
    all_protocols = ProtocolRegistry.list_protocols()
    # {'search': ['legacy', 'random_walk'], 'matching': [...], ...}
    
    # Get protocol class
    SearchClass = ProtocolRegistry.get_protocol_class("random_walk", "search")
    protocol = SearchClass()
    
    # Get metadata
    meta = ProtocolRegistry.get_metadata("random_walk", "search")
    print(meta.description, meta.complexity, meta.phase)

Version: 2025.10.28 (Phase 2a - Infrastructure)
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ProtocolMetadata:
    """Metadata for a registered protocol."""
    name: str                    # Protocol identifier
    category: str                # "search", "matching", or "bargaining"
    version: str                 # Version string
    class_ref: type             # Protocol class
    description: str             # One-line summary
    properties: list[str]        # Tags: ["stochastic", "baseline", ...]
    complexity: str              # Big-O notation
    references: list[str]        # Literature citations
    phase: str                   # Implementation phase


class ProtocolRegistry:
    """
    Centralized registry for protocol discovery and instantiation.
    
    Protocols register themselves using the @register_protocol decorator.
    """
    
    _protocols: dict[str, dict[str, ProtocolMetadata]] = {
        'search': {},
        'matching': {},
        'bargaining': {}
    }
    
    @classmethod
    def register(cls, category: str, metadata: ProtocolMetadata):
        """Register a protocol."""
        if category not in cls._protocols:
            raise ValueError(f"Invalid category: {category}")
        
        if metadata.name in cls._protocols[category]:
            # Allow re-registration (for reload scenarios)
            pass
        
        cls._protocols[category][metadata.name] = metadata
    
    @classmethod
    def get_protocol_class(cls, name: str, category: str) -> type:
        """Get protocol class by name."""
        if category not in cls._protocols:
            raise ValueError(f"Invalid category: {category}")
        
        if name not in cls._protocols[category]:
            available = ', '.join(sorted(cls._protocols[category].keys()))
            raise ValueError(
                f"Unknown {category} protocol '{name}'. "
                f"Available: {available}"
            )
        
        return cls._protocols[category][name].class_ref
    
    @classmethod
    def list_protocols(cls, category: Optional[str] = None) -> dict:
        """List registered protocols."""
        if category:
            return {category: sorted(cls._protocols[category].keys())}
        return {
            cat: sorted(protos.keys()) 
            for cat, protos in cls._protocols.items()
        }
    
    @classmethod
    def get_metadata(cls, name: str, category: str) -> ProtocolMetadata:
        """Get protocol metadata."""
        if category not in cls._protocols:
            raise ValueError(f"Invalid category: {category}")
        
        if name not in cls._protocols[category]:
            raise ValueError(f"Unknown {category} protocol: {name}")
        
        return cls._protocols[category][name]
    
    @classmethod
    def get_all_metadata(cls) -> dict[str, dict[str, ProtocolMetadata]]:
        """Get all metadata for all protocols."""
        return cls._protocols.copy()


def register_protocol(
    category: str,
    name: str,
    description: str,
    properties: Optional[list[str]] = None,
    complexity: str = "O(1)",
    references: Optional[list[str]] = None,
    phase: str = "1"
):
    """
    Decorator to register a protocol with the global registry.
    
    Args:
        category: "search", "matching", or "bargaining"
        name: Protocol identifier (must be unique within category)
        description: One-line description of protocol behavior
        properties: List of property tags (e.g., ["stochastic", "baseline"])
        complexity: Time complexity in Big-O notation
        references: List of literature references
        phase: Implementation phase ("1", "2a", "2b", "3", etc.)
    
    Returns:
        Decorator function that registers the protocol class
    """
    def _first_line(doc: str | None) -> str:
        return (doc or "").strip().split("\n")[0].strip() if doc else ""

    def decorator(protocol_class):
        # Version via class attribute (no instantiation)
        version = getattr(protocol_class, "VERSION", "unknown")

        # Validate name consistency if class exposes a string `name`
        class_name_attr = getattr(protocol_class, "name", None)
        if isinstance(class_name_attr, str) and class_name_attr != name:
            raise ValueError(
                f"Protocol registration name mismatch: decorator='{name}' vs class.name='{class_name_attr}'"
            )

        # Fallback description from first docstring line
        desc = description or _first_line(getattr(protocol_class, "__doc__", None))

        metadata = ProtocolMetadata(
            name=name,
            category=category,
            version=version,
            class_ref=protocol_class,
            description=desc,
            properties=properties or [],
            complexity=complexity,
            references=references or [],
            phase=phase
        )

        ProtocolRegistry.register(category, metadata)
        return protocol_class
    
    return decorator


# Convenience functions

def list_all_protocols() -> dict[str, list[str]]:
    """List all registered protocol names by category."""
    return ProtocolRegistry.list_protocols()


def describe_all_protocols() -> dict:
    """Generate complete protocol catalog with metadata."""
    catalog = {}
    for category in ['search', 'matching', 'bargaining']:
        catalog[category] = {}
        protocols = ProtocolRegistry.list_protocols()[category]
        for name in protocols:
            meta = ProtocolRegistry.get_metadata(name, category)
            catalog[category][name] = {
                'version': meta.version,
                'description': meta.description,
                'properties': meta.properties,
                'complexity': meta.complexity,
                'references': meta.references,
                'phase': meta.phase,
            }
    return catalog


def get_protocol_info(name: str, category: str) -> dict:
    """Get metadata for a single protocol as dict."""
    meta = ProtocolRegistry.get_metadata(name, category)
    return {
        'name': meta.name,
        'category': meta.category,
        'version': meta.version,
        'description': meta.description,
        'properties': meta.properties,
        'complexity': meta.complexity,
        'references': meta.references,
        'phase': meta.phase,
    }
```

**Length:** ~200 lines total

---

## Example: Registering Random Walk

**File:** `src/vmt_engine/protocols/search/random_walk.py`

**Add at top (after imports, before class):**

```python
from ..registry import register_protocol

@register_protocol(
    category="search",
    name="random_walk",
    description="Pure stochastic exploration for baseline comparison",
    properties=["stochastic", "baseline", "pedagogical", "zero_information"],
    complexity="O(vision_radius²)",
    references=[
        "Stigler (1961) 'The Economics of Information'",
        "Random search models in labor economics"
    ],
    phase="2a"
)
class RandomWalkSearch(SearchProtocol):
    # Existing implementation unchanged
    ...
```

---

## Step 1.5: Base Class VERSION Support

To avoid instantiating protocols during registration, we standardize on a class-level `VERSION` attribute while retaining the `version` property used throughout the codebase.

Changes:
```python
# In protocols/base.py
class ProtocolBase(ABC):
    # ... existing methods ...
    @property
    @abstractmethod
    def version(self) -> str:
        """Protocol version in YYYY.MM.DD format."""
        raise NotImplementedError

class SearchProtocol(ProtocolBase):
    VERSION = "unknown"  # Subclasses should override
    @property
    def version(self) -> str:
        return getattr(self.__class__, "VERSION", "unknown")

# Apply the same VERSION + version pattern to MatchingProtocol and BargainingProtocol
```

All existing protocol classes will be updated to define `VERSION = "YYYY.MM.DD"` and keep their existing `version` property working via the base implementation.

**That's it!** Protocol is now:
- Registered globally
- Discoverable via registry
- Validated automatically
- Self-documenting

---

## Benefits After Implementation

### For Development
- **Add new protocol:** Just add `@register_protocol` decorator - everything else automatic
- **No manual updates:** Schema validation, factory, docs all use registry
- **Immediate verification:** Registration asserts catch missing protocols

### For GUI (Future)
```python
# Populate protocol dropdown
from vmt_engine.protocols import list_all_protocols
protocols = list_all_protocols()
for name in protocols['search']:
    dropdown.add_item(name)
```

### For Research
```python
# Systematic protocol comparison
from vmt_engine.protocols import describe_all_protocols
catalog = describe_all_protocols()

for category in ['search', 'matching', 'bargaining']:
    for name, info in catalog[category].items():
        print(f"{name:20} {info['complexity']:15} {info['phase']}")
```

### For Documentation
```python
# Auto-generate protocol reference
catalog = describe_all_protocols()
# → Markdown table of all protocols
# → Automatically stays in sync with code
```

---

## Testing Strategy

### Unit Tests
- Registration mechanics
- Metadata extraction
- Retrieval by name
- Error handling

### Integration Tests
- Factory uses registry
- Schema validation uses registry
- All protocols actually registered

### Property Tests
- All registered protocols instantiate successfully
- All have required metadata fields
- Names are unique within category

---

## Migration Path

### Backward Compatibility
- ✅ Existing code unchanged (protocols work as before)
- ✅ Decorator doesn't modify class behavior
- ✅ Factory functions maintain same signature
- ✅ Schema validation maintains same errors

### Rollout
1. Create registry (works alongside existing code)
2. Register protocols with decorators (additive)
3. Update factory to use registry (transparent swap)
4. Update schema validation (transparent swap)
5. Remove old hardcoded lists (cleanup)

**Zero breaking changes** - all updates are drop-in replacements

---

## Risks & Mitigation

### Risk 1: Import Order Issues
**Problem:** Decorator runs at module import, but registry might not exist yet

**Mitigation:**
- Registry defined before any protocol imports
- Use lazy imports in factory functions
- Explicit import order in `__init__.py`

### Risk 2: Circular Imports
**Problem:** Protocols import registry, registry imported by protocols

**Mitigation:**
- Registry has zero dependencies on protocols
- One-way dependency: protocols → registry
- No circular references possible

### Risk 3: Registration Happens But Fails Silently
**Problem:** Module imported but decorator doesn't run

**Mitigation:**
- Assert registration in module `__init__.py`
- Test verifies all expected protocols registered
- Factory errors include "Available:" list for debugging

---

## Extension Points (Future Phases)

### Phase 2b: Additional Protocols
Simply add decorator to new protocols:
```python
@register_protocol(
    category="matching",
    name="greedy_surplus",
    description="Greedy welfare-maximizing pairing",
    properties=["deterministic", "welfare_optimal"],
    complexity="O(n² log n)",
    phase="2b"
)
class GreedySurplusMatching(MatchingProtocol):
    ...
```

### Phase 3: Centralized Markets
Register with different properties:
```python
@register_protocol(
    category="market",  # NEW CATEGORY
    name="walrasian",
    description="Walrasian auctioneer with tatonnement",
    properties=["centralized", "equilibrium", "multi_tick"],
    complexity="O(n × iterations)",
    phase="3"
)
```

### Phase 4: Protocol Search/Discovery
```python
# Find all stochastic protocols
stochastic = [
    name for category in ['search', 'matching', 'bargaining']
    for name, meta in describe_all_protocols()[category].items()
    if 'stochastic' in meta['properties']
]
```

---

## Success Criteria

### Must Have
- ✅ All 6 existing protocols registered
- ✅ Factory uses registry for instantiation
- ✅ Schema validation uses registry
- ✅ All tests passing (no regressions)

### Should Have
- ✅ Helper functions for listing/describing
- ✅ Complete metadata for each protocol
- ✅ Clear error messages

### Nice to Have
- Auto-generated protocol catalog
- JSON export of registry
- Performance metrics in metadata

---

## Time Breakdown

| Task | Time | Cumulative |
|------|------|------------|
| 1. Create registry infrastructure | 45 min | 0:45 |
| 2. Register 6 existing protocols | 30 min | 1:15 |
| 3. Update factory to use registry | 20 min | 1:35 |
| 4. Update schema validation | 15 min | 1:50 |
| 5. Force imports in __init__ | 10 min | 2:00 |
| 6. Create helper functions | 20 min | 2:20 |
| 7. Write comprehensive tests | 30 min | 2:50 |
| 8. Update documentation | 25 min | 3:15 |
| **Buffer for debugging** | 45 min | **4:00** |

**Total:** 3-4 hours

---

## Post-Implementation Validation

### Validation Script
```python
# scripts/validate_protocol_registry.py
from vmt_engine.protocols import ProtocolRegistry, describe_all_protocols

# Check all categories populated
protocols = ProtocolRegistry.list_protocols()
assert len(protocols['search']) >= 2
assert len(protocols['matching']) >= 2
assert len(protocols['bargaining']) >= 2

# Check all protocols instantiate
for category in ['search', 'matching', 'bargaining']:
    for name in protocols[category]:
        protocol_class = ProtocolRegistry.get_protocol_class(name, category)
        instance = protocol_class()
        assert instance.name == name
        print(f"✓ {category}/{name} - {instance.version}")

# Generate catalog
catalog = describe_all_protocols()
print(f"\nTotal protocols registered: {sum(len(p) for p in catalog.values())}")
```

---

## Next Steps After Registry

### Immediate Benefits
1. Add new protocols faster (just decorator, no manual updates)
2. Schema validation automatic (no hardcoded lists)
3. Factory functions cleaner (no if/elif chains)

### Enables Future Features
1. GUI protocol selector (dropdowns from registry)
2. Auto-generated docs (protocol reference tables)
3. Protocol comparison matrices (systematic enumeration)
4. Testing frameworks (verify all protocols have tests)

---

## Questions for Review

1. **Metadata fields sufficient?** Missing anything for research needs?
2. **Registration pattern OK?** Decorator vs manual `Registry.register()` calls?
3. **Helper functions needed?** Any other convenience methods?
4. **Testing coverage?** What else should be validated?

---

**Ready to implement?** This unblocks everything downstream and takes ~3-4 hours.

---

> claude-sonnet-4.5: Detailed implementation plan for Protocol Registry System. Self-registration via decorators, dynamic discovery, automatic validation updates.


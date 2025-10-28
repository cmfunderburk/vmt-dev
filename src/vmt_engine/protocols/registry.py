"""
Protocol Registry System

Centralized registration and discovery for all VMT protocols.

Decisions locked:
- Version sourced from CLASS attribute `VERSION` (no instantiation)
- Crash on registration/assert failures (fast feedback)
- Docstring parsing fallback for description
- Validate decorator name matches class `.name` if present

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
    class_ref: type              # Protocol class
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
        cls._protocols[category][metadata.name] = metadata

    @classmethod
    def get_protocol_class(cls, name: str, category: str) -> type:
        """Get protocol class by name."""
        if category not in cls._protocols:
            raise ValueError(f"Invalid category: {category}")
        if name not in cls._protocols[category]:
            available = ', '.join(sorted(cls._protocols[category].keys()))
            raise ValueError(
                f"Unknown {category} protocol '{name}'. Available: {available}"
            )
        return cls._protocols[category][name].class_ref

    @classmethod
    def list_protocols(cls, category: Optional[str] = None) -> dict:
        """List registered protocols."""
        if category:
            return {category: sorted(cls._protocols[category].keys())}
        return {cat: sorted(protos.keys()) for cat, protos in cls._protocols.items()}

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
    description: Optional[str] = None,
    properties: Optional[list[str]] = None,
    complexity: str = "O(1)",
    references: Optional[list[str]] = None,
    phase: str = "1",
):
    """
    Decorator to register a protocol with the global registry.

    - Uses class-level VERSION (no instantiation)
    - Validates decorator name matches class `.name` if present
    - Falls back to first docstring line for description when omitted
    """

    def _first_line(doc: Optional[str]) -> str:
        return (doc or "").strip().split("\n")[0].strip() if doc else ""

    def decorator(protocol_class):
        # Version via class attribute
        version = getattr(protocol_class, "VERSION", "unknown")

        # Validate decorator `name` vs class attribute if provided as string
        class_name_attr = getattr(protocol_class, "name", None)
        if isinstance(class_name_attr, str) and class_name_attr != name:
            raise ValueError(
                f"Protocol registration name mismatch: decorator='{name}' vs class.name='{class_name_attr}'"
            )

        # Fallback description from docstring
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
            phase=phase,
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

"""
Protocol Registry

Central registry for protocol implementations. Protocols register themselves
on module import, and can be looked up by name and version.

Usage:
    # Register a protocol (typically done in protocol __init__.py)
    @ProtocolRegistry.register
    class MyProtocol(SearchProtocol):
        name = "my_protocol"
        version = "2025.10.26"
        ...
    
    # Look up a protocol
    protocol_class = ProtocolRegistry.get("my_protocol", version="2025.10.26")
    protocol = protocol_class()

Version: 2025.10.26 (Phase 0 - Infrastructure)
"""

from typing import Optional, Type

from .base import ProtocolBase


class ProtocolRegistry:
    """
    Central registry for protocol implementations.
    
    Protocols register themselves using the @register decorator:
        @ProtocolRegistry.register
        class MyProtocol(ProtocolBase):
            ...
    
    Protocols can be looked up by name and version:
        protocol_class = ProtocolRegistry.get("my_protocol", "2025.10.26")
    """
    
    _registry: dict[str, dict[str, Type[ProtocolBase]]] = {}
    # Structure: {protocol_name: {version: protocol_class}}
    
    @classmethod
    def register(cls, protocol_class: Type[ProtocolBase]) -> Type[ProtocolBase]:
        """
        Register a protocol class.
        
        Can be used as a decorator:
            @ProtocolRegistry.register
            class MyProtocol(ProtocolBase):
                ...
        
        Or called directly:
            ProtocolRegistry.register(MyProtocol)
        
        Args:
            protocol_class: Protocol class to register
        
        Returns:
            The protocol class (for decorator compatibility)
        
        Raises:
            ValueError: If protocol with same name/version already registered
        """
        # Instantiate to get name and version
        instance = protocol_class()
        name = instance.name
        version = instance.version
        
        # Initialize name entry if needed
        if name not in cls._registry:
            cls._registry[name] = {}
        
        # Check for conflicts
        if version in cls._registry[name]:
            existing = cls._registry[name][version]
            if existing is not protocol_class:
                raise ValueError(
                    f"Protocol '{name}' version '{version}' already registered "
                    f"as {existing.__name__}, cannot register {protocol_class.__name__}"
                )
        
        # Register
        cls._registry[name][version] = protocol_class
        
        return protocol_class
    
    @classmethod
    def get(
        cls, name: str, version: Optional[str] = "latest"
    ) -> Type[ProtocolBase]:
        """
        Get a protocol class by name and version.
        
        Args:
            name: Protocol name
            version: Protocol version (YYYY.MM.DD format) or "latest"
        
        Returns:
            Protocol class
        
        Raises:
            KeyError: If protocol not found
        """
        if name not in cls._registry:
            raise KeyError(
                f"Protocol '{name}' not found. "
                f"Available protocols: {list(cls._registry.keys())}"
            )
        
        versions_available = cls._registry[name]
        
        if version == "latest":
            # Get most recent version (lexicographically largest for YYYY.MM.DD)
            version = max(versions_available.keys())
        
        if version not in versions_available:
            raise KeyError(
                f"Protocol '{name}' version '{version}' not found. "
                f"Available versions: {list(versions_available.keys())}"
            )
        
        return versions_available[version]
    
    @classmethod
    def list_protocols(cls) -> dict[str, list[str]]:
        """
        List all registered protocols and their versions.
        
        Returns:
            Dict of {protocol_name: [version1, version2, ...]}
        """
        return {name: list(versions.keys()) for name, versions in cls._registry.items()}
    
    @classmethod
    def clear(cls) -> None:
        """
        Clear the registry (primarily for testing).
        """
        cls._registry.clear()


"""
Protocol Registry System

Centralized registration and discovery for all VMT protocols.

Decisions locked:
- Version sourced from CLASS attribute `VERSION` (no instantiation)
- Crash on registration/assert failures (fast feedback)
- Docstring parsing fallback for description
- Validate decorator name matches class `.name` if present

Version: 2025.10.28
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
    }



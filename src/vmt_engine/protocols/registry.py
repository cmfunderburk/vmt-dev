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


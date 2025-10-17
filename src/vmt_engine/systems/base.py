from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from ..simulation import Simulation


class System(Protocol):
    """The interface for a simulation system, representing one phase of a tick."""

    def execute(self, sim: "Simulation") -> None:
        """Executes the system's logic for a single tick."""
        ...

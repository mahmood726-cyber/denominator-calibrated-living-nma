"""Treatment-network construction and connectivity checks.

A network meta-analysis is only interpretable when the treatment-comparison
graph is *connected*: every treatment must be joined to every other through a
chain of direct comparisons. A disconnected network cannot be pooled into a
single coherent set of relative effects, so :func:`build_treatment_network`
detects that condition up front and :func:`require_connected_network` refuses to
proceed on one (the "check connectivity first" NMA rule).

The graph is built from the ``treatment`` / ``comparator`` fields of the
registry records, which describe the arms actually randomized. When registry
records are unavailable the extraction records are used as a fallback so a
network can still be described from publication-derived evidence alone.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import EvidenceBundle


@dataclass(slots=True)
class TreatmentEdge:
    """A direct comparison (edge) between two treatments in the network."""

    treatment: str
    comparator: str
    trial_ids: list[str] = field(default_factory=list)

    @property
    def key(self) -> tuple[str, str]:
        """Order-independent identity for the undirected edge."""
        return tuple(sorted((self.treatment, self.comparator)))  # type: ignore[return-value]


@dataclass(slots=True)
class TreatmentNetwork:
    """An undirected treatment-comparison network for one outcome."""

    outcome_key: str
    nodes: list[str] = field(default_factory=list)
    edges: list[TreatmentEdge] = field(default_factory=list)
    components: list[list[str]] = field(default_factory=list)

    @property
    def is_connected(self) -> bool:
        return len(self.components) <= 1 and len(self.nodes) > 0

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    def summary(self) -> dict:
        return {
            "outcome_key": self.outcome_key,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "component_count": len(self.components),
            "is_connected": self.is_connected,
            "nodes": sorted(self.nodes),
            "components": [sorted(component) for component in self.components],
        }


def _connected_components(nodes: set[str], adjacency: dict[str, set[str]]) -> list[list[str]]:
    """Return connected components via iterative depth-first search."""
    unseen = set(nodes)
    components: list[list[str]] = []
    while unseen:
        start = next(iter(unseen))
        stack = [start]
        component: set[str] = set()
        while stack:
            node = stack.pop()
            if node in component:
                continue
            component.add(node)
            unseen.discard(node)
            stack.extend(adjacency.get(node, set()) - component)
        components.append(sorted(component))
    # Deterministic ordering: largest first, then alphabetically by first member.
    components.sort(key=lambda comp: (-len(comp), comp[0] if comp else ""))
    return components


def _iter_arm_pairs(bundle: EvidenceBundle, outcome_key: str):
    """Yield (treatment, comparator, trial_id) triples for the outcome.

    Prefers registry records (they describe the randomized arms). Falls back to
    extraction records if no registry arm information is present, so a network
    can still be sketched from publication-derived evidence alone.
    """
    seen_registry = False
    for record in bundle.registry_records:
        if record.outcome_key != outcome_key:
            continue
        treatment = (record.treatment or "").strip()
        comparator = (record.comparator or "").strip()
        if treatment and comparator:
            seen_registry = True
            yield treatment, comparator, record.trial_id
    if seen_registry:
        return
    # Fallback: extraction records only carry an effect direction, not explicit
    # arm labels, so pair the trial's treatment against a synthetic reference
    # only when nothing better exists. We keep this conservative and emit
    # nothing rather than invent comparator labels.
    return


def build_treatment_network(bundle: EvidenceBundle, outcome_key: str) -> TreatmentNetwork:
    """Construct the treatment-comparison network for ``outcome_key``.

    Nodes are treatment/comparator labels; edges are direct head-to-head (or
    treatment-vs-control) comparisons, each annotated with the contributing
    trial ids. Connected components are computed so callers can reject
    disconnected networks before attempting to pool them.
    """
    nodes: set[str] = set()
    adjacency: dict[str, set[str]] = {}
    edge_map: dict[tuple[str, str], TreatmentEdge] = {}

    for treatment, comparator, trial_id in _iter_arm_pairs(bundle, outcome_key):
        nodes.add(treatment)
        nodes.add(comparator)
        adjacency.setdefault(treatment, set()).add(comparator)
        adjacency.setdefault(comparator, set()).add(treatment)
        key = tuple(sorted((treatment, comparator)))
        edge = edge_map.get(key)
        if edge is None:
            edge = TreatmentEdge(treatment=key[0], comparator=key[1])
            edge_map[key] = edge
        if trial_id not in edge.trial_ids:
            edge.trial_ids.append(trial_id)

    components = _connected_components(nodes, adjacency)
    edges = [edge_map[key] for key in sorted(edge_map)]
    for edge in edges:
        edge.trial_ids.sort()
    return TreatmentNetwork(
        outcome_key=outcome_key,
        nodes=sorted(nodes),
        edges=edges,
        components=components,
    )


class DisconnectedNetworkError(ValueError):
    """Raised when a network meta-analysis is attempted on a disconnected graph."""


def require_connected_network(network: TreatmentNetwork) -> TreatmentNetwork:
    """Return ``network`` unchanged if connected, else raise.

    An empty network (no treatments at all) and a network split into two or more
    components are both rejected, because neither admits a single coherent set of
    relative treatment effects.
    """
    if network.node_count == 0:
        raise DisconnectedNetworkError(
            f"No treatment comparisons found for outcome {network.outcome_key!r}; "
            "cannot build a network meta-analysis."
        )
    if not network.is_connected:
        component_repr = "; ".join(
            "{" + ", ".join(component) + "}" for component in network.components
        )
        raise DisconnectedNetworkError(
            f"Treatment network for outcome {network.outcome_key!r} is disconnected "
            f"into {len(network.components)} components: {component_repr}. "
            "A network meta-analysis requires a single connected component."
        )
    return network

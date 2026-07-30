"""Scenario tree construction from bootstrapped return paths.

Kim et al. (2019) index decisions by scenario ``s in S`` and enforce
non-anticipativity via explicit equality constraints (their equation 11)
between scenarios sharing an ancestor node. This module instead builds an
explicit **node-indexed tree** and has :mod:`stochastic_optimizer` attach one
decision variable per *node* rather than per *scenario*. Every scenario
passing through a node is automatically forced to share that node's decision
-- non-anticipativity is structural, not a separate linear constraint. This
is mathematically equivalent to the paper's formulation but is the standard,
more efficient way multi-stage stochastic programs are implemented in
practice (Birge & Louveaux, *Introduction to Stochastic Programming*), and it
removes ``O(|S|^2)`` redundant equality constraints.

Tree construction method
-------------------------
Following the paper's own footnote (citing Hoyland & Wallace 2001; Xu et al.
2012, k-means-based scenario tree generation), we build the tree by
recursively clustering bootstrapped paths stage by stage:

1. Draw ``n_paths`` full historical-bootstrap paths (see
   :mod:`scenario_generation`), each a sequence of per-stage returns.
2. At stage 1, run k-means with ``branching[0]`` clusters on the stage-1
   returns of all paths. Each cluster becomes a stage-1 node; its
   probability is the cluster's path-count fraction, and its return is the
   cluster centroid.
3. For each stage-1 node, take the subset of paths assigned to it and run
   k-means with ``branching[1]`` clusters on *their* stage-2 returns,
   producing that node's children. Repeat through stage ``T``.

Because clustering at each node only uses the paths that reached it, the
tree preserves whatever serial dependence the block bootstrap generated
across stages (e.g. a path that drew a historically bad decade at stage 1 is
only eligible to inform stage-2 clusters descending from the "bad" node),
rather than assuming stage-wise independence.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from sklearn.cluster import KMeans


@dataclass
class ScenarioNode:
    """A single node in the scenario tree.

    Attributes
    ----------
    node_id : int
        Unique identifier, 0 = root (stage 0).
    stage : int
        Stage index, 0..T.
    parent_id : int | None
        Parent node id, ``None`` only for the root.
    children_ids : list[int]
        Child node ids (empty for leaves).
    probability : float
        Unconditional probability of reaching this node from the root
        (``pi_{t,s}`` in the paper's notation, but indexed by node).
    asset_return : np.ndarray | None
        Return vector realized on the transition *into* this node from its
        parent (``r_{i,t,s}``); ``None`` for the root, which has no
        incoming transition.
    inflation_rate : float
        Inflation rate realized on the transition into this node
        (``f_{t,s}``); 0.0 for the root.
    n_paths : int
        Number of underlying bootstrap paths assigned to this node's
        cluster (diagnostic only).
    """

    node_id: int
    stage: int
    parent_id: int | None
    children_ids: list[int] = field(default_factory=list)
    probability: float = 1.0
    asset_return: np.ndarray | None = None
    inflation_rate: float = 0.0
    n_paths: int = 0


class ScenarioTree:
    """A recombining-free scenario tree with node-indexed decisions.

    Parameters
    ----------
    nodes : dict[int, ScenarioNode]
        All nodes keyed by ``node_id``.
    n_stages : int
        Number of stages ``T`` (root is stage 0).
    asset_names : list[str]
        Asset labels, matching the column order of ``asset_return`` vectors.
    """

    def __init__(self, nodes: dict[int, ScenarioNode], n_stages: int, asset_names: list[str]):
        self.nodes = nodes
        self.n_stages = n_stages
        self.asset_names = asset_names
        self._by_stage: dict[int, list[int]] = {}
        for nid, node in nodes.items():
            self._by_stage.setdefault(node.stage, []).append(nid)

    @property
    def root_id(self) -> int:
        return 0

    def nodes_at_stage(self, stage: int) -> list[int]:
        """Node ids present at a given stage, in insertion order."""
        return list(self._by_stage.get(stage, []))

    def leaves(self) -> list[int]:
        """Node ids at the final stage ``T``."""
        return self.nodes_at_stage(self.n_stages)

    def path_to_root(self, node_id: int) -> list[int]:
        """Node ids from the root to ``node_id`` inclusive, root first."""
        path = []
        cur: int | None = node_id
        while cur is not None:
            path.append(cur)
            cur = self.nodes[cur].parent_id
        return list(reversed(path))

    def ancestor_at_stage(self, node_id: int, stage: int) -> int:
        """The ancestor of ``node_id`` living at ``stage`` (``stage <= node's stage``)."""
        node = self.nodes[node_id]
        if stage > node.stage:
            raise ValueError(f"Node {node_id} is at stage {node.stage}, before stage {stage}.")
        path = self.path_to_root(node_id)
        return path[stage]

    def leaf_probabilities(self) -> dict[int, float]:
        """Terminal (leaf) node probabilities, used for wealth-distribution stats."""
        return {nid: self.nodes[nid].probability for nid in self.leaves()}

    def total_nodes(self) -> int:
        return len(self.nodes)

    def summary(self) -> str:
        lines = [f"Scenario tree: {self.n_stages} stages, {len(self.asset_names)} assets"]
        for t in range(self.n_stages + 1):
            n_nodes = len(self.nodes_at_stage(t))
            lines.append(f"  stage {t}: {n_nodes} node(s)")
        return "\n".join(lines)


def build_scenario_tree(
    paths: np.ndarray,
    branching: list[int],
    asset_names: list[str],
    inflation_paths: np.ndarray | None = None,
    random_state: int | None = None,
) -> ScenarioTree:
    """Build a scenario tree from bootstrapped paths via sequential k-means.

    Parameters
    ----------
    paths : np.ndarray
        Shape ``(n_paths, n_stages, n_assets)`` bootstrapped, stage-compounded
        returns (see :func:`scenario_generation.generate_bootstrap_stage_paths`).
    branching : list[int]
        Number of children per node at each stage, length ``n_stages``. E.g.
        ``[4, 3, 3, 2]`` for a 4-stage tree.
    asset_names : list[str]
        Asset labels in the same order as ``paths``' last axis.
    inflation_paths : np.ndarray, optional
        Shape ``(n_paths, n_stages)`` inflation realizations aligned with
        ``paths``. If omitted, inflation is assumed zero at every node.
    random_state : int, optional
        Seed for k-means reproducibility.

    Returns
    -------
    ScenarioTree
    """
    n_paths, n_stages, n_assets = paths.shape
    if len(branching) != n_stages:
        raise ValueError(f"branching must have length {n_stages}, got {len(branching)}.")

    nodes: dict[int, ScenarioNode] = {
        0: ScenarioNode(node_id=0, stage=0, parent_id=None, probability=1.0, n_paths=n_paths)
    }
    next_id = 1

    # frontier: list of (node_id, path_indices assigned to that node)
    frontier: list[tuple[int, np.ndarray]] = [(0, np.arange(n_paths))]

    for stage in range(1, n_stages + 1):
        new_frontier: list[tuple[int, np.ndarray]] = []
        k = branching[stage - 1]
        for parent_id, path_idx in frontier:
            parent_node = nodes[parent_id]
            if path_idx.size == 0:
                continue

            stage_returns = paths[path_idx, stage - 1, :]  # returns for this transition
            effective_k = min(k, path_idx.size)
            if effective_k <= 1:
                labels = np.zeros(path_idx.size, dtype=int)
                centroids = stage_returns.mean(axis=0, keepdims=True)
            else:
                km = KMeans(n_clusters=effective_k, n_init=10, random_state=random_state)
                labels = km.fit_predict(stage_returns)
                centroids = km.cluster_centers_

            for cluster_id in range(centroids.shape[0]):
                mask = labels == cluster_id
                count = int(mask.sum())
                if count == 0:
                    continue
                cluster_paths = path_idx[mask]
                cond_prob = count / path_idx.size
                node_prob = parent_node.probability * cond_prob

                infl = 0.0
                if inflation_paths is not None:
                    infl = float(inflation_paths[cluster_paths, stage - 1].mean())

                child = ScenarioNode(
                    node_id=next_id,
                    stage=stage,
                    parent_id=parent_id,
                    probability=node_prob,
                    asset_return=centroids[cluster_id].copy(),
                    inflation_rate=infl,
                    n_paths=count,
                )
                nodes[next_id] = child
                parent_node.children_ids.append(next_id)
                new_frontier.append((next_id, cluster_paths))
                next_id += 1
        frontier = new_frontier

    return ScenarioTree(nodes=nodes, n_stages=n_stages, asset_names=asset_names)

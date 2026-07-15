"""Contact-map graph construction and rendering for the structure figure.

Shared helpers behind the structure notebook: build a residue contact-map graph from a
PDB file, map residues to complex regions (MHC / peptide / TCRalpha / TCRbeta / CDR3a /
CDR3b), and render the four figure panels (colored contact-map matrix, base graph,
GCN node-importance graph, GAT node/edge-importance graph).

    import sys; sys.path.insert(0, str(PUB / "lib"))
    from structure_graph import (
        calculate_contact_map, build_graph_from_contact_map, region_assignment,
        plot_colored_contact_map, plot_base_graph, plot_gcn_importance, plot_gat_importance,
    )
"""

from __future__ import annotations

from collections import defaultdict

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from Bio.PDB import PDBParser
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

# Distance threshold (Angstrom) below which two residues count as in contact.
CONTACT_THRESHOLD = 10.0
# Deterministic layout seed so every panel shares the same node positions.
LAYOUT_SEED = 69

# Region order defines priority for residue assignment: CDR3 loops win over their
# parent TCR chain, so they are tested first.
REGION_PRIORITY = ["cdr3a", "cdr3b", "tcra", "tcrb", "peptide", "mhc"]

# Node colors per complex region.
COMPLEX_COLORS = {
    "mhc": "#33B333",
    "peptide": "#CC3333",
    "tcra": "#3399CC",
    "tcrb": "#197399",
    "cdr3a": "#9966E6",
    "cdr3b": "#6619B3",
    "unknown": "#808080",
}

# Edge/contact colors per interaction type (sorted region pair). "intra" collapses
# same-complex and CDR3<->parent-chain contacts; "other" catches unlisted pairs.
EDGE_COLORS = {
    "cdr3a-peptide": "#EA616A",
    "cdr3b-peptide": "#E0252E",
    "cdr3a-mhc": "#90E2B9",
    "cdr3b-mhc": "#66CC99",
    "peptide-tcra": "#EEDFEE",
    "peptide-tcrb": "#D9ABD9",
    "mhc-tcra": "#B0E5C7",
    "mhc-tcrb": "#90CCAD",
    "mhc-peptide": "#F9C48E",
    "cdr3a-cdr3b": "#BDA8E4",
    "cdr3a-tcra": "#F7CAB6",
    "cdr3b-tcrb": "#F9D9C1",
    "cdr3b-tcra": "#F9AB89",
    "cdr3a-tcrb": "#F4C0A9",
    "tcra-tcrb": "#A1C6ED",
    "intra": "#8C8C8C",
    "other": "#000000",
}

# CDR3<->parent-chain pairs treated as intra-complex rather than inter-complex.
INTRA_LIST = ["cdr3a-tcra", "cdr3b-tcrb", "tcra-cdr3a", "tcrb-cdr3b"]

# Human-readable labels used in the node legend.
_NODE_LEGEND_LABELS = [
    ("mhc", "MHC"), ("peptide", "Peptide"), ("tcra", "TCRα"),
    ("tcrb", "TCRβ"), ("cdr3a", "CDR3α"), ("cdr3b", "CDR3β"),
]


# --------------------------------------------------------------------------- #
# Contact map + graph
# --------------------------------------------------------------------------- #
def calculate_contact_map(pdb_file, threshold=CONTACT_THRESHOLD):
    """Read C-alpha coordinates from a PDB file and build a binary residue contact map.

    Returns ``(contact_map, residues, coords)`` where ``contact_map[i, j] == 1`` when the
    C-alpha atoms of residues i and j are within ``threshold`` Angstrom.
    """
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("Protein", pdb_file)

    coords = []
    residues = []
    for model in structure:
        for chain in model:
            for residue in chain:
                if "CA" in residue:
                    coords.append(residue["CA"].coord)
                    residues.append(residue.resname)

    coords = np.array(coords)
    n = len(coords)
    contact_map = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j and np.linalg.norm(coords[i] - coords[j]) <= threshold:
                contact_map[i, j] = 1
    return contact_map, residues, coords


def build_graph_from_contact_map(contact_map, residues, coords):
    """Build an undirected graph: one node per residue, one edge per contact."""
    g = nx.Graph()
    for i, residue in enumerate(residues):
        g.add_node(i, residue=residue)
    n = len(residues)
    for i in range(n):
        for j in range(i + 1, n):
            if contact_map[i, j] == 1:
                g.add_edge(i, j, distance=float(np.linalg.norm(coords[i] - coords[j])))
    return g


def layout(g):
    """Deterministic spring layout shared across all panels."""
    return nx.spring_layout(g, seed=LAYOUT_SEED)


# --------------------------------------------------------------------------- #
# Residue -> complex region assignment
# --------------------------------------------------------------------------- #
def region_assignment(meta_row, n_residues):
    """Map each residue index to a complex region from the chain sequences.

    ``meta_row`` is a one-row metadata frame (or Series) carrying ``target_chainseq``
    (``mhc/peptide/tcra/tcrb`` slash-separated) plus ``cdr3a`` and ``cdr3b``. Returns a
    list of length ``n_residues`` with one region label per residue.
    """
    row = meta_row.iloc[0] if hasattr(meta_row, "iloc") else meta_row
    chainseq = row["target_chainseq"]
    flat = chainseq.replace("/", "")
    parts = chainseq.split("/")

    # Full-chain sequences come from the slash-separated chainseq; CDR3 loops are columns.
    seqs = {
        "mhc": parts[0],
        "peptide": parts[1],
        "tcra": parts[2],
        "tcrb": parts[3],
        "cdr3a": row["cdr3a"],
        "cdr3b": row["cdr3b"],
    }

    def coord_range(seq):
        start = flat.find(seq)
        if start < 0:
            return []
        return list(range(start, start + len(seq)))

    coords = {region: coord_range(seq) for region, seq in seqs.items()}

    regions = ["unknown"] * n_residues
    # Assign in reverse priority so earlier-priority regions overwrite later ones.
    for region in reversed(REGION_PRIORITY):
        for i in coords[region]:
            if 0 <= i < n_residues:
                regions[i] = region
    return regions, coords


def edge_key(a, b):
    """Return the EDGE_COLORS key for a contact between regions ``a`` and ``b``."""
    if a == b or f"{a}-{b}" in INTRA_LIST:
        return "intra"
    key = "-".join(sorted([a, b]))
    return key if key in EDGE_COLORS else "other"


# --------------------------------------------------------------------------- #
# Legends
# --------------------------------------------------------------------------- #
def node_legend():
    """Fixed node legend (one patch per complex region)."""
    return [Patch(facecolor=COMPLEX_COLORS[k], label=lbl) for k, lbl in _NODE_LEGEND_LABELS]


def edge_legend(keys):
    """Edge legend for the interaction keys actually present in a panel."""
    handles = []
    for key in keys:
        label = "Intra-complex" if key == "intra" else key
        handles.append(Line2D([0], [0], color=EDGE_COLORS.get(key, "#808080"), lw=3, label=label))
    return handles


def _attach_legends(ax, edge_keys):
    """Place the node and edge legends to the right of ``ax``."""
    leg_nodes = ax.legend(handles=node_legend(), title="Nodes (Complexes)",
                          loc="upper left", bbox_to_anchor=(1.02, 0.8), fontsize=12)
    ax.legend(handles=edge_legend(edge_keys), title="Edges (Interactions)",
              loc="upper left", bbox_to_anchor=(1.02, 0.6), fontsize=12)
    ax.add_artist(leg_nodes)


# --------------------------------------------------------------------------- #
# Node-importance styling (shared by GCN and GAT panels)
# --------------------------------------------------------------------------- #
def importance_style(nodes, importance, regions, top_pct=75, scale=2500,
                     min_size=50, faded_size=30, faded_color="#D3D3D3"):
    """Color/size nodes by importance: top ``top_pct``% keep their region color and a
    size scaled by importance; the rest fade to grey. Returns ``(colors, sizes, top_set)``.
    """
    values = list(importance.values())
    threshold = np.percentile(values, top_pct)
    top = {n for n, w in importance.items() if w >= threshold}

    colors, sizes = [], []
    for n in nodes:
        if n in top:
            colors.append(COMPLEX_COLORS[regions[n]])
            sizes.append(max(importance.get(n, 0.0) * scale, min_size))
        else:
            colors.append(faded_color)
            sizes.append(faded_size)
    return colors, sizes, top


# --------------------------------------------------------------------------- #
# Panel 1 - colored contact-map matrix
# --------------------------------------------------------------------------- #
def plot_colored_contact_map(contact_map, regions, figsize=(16, 8)):
    """Render the contact map as an image, coloring each contact by interaction type and
    drawing labelled region separators along both axes. Returns the Figure.
    """
    n = contact_map.shape[0]
    rgb = {k: mcolors.to_rgb(v) for k, v in EDGE_COLORS.items()}

    colored = np.ones((n, n, 3))  # white background
    for i in range(n):
        for j in range(n):
            if contact_map[i, j] == 1:
                key = edge_key(regions[i], regions[j])
                colored[i, j] = rgb[key]
                colored[j, i] = rgb[key]

    fig, ax = plt.subplots(figsize=figsize)
    ax.imshow(colored, interpolation="none", aspect="equal")

    # Region separators + labels along the x and y axes.
    _draw_region_separators(ax, regions, n)

    ax.set_xlim(-0.5, n - 0.5)
    ax.set_ylim(n - 0.5, -0.5)
    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)
    ax.grid(True, alpha=0.2, linewidth=0.5)

    handles = [Line2D([0], [0], color=c, lw=3, label=k)
               for k, c in rgb.items() if k != "other"]
    ax.legend(handles=handles, title="Contacts", loc="center left",
              bbox_to_anchor=(1, 0.5), fontsize=12, title_fontsize=12,
              frameon=True, handlelength=2.2, borderpad=0.6)
    fig.tight_layout()
    return fig


def _draw_region_separators(ax, regions, n):
    """Draw region boundary ticks and rotated labels on both axes of the contact map."""
    # X axis (bottom) labels.
    current, start = None, 0
    for i, region in enumerate(regions + ["end"]):
        if region != current or i == len(regions):
            if current is not None:
                ax.axvline(x=i - 0.5, ymin=-0.025, ymax=-0.001, color="black",
                           linewidth=1.5, clip_on=False)
                center = (start + i - 1) / 2
                ax.text(center, n + n * 0.05 + len(current) + 6, current.upper(),
                        ha="center", va="bottom", fontsize=10, rotation=90)
            current, start = region, i
    # Y axis (left) labels.
    current, start = None, 0
    for i, region in enumerate(regions + ["end"]):
        if region != current or i == len(regions):
            if current is not None:
                ax.axhline(y=i - 0.5, xmin=-0.025, xmax=-0.001, color="black",
                           linewidth=1.5, clip_on=False)
                center = (start + i - 1) / 2
                ax.text(-n * 0.035, center, current.upper(), ha="right", va="center",
                        fontsize=10, transform=ax.transData, clip_on=False)
            current, start = region, i


# --------------------------------------------------------------------------- #
# Panel 2 - base graph
# --------------------------------------------------------------------------- #
def plot_base_graph(g, pos, regions, figsize=(15, 12)):
    """Draw the contact-map graph with nodes colored by complex and edges by interaction."""
    node_colors = [COMPLEX_COLORS[regions[n]] for n in g.nodes()]

    edge_colors, edge_keys = [], set()
    for u, v in g.edges():
        key = edge_key(regions[u], regions[v])
        edge_colors.append(EDGE_COLORS[key])
        edge_keys.add(key)

    fig, ax = plt.subplots(figsize=figsize)
    nx.draw(g, pos, ax=ax, node_color=node_colors, edge_color=edge_colors,
            node_size=80, with_labels=False, alpha=0.8, linewidths=1,
            edgecolors="black", width=1.5)
    _attach_legends(ax, sorted(edge_keys))
    ax.axis("off")
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------- #
# Panel 3 - GCN node importance
# --------------------------------------------------------------------------- #
def plot_gcn_importance(g, pos, regions, importance, top_pct=75, figsize=(15, 12)):
    """Highlight the top ``top_pct``% most important nodes (size scaled by importance);
    edges incident to an important node keep their interaction color, the rest fade.
    """
    node_colors, node_sizes, top = importance_style(g.nodes(), importance, regions, top_pct)

    edge_colors, edge_widths, edge_alphas, edge_keys = [], [], [], set()
    for u, v in g.edges():
        if u in top or v in top:
            key = edge_key(regions[u], regions[v])
            edge_colors.append(EDGE_COLORS[key])
            edge_widths.append(1.2)
            edge_alphas.append(0.75)
            edge_keys.add(key)
        else:
            edge_colors.append("lightgray")
            edge_widths.append(0.4)
            edge_alphas.append(0.4)

    fig, ax = plt.subplots(figsize=figsize)
    nx.draw_networkx_edges(g, pos, ax=ax, edge_color=edge_colors,
                           alpha=edge_alphas, width=edge_widths)
    nx.draw_networkx_nodes(g, pos, ax=ax, node_color=node_colors,
                           node_size=node_sizes, edgecolors="black", alpha=0.9)
    _attach_legends(ax, sorted(edge_keys))
    ax.axis("off")
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------- #
# Panel 4 - GAT node + edge importance
# --------------------------------------------------------------------------- #
def _top_edge_attention(edge_df, top_pct=95):
    """Average attention per (src, dst) edge, drop self-loops, keep the top ``top_pct``%."""
    attn = defaultdict(list)
    for u, v, w in zip(edge_df["src_node"], edge_df["dst_node"], edge_df["attention_weight"]):
        attn[(int(u), int(v))].append(float(w))
    attn = {k: np.mean(v) for k, v in attn.items() if k[0] != k[1]}
    threshold = np.percentile(list(attn.values()), top_pct)
    return {k: v for k, v in attn.items() if v >= threshold}


def plot_gat_importance(g, pos, regions, importance, edge_df,
                        node_top_pct=75, edge_top_pct=95, figsize=(15, 12)):
    """Draw GAT node importance (size, top ``node_top_pct``%) with a directed overlay of the
    top ``edge_top_pct``% attention edges (width scaled by attention) over a grey backdrop.
    """
    node_colors, node_sizes, _ = importance_style(g.nodes(), importance, regions, node_top_pct)

    edge_attn = _top_edge_attention(edge_df, edge_top_pct)
    g_attn = nx.DiGraph()
    g_attn.add_nodes_from(g.nodes(data=True))
    for (u, v), w in edge_attn.items():
        g_attn.add_edge(u, v, weight=w)

    edge_colors, edge_widths, edge_keys = [], [], set()
    for u, v, data in g_attn.edges(data=True):
        key = edge_key(regions[u], regions[v])
        edge_colors.append(EDGE_COLORS[key])
        edge_widths.append(1 + 6 * data["weight"])
        edge_keys.add(key)

    fig, ax = plt.subplots(figsize=figsize)
    # Structural contact edges as a faint backdrop.
    nx.draw_networkx_edges(g, pos, ax=ax, edge_color="lightgray", alpha=0.25, width=0.5)
    # Attention edges on top.
    nx.draw_networkx_edges(g_attn, pos, ax=ax, edge_color=edge_colors,
                           width=edge_widths, alpha=0.9)
    nx.draw_networkx_nodes(g, pos, ax=ax, node_color=node_colors,
                           node_size=node_sizes, edgecolors="black", alpha=0.95)
    _attach_legends(ax, sorted(edge_keys))
    ax.axis("off")
    fig.tight_layout()
    return fig

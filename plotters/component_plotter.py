"""component_plotter.py -- draw ONE component, from its spec, computing nothing.

Replaces `plot_detail` / `render_*` / `letters_*` in the frozen
`plot_schematic.py` (plan Sec.6).

THE ONE RULE. Every coordinate drawn here arrives through a
`component_spec` ACCESSOR:

    geometry_nodes()   geometry_lines()   structural_nodes()
    structural_lines() contact_at(x)      active_connectors(system)
    extent             point_masses()     junctions()

No shape is rebuilt from parameters. There is no `c - L_comp/2` here, no
rectangle assembled from V/L1/L2, no connector-slot ratio. That class of
code is how the DRAWN connector slots once drifted away from the MODELLED
ones -- the plotter had settled on P_c1 = 0.5*B while the spec used B/3,
and both looked right in isolation.

WHY THE PRIMITIVES LIVE HERE and not in a third module. `ils_plotter`
imports this one and reuses these functions, so an assembly figure and a
detail figure draw a GD-SB with the same code. The alternative the plan
sketched -- two independent plotters -- would have duplicated all of it,
and duplicated drawing code drifts exactly the way duplicated geometry
does. Two files, one renderer, no `schematic_lib`, no `spec_render`.

DEPENDENCIES: matplotlib, numpy, component_spec -- and TRANSITIVELY
`config` and `slay_config.yaml`, because `component_spec` imports `config`
at module level and `config` raises FileNotFoundError on import when the
YAML is absent. This module names no config value of its own, but that
buys nothing at handover: the file set is

    component_plotter.py  component_spec.py  config.py  slay_config.yaml

An earlier version of this docstring claimed the module could be exercised
without `slay_config.yaml`. It cannot, and the failure looks like a fault
in whatever imported it.

y IS POSITIVE DOWN (item 26). Values are drawn AS-IS and the AXIS is
inverted for display. The data is never negated, because a negated
coordinate is a coordinate no accessor returned.

WHAT IS DELIBERATELY ABSENT: lettered dimension arrows (P_c1 with a
labelled arrow, L_top with another). Those live in the frozen module as
seven hand-written per-component functions, each of which recomputes where
the arrow ends belong -- geometry rebuilt from parameters, the drift class
this module exists to exclude. What is drawn instead is (a) dimension
arrows whose ENDPOINTS ARE ACCESSOR COORDINATES, which is drift-free, and
(b) a table of the component's FREE parameters, read off the dataclass.
The table states what was chosen; the drawing states what the spec makes
of it. If the two disagree the figure shows it, which a hand-placed arrow
would not.
"""
from __future__ import annotations

import dataclasses as dc

import numpy as np
import matplotlib.patches as mpatches

from component_spec import NodePriority, LoadPath
from plot_settings import STYLE, body_color, component_label, connector_symbol, require_renderer

# --- palette ---------------------------------------------------------------
GEOM_CONTACT = STYLE['colors']['GEOM_CONTACT']     # geometry line that OWNS contact
GEOM_SHAPE = STYLE['colors']['GEOM_SHAPE']       # geometry line that is shape-only
STRUCT = STYLE['colors']['STRUCT']           # structural line
CONTACT_ENV = STYLE['colors']['CONTACT_ENV']      # sampled contact envelope
CONN = STYLE['colors']['CONN']             # connector tie lines
CONN_BLUE = STYLE['colors']['CONN_BLUE']        # ring/border on P, S and D symbols
CONTACT_VIA_CONN = STYLE['colors']['CONTACT_VIA_CONN'] # contact whose reaction runs through a connector
PIPE = STYLE['colors']['PIPE']             # pipe centreline and surfaces
MASS = STYLE['colors']['MASS']             # point masses
DIM = STYLE['colors']['DIM']                 # dimension arrows

BODY_FILL = STYLE['component_colors']


def _node_map(nodes):
    return {n.node_id: n for n in nodes}


# ---------------------------------------------------------------------------
# Pipe reference -- the header pipeline, shown by BOTH plotters
# ---------------------------------------------------------------------------

def draw_pipe_reference(ax, pipe, lo, hi, band=True, label=True):
    """Centreline and the two pipe surfaces, from `BasePipeline` only.

    This is the HEADER PIPELINE. GD-TP, GD-TT, GD-SH and GD-VLV have no
    structural line of their own -- they ARE the pipeline over their
    extent -- so without this there is nothing for them to modify and the
    figure shows a component floating in space.

    Radius comes from `pipe.OD_pipe`; the LOCAL section over a component's
    extent is NOT drawn here, because that belongs to `section_at` and is
    the component's own business.
    """
    r = pipe.OD_pipe / 2.0
    ax.plot([lo, hi], [0.0, 0.0], color=PIPE, lw=STYLE['line_widths']['stroke_1_0'], ls='-.', zorder=1,
            label='pipe centreline' if label else None)
    for y in (r, -r):
        ax.plot([lo, hi], [y, y], color=PIPE, lw=STYLE['line_widths']['stroke_1_0'], alpha=0.55, zorder=1)
    if band:
        ax.fill_between([lo, hi], [-r, -r], [r, r], color=PIPE, alpha=0.07,
                        zorder=0)
    return r


def draw_section_band(ax, owner, lo=None, hi=None, label=True):
    """The pipe's LOCAL wall over a component that thickens it.

    Sampled from `section_at`, so a taper is drawn as a taper rather than
    as a step. Draws nothing for a component whose `section_at` returns
    None -- GD-SH is the case that matters: Sec.2.4 states the shroud adds
    NO material to the pipe cross-section, so an absent band here is the
    correct picture, not a gap.
    """
    x0, x1 = (owner.extent if lo is None else (lo, hi))
    xs, hi_y, lo_y = [], [], []
    for x in np.linspace(x0, x1, 241):
        s = owner.section_at(float(x))
        if s is None:
            continue
        xs.append(x)
        hi_y.append(s.OD / 2.0)
        lo_y.append(-s.OD / 2.0)
    if not xs:
        return False
    ax.fill_between(xs, lo_y, hi_y, color=PIPE, alpha=0.30, zorder=2,
                    lw=STYLE['line_widths']['stroke_0'], label='pipe section (section_at)' if label else None)
    return True


# ---------------------------------------------------------------------------
# The component's own lines
# ---------------------------------------------------------------------------

def draw_geometry(ax, comp, label=True):
    """Geometry lines, coloured by whether the segment OWNS CONTACT.

    `owns_contact` is a property of the LINE, not of the component, which
    is why the colour is decided per segment: a GD-SB's bottom face owns
    contact while its side walls do not.
    """
    nm = _node_map(comp.geometry_nodes())
    seen = set()
    for gl in comp.geometry_lines():
        a, b = nm[gl.node_ids[0]], nm[gl.node_ids[1]]
        col = GEOM_CONTACT if gl.owns_contact else GEOM_SHAPE
        lab = None
        if label and gl.owns_contact not in seen:
            lab = ('geometry line -- owns contact' if gl.owns_contact
                   else 'geometry line -- shape only')
            seen.add(gl.owns_contact)
        ax.plot([a.x, b.x], [a.y, b.y], ls='--', lw=STYLE['line_widths']['stroke_1_9'], color=col,
                zorder=8, label=lab)
    for n in nm.values():
        mand = n.priority is NodePriority.MANDATORY
        ax.plot([n.x], [n.y], 'o', ms=7.5 if mand else 6.0,
                mfc=GEOM_CONTACT if mand else 'white',
                mec=GEOM_CONTACT, mew=1.6, zorder=10)


def draw_structural(ax, comp, label=True):
    """Structural lines as a thick translucent underlay.

    For GD-ST and GD-SB the geometry and structural sets are COINCIDENT by
    design -- one structural node per geometry node, same x and y (rule 1).
    They are distinguished by WEIGHT, never by nudging one aside: an offset
    introduced to make the picture legible is a coordinate no accessor
    returned.

    Returns False for a component owning no structural line of its own
    (GD-SH points at the pipeline's), and says so in the legend.
    """
    sn = comp.structural_nodes()
    if not sn:
        x0, x1 = comp.extent
        ax.plot([x0, x1], [0.0, 0.0], ls=':', lw=STYLE['line_widths']['stroke_2_4'], color=STRUCT, zorder=6,
                label="structural line -- none of its own, uses pipeline's"
                if label else None)
        return False
    nm = _node_map(sn)
    first = True
    for sl in comp.structural_lines():
        a, b = nm[sl.node_ids[0]], nm[sl.node_ids[1]]
        ax.plot([a.x, b.x], [a.y, b.y], ls='-', lw=STYLE['line_widths']['stroke_5_0'], color=STRUCT,
                alpha=0.30, solid_capstyle='round', zorder=6,
                label='structural line' if (label and first) else None)
        first = False
    for n in nm.values():
        mand = n.priority is NodePriority.MANDATORY
        ax.plot([n.x], [n.y], 's', ms=8.5 if mand else 7.0,
                mfc=STRUCT if mand else 'white',
                mec=STRUCT, mew=1.6, zorder=9)
    return True


def draw_contact_envelope(ax, comp, n=241, label=True, lw=STYLE['line_widths']['stroke_3_0']):
    """The surface a roller sees, SAMPLED from `contact_at`, and DRAWN BY
    LOAD PATH.

    `Contact` returns four things -- y, owner, load_path and arm -- and an
    earlier version of this function used two. That made a GD-SB and a
    GD-TP at the same depth draw an IDENTICAL line, although one reacts
    straight into the pipe wall and the other runs the reaction through
    the structure and a connector, carrying a real moment arm. The module
    reference warns about exactly that: dropping the arm silently discards
    the elevation effect the structure exists to produce. A figure that
    cannot tell the two apart is the first place that loss happens.

    Sampled rather than joined between node coordinates because
    `contact_at` is CONTINUOUS within a segment: GD-SH's and GD-TT's
    tapers change elevation between their end nodes, and a straight line
    would cut the corner.

    Draws nothing for a component owning no contact (GD-ST sits above the
    pipe, GD-B off to the side). That absence is the correct picture.
    """
    x0, x1 = comp.extent
    runs, cur, path = [], None, None
    for x in np.linspace(x0, x1, n):
        c = comp.contact_at(float(x))
        lp = None if c is None else c.load_path
        if lp is not path:
            if cur:
                runs.append((path, cur))
            cur, path = ([], []), lp
        if c is not None:
            cur[0].append(x)
            cur[1].append(c.y)
    if cur and cur[0]:
        runs.append((path, cur))

    seen = set()
    for lp, (xs, ys) in runs:
        if lp is None or not xs:
            continue
        via_conn = lp is LoadPath.CONNECTOR
        lab = None
        if label and lp not in seen:
            lab = ('contact -- reaction via CONNECTOR (moment arm)'
                   if via_conn else 'contact -- reaction into PIPE WALL')
            seen.add(lp)
        ax.plot(xs, ys, lw=lw,
                color=CONTACT_VIA_CONN if via_conn else CONTACT_ENV,
                ls=(0, (6, 2)) if via_conn else '-',
                alpha=0.9, zorder=7, solid_capstyle='butt', label=lab)
        if via_conn:
            i = len(xs) // 2
            c = comp.contact_at(float(xs[i]))
            ax.annotate(f'arm {c.arm:.3f} m', (xs[i], ys[i]),
                        textcoords='offset points', xytext=(0, 12),
                        ha='center', fontsize=STYLE['fonts']['annotation'], color=CONTACT_VIA_CONN,
                        weight='bold', zorder=12)
    return bool(runs)


def draw_connector_symbol(ax, x, y_pipe, y_struct, ctype, size=0.13):
    """The TYPED connector symbol, per Fig 16 / Fig 17.

        F  filled black square                -- fixed, all DOF restrained
        P  black disc inside a blue ring      -- pin
        S  black CAPSULE inside a blue ring   -- slot; the elongation is
                                                 what separates it from P
        D  blue-bordered square, black/white/black bands -- deadband

    Reinstated 27 Aug 2026. When these plotters were written to drop the
    `schematic_lib` dependency, this vocabulary went with it and every
    connector became an identical green dot with a letter beside it. That
    lost the thing the taxonomy figure is FOR: F1D and F2D differ only in
    their connector types, and at a glance the two figures were the same
    picture. The shapes carry the meaning; the letters only confirm it.

    S is deliberately oblong. It was squared off once to match the others
    and had to be reverted -- a slot that looks like a pin defeats the
    only distinction being drawn.
    """
    ym = (y_pipe + y_struct) / 2.0
    fs = 6.5 + size * 22.0

    if ctype == 'F':
        ax.add_patch(mpatches.Rectangle((x - size/2, ym - size/2), size, size,
                                        facecolor=STYLE['connector']['foreground'], edgecolor=STYLE['connector']['foreground'],
                                        zorder=13))
        ax.annotate(connector_symbol('F'), (x, ym), fontsize=fs, color=STYLE['connector']['background'], ha='center',
                    va='center', zorder=14, fontweight='bold')

    elif ctype == 'P':
        ax.add_patch(mpatches.Circle((x, ym), size * 0.50, facecolor='none',
                                     edgecolor=CONN_BLUE, lw=size * 16,
                                     zorder=12))
        ax.add_patch(mpatches.Circle((x, ym), size * 0.34, facecolor=STYLE['connector']['foreground'],
                                     edgecolor='none', zorder=13))
        ax.annotate(connector_symbol('P'), (x, ym), fontsize=fs, color=STYLE['connector']['background'], ha='center',
                    va='center', zorder=14, fontweight='bold')

    elif ctype == 'S':
        w, h = size * 1.18, size
        ax.add_patch(mpatches.FancyBboxPatch(
            (x - w/2, ym - h/2), w, h,
            boxstyle=f'round,pad=0,rounding_size={h/2}', facecolor='none',
            edgecolor=CONN_BLUE, lw=size * 16, zorder=12))
        wi, hi = w * 0.72, h * 0.68
        ax.add_patch(mpatches.FancyBboxPatch(
            (x - wi/2, ym - hi/2), wi, hi,
            boxstyle=f'round,pad=0,rounding_size={hi/2}', facecolor=STYLE['connector']['foreground'],
            edgecolor='none', zorder=13))
        ax.annotate(connector_symbol('S'), (x, ym), fontsize=fs, color=STYLE['connector']['background'], ha='center',
                    va='center', zorder=14, fontweight='bold')

    elif ctype == 'D':
        b = size
        ax.add_patch(mpatches.Rectangle((x - b/2, ym - b/2), b, b,
                                        facecolor=STYLE['connector']['background'],
                                        edgecolor=CONN_BLUE, lw=size * 13,
                                        zorder=12))
        bh = b / 3.0
        for y0 in (ym + bh/2, ym - 1.5*bh):
            ax.add_patch(mpatches.Rectangle((x - b/2, y0), b, bh,
                                            facecolor=STYLE['connector']['foreground'],
                                            edgecolor='none', zorder=13))
        ax.annotate(connector_symbol('D'), (x, ym), fontsize=fs*0.9, color=STYLE['connector']['foreground'], ha='center',
                    va='center', zorder=14, fontweight='bold')


def connector_legend_handles(kinds):
    """Legend entries for only the types actually present."""
    out = []
    for k in ('F', 'P', 'S', 'D'):
        if k not in kinds:
            continue
        if k == 'F':
            out.append(mpatches.Patch(facecolor=STYLE['connector']['foreground'], edgecolor=STYLE['connector']['foreground'],
                                      label='F -- fixed, all DOF'))
        elif k == 'P':
            out.append(mpatches.Patch(facecolor=STYLE['connector']['foreground'], edgecolor=CONN_BLUE,
                                      lw=STYLE['line_widths']['stroke_2'], label='P -- pin'))
        elif k == 'S':
            out.append(mpatches.Patch(facecolor=STYLE['connector']['foreground'], edgecolor=CONN_BLUE,
                                      lw=STYLE['line_widths']['stroke_2'], label='S -- slot (releases axial)'))
        else:
            out.append(mpatches.Patch(facecolor=STYLE['connector']['background'], edgecolor=CONN_BLUE,
                                      lw=STYLE['line_widths']['stroke_2'], label='D -- deadband (gap)'))
    return out


def draw_connectors(ax, comp, system=None, label=True):
    """The 2-node connector elements, from `active_connectors(system)`.

    WHICH slots are active is the ILS-level connection system's choice, so
    the system is passed IN. Calling `active_connectors()` with its own
    default is how a definition asking for F2 came out drawn as F2D --
    four connectors where two were specified.

    Pipe-side node at y = 0, structure-side node on the near face. The
    slot positions come from the component's own `connector_xs`.
    """
    if not hasattr(comp, 'active_connectors'):
        return []
    conns = (comp.active_connectors() if system is None
             else comp.active_connectors(system))
    y_face = comp.y_near if hasattr(comp, 'y_near') else comp.y_top
    first = True
    span = abs(comp.extent[1] - comp.extent[0])
    size = max(0.09, min(0.20, span * 0.028))
    # ZERO STANDOFF is a real case, not a degenerate one. The published
    # EA-SB set runs P_vt = 0 throughout, which puts the structure face on
    # the pipe centreline and makes every connector GENUINELY zero-length
    # -- which is exactly what the zero-length nodal element framing
    # asserts. Drawing a tie line there, or advertising one in the legend,
    # would contradict the thing the symbol represents.
    zero_len = abs(y_face) < 1e-9
    # 5-tuple since 28 Aug 2026: (slot, x, type, arm, gap). `gap` is unused
    # for drawing -- a deadband has no length on the page -- but it must be
    # unpacked, and it is deliberately not silently swallowed with *_ so a
    # future widening fails here rather than drawing something wrong.
    for slot, x, ctype, arm, gap in conns:
        if not zero_len:
            ax.plot([x, x], [0.0, y_face], lw=STYLE['line_widths']['stroke_2_0'], color=CONN, zorder=11,
                    label='connector element (2-node)'
                    if (label and first) else None)
            ax.plot([x], [0.0], 'o', ms=5, mfc='white', mec=CONN, mew=1.6,
                    zorder=12)
        draw_connector_symbol(ax, x, 0.0, y_face, ctype, size=size)
        ax.annotate(f'{slot}', (x, y_face), textcoords='offset points',
                    xytext=(0, 15), ha='center', fontsize=STYLE['fonts']['small'], color='0.35',
                    zorder=12)
        first = False
    if label and conns:
        # Symbols are patches, so they carry no automatic legend entry.
        # Stash proxy handles for the caller to merge into the legend.
        ax._connector_handles = connector_legend_handles(
            {c[2] for c in conns})
    return conns


def draw_branch_support(ax, comp, label=True):
    """The connector tying a BRANCH END to the structure that carries it.

    `support_connector` is 'F' or 'S' -- the paper's -FT- / -ST- support
    taxonomy -- and it was drawn NOWHERE. GD-B has no `active_connectors`,
    so the generic connector pass skipped it entirely and an L-FT-F1p and
    an L-ST-F1p came out as the same picture, although the support type is
    the only thing their names differ by. The symbol is the distinction;
    without it the figure cannot tell them apart.

    Drawn AT the branch end node, since that is where the tie lives.
    """
    if comp.code != 'GD-B' or not hasattr(comp, 'support_connector'):
        return None
    ends = [n for n in comp.structural_nodes()
            if n.node_id.endswith(':send')]
    if not ends:
        return None
    e = ends[0]
    ctype = comp.support_connector
    span = abs(comp.extent[1] - comp.extent[0])
    draw_connector_symbol(ax, e.x, e.y, e.y, ctype,
                          size=max(0.09, min(0.20, span * 0.028)))
    ax.annotate('support', (e.x, e.y), textcoords='offset points',
                xytext=(0, 15), ha='center', fontsize=STYLE['fonts']['small'], color='0.35',
                zorder=14)
    if label:
        prev = getattr(ax, '_connector_handles', [])
        have = {h.get_label()[0] for h in prev}
        if ctype not in have:
            ax._connector_handles = prev + connector_legend_handles({ctype})
    return ctype


def draw_point_masses(ax, comp, label=True):
    """Inertia elements, positioned by resolving each declared node id
    against the component's own structural nodes.

    `point_masses()` returns (node_id, mass) and NO coordinates, so an
    unresolved id would silently vanish from the figure. Anything that
    fails to resolve is drawn nowhere and REPORTED, never quietly dropped.
    """
    if not hasattr(comp, 'point_masses'):
        return [], []
    coords = {n.node_id: (n.x, n.y) for n in comp.structural_nodes()}
    drawn, missing = [], []
    first = True
    for nid, m in comp.point_masses():
        if nid not in coords:
            missing.append(nid)
            continue
        x, y = coords[nid]
        ax.plot([x], [y], '*', ms=15, mfc=MASS, mec='white', mew=1.0,
                zorder=13, label='point mass' if (label and first) else None)
        ax.annotate(f'{m/1000:.1f} t', (x, y), textcoords='offset points',
                    xytext=(9, 6), fontsize=STYLE['fonts']['annotation'], color=MASS, weight='bold',
                    zorder=13)
        drawn.append((nid, m, x, y))
        first = False
    return drawn, missing


def draw_junctions(ax, comp, label=True):
    """Where a second structural line joins this one -- a Tee. MANDATORY
    mesh nodes: a branch line cannot attach to the interior of an element.
    """
    if not hasattr(comp, 'junctions'):
        return
    coords = {n.node_id: (n.x, n.y) for n in comp.structural_nodes()}
    first = True
    for entry in comp.junctions():
        nid = entry[0] if isinstance(entry, (tuple, list)) else entry
        if nid not in coords:
            continue
        x, y = coords[nid]
        ax.plot([x], [y], 'X', ms=11, mfc='none', mec='black', mew=2.0,
                zorder=14, label='junction (mandatory node)'
                if (label and first) else None)
        first = False


# ---------------------------------------------------------------------------
# Body fill -- from the SAME source as the outline
# ---------------------------------------------------------------------------

def outline_polygon(comp, require_closed=True):
    """Ordered (x, y) loop walked from `geometry_lines()`, so the FILL and
    the OUTLINE come from one source.

    Returns None when the lines do not form a single chain, and -- with
    `require_closed` -- when the chain does not RETURN TO ITS START.

    The closure test is not fussiness. GD-SB and GD-ST are genuine closed
    loops (9 lines / 9 nodes, 12 / 12) and fill correctly. GD-B is an open
    chain of 3 lines: Tee, up the riser, along the spool. Filling it draws
    a triangle back from the spool end to the Tee -- a face that exists in
    no accessor, over ground the branch does not occupy. GD-TT's 5
    collinear segments are open for the same reason. A component whose
    body is a thickened pipe wall is shaded by `draw_section_band` from
    `section_at`, which is the accessor that actually describes it.
    """
    nm = _node_map(comp.geometry_nodes())
    segs = [(g.node_ids[0], g.node_ids[1]) for g in comp.geometry_lines()]
    if not segs:
        return None
    chain = [segs[0][0], segs[0][1]]
    remaining = segs[1:]
    while remaining:
        for i, (a, b) in enumerate(remaining):
            if a == chain[-1]:
                chain.append(b)
            elif b == chain[-1]:
                chain.append(a)
            else:
                continue
            remaining.pop(i)
            break
        else:
            return None
    if require_closed and chain[0] != chain[-1]:
        return None
    return [(nm[i].x, nm[i].y) for i in chain]


def fill_outline(ax, comp, color=None, alpha=0.20, zorder=4):
    """Shade the body, but ONLY where the spec describes a closed face."""
    if hasattr(comp, 'geometry_faces'):
        for face in comp.geometry_faces():
            ax.fill(*zip(*face), color=color or body_color(comp.code, '0.5'),
                    alpha=alpha, zorder=zorder, lw=0)
        return True
    poly = outline_polygon(comp, require_closed=True)
    if poly is None or len(poly) < 3:
        return False
    col = color or body_color(comp.code, '0.5')
    ax.fill([p[0] for p in poly], [p[1] for p in poly],
            color=col, alpha=alpha, zorder=zorder, lw=STYLE['line_widths']['stroke_0'])
    return True


# ---------------------------------------------------------------------------
# Dimensions -- endpoints from accessors ONLY
# ---------------------------------------------------------------------------

def dim_arrow(ax, x0, x1, y, text, color=DIM, fs=STYLE['fonts']['dimension']):
    """A dimension between two x that were RETURNED BY AN ACCESSOR.

    Never between two x this module computed. That restriction is what
    separates a dimension from a second source of geometry.
    """
    if abs(x1 - x0) < 1e-9:
        return
    ax.annotate('', xy=(x1, y), xytext=(x0, y),
                arrowprops=dict(arrowstyle='<->', color=color, lw=STYLE['line_widths']['stroke_1_1']))
    ax.annotate(text, ((x0 + x1) / 2.0, y), textcoords='offset points',
                xytext=(0, 3), ha='center', fontsize=fs, color=color)


def draw_accessor_dimensions(ax, comp, system=None, y_dim=None, gap=0.34):
    """The dimensions that ARE accessor facts: overall extent, and the
    connector slot spacing taken from the active slot positions.

    Deliberately not the full lettered set -- see the module docstring.
    """
    x0, x1 = comp.extent
    r = comp.pipe.OD_pipe / 2.0
    y = (r + 0.55) if y_dim is None else y_dim
    dim_arrow(ax, x0, x1, y, f'extent {x1 - x0:.4f} m')
    if hasattr(comp, 'active_connectors'):
        conns = (comp.active_connectors() if system is None
                 else comp.active_connectors(system))
        xs = sorted(c[1] for c in conns)
        if len(xs) >= 2:
            # Stacked BELOW the extent line, both keyed off the same y_dim.
            # Keying this one off the structure face instead put the two
            # arrows within a few centimetres of each other and the labels
            # overprinted.
            dim_arrow(ax, xs[0], xs[-1], y + gap,
                      f'active connector span {xs[-1] - xs[0]:.4f} m')


def free_parameters(comp):
    """(name, value) for every FREE parameter actually set on the component.

    Read off the dataclass, so a new field appears the moment it exists.
    `pipe` is excluded -- it is the context, not a parameter of this
    component.
    """
    out = []
    for f in dc.fields(comp):
        if not f.init or f.name == 'pipe':
            continue
        out.append((f.name, getattr(comp, f.name)))
    return out


def _param_table(ax, comp):
    ax.axis('off')
    rows = []
    for name, val in free_parameters(comp):
        if isinstance(val, float):
            s = f'{val:.4f}'
        elif isinstance(val, tuple):
            s = ', '.join(f'{v:.4f}' if isinstance(v, float) else str(v)
                          for v in val)
        else:
            s = getattr(val, 'name', str(val))
        rows.append([name, s])
    # bbox, not loc= -- a matplotlib table does not clip to its axes, so a
    # long parameter list drawn with loc='upper left' overflows the figure.
    n = max(len(rows), 1)
    hh = min(1.0, 0.062 * (n + 1))
    t = ax.table(cellText=rows, colLabels=['free parameter', 'value'],
                 cellLoc='left', colWidths=[0.55, 0.45],
                 bbox=[0.0, 1.0 - hh, 1.0, hh])
    t.auto_set_font_size(False)
    t.set_fontsize(STYLE['fonts']['annotation'])
    for (row, _), cell in t.get_celld().items():
        cell.set_edgecolor('0.85')
        if row == 0:
            cell.set_facecolor('0.93')
            cell.set_text_props(weight='bold')


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def data_bounds(comp, lo, hi, system=None):
    """Vertical extent of everything that will be drawn, from ACCESSORS.

    Needed BEFORE the figure exists: the tool standard is equal X/Y aspect
    (Sec.0.3), so a figure whose shape does not match the data's shape
    cannot be fixed afterwards -- matplotlib shrinks the axes to satisfy
    the aspect and leaves the rest as white space, with the legend then
    landing on top of the drawing.
    """
    ys = [comp.pipe.OD_pipe / 2.0, -comp.pipe.OD_pipe / 2.0]
    ys += [n.y for n in comp.geometry_nodes()]
    ys += [n.y for n in comp.structural_nodes()]
    for x in np.linspace(comp.extent[0], comp.extent[1], 61):
        c = comp.contact_at(float(x))
        if c is not None:
            ys.append(c.y)
    if hasattr(comp, 'active_connectors'):
        ys.append(comp.y_near if hasattr(comp, 'y_near') else comp.y_top)
    return min(ys), max(ys)


def plot_component(comp, system=None, title=None, path=None, table=True,
                   dimensions=True, pad_frac=0.12, width=STYLE['figure']['component_width']):
    """Detail view of ONE component on its pipe.

    `system` is the ILS-level connection system. Omitted, the component
    falls back to its own default -- fine for a standalone figure, wrong
    for one illustrating a particular ILS, which is why the caller says.
    """
    import matplotlib.pyplot as plt

    require_renderer(comp.code)
    x0, x1 = comp.extent
    pad = max(0.35, (x1 - x0) * pad_frac)
    lo, hi = x0 - pad, x1 + pad
    y_lo, y_hi = data_bounds(comp, lo, hi, system=system)
    # Margins PROPORTIONAL to the component, not absolute. A fixed 0.80 m
    # dimension allowance is reasonable for a 8 m structure and absurd for
    # a 1 m GD-TP, where it dominated the vertical range and produced a
    # figure mostly empty below the drawing.
    x_span = hi - lo
    dim_space = max(0.28, 0.16 * x_span)      # room for TWO stacked arrows
    top_space = max(0.12, 0.06 * x_span)
    y_lo -= dim_space
    y_hi += top_space
    y_span = max(y_hi - y_lo, 0.3)

    ax_frac = 0.72 if table else 0.97
    h = width * ax_frac * (y_span / x_span) + 2.4      # + title, legend, labels
    h = min(max(h, 4.0), 13.0)

    fig = plt.figure(figsize=(width, h))
    if table:
        gs = fig.add_gridspec(1, 2, width_ratios=[3.1, 1.0], wspace=0.05)
        ax = fig.add_subplot(gs[0])
        ax_t = fig.add_subplot(gs[1])
    else:
        ax = fig.add_subplot(1, 1, 1)
        ax_t = None

    draw_pipe_reference(ax, comp.pipe, lo, hi)
    draw_section_band(ax, comp)
    fill_outline(ax, comp)
    draw_structural(ax, comp)
    draw_geometry(ax, comp)
    draw_contact_envelope(ax, comp)
    draw_connectors(ax, comp, system=system)
    _, missing = draw_point_masses(ax, comp)
    draw_branch_support(ax, comp)
    draw_junctions(ax, comp)
    if dimensions:
        # BELOW everything drawn, so it never crosses the body, and
        # stacked by a gap that scales with the component too.
        draw_accessor_dimensions(ax, comp, system=system,
                                 y_dim=y_lo + 0.25 * dim_space,
                                 gap=0.42 * dim_space)

    ax.set_aspect('equal', adjustable='box')
    ax.set_xlim(lo, hi)
    ax.set_ylim(y_lo, y_hi)
    ax.invert_yaxis()                       # item 26: y is positive DOWN
    ax.set_xlabel('x (m)', labelpad=2)
    ax.set_ylabel('y (m, positive DOWN)')
    ax.spines[['top', 'right']].set_visible(False)
    sysline = f'   [{system}]' if system else ''
    ax.set_title(title or f'{component_label(comp.code)}  --  detail{sysline}',
                 fontsize=STYLE['fonts']['title'], weight='bold')
    h, l = ax.get_legend_handles_labels()
    for ph in getattr(ax, '_connector_handles', []):
        h.append(ph); l.append(ph.get_label())
    ax.legend(h, l, loc='upper center', bbox_to_anchor=(0.5, -0.26), ncol=3,
              fontsize=STYLE['fonts']['small'], framealpha=0.92)

    if missing:
        ax.annotate('UNRESOLVED point mass node(s): ' + ', '.join(missing),
                    xy=(0.01, 0.02), xycoords='axes fraction', fontsize=STYLE['fonts']['annotation'],
                    color=STYLE['colors']['WARNING'], weight='bold')
    if ax_t is not None:
        _param_table(ax_t, comp)
    else:
        fig.tight_layout()
    if path:
        fig.savefig(path, dpi=STYLE['figure']['export_dpi'], bbox_inches='tight')
    return fig

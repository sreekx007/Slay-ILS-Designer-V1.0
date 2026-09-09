"""ils_plotter.py -- draw a whole ILS on its header, with the surface a
roller would touch, and the ASSEMBLY-level parameters.

Replaces `plot_assembly` in the frozen `plot_schematic.py` (plan Sec.6).

SCOPE, and the line it does not cross
-------------------------------------
This module draws THE ILS AND ITS HEADER -- roughly 12 m of pipe, the
header the design owns (plan Sec.4), auto-extended only when a component
would otherwise overhang it.

It does NOT draw the lay pipeline, the stinger, the rollers, or a passage
sequence. Those belong to a SLAY-tier plotter, because they belong to a
lay configuration, and an ILS exists precisely so a design can be
reviewed, stored and compared BEFORE one is chosen. A plotter reaching for
roller stations would make every ILS figure depend on a stinger the
definition never named.

The physical reading of that boundary: this figure answers "what shape is
this structure, and what surface does it present downwards?" A SLAY figure
answers "what happens when that shape passes over these rollers?" The
first is a property of the design alone; the second of the design AND the
lay. Separate figures keep them separately reviewable.

WHAT THIS ADDS over `component_plotter`, which it imports and reuses:

  * the HEADER PIPELINE the assembly sits on
  * the CONTACT ENVELOPE resolved ACROSS components by `Assembly.contact_at`
  * the DEEPEST POINT, which is what governs clearance
  * the ASSEMBLY-LEVEL parameter panel -- mass, CoG, extent, system

DIVISION OF THE TWO PANELS. This module shows what only an ASSEMBLY can
know: total mass and where it acts, overall extent against the header, the
one named connection system, who owns contact. `component_plotter` shows
what a COMPONENT knows: its own geometry parameters. Neither repeats the
other, so no figure carries two versions of one number.

WHY THE ENVELOPE IS RESOLVED, NOT OVERLAID. What a roller would feel at a
station is the LOWEST surface there, whichever component owns it, and
ownership changes along the length -- a base structure takes over from the
bare pipe, a shroud from the wall. `Assembly.contact_at` resolves that;
drawing each component's own envelope separately would show several
candidate surfaces and leave the reader to pick.

y IS POSITIVE DOWN (item 26), so the DEEPEST surface is at MAXIMUM y and
the axis is inverted for display. `plot_assembly` lacked the inversion
until 24 Aug 2026 and drew every assembly figure upside down while
reporting the deepest point as `min(y)` -- naming the structure furthest
ABOVE the pipe as the deepest surface a roller sees. The numbers were
right throughout, which is why it survived.

DEPENDENCIES: matplotlib, numpy, component_plotter, component_spec, and
transitively config + slay_config.yaml. It does NOT import `ils_builder`:
the ILS is duck-typed on `.components`, `.assembly`, `.header`, `.pipe`,
so this can be exercised without the builder.
"""
from __future__ import annotations

import numpy as np

import component_plotter as cp
from component_spec import LoadPath

DEEPEST = '#B71C1C'
AMBIG = '#F9A825'


def _codes_of(ils):
    return getattr(ils, 'codes', None) or [c.code for c in ils.components]


def contact_profile(ils, n=800, lo=None, hi=None):
    """Sample the assembly contact envelope across the header.

    Returns (xs, ys, owners, load_paths, arms, ambiguous_xs).

    LOAD PATH AND ARM ARE CARRIED, not discarded. `Contact` answers four
    things and an earlier version of this module used two, so an envelope
    borne through a connector drew identically to one bearing on the pipe
    wall. Those are different mechanical objects: one has a moment arm
    through a structure, the other does not.

    STRICT ownership RAISES where two components both claim a station,
    rather than guessing -- the right default, since a plausible assembly
    with the wrong envelope produces an FEA run that converges and reports
    a believable strain. But a FIGURE is exactly where such a clash should
    be VISIBLE rather than fatal, so the raise is caught per sample, the
    station recorded, and the span drawn and captioned instead of the plot
    aborting.
    """
    if lo is None:
        lo, hi = ils.header
    asm = ils.assembly
    xs, ys, owners, paths, arms, ambiguous = [], [], [], [], [], []
    for x in np.linspace(lo, hi, n):
        x = float(x)
        try:
            c = asm.contact_at(x)
        except Exception:
            ambiguous.append(x)
            xs.append(x); ys.append(np.nan)
            owners.append(None); paths.append(None); arms.append(np.nan)
            continue
        xs.append(x)
        ys.append(c.y if c is not None else np.nan)
        owners.append(c.owner if c is not None else None)
        paths.append(c.load_path if c is not None else None)
        arms.append(c.arm if c is not None else np.nan)
    return xs, ys, owners, paths, arms, ambiguous


def draw_contact_envelope(ax, ils, n=800, lo=None, hi=None, label=True,
                          annotate_deepest=True):
    """The bottom surface a roller would see, across the whole assembly."""
    xs, ys, owners, paths, arms, ambiguous = contact_profile(
        ils, n=n, lo=lo, hi=hi)

    # Split the envelope into runs of constant LOAD PATH and draw each in
    # its own style, so a reaction through a connector cannot be mistaken
    # for one bearing straight on the pipe wall.
    seen, i = set(), 0
    while i < len(xs):
        j = i
        while j < len(xs) and paths[j] is paths[i]:
            j += 1
        lp = paths[i]
        if lp is not None:
            via = lp is LoadPath.CONNECTOR
            lab = None
            if label and lp not in seen:
                lab = ('contact envelope -- via CONNECTOR (moment arm)'
                       if via else 'contact envelope -- into PIPE WALL')
                seen.add(lp)
            ax.plot(xs[i:j], ys[i:j], lw=3.4,
                    color=cp.CONTACT_VIA_CONN if via else cp.CONTACT_ENV,
                    ls=(0, (6, 2)) if via else '-',
                    zorder=8, solid_capstyle='butt', label=lab)
            if via:
                k = (i + j) // 2
                # BELOW the line on screen: the deepest-point caption sits
                # above it and the two collided.
                ax.annotate(f'arm {arms[k]:.3f} m', (xs[k], ys[k]),
                            textcoords='offset points', xytext=(0, -15),
                            ha='center', fontsize=8,
                            color=cp.CONTACT_VIA_CONN, weight='bold',
                            zorder=13)
        i = j

    if ambiguous:
        ax.axvspan(min(ambiguous), max(ambiguous), color=AMBIG, alpha=0.30,
                   zorder=3,
                   label='CONTACT AMBIGUOUS -- two owners claim this span'
                   if label else None)

    finite = [(x, y) for x, y in zip(xs, ys) if np.isfinite(y)]
    deepest = None
    if finite:
        # y positive DOWN, so the deepest surface is at MAX y.
        xd, yd = max(finite, key=lambda p: p[1])
        i = xs.index(xd)
        own = owners[i] if i < len(owners) else None
        deepest = (xd, yd, own)
        if annotate_deepest:
            ax.plot([xd], [yd], 'v', ms=10, color=DEEPEST, zorder=13)
            # BELOW the envelope on screen. Above it is where the
            # component captions sit, and on a shallow assembly the two
            # printed over each other.
            ax.annotate(f'deepest {yd:.4f} m' + (f'  ({own})' if own else ''),
                        xy=(xd, yd), textcoords='offset points',
                        xytext=(8, -14), fontsize=8.5, color=DEEPEST,
                        weight='bold', zorder=13, va='top')
    return xs, ys, owners, paths, arms, ambiguous, deepest


# ---------------------------------------------------------------------------
# Assembly-level parameters -- what no single component can state
# ---------------------------------------------------------------------------

def assembly_parameters(ils, deepest=None, ambiguous=None, paths=None):
    """(label, value) pairs an ASSEMBLY knows and a component cannot.

    Mass and CoG are the clearest case: no component can compute either,
    because each needs to see the whole. They are read from the ILS when
    it offers them and omitted when it does not, so a duck-typed object
    lacking them still plots.

    MASS IS REPORTED AS A FLOOR. GD-ST and GD-SB carry no mass parameter at
    all, so a total quietly excluding them would still look like a total.
    The panel says so on the figure rather than in a footnote elsewhere.
    """
    rows = []
    codes = _codes_of(ils)
    name = getattr(ils, 'definition', {}).get('ils', {}).get('name')
    if name:
        rows.append(('name', str(name)))
    rows.append(('components', f'{len(ils.components)}'))
    rows.append(('codes', ', '.join(codes)))

    sysname = getattr(ils, 'connection_system', None)
    rows.append(('connection system', sysname or 'per-component default'))
    own = getattr(ils, 'ownership', None)
    if own is not None:
        rows.append(('ownership', getattr(own, 'value', str(own))))

    lo, hi = ils.header
    auto = getattr(ils, 'header_auto', None)
    rows.append(('header', f'{lo:+.3f} .. {hi:+.3f} m'))
    if auto:
        rows.append(('', 'AUTO-EXTENDED past 12 m'))
    ex = getattr(ils, 'extent', None)
    if ex:
        rows.append(('assembly extent', f'{ex[0]:+.3f} .. {ex[1]:+.3f} m'))
        rows.append(('span', f'{ex[1] - ex[0]:.3f} m'))

    try:
        bd = ils.mass_breakdown
        rows.append(('mass (FLOOR)', f'{bd["total_kg"]:,.0f} kg'))
        rows.append(('  pipe steel', f'{bd["pipe_steel_kg"]:,.0f} kg'))
        rows.append(('  point masses', f'{bd["point_masses_kg"]:,.0f} kg'))
        cx, cy = ils.cog
        rows.append(('CoG x', f'{cx:+.4f} m'))
        rows.append(('CoG y', f'{cy:+.4f} m'))
    except Exception:
        pass

    if paths:
        kinds = sorted({p.value for p in paths if p is not None})
        rows.append(('contact load path', ', '.join(kinds) or '--'))
    if deepest:
        xd, yd, own_d = deepest
        rows.append(('deepest contact', f'{yd:+.4f} m'))
        rows.append(('  at x', f'{xd:+.3f} m'))
        if own_d:
            rows.append(('  owner', str(own_d)))
    if ambiguous:
        rows.append(('CONTACT CLASH', f'{min(ambiguous):+.3f} .. '
                                       f'{max(ambiguous):+.3f} m'))

    prov = getattr(getattr(ils, 'assembly', None), 'provenance', None)
    if prov is not None:
        rows.append(('provenance', getattr(prov, 'name', str(prov))))

    # PER-COMPONENT free parameters and the CONNECTOR layout. An assembly
    # panel listing only assembly-level quantities is not enough to read an
    # ILT: the branch run, the frame size and where the connectors sit are
    # what the layout IS, and they live on the components. Listed per body,
    # so nothing has to be looked up in a second figure.
    import component_plotter as _cp
    ids = getattr(ils, 'ids', None) or [f'C{i+1}' for i in range(len(ils.components))]
    for cid, c in zip(ids, ils.components):
        rows.append(('', ''))
        rows.append((f'-- {cid} / {c.code}', ''))
        for nm, val in _cp.free_parameters(c):
            if nm in ('provenance',):
                continue
            if isinstance(val, float):
                rows.append((f'  {nm}', f'{val:.4f} m' if abs(val) < 100
                             else f'{val:.4g}'))
            elif isinstance(val, tuple):
                rows.append((f'  {nm}', ', '.join(
                    f'{v:.4f}' if isinstance(v, float) else str(v)
                    for v in val)))
            elif val is not None:
                rows.append((f'  {nm}', str(val)))
        # connector layout, from the ILS-level system
        if hasattr(c, 'active_connectors'):
            try:
                conns = ils.connectors_of(c)
            except Exception:
                conns = []
            # 5-tuple since 28 Aug 2026: (slot, x, type, arm, gap). The gap
            # is the deadband on a 'D' connector and None on every other
            # type -- it is shown when present, because a deadband changes
            # where strain goes and a panel that omitted it would describe
            # the connector as though it engaged immediately.
            for slot, x, t, arm, gap in conns:
                detail = f'x = {x:+.4f} m, arm {arm:.4f} m'
                if gap is not None:
                    detail += f', gap {gap:.4f} m'
                rows.append((f'  slot {slot} [{t}]', detail))
        if c.code == 'GD-B':
            ends = [n for n in c.structural_nodes()
                    if n.node_id.endswith(':send')]
            if ends:
                rows.append((f'  support [{c.support_connector}]',
                             f'x = {ends[0].x:+.4f}, y = {ends[0].y:+.4f} m'))
    return rows


def _param_panel(ax, rows):
    ax.axis('off')
    if not rows:
        return
    # bbox rather than loc=: a matplotlib table does NOT clip to its axes,
    # so a 16-row panel drawn with loc='upper left' overflowed downward
    # across the exclusion note beneath it. bbox pins it to exactly this
    # axes, whatever the row count.
    t = ax.table(cellText=[[k, v] for k, v in rows],
                 colLabels=['assembly parameter', 'value'],
                 cellLoc='left', colWidths=[0.44, 0.56],
                 bbox=[0.0, 0.0, 1.0, 1.0])
    t.auto_set_font_size(False)
    t.set_fontsize(7.4)
    for (row, _), cell in t.get_celld().items():
        cell.set_edgecolor('0.85')
        if row == 0:
            cell.set_facecolor('0.93')
            cell.set_text_props(weight='bold')
def _exclusion_note(ax, exclusions):
    """The mass exclusions, in their OWN axes below the table.

    Annotating them inside the table's axes overlapped the last rows
    whenever the figure was short -- and the row it covered was
    'provenance', which is exactly the sort of thing a reader needs to
    see. A separate axes cannot collide.
    """
    ax.axis('off')
    if not exclusions:
        return
    import textwrap
    lines = []
    for e in exclusions:
        # Keep the component prefix. Stripping it made the GD-ST and GD-SB
        # entries read as one repeated note; truncating lost the reason.
        lines += textwrap.wrap(e, width=62, initial_indent='- ',
                               subsequent_indent='   ')
    ax.annotate('MASS EXCLUDES\n' + '\n'.join(lines),
                xy=(0.0, 1.0), xycoords='axes fraction',
                va='top', ha='left', fontsize=6.2, color='#B71C1C')


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def plot_ils(ils, system=None, title=None, path=None, width=15.0, n=800,
             label_components=True, panel=True, show_exclusions=True,
             xlim=None):
    """An ILS on its header, with the contact envelope and the
    assembly-level parameters.

    No stinger, no rollers, no passage -- see the module docstring.
    """
    import matplotlib.pyplot as plt

    comps = list(ils.components)
    codes = _codes_of(ils)
    sysname = system or getattr(ils, 'connection_system', None)
    lo, hi = ils.header
    # OPTIONAL focus window. The header is the design container and is
    # always what the panel reports; but on an ILT the interesting part can
    # be a 0.4 m post on a 12.7 m header, where equal aspect renders it 3%
    # of the width and unreadable. Clipping the VIEW is not the same as
    # changing the header, so the figure says which it is showing.
    clipped = None
    if xlim:
        clipped = (lo, hi)
        lo, hi = xlim

    # Vertical extent from accessors, so equal aspect (Sec.0.3's tool
    # standard) is satisfied by SIZING the figure rather than by letting
    # matplotlib shrink the axes inside a fixed one and leave the rest
    # white.
    ys = [ils.pipe.OD_pipe / 2.0, -ils.pipe.OD_pipe / 2.0]
    for c in comps:
        ys += [nd.y for nd in c.geometry_nodes()]
        ys += [nd.y for nd in c.structural_nodes()]
    pre = contact_profile(ils, n=241, lo=lo, hi=hi)
    ys += [y for y in pre[1] if np.isfinite(y)]
    # Margin scaled to the DATA height, not to the header length. A margin
    # tied to x_span would be ~0.7 m on a 12 m header and swamp an assembly
    # only half a metre tall.
    data_h = max(max(ys) - min(ys), 0.2)
    marg = max(0.18, 0.22 * data_h)
    y_lo, y_hi = min(ys) - marg, max(ys) + marg
    x_span, y_span = hi - lo, max(y_hi - y_lo, 0.3)

    ax_frac = 0.68 if panel else 0.97
    # Equal aspect is the tool standard (Sec.0.3), so a 12 m header holding
    # a 0.5 m assembly IS a thin strip -- that is the honest shape and is
    # not corrected. What must adapt is everything AROUND it.
    ax_h_in = width * ax_frac * (y_span / x_span)
    h = min(max(ax_h_in + 2.2, 3.4), 14.0)

    # ...and the PANEL must fit too. Once per-component parameters went in,
    # a two-body ILT produced ~35 rows into a table sized only by the
    # drawing, and the rows printed over each other. Height is now the
    # greater of what the drawing needs and what the panel needs.
    if panel:
        n_rows = len(assembly_parameters(ils)) + 1
        h = min(max(h, n_rows * 0.175 + 1.4), 20.0)

    fig = plt.figure(figsize=(width, h))
    if panel:
        gs = fig.add_gridspec(1, 2, width_ratios=[2.7, 1.0], wspace=0.05)
        ax = fig.add_subplot(gs[0])
        sub = gs[1].subgridspec(2, 1, height_ratios=[3.4, 1.0], hspace=0.06)
        ax_p = fig.add_subplot(sub[0])
        ax_e = fig.add_subplot(sub[1])
    else:
        ax = fig.add_subplot(1, 1, 1)
        ax_p = ax_e = None
    ax.set_aspect('equal', adjustable='box')

    # --- the header the whole assembly sits on -------------------------
    cp.draw_pipe_reference(ax, ils.pipe, lo, hi)

    # --- each component, through the SAME renderer as the detail view --
    first = True
    for comp in comps:
        cp.draw_section_band(ax, comp, label=first)
        cp.fill_outline(ax, comp)
        cp.draw_structural(ax, comp, label=first)
        cp.draw_geometry(ax, comp, label=first)
        cp.draw_connectors(ax, comp, system=sysname, label=first)
        cp.draw_point_masses(ax, comp, label=first)
        # AFTER the masses, and always label=True. The branch connector
        # mass sits on the SAME node as the support, so drawing the symbol
        # first let the mass marker cover it; and gating the legend on
        # `first` hid the entry entirely whenever the branch was not the
        # first component -- which it never is.
        cp.draw_branch_support(ax, comp, label=True)
        cp.draw_junctions(ax, comp, label=first)
        first = False

    # --- the assembly-level envelope -----------------------------------
    _, _, _, _paths, _, ambiguous, deepest = draw_contact_envelope(
        ax, ils, n=n, lo=lo, hi=hi)

    # --- component labels ----------------------------------------------
    # Anchored to each component's OWN body and coloured to match its fill.
    # Stacking them in the empty strip above the pipe -- the obvious
    # approach, since an ILS normally has GD-TT, GD-ST, GD-SB and GD-B all
    # at centre_x = 0 -- puts every caption where the reader associates it
    # with whichever body it happens to overlap.
    if label_components:
        used = []
        x_tol = 0.06 * (hi - lo)
        for comp, code in zip(comps, codes):
            ys_n = [nd.y for nd in comp.geometry_nodes()]
            y_anchor = (sum(ys_n) / len(ys_n)) if ys_n else 0.0
            # Collision is a 2-D test. Checking y alone pushed two GD-TP
            # captions apart vertically although they sat 3 m apart in x,
            # which reads as a difference in elevation between two
            # identical components.
            # A ZERO-LENGTH component has no body to sit on and nothing
            # drawn to identify it, so its caption is the only evidence it
            # exists. GD-Con is zero-length whenever y_struct == 0, which is
            # every connector on a structure with P_vt = 0 -- a whole set of
            # them at once, not an edge case.
            #
            # Collision-avoidance must not move those: displacing a caption
            # off a body the reader can see is a cosmetic loss, but
            # displacing the ONLY mark of an invisible component makes it
            # read as absent. OBSERVED 5Sep26 -- an EA-SB F1D layout was
            # reported as missing its centre connector, which was present
            # and correctly associated; its caption had been pushed 0.52 m
            # clear of the assembly because GD-TP and GD-SB shared the same
            # station.
            #
            # So: pin a zero-length component's caption to its own station
            # and let it overlap. Everything with a real body still shifts.
            zero_len = abs(comp.extent[1] - comp.extent[0]) < 1e-9
            if not zero_len:
                while any(abs(y_anchor - uy) < 0.22 and
                          abs(comp.centre_x - ux) < x_tol for ux, uy in used):
                    y_anchor -= 0.26
                used.append((comp.centre_x, y_anchor))
            ax.annotate(code, xy=(comp.centre_x, y_anchor),
                        fontsize=9, ha='center', va='center', zorder=15,
                        color=cp.BODY_FILL.get(code, '0.25'), weight='bold',
                        bbox=dict(boxstyle='round,pad=0.22', fc='white',
                                  ec=cp.BODY_FILL.get(code, '0.6'),
                                  lw=0.9, alpha=0.90))

    ax.set_xlim(lo, hi)
    ax.set_ylim(y_lo, y_hi)
    ax.invert_yaxis()                       # item 26: y is positive DOWN
    ax.set_xlabel('x (m)   -- ILS-LOCAL, origin at the ILS reference point',
                  labelpad=2)
    if clipped:
        ax.annotate(f'VIEW CLIPPED to {lo:+.2f}..{hi:+.2f} m -- '
                    f'header is {clipped[0]:+.3f}..{clipped[1]:+.3f} m',
                    xy=(0.5, 1.005), xycoords='axes fraction', ha='center',
                    fontsize=7.5, color='#B3261E', weight='bold')
    ax.set_ylabel('y (m, positive DOWN)')
    ax.spines[['top', 'right']].set_visible(False)

    name = getattr(ils, 'definition', {}).get('ils', {}).get('name')
    head = title or ('ILS' + (f' "{name}"' if name else '') + '  --  '
                     + ' + '.join(codes))
    ax.set_title(head + (f'   [{sysname}]' if sysname else ''),
                 fontsize=11, weight='bold')
    # Legend offset in AXES fractions must be converted from a physical
    # clearance, or it collapses onto the drawing whenever the axes is
    # short: -0.20 of a 0.9 in strip is 2 mm, not the ~15 mm intended.
    leg_off = -(0.62 / max(ax_h_in, 0.35))
    h, l = ax.get_legend_handles_labels()
    for ph in getattr(ax, '_connector_handles', []):
        h.append(ph); l.append(ph.get_label())
    ax.legend(h, l, loc='upper center', bbox_to_anchor=(0.5, leg_off), ncol=3,
              fontsize=7.5, framealpha=0.92)

    if ax_p is not None:
        exc = None
        if show_exclusions:
            try:
                exc = ils.mass_exclusions()
            except Exception:
                exc = None
        _param_panel(ax_p, assembly_parameters(ils, deepest=deepest,
                                                ambiguous=ambiguous,
                                                paths=_paths))
        _exclusion_note(ax_e, exc)
    else:
        fig.tight_layout()

    if path:
        fig.savefig(path, dpi=150, bbox_inches='tight')
    return fig

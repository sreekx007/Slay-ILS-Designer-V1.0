#!/usr/bin/env python3
"""Generate preliminary deterministic diagrams for Paper 01A and Paper 01B."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "slay-ils-paper-figures-v1"
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "preliminary"
OUT.mkdir(parents=True, exist_ok=True)

COLORS = {
    "navy": "#17324D",
    "blue": "#2878B5",
    "cyan": "#54B6C7",
    "green": "#4A9B73",
    "amber": "#D69E2E",
    "red": "#C95555",
    "purple": "#7663B0",
    "grey": "#667785",
    "light": "#F4F7FA",
    "ink": "#17212B",
}

FONT_SCALE = 1.55


def font_size(value):
    """Scale diagram text for manuscript-width readability."""
    return value * FONT_SCALE


def box(ax, x, y, w, h, title, body="", color="blue", fontsize=9, dashed=False):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.015,rounding_size=0.025",
        facecolor="white",
        edgecolor=COLORS[color],
        linewidth=1.8,
        linestyle="--" if dashed else "-",
        zorder=2,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h * 0.66, title, ha="center", va="center",
            fontsize=font_size(fontsize), fontweight="bold", color=COLORS["ink"], zorder=3)
    if body:
        ax.text(x + w / 2, y + h * 0.30, body, ha="center", va="center",
                fontsize=font_size(fontsize - 1.7), color=COLORS["grey"], linespacing=1.25, zorder=3)
    return patch


def arrow(ax, x1, y1, x2, y2, color="grey", style="-|>", curve=0.0, label=None):
    p = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle=style,
        mutation_scale=13,
        linewidth=1.5,
        color=COLORS[color],
        connectionstyle=f"arc3,rad={curve}",
        zorder=1,
    )
    ax.add_patch(p)
    if label:
        ax.text((x1+x2)/2, (y1+y2)/2 + 0.025, label, ha="center", va="bottom",
                fontsize=font_size(7.5), color=COLORS[color])
    return p


def setup(title, subtitle, size=(13, 7.2), footer="PRELIMINARY - CONCEPTUAL WORKFLOW, NOT DESIGN VERIFICATION"):
    fig, ax = plt.subplots(figsize=size)
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.03, 0.96, title, fontsize=font_size(16), fontweight="bold",
            color=COLORS["navy"], va="top")
    ax.text(0.03, 0.905, subtitle, fontsize=font_size(9), color=COLORS["grey"], va="top")
    ax.text(0.97, 0.025, footer,
            fontsize=font_size(6.8), color=COLORS["red"], ha="right")
    return fig, ax


def save(fig, name):
    svg_path = OUT / f"{name}.svg"
    fig.savefig(svg_path, bbox_inches="tight", facecolor="white", metadata={"Date": None})
    normalized = "\n".join(line.rstrip() for line in svg_path.read_text(encoding="utf-8").splitlines()) + "\n"
    svg_path.write_text(normalized, encoding="utf-8")
    fig.savefig(OUT / f"{name}.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def engineering_workflow():
    fig, ax = setup(
        "Engineering AI workflow: from request to reviewed output",
        "Paper 01A explanatory view - each gate produces an inspectable engineering record",
        (14, 8),
    )
    xs = [0.015, 0.212, 0.409, 0.606, 0.803]
    titles = ["1. Engineer\nrequest", "2. EDPR", "3. Governed\nknowledge", "4. Deterministic\ntools", "5. Review\npackage"]
    bodies = [
        "purpose, constraints,\nknowns and questions",
        "requirements, unknowns,\nobjectives and checks",
        "EDES components\nEDAS assemblies\nEDIKB evidence",
        "validate, retrieve,\nbuild, calculate,\nplot and inspect",
        "candidate or gap\nplot + report\nand evidence",
    ]
    colors = ["navy", "purple", "blue", "green", "amber"]
    for i, x in enumerate(xs):
        box(ax, x, 0.56, 0.18, 0.26, titles[i], bodies[i], colors[i], 9)
        if i:
            arrow(ax, xs[i-1] + 0.18, 0.69, x, 0.69)
    box(ax, 0.74, 0.25, 0.22, 0.17, "Human\ndecision", "approve, clarify, reject,\nor request analysis", "navy", 9)
    box(ax, 0.47, 0.22, 0.22, 0.19, "KEL evolutionary\nloop", "capture feedback, group,\nreview and evolve graph", "purple", 9)
    box(ax, 0.19, 0.20, 0.22, 0.21, "Explicit gap\noutcome", "missing input\nmissing evidence\nunsupported topology", "red", 9, dashed=True)
    arrow(ax, 0.85, 0.56, 0.85, 0.42, "navy")
    arrow(ax, 0.74, 0.335, 0.69, 0.315, "purple")
    arrow(ax, 0.58, 0.41, 0.50, 0.56, "purple", curve=0.10)
    ax.text(0.565, 0.475, "approved\nupdate", ha="center", va="center",
            fontsize=font_size(6.5), color=COLORS["purple"], linespacing=1.05)
    arrow(ax, 0.62, 0.56, 0.36, 0.41, "red", curve=-0.10, label="stop safely")
    ax.text(0.03, 0.055,
            "LLM role: interpret language, propose records, plan retrieval, explain results.\n"
            "Tool role: enforce schemas, topology, arithmetic, layout construction and plot QA.\n"
            "Engineer role: confirm intent, judge evidence applicability and authorize knowledge change.",
            fontsize=font_size(7.4), color=COLORS["ink"], va="bottom", linespacing=1.30)
    save(fig, "paper01a_engineering_workflow")


def component_ontology_primer():
    """Draw the paper-scope component vocabulary before either paper uses its codes."""
    fig, ax = setup(
        "Canonical GD component vocabulary",
        "Shared ontology primer - simplified symbols show identity and mechanical role, not fabrication detail",
        (16, 8.7),
        "PRELIMINARY - SCHEMATIC ONTOLOGY, NOT DESIGN VERIFICATION",
    )

    cards = [
        ("GD-HdPipe", "Header pipe", "main pipeline\nsegment", "pipe", "blue"),
        ("GD-BrPipe", "Branch pipe", "straight branch\nsegment", "branch_pipe", "blue"),
        ("GD-TP", "Thick pipe", "square-shouldered\nconcept section", "thick", "blue"),
        ("GD-TT", "Tapered thick pipe", "tapered design\nrealization", "taper", "blue"),
        ("GD-VLV", "Valve", "inline body, stem\nand envelope", "valve", "navy"),
        ("GD-B", "Branch piping assembly", "L or Z multi-member\nbranch", "branch", "purple"),
        ("GD-SH", "Shroud", "offset roller-contact\nenvelope", "shroud", "cyan"),
        ("GD-ST", "Top structure", "frame above\nheader", "top", "green"),
        ("GD-SB", "Base structure", "frame and contact\nbelow header", "base", "green"),
        ("GD-Con", "Connector", "vertical connection\nand top node", "connector", "amber"),
    ]

    x0, y0 = 0.035, 0.09
    card_w, card_h = 0.225, 0.235
    x_gap, y_gap = 0.018, 0.025

    def line(x1, y1, x2, y2, color="ink", width=2.0, style="-"):
        ax.plot([x1, x2], [y1, y2], color=COLORS[color], lw=width,
                linestyle=style, solid_capstyle="round", zorder=4)

    def draw_icon(kind, cx, cy, scale, color):
        c = COLORS[color]
        if kind == "pipe":
            line(cx-scale, cy, cx+scale, cy, color, 5.0)
            line(cx-scale, cy, cx+scale, cy, "ink", 1.2)
        elif kind == "branch_pipe":
            line(cx-scale*0.88, cy, cx+scale*0.88, cy, color, 4.0)
        elif kind == "thick":
            line(cx-scale, cy, cx-scale*0.55, cy, "ink", 2.0)
            ax.add_patch(Rectangle((cx-scale*0.55, cy-scale*0.28), scale*1.1, scale*0.56,
                                   facecolor="white", edgecolor=c, lw=3.0, zorder=4))
            line(cx+scale*0.55, cy, cx+scale, cy, "ink", 2.0)
        elif kind == "taper":
            pts = [(cx-scale,cy-scale*0.12),(cx-scale*0.55,cy-scale*0.34),
                   (cx+scale*0.55,cy-scale*0.34),(cx+scale,cy-scale*0.12),
                   (cx+scale,cy+scale*0.12),(cx+scale*0.55,cy+scale*0.34),
                   (cx-scale*0.55,cy+scale*0.34),(cx-scale,cy+scale*0.12)]
            ax.add_patch(Polygon(pts, closed=True, facecolor="white", edgecolor=c, lw=2.5, zorder=4))
            line(cx-scale, cy, cx+scale, cy, "ink", 1.1)
        elif kind == "valve":
            line(cx-scale, cy, cx-scale*0.42, cy, "ink", 2.0)
            line(cx+scale*0.42, cy, cx+scale, cy, "ink", 2.0)
            ax.add_patch(Polygon([(cx-scale*0.42,cy-scale*0.35),(cx,cy),(cx-scale*0.42,cy+scale*0.35)],
                                 closed=True, facecolor="white", edgecolor=c, lw=2.2, zorder=4))
            ax.add_patch(Polygon([(cx+scale*0.42,cy-scale*0.35),(cx,cy),(cx+scale*0.42,cy+scale*0.35)],
                                 closed=True, facecolor="white", edgecolor=c, lw=2.2, zorder=4))
            line(cx, cy+scale*0.05, cx, cy+scale*0.62, color, 2.0)
            line(cx-scale*0.22, cy+scale*0.62, cx+scale*0.22, cy+scale*0.62, color, 2.0)
        elif kind == "branch":
            line(cx-scale, cy-scale*0.55, cx+scale, cy-scale*0.55, "ink", 2.0)
            line(cx, cy-scale*0.55, cx, cy+scale*0.18, color, 3.0)
            line(cx, cy+scale*0.18, cx+scale*0.62, cy+scale*0.18, color, 3.0)
            line(cx+scale*0.62, cy+scale*0.18, cx+scale*0.62, cy+scale*0.62, color, 3.0)
        elif kind == "shroud":
            line(cx-scale, cy+scale*0.38, cx+scale, cy+scale*0.38, "ink", 2.0)
            line(cx-scale*0.72, cy+scale*0.14, cx+scale*0.72, cy+scale*0.14, color, 4.5)
            line(cx-scale*0.72, cy+scale*0.14, cx-scale*0.46, cy-scale*0.42, color, 2.2)
            line(cx+scale*0.72, cy+scale*0.14, cx+scale*0.46, cy-scale*0.42, color, 2.2)
            line(cx-scale*0.46, cy-scale*0.42, cx+scale*0.46, cy-scale*0.42, color, 2.2)
        elif kind == "top":
            line(cx-scale, cy-scale*0.42, cx+scale, cy-scale*0.42, "ink", 2.0)
            ax.add_patch(Rectangle((cx-scale*0.70,cy-scale*0.25),scale*1.40,scale*0.88,
                                   facecolor="none",edgecolor=c,lw=2.5,zorder=4))
        elif kind == "base":
            line(cx-scale, cy+scale*0.42, cx+scale, cy+scale*0.42, "ink", 2.0)
            pts=[(cx-scale*0.92,cy+scale*0.24),(cx-scale*0.60,cy-scale*0.55),
                 (cx+scale*0.60,cy-scale*0.55),(cx+scale*0.92,cy+scale*0.24)]
            ax.add_patch(Polygon(pts,closed=True,facecolor="none",edgecolor=c,lw=2.5,zorder=4))
        elif kind == "connector":
            node_y = cy + scale*0.52
            line(cx, cy-scale*0.72, cx, node_y-scale*0.18, "ink", 2.4)
            ax.add_patch(Circle((cx,node_y),scale*0.18,facecolor="white",edgecolor=c,lw=2.5,zorder=4))
            ax.text(cx,node_y,"C",ha="center",va="center",fontsize=font_size(6.4),
                    fontweight="bold",color=c,zorder=5)

    for index, (code, name, role, kind, color) in enumerate(cards):
        row, col = divmod(index, 4)
        col_offset = 1 if row == 2 else 0
        x = x0 + (col + col_offset) * (card_w + x_gap)
        y = y0 + (2-row) * (card_h + y_gap)
        patch = FancyBboxPatch((x,y),card_w,card_h,
                               boxstyle="round,pad=0.010,rounding_size=0.018",
                               facecolor="white",edgecolor=COLORS[color],lw=1.5,zorder=2)
        ax.add_patch(patch)
        ax.add_patch(Rectangle((x,y+card_h-0.038),card_w,0.038,
                               facecolor=COLORS[color],edgecolor="none",alpha=0.13,zorder=2))
        draw_icon(kind, x+card_w/2, y+card_h*0.70, 0.052, color)
        ax.text(x+card_w/2,y+card_h*0.40,code,ha="center",va="center",
                fontsize=font_size(10.0),fontweight="bold",color=COLORS["ink"],zorder=5)
        ax.text(x+card_w/2,y+card_h*0.27,name,ha="center",va="center",
                fontsize=font_size(8.5),color=COLORS[color],fontweight="bold",zorder=5)
        ax.text(x+card_w/2,y+card_h*0.10,role,ha="center",va="center",
                fontsize=font_size(7.3),color=COLORS["grey"],zorder=5)

    ax.text(0.035,0.055,
            "EDES defines component identity and parameters; EDAS defines placement, connection, contact and assembly relations.",
            fontsize=font_size(8.2),color=COLORS["ink"],ha="left")
    save(fig, "shared_component_ontology_primer")


def abstraction_ladder():
    fig, ax = setup(
        "S-lay ILT abstraction ladder",
        "Shared introductory figure - physical meaning is retained as the design becomes machine-readable",
        (14, 7.4),
    )
    xs = [0.015, 0.212, 0.409, 0.606, 0.803]
    titles = ["Physical\nassembly", "Engineering\nschematic", "Parameterized\nobjects", "Typed\nknowledge", "Executable\noutcome"]
    bodies = [
        "header, valve, branch,\nframes, supports, rollers",
        "positions, shapes,\nconnections, contact",
        "dimensions, stiffness,\nslots, envelopes, units",
        "EDES + EDAS + EDIKB\nused by one EDPR",
        "candidate, clarification,\nevidence or topology gap",
    ]
    colors = ["navy", "cyan", "blue", "purple", "green"]
    for i, x in enumerate(xs):
        box(ax, x, 0.53, 0.18, 0.26, titles[i], bodies[i], colors[i], 9)
        if i:
            arrow(ax, xs[i-1] + 0.18, 0.66, x, 0.66)
    y=0.31
    labels=[
        ("Object identity","GD-VLV, GD-ST, GD-SB, GD-B"),
        ("Associations","connects to, contains, supports"),
        ("Evidence scope","case, range, response, limitation"),
        ("Problem intent","objective, constraint, unknown"),
    ]
    for i,(t,b) in enumerate(labels):
        box(ax, 0.035+i*0.24, y, 0.21, 0.15, t, b, ["navy","blue","amber","purple"][i], 8)
    ax.text(0.5, 0.15,
            "The schematic is an information model. Geometry alone is insufficient unless component identity,\n"
            "active connectors, parent-child associations, evidence scope and unresolved inputs are visible.",
            ha="center", va="center", fontsize=font_size(9.5), color=COLORS["ink"])
    save(fig, "shared_ilt_abstraction_ladder")


def ai_architecture():
    fig, ax = setup(
        "Governed neuro-symbolic design architecture",
        "Paper 01B system view - neural interpretation is bounded by symbolic knowledge and executable gates",
        (14, 8.2),
    )
    box(ax, 0.035, 0.70, 0.16, 0.14, "Natural-language\ninput", "design request\nor feedback", "navy", 9)
    box(ax, 0.245, 0.70, 0.17, 0.14, "LLM interface", "parse, query,\nexplain", "purple", 9)
    arrow(ax, 0.195, 0.77, 0.245, 0.77)

    box(ax, 0.47, 0.70, 0.13, 0.14, "EDPR: G_P", "problem\ninstance", "purple", 9)
    arrow(ax, 0.415, 0.77, 0.47, 0.77)

    layers=[("EDES: G_E","components\ninterfaces","blue",0.08),
            ("EDAS: G_A","topology\nassociations","cyan",0.29),
            ("EDIKB: G_K","behavior\nprovenance","amber",0.50)]
    for title,body,color,x in layers:
        box(ax,x,0.43,0.18,0.14,title,body,color,9)
        arrow(ax,0.535,0.70,x+0.09,0.57,color,curve=0.08 if x<0.3 else -0.08)
    box(ax,0.74,0.39,0.20,0.20,"Deterministic\ntransition T","validate -> retrieve\nbuild -> screen\nmaterialize -> QA","green",9)
    for _,_,color,x in layers:
        arrow(ax,x+0.18,0.50,0.74,0.50,color)
    arrow(ax,0.60,0.77,0.84,0.57,"purple",curve=-0.08)

    box(ax,0.70,0.20,0.26,0.13,"Outcome O","candidate | clarification\ngap | failure","green",9)
    arrow(ax,0.84,0.39,0.84,0.33,"green")

    box(ax,0.37,0.18,0.23,0.16,"KEL state\nmachine","experience -> feedback\nreview -> graph change","purple",9)
    arrow(ax,0.70,0.265,0.60,0.265,"purple",style="<|-|>")
    box(ax,0.06,0.18,0.22,0.16,"Expert\ngovernance","confirm intent/evidence\napprove graph change","navy",9)
    arrow(ax,0.37,0.26,0.28,0.26,"navy",style="<|-|>")
    ax.text(0.50,0.09,
            "Persistent knowledge changes only after review. Missing knowledge is emitted as a typed outcome,\n"
            "allowing calibrated refusal to be evaluated as system behavior rather than treated as a failed answer.",
            ha="center",fontsize=font_size(9),color=COLORS["ink"])
    save(fig, "paper01b_governed_architecture")


def kel_lifecycle():
    fig, ax = setup(
        "Knowledge Evolution Loop",
        "Shared governance view - feedback remains traceable from observation to released knowledge",
        (14, 7.5),
    )
    xs=[0.035,0.19,0.345,0.50,0.655,0.81]
    titles=["Experience","Atomic\nfeedback","Feedback\ngroup","Change\nrequest","Expert\nreview","Implementation"]
    bodies=["query + output\nplot + evidence","one issue per record\nsource text retained","fingerprint +\nde-duplication","target layer +\nevidence need","accept, reject,\nor request evidence","plan + tests +\nrelease reference"]
    colors=["navy","purple","purple","blue","amber","green"]
    for i,x in enumerate(xs):
        box(ax,x,0.57,0.13,0.18,titles[i],bodies[i],colors[i],8.5)
        if i: arrow(ax,xs[i-1]+0.13,0.66,x,0.66)
    box(ax,0.35,0.29,0.18,0.13,"Superseded", "retained for audit\nnon-authoritative", "grey",9,dashed=True)
    box(ax,0.60,0.28,0.23,0.15,"Released knowledge", "EDES / EDAS / EDIKB\nEDPR / tooling", "green",8.2)
    arrow(ax,0.875,0.57,0.71,0.42,"green",curve=-0.12)
    arrow(ax,0.655,0.63,0.44,0.42,"grey",curve=0.12)
    ax.text(0.545,0.47,"rejected or replaced",ha="center",fontsize=font_size(7.0),color=COLORS["grey"])
    arrow(ax,0.62,0.355,0.16,0.57,"purple",curve=-0.25,label="new evidence and use")
    ax.text(0.5,0.14,
            "Lifecycle reconciliation permits one authoritative state per change-request identity.\n"
            "The loop records learning activity without allowing unreviewed conversation text to become design truth.",
            ha="center",fontsize=font_size(9.5),color=COLORS["ink"])
    save(fig, "shared_kel_lifecycle")


if __name__ == "__main__":
    engineering_workflow()
    component_ontology_primer()
    abstraction_ladder()
    ai_architecture()
    kel_lifecycle()
    records = [
        {"id":"P01A-F5","file":"preliminary/paper01a_engineering_workflow.svg","type":"generated_vector","status":"preliminary","source":"repository architecture and workflow documentation"},
        {"id":"P01-SC1","file":"preliminary/shared_component_ontology_primer.svg","type":"generated_vector","status":"preliminary","source":"EDES component definitions and plotter component catalog"},
        {"id":"P01-S2","file":"preliminary/shared_ilt_abstraction_ladder.svg","type":"generated_vector","status":"preliminary","source":"R7/R8 ontology mapping and repository crosswalk"},
        {"id":"P01B-F2","file":"preliminary/paper01b_governed_architecture.svg","type":"generated_vector","status":"preliminary","source":"EDPR/EDES/EDAS/EDIKB/KEL implementation"},
        {"id":"P01-S6","file":"preliminary/shared_kel_lifecycle.svg","type":"generated_vector","status":"preliminary","source":"KEL schemas, tools, and lifecycle documentation"},
        {"id":"P01-S1","file":"preliminary/shared_repository_ilt_schematic.svg","type":"ils_plotter_output","status":"preliminary_warning","source":"standard_ils_layouts.json archetype ILS-ILT","generator":"generate_repository_schematic.py","report":"preliminary/shared_repository_ilt_schematic.svg.report.json"},
    ]
    (ROOT / "figure_sources.json").write_text(json.dumps({"schema":"paper-figure-sources/0.1","figures":records},indent=2)+"\n",encoding="utf-8")
    print("generated", len(records), "preliminary figures")

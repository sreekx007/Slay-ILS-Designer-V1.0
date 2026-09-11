"""Rendered layout inspection and bounded correction, without model mutation."""
import textwrap
import numpy as np
from matplotlib.text import Annotation, Text
from matplotlib.patches import FancyArrowPatch
from matplotlib.path import Path
from matplotlib.transforms import Bbox, Affine2D


def snapshot(fig):
    fig.canvas.draw()
    ax = fig.axes[0]
    renderer = fig.canvas.get_renderer()
    labels = [t for t in ax.texts if isinstance(t, Annotation) and t.get_visible() and t.get_text()]
    boxes = [(t.get_bbox_patch().get_window_extent(renderer) if t.get_bbox_patch()
              else Text.get_window_extent(t, renderer)).expanded(1.08, 1.15) for t in labels]
    paths = [line.get_path().transformed(line.get_transform())
             for line in ax.lines if line.get_visible()]
    for collection in ax.collections:
        if not collection.get_visible():
            continue
        if collection.__class__.__name__ == 'PathCollection':
            points = collection.get_offset_transform().transform(collection.get_offsets())
            sizes = collection.get_sizes()
            radius = max(5, np.sqrt(max(sizes, default=36)) * fig.dpi / 144)
            paths.extend(Path.unit_rectangle().transformed(
                Affine2D().scale(2*radius).translate(x-radius, y-radius)) for x, y in points)
        else:
            paths.extend(p.transformed(collection.get_transform()) for p in collection.get_paths())
    for patch in ax.patches:
        if patch.get_visible():
            paths.append(patch.get_path().transformed(patch.get_transform()))
    return labels, boxes, paths


def inspect_layout(fig):
    labels, boxes, paths = snapshot(fig)
    out = []
    ax = fig.axes[0]
    renderer = fig.canvas.get_renderer()
    for i, (label, box) in enumerate(zip(labels, boxes)):
        reasons = []
        if any(box.overlaps(b) for j, b in enumerate(boxes) if j != i):
            reasons.append('label_overlap')
        if any(p.intersects_bbox(box, filled=True) for p in paths):
            reasons.append('structure_overlap')
        # Compare against figure, not axes: intentional external annotations are legal.
        if not fig.bbox.contains(box.x0, box.y0) or not fig.bbox.contains(box.x1, box.y1):
            reasons.append('outside_figure')
        axis_text = [ax.title, ax.xaxis.label, ax.yaxis.label,
                     *ax.get_xticklabels(), *ax.get_yticklabels()]
        if any(t.get_visible() and t.get_text() and box.overlaps(t.get_window_extent(renderer))
               for t in axis_text):
            reasons.append('axis_text_overlap')
        if reasons:
            out.append({'label': label.get_text(), 'index': i, 'reasons': reasons})
    legend = ax.get_legend()
    if legend:
        b = legend.get_window_extent(renderer)
        if any(b.overlaps(x) for x in boxes) or any(p.intersects_bbox(b, filled=True) for p in paths):
            out.append({'label': 'legend', 'reasons': ['legend_overlap']})
    title_box = ax.title.get_window_extent(renderer)
    if title_box.width > ax.bbox.width + 2:
        out.append({'label': 'title', 'reasons': ['title_overflow']})
    for panel_index, panel in enumerate(fig.axes):
        for table in panel.tables:
            for key, cell in table.get_celld().items():
                tb = cell.get_text().get_window_extent(renderer)
                cb = cell.get_window_extent(renderer)
                if tb.width > cb.width*0.95 or tb.height > cb.height*0.95:
                    out.append({'label': f'table {panel_index}:{key}', 'reasons': ['table_overflow']})
    return out


def correct_layout(fig, max_attempts=100):
    """Try finite display-space candidates and audit every presentation change.

    Anchors are retained, moved text gets leaders, and axis aspect is unchanged.
    Remaining collisions are warnings; no success claim is made for them.
    """
    corrections = []
    ax = fig.axes[0]
    initial = inspect_layout(fig)
    renderer = fig.canvas.get_renderer()
    title = ax.title
    original = title.get_text()
    width = title.get_window_extent(renderer).width
    if width > ax.bbox.width:
        title.set_text(textwrap.fill(original, max(16, int(len(original)*ax.bbox.width/width*0.8))))
        corrections.append({'type': 'title_wrap', 'before': original, 'after': title.get_text()})
    for panel_index, panel in enumerate(fig.axes):
        for table in panel.tables:
            rows = {}
            for (r, c), cell in table.get_celld().items():
                text = cell.get_text()
                original = text.get_text()
                w = text.get_window_extent(renderer).width
                target = cell.get_window_extent(renderer).width*0.78
                if w > target and original:
                    text.set_text(textwrap.fill(original, max(3, int(len(original)*target/w))))
                    corrections.append({'type': 'table_wrap', 'panel': panel_index, 'row': r,
                                        'column': c, 'before': original, 'after': text.get_text()})
                rows[r] = max(rows.get(r, 1), text.get_text().count('\n')+1)
            for (r, c), cell in table.get_celld().items():
                cell.set_height(rows[r]/sum(rows.values()))
    # Size tables from measured text heights, including wrapped lines.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    growth = 1.0
    for panel in fig.axes:
        for table in panel.tables:
            heights = {}
            for (r, c), cell in table.get_celld().items():
                heights[r] = max(heights.get(r, 0), cell.get_text().get_window_extent(renderer).height + 6)
            required = sum(heights.values())
            growth = max(growth, required / panel.bbox.height)
            for (r, c), cell in table.get_celld().items():
                cell.set_height(heights[r]/required)
    if growth > 1.01:
        before = list(fig.get_size_inches())
        fig.set_size_inches(before[0], min(36, before[1]*growth*1.03))
        corrections.append({'type': 'figure_height', 'before': before, 'after': list(fig.get_size_inches())})
    fig.canvas.draw()
    if any('structure_overlap' in item['reasons'] or 'label_overlap' in item['reasons']
           for item in initial):
        before = list(ax.get_ylim())
        span = before[1]-before[0]
        ax.set_ylim(before[0]-span*0.7, before[1]+span*0.7)
        corrections.append({'type': 'view_margin', 'before': before, 'after': list(ax.get_ylim())})
    labels, boxes, paths = snapshot(fig)
    renderer = fig.canvas.get_renderer()
    for i, label in enumerate(labels):
        box = boxes[i]
        if not any(box.overlaps(b) for j, b in enumerate(boxes) if j != i) and not any(p.intersects_bbox(box, filled=True) for p in paths) and ax.bbox.contains(box.x0, box.y0) and ax.bbox.contains(box.x1, box.y1):
            continue
        anchor = np.asarray(label._get_xy(renderer, label.xy, label.xycoords))
        before = list(label.get_position())
        coords = str(label.anncoords)
        for attempt in range(max_attempts):
            row = attempt//10
            side = 1 if attempt % 2 == 0 else -1
            x = np.clip(anchor[0]+((attempt//2)%5-2)*(box.width+10),
                        ax.bbox.x0+box.width/2+4, ax.bbox.x1-box.width/2-4)
            y = anchor[1]+side*(30+row*(box.height+10))
            b = Bbox.from_bounds(x-box.width/2, y-box.height/2, box.width, box.height)
            if not ax.bbox.contains(b.x0, b.y0) or not ax.bbox.contains(b.x1, b.y1):
                continue
            if any(b.overlaps(other) for j, other in enumerate(boxes) if j != i):
                continue
            if any(p.intersects_bbox(b, filled=True) for p in paths):
                continue
            label.set_anncoords('offset points')
            label.set_position(tuple((np.array([x, y])-anchor)*72/fig.dpi))
            label.set_ha('center')
            label.set_va('center')
            if label.arrow_patch is None:
                label.arrowprops = {'arrowstyle': '-', 'color': '0.45', 'lw': 0.7}
                label._arrow_relpos = (0.5, 0.5)
                label.arrow_patch = FancyArrowPatch((0, 0), (1, 1), **label.arrowprops)
                label.arrow_patch.set_figure(fig)
            boxes[i] = b
            corrections.append({'type': 'label_move', 'label': label.get_text(),
                                'anchor': list(label.xy), 'before': before,
                                'before_coordinates': coords, 'after': list(label.get_position()),
                                'after_coordinates': 'offset points'})
            break
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    legend = ax.get_legend()
    if legend:
        bottom = ax.xaxis.label.get_window_extent(renderer).y0
        if legend.get_window_extent(renderer).y1 > bottom-10:
            pos = (0.5, (bottom-22-ax.bbox.y0)/ax.bbox.height)
            legend.set_bbox_to_anchor(pos)
            corrections.append({'type': 'legend_move', 'after_axes_anchor': list(pos)})
    remaining = inspect_layout(fig)
    result = {'corrections': corrections, 'initial_issues': initial,
              'remaining_issues': remaining, 'max_attempts_per_label': max_attempts}
    fig._layout_qa = result
    return result

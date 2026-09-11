"""Basic plot QA. Inspect presentation and exports without changing geometry."""
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image


def check_plot(fig, components, output):
    """Check the first (geometry) axes and its exported image.

    Geometry bounds cover accessor nodes, extents and sampled contact surfaces.
    Label/legend overlap and iterative corrections belong to Phase 5.
    Vector exports are checked structurally, not independently rasterized.
    """
    checks = []
    def add(key, status, message):
        checks.append({'id': key, 'status': status, 'message': message})
    path = Path(output)
    if not path.is_file() or path.stat().st_size == 0:
        add('output_exists', 'failed', 'Export is missing or zero bytes.')
    else:
        add('output_exists', 'passed', 'Export exists and is nonempty.')
        try:
            if path.suffix.lower() == '.png':
                with Image.open(path) as image:
                    image.load()
                    rgba = image.convert('RGBA')
                    background = Image.new('RGBA', rgba.size, 'white')
                    pixels = np.asarray(Image.alpha_composite(background, rgba).convert('RGB'))
                    blank = bool(np.all(pixels == pixels[0, 0]))
                add('export_integrity', 'passed', 'PNG decoded successfully.')
                add('export_nonblank', 'failed' if blank else 'passed',
                    'PNG is a uniform image.' if blank else 'PNG contains pixel variation.')
            elif path.suffix.lower() == '.svg':
                root = ET.parse(path).getroot()
                if root.tag.split('}')[-1] != 'svg':
                    raise ValueError('Root element is not SVG')
                add('export_integrity', 'passed', 'SVG XML parsed successfully.')
                add('export_nonblank', 'not_applicable', 'SVG is not independently rasterized; live figure checked below.')
            elif path.suffix.lower() == '.pdf':
                data = path.read_bytes()
                if not data.startswith(b'%PDF-') or b'%%EOF' not in data[-1024:]:
                    raise ValueError('Missing PDF header or EOF marker')
                add('export_integrity', 'passed', 'PDF header and EOF present; full PDF decoding not performed.')
                add('export_nonblank', 'not_applicable', 'PDF is not independently rasterized; live figure checked below.')
            else:
                add('export_integrity', 'failed', 'Unsupported export format.')
        except Exception as exc:
            add('export_integrity', 'failed', f'Cannot read export: {exc}')
    if not fig.axes:
        add('figure_content', 'failed', 'Figure has no geometry axes.')
    else:
        ax = fig.axes[0]
        fig.canvas.draw()
        limits = np.array([*ax.get_xlim(), *ax.get_ylim()])
        valid = bool(np.isfinite(limits).all() and limits[0] != limits[1] and limits[2] != limits[3])
        add('axis_bounds', 'passed' if valid else 'failed', 'Axes require finite, nonzero x/y ranges.')
        visible = any(a.get_visible() for a in [*ax.lines, *ax.collections, *ax.patches, *ax.images])
        # Inspect the axes interior; titles, tables and legends cannot make an empty plot pass.
        pixels = np.asarray(fig.canvas.buffer_rgba())
        x0, y0, x1, y1 = ax.bbox.extents
        crop = pixels[max(0, int(pixels.shape[0]-y1)+2):int(pixels.shape[0]-y0)-2,
                      max(0, int(x0)+2):int(x1)-2, :3]
        nonblank = bool(crop.size and np.any(crop != crop[0, 0]))
        add('figure_content', 'passed' if visible and nonblank else 'failed',
            'Geometry axes contain visible artists and pixel variation.' if visible and nonblank else 'Geometry axes are empty or uniform.')
        points = []
        for comp in components:
            nodes = [*comp.geometry_nodes(), *comp.structural_nodes()]
            points.extend((node.x, node.y) for node in nodes)
            lo, hi = comp.extent
            points.extend([(lo, 0), (hi, 0)])
            for x in np.linspace(lo, hi, 241):
                contact = comp.contact_at(float(x))
                if contact is not None:
                    points.append((x, contact.y))
        coordinates = np.asarray(points, dtype=float)
        if not points or not np.isfinite(coordinates).all():
            add('geometry_bounds', 'failed', 'Geometry coordinates are missing or non-finite.')
        elif valid:
            xmin, xmax = sorted(ax.get_xlim()); ymin, ymax = sorted(ax.get_ylim())
            tolerance = 1e-8 * max(xmax-xmin, ymax-ymin, 1)
            outside = ((coordinates[:, 0] < xmin-tolerance) | (coordinates[:, 0] > xmax+tolerance)
                       | (coordinates[:, 1] < ymin-tolerance) | (coordinates[:, 1] > ymax+tolerance))
            add('geometry_clipping', 'warning' if outside.any() else 'passed',
                f'{int(outside.sum())} sampled geometry points outside the axes; no geometry moved.' if outside.any() else 'Accessor geometry and sampled contact surfaces fit the axes.')
            sx = ax.bbox.width / (xmax-xmin); sy = ax.bbox.height / (ymax-ymin)
            add('physical_scale', 'passed' if np.isclose(sx, sy, rtol=0.01) else 'warning',
                'Compared x/y physical scale with 1% tolerance; no correction applied.')
    if fig.axes:
        ax = fig.axes[0]
        data = ax.dataLim
        if np.isfinite(data.extents).all():
            xfill = min(1.0, abs(data.width) / abs(np.diff(ax.get_xlim())[0]))
            yfill = min(1.0, abs(data.height) / abs(np.diff(ax.get_ylim())[0]))
            add('whitespace_zoom', 'warning' if xfill < 0.05 and yfill < 0.05 else 'passed',
                f'Drawn data span uses {xfill:.1%} of x and {yfill:.1%} of y; header extent is retained.')
    from checkers.label_overlap_checker import inspect_layout
    remaining = inspect_layout(fig)
    corrections = getattr(fig, '_layout_qa', {}).get('corrections', [])
    add('label_legend_overlap', 'warning' if remaining else 'corrected' if corrections else 'passed', str(remaining) if remaining else 'No detected layout collisions remain.')
    errors = [c['message'] for c in checks if c['status'] == 'failed']
    warnings = [c['message'] for c in checks if c['status'] == 'warning']
    return {'plot_qa_status': 'failed' if errors else 'warning' if warnings else 'passed_with_corrections' if corrections else 'passed',
            'checks': checks, 'errors': errors, 'warnings': warnings, 'corrections': corrections, 'remaining_issues': remaining}

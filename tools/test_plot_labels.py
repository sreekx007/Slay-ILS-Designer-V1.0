"""Phase 5 collision, bounded failure and model-preservation regression tests."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plotters'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from checkers.label_overlap_checker import correct_layout, inspect_layout
from ils_builder import build_ils


class LabelLayoutTests(unittest.TestCase):
    def tearDown(self):
        plt.close('all')

    def test_overlapping_structure_labels_gain_leaders(self):
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot([0, 1], [0, 0])
        ax.set_xlim(-0.5, 1.5)
        ax.set_ylim(-0.5, 0.5)
        labels = [ax.annotate(name, (0.5, 0), bbox={'fc':'white'}) for name in ['one','two']]
        anchors = [t.xy for t in labels]
        self.assertTrue(inspect_layout(fig))
        result = correct_layout(fig)
        self.assertFalse(result['remaining_issues'], result)
        self.assertTrue(any(c['type']=='label_move' for c in result['corrections']))
        self.assertEqual([t.xy for t in labels], anchors)
        self.assertTrue(all(t.arrow_patch is not None for t in labels))

    def test_no_candidate_is_reported_not_hidden(self):
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 0])
        ax.annotate('A', (0.5, 0))
        ax.annotate('B', (0.5, 0))
        result = correct_layout(fig, max_attempts=0)
        self.assertTrue(result['remaining_issues'])

    def test_title_and_table_fit_after_wrapping(self):
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot([0, 1], [0, 1])
        ax.set_title('A very long title ' * 12)
        panel=fig.add_axes([0.7,0.6,0.25,0.3])
        panel.axis('off')
        table=panel.table(cellText=[['parameter', 'a long parameter value ' * 4]],
                          bbox=[0,0,1,1], colWidths=[0.4,0.6])
        table.auto_set_font_size(False)
        result=correct_layout(fig)
        self.assertTrue(any(c['type']=='table_wrap' for c in result['corrections']))
        self.assertFalse(any('table_overflow' in x['reasons'] or 'title_overflow' in x['reasons']
                             for x in result['remaining_issues']))


    def test_declared_connection_labels_are_added_to_figure(self):
        spec = {
            'schema_version': 1,
            'ils': {'connection_system': 'F1'},
            'pipeline': {'OD_pipe': 0.4064, 't_pipe': 0.021},
            'components': [
                {'id': 'st1', 'code': 'GD-ST', 'centre_x': 0.0, 'P_vt': -1.0, 'P_c1': 1.0, 'P_c2': 1.0},
                {'id': 'con1', 'code': 'GD-Con', 'centre_x': 0.0, 'conn_type': 'F', 'y_struct': -1.0},
                {'id': 'tp1', 'code': 'GD-TP', 'centre_x': 0.0, 't_comp': 0.032},
            ],
            'associations': [
                {'type': 'Connection', 'connection': 'F', 'from': {'component': 'con1', 'feature': 'pipeEnd'}, 'to': {'component': 'st1', 'feature': 'slot3'}},
                {'type': 'Connection', 'connection': 'F', 'from': {'component': 'con1', 'feature': 'pipeEnd'}, 'to': {'component': 'tp1', 'feature': 'conMid'}},
            ],
        }
        ils = build_ils(spec)
        fig = ils.plot()
        labels = getattr(fig, '_connection_labels', [])
        self.assertGreaterEqual(len(labels), 1)
        self.assertTrue(any('F' == item['text'] for item in labels))


    def test_branch_valve_and_connections_use_review_symbols(self):
        spec = {
            'schema_version': 1,
            'ils': {'connection_system': 'PS'},
            'pipeline': {'OD_pipe': 0.4064, 't_pipe': 0.021},
            'components': [
                {'id': 'B', 'code': 'GD-B', 'centre_x': 0.0, 'variant': 'Z',
                 'support_connector': 'S', 'P_b1': 4.064, 'P_b2': 1.4224,
                 'P_b3': 0.7112, 'P_bc': 0.2032, 'P_bv': 2.032,
                 'OD_branch': 0.2032, 't_branch': 0.0127},
                {'id': 'ST', 'code': 'GD-ST', 'centre_x': 2.032, 'L_top': 5.6896,
                 'H_top': 1.016, 'P_vt': -0.4064, 'P_c1': 3.6576,
                 'P_c2': 0.4064, 'top_connector_x': [4.064]},
            ],
            'associations': [
                {'type': 'Connection', 'connection': 'S',
                 'from': {'component': 'B', 'feature': 'end'},
                 'to': {'component': 'ST', 'feature': 'top1'}},
            ],
            'plot_annotations': [
                {'id': 'probable_peak_strain_location', 'kind': 'strain_watch',
                 'text': 'Probable high strain location',
                 'anchor': {'component': 'B', 'feature': 'tee'}},
            ],
        }
        ils = build_ils(spec)
        fig = ils.plot()
        texts = [text.get_text() for ax in fig.axes for text in ax.texts]
        self.assertIn('GD-VLV', texts)
        self.assertIn('Probable high strain location', texts)
        self.assertNotIn('3.0 t', texts)
        labels = getattr(fig, '_connection_labels', [])
        self.assertTrue(any(item['text'] == 'S' for item in labels))
        geometry_ax = fig.axes[0]
        markers = [line.get_marker() for line in geometry_ax.lines]
        self.assertNotIn('*', markers)
        self.assertNotIn('X', markers)

    def test_model_and_anchor_coordinates_preserved(self):
        spec={'schema_version':1,'pipeline':{'OD_pipe':0.4064,'t_pipe':0.021},
              'components':[{'code':'GD-TP','centre_x':0}]}
        ils=build_ils(spec)
        before=copy.deepcopy(ils.components[0].geometry_nodes())
        definition=copy.deepcopy(ils.definition)
        fig=ils.plot_component(0)
        correct_layout(fig)
        self.assertEqual(ils.components[0].geometry_nodes(),before)
        self.assertEqual(ils.definition,definition)


if __name__ == '__main__':
    unittest.main()

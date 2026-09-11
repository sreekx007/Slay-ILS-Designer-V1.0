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

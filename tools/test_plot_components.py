"""Phase 6: Boss constraints and every registered EDES component."""
import copy
import json
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'plotters'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ils_builder import build_ils, CLS, weld_chain
import component_spec as cs


class ComponentCoverageTests(unittest.TestCase):
    def tearDown(self):
        plt.close('all')

    def definition(self, entries):
        return {'schema_version':1,'ils':{'ownership':'lowest'},
                'pipeline':{'OD_pipe':0.4064,'t_pipe':0.021},'components':entries}

    def test_every_edes_component_builds_and_renders(self):
        files=Path(__file__).resolve().parents[1]/'knowledge/edes'
        expected={p.stem[len('EDES_'):-len('_KNOWLEDGE')] for p in files.glob('EDES_GD-*_KNOWLEDGE.json')}
        self.assertEqual(set(CLS),expected)
        for code in sorted(CLS):
            with self.subTest(code=code):
                entry={'id':'part','code':code,'centre_x':0}
                if code in ('GD-HdPipe','GD-BrPipe'):
                    entry['L_pipe']=1.0
                if code=='GD-PIP':
                    entry['x_interior_R']=0.1
                    entry['t_outer']=0.015
                if code=='GD-BOSS':
                    entry.update(OD_boss=0.6,t_boss=0.025)
                entries=[entry]
                if code=='GD-Con':
                    entries.append({'id':'host','code':'GD-TP','centre_x':0,'t_comp':0.021})
                ils=build_ils(self.definition(entries))
                self.assertFalse([f for f in ils.findings if f.severity=='error'],ils.findings)
                for fig in [ils.plot_component(0),ils.plot()]:
                    fig.canvas.draw()
                    self.assertTrue(fig.axes[0].lines or fig.axes[0].collections)
                    plt.close(fig)

    def test_boss_preserves_header_and_adds_mass(self):
        host={'id':'host','code':'GD-TP','centre_x':0,'L_comp':2,'t_comp':0.042}
        boss={'id':'boss','code':'GD-BOSS','centre_x':0.1,'OD_boss':0.6,'t_boss':0.025,'L_boss':1.5}
        original=build_ils(self.definition([host]))
        with_boss=build_ils(self.definition([host,boss]))
        b=with_boss.components[1]
        self.assertIsNone(b.section_at(0))
        self.assertEqual(original.assembly.section_at(0),with_boss.assembly.section_at(0))
        self.assertAlmostEqual(with_boss.mass-original.mass,b.steel_mass,places=3)
        self.assertAlmostEqual(with_boss.cog[0]*with_boss.mass,b.steel_mass*0.1,places=3)
        self.assertEqual(weld_chain(with_boss),[])
        self.assertEqual(with_boss.feature_xy('boss','conMid'),(0.1,0.0))
        self.assertNotIn('weldL',with_boss.features_of('boss'))
        self.assertGreater(b.ID_boss,original.assembly.section_at(0).OD)

    def test_clearance_checks_actual_short_thick_section(self):
        entries=[{'code':'GD-TP','centre_x':0.123,'L_comp':0.001,'t_comp':0.09},
                 {'code':'GD-BOSS','centre_x':0,'L_boss':2,'OD_boss':0.6,'t_boss':0.04}]
        ils=build_ils(self.definition(entries))
        self.assertTrue(any(f.severity=='error' and 'bore' in f.message for f in ils.findings))

    def test_invalid_dimensions(self):
        for kw in [dict(OD_boss=0.4,t_boss=0.02),dict(OD_boss=0.6,t_boss=-0.02),
                   dict(OD_boss=0.6,t_boss=0.02,L_boss=0),dict(OD_boss=math.nan,t_boss=0.02)]:
            with self.subTest(kw=kw),self.assertRaises(cs.GeometryRuleError):
                cs.Boss(cs.STD_PIPELINE,**kw)

    def test_source_reference_order_and_roundtrip(self):
        spec=self.definition([{'id':'boss','code':'GD-BOSS','centre_x':3,'source_pip':'pip'},
                              {'id':'pip','code':'GD-PIP','centre_x':0,'x_interior_R':0.1,'t_outer':0.015}])
        before=copy.deepcopy(spec)
        ils=build_ils(spec)
        b,p=ils.components
        self.assertEqual(b.OD_boss,p.OD_outer)
        self.assertEqual(b.t_boss,p.t_outer)
        self.assertEqual(b.L_boss,3*p.OD_outer)
        self.assertEqual(spec,before)
        self.assertNotIn('OD_boss',json.loads(ils.to_json())['components'][0])
        spec['components'][0]['OD_boss']=0.7
        with self.assertRaises(Exception):
            build_ils(spec)

    def test_branch_part_is_not_branch_assembly(self):
        pipe=cs.STD_PIPELINE
        part=cs.BranchPipeSegment(pipe,L_pipe=1)
        assembly=cs.BranchPiping(pipe,**cs.BranchPiping.default_for(pipe))
        self.assertEqual(part.code,'GD-BrPipe')
        self.assertEqual(assembly.code,'GD-B')
        self.assertIsNone(part.contact_at(0))
        self.assertGreater(len(assembly.structural_lines()),len(part.structural_lines()))


if __name__=='__main__':
    unittest.main()

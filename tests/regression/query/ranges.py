from stdnet.utils.populate import populate
from stdnet.utils.py2py3 import zip

from examples.models import NumericData
from examples.data import data_generator, DataTest


class NumberGenerator(data_generator):
    
    def generate(self, **kwargs):
        self.d1 = populate('integer', self.size, start=-5, end=5)
        self.d2 = populate('float', self.size, start=-10, end=10)
        self.d3 = populate('float', self.size, start=-10, end=10)
        self.d4 = populate('float', self.size, start=-10, end=10)


class TestNumericRange(DataTest):
    data_cls = NumberGenerator
    models = (NumericData,)
    
    def setUp(self):
        session = self.session()
        d = self.data
        with session.begin() as t:
            for a, b, c, d in zip(d.d1, d.d2, d.d3, d.d4):
                t.add(self.model(pv=a, vega=b, delta=c, gamma=d))
                
    def testGT(self):
        session = self.session()
        qs = session.query(NumericData).filter(pv__gt=1)
        self.assertTrue(qs)
        for v in qs:
            self.assertTrue(v.pv > 1)
        qs = session.query(NumericData).filter(pv__gt=-2)
        self.assertTrue(qs)
        for v in qs:
            self.assertTrue(v.pv > -2)
    
    def testGE(self):
        session = self.session()
        qs = session.query(NumericData).filter(pv__ge=-2)
        self.assertTrue(qs)
        for v in qs:
            self.assertTrue(v.pv >= -2)
        qs = session.query(NumericData).filter(pv__ge=0)
        self.assertTrue(qs)
        for v in qs:
            self.assertTrue(v.pv >= 0)
            
    def testLT(self):
        session = self.session()
        qs = session.query(NumericData).filter(pv__lt=2)
        self.assertTrue(qs)
        for v in qs:
            self.assertTrue(v.pv < 2)
        qs = session.query(NumericData).filter(pv__lt=-1)
        self.assertTrue(qs)
        for v in qs:
            self.assertTrue(v.pv < -1)
            
    def testLE(self):
        session = self.session()
        qs = session.query(NumericData).filter(pv__le=1)
        self.assertTrue(qs)
        for v in qs:
            self.assertTrue(v.pv <= 1)
        qs = session.query(NumericData).filter(pv__le=-1)
        self.assertTrue(qs)
        for v in qs:
            self.assertTrue(v.pv <= -1)
            
    def testMix(self):
        session = self.session()
        qs = session.query(NumericData).filter(pv__gt=1, pv__lt=0)
        self.assertFalse(qs)
        qs = session.query(NumericData).filter(pv__ge=-2, pv__lt=3)
        self.assertTrue(qs)
        for v in qs:
            self.assertTrue(v.pv < 3)
            self.assertTrue(v.pv >= -2)
        
            
    
from truthiness.truthtable import TruthTable, Variable, BoolDomain, EQ, IntDomain
from truthiness.truthtable import GT, LT, GTE, LTE, EQ, NE, RangeCondition, sortConditions

from twisted.trial.unittest import TestCase


class TruthTests(TestCase):
    def test_evaluate(self):
        tt = TruthTable(a=BoolDomain(), b=BoolDomain())
        tt.addCondition({'a': EQ(True), 'b': EQ(True)}, 'woo')
        self.assertEquals(tt.evaluate({'a': True, 'b': True}), 'woo')

    def test_intGapsGT(self):
        tt = TruthTable(a=IntDomain())
        tt.addCondition({'a': GT(5)}, 'woo')
        gaps = tt.findGaps()
        self.assertEquals(gaps, [{'a': [LTE(5)]}])

    def test_intGapsGTE(self):
        tt = TruthTable(a=IntDomain())
        tt.addCondition({'a': GTE(5)}, 'woo')
        gaps = tt.findGaps()
        self.assertEquals(gaps, [{'a': [LT(5)]}])

    def test_intGapsLT(self):
        tt = TruthTable(a=IntDomain())
        tt.addCondition({'a': LT(5)}, 'woo')
        gaps = tt.findGaps()
        self.assertEquals(gaps, [{'a': [GTE(5)]}])

    def test_intGapsLTE(self):
        tt = TruthTable(a=IntDomain())
        tt.addCondition({'a': LTE(5)}, 'woo')
        gaps = tt.findGaps()
        self.assertEquals(gaps, [{'a': [GT(5)]}])

    def test_intGapsMiddle(self):
        tt = TruthTable(a=IntDomain())
        tt.addCondition({'a': LT(0)}, 'woo')
        tt.addCondition({'a': GT(10)}, 'woobar')
        self.assertEquals(tt.findGaps(), [{'a': [RangeCondition(0, 10)]}])
        
    def test_intGapsRange(self):
        tt = TruthTable(a=IntDomain())
        tt.addCondition({'a': RangeCondition(0, 10)}, 'woo')
        self.assertEquals(tt.findGaps(), [{'a': [LT(0), GT(10)]}])

    def test_intGapsEQ(self):
        tt = TruthTable(a=IntDomain())
        tt.addCondition({'a': EQ(0)}, 'woo')
        self.assertEquals(tt.findGaps(), [{'a': [LT(0), GT(0)]}])

    def test_intGapsNEQ(self):
        tt = TruthTable(a=IntDomain())
        tt.addCondition({'a': NE(0)}, 'woo')
        self.assertEquals(tt.findGaps(), [{'a': [EQ(0)]}])

    def test_generateEQInnerGap(self):
        tt = TruthTable(a=IntDomain())
        tt.addCondition({'a': LT(0)}, 'woo')
        tt.addCondition({'a': GT(0)}, 'woobar')
        self.assertEquals(tt.findGaps(), [{'a': [EQ(0)]}])

    def test_sortConditions(self):
        conditions = [EQ(5), GT(7), LT(3)]
        self.assertEquals(sortConditions(conditions),
                          [conditions[2], conditions[0], conditions[1]])

    def test_sortConditionsIncomplete(self):
        conditions = [EQ(5), LT(3)]
        self.assertEquals(sortConditions(conditions), [conditions[1], conditions[0]])

    def test_conditionEquality(self):
        self.assertEquals(LT(5), LT(5))
        self.assertNotEquals(LT(3), LT(5))
        self.assertEquals([LT(5)], [LT(5)])
        self.assertEquals(set([LT(5)]), set([LT(5)]))

        self.assertEquals(RangeCondition(5, 8), RangeCondition(5, 8))
        self.assertNotEquals(RangeCondition(5, 8), RangeCondition(6, 8))
        self.assertEquals([RangeCondition(5, 8)], [RangeCondition(5, 8)])
        self.assertEquals(set([RangeCondition(5, 8)]), set([RangeCondition(5, 8)]))

    def test_highest(self):
        self.assertEquals(LT(5).highest(), 4)
        self.assertEquals(LTE(5).highest(), 5)
        self.assertEquals(EQ(5).highest(), 5)
        self.assertEquals(RangeCondition(3, 5).highest(), 5)
        self.assertEquals(GT(5).highest(), None)
        self.assertEquals(GTE(5).highest(), None)
    
    def test_lowest(self):
        self.assertEquals(LT(5).lowest(), None)
        self.assertEquals(LTE(5).lowest(), None)
        self.assertEquals(EQ(5).lowest(), 5)
        self.assertEquals(RangeCondition(3, 5).lowest(), 3)
        self.assertEquals(GT(5).lowest(), 6)
        self.assertEquals(GTE(5).lowest(), 5)

    def test_boolGaps(self):
        tt = TruthTable(a=BoolDomain())
        tt.addCondition({'a': EQ(False)}, 'woo')
        self.assertEquals(tt.findGaps(), [{'a': [EQ(True)]}])

    def test_multiColumnGaps(self):
        tt = TruthTable(a=BoolDomain(), b=BoolDomain())
        tt.addCondition({'a': EQ(True), 'b': EQ(True)}, 'woo')
        self.assertEquals(tt.findGaps(), [{'a': EQ(True), 'b': EQ(False)},
                                          {'a': EQ(False), 'b': EQ(True)},
                                          {'a': EQ(False), 'b': EQ(False)}])

# XXX Implement IrrelevantCondition, ignored by the coverage checker.
# XXX Implement FullDomainCondition.

from operator import eq, gt, ge, lt, le, ne


class Domain(object):
    def checkCoverage(self, conditions):
        """
        Return a list of "gaps", or conditions that need to be met in order
        to complete the domain.
        """
        raise NotImplementedError()


class UnsupportedCondition(Exception):
    pass


class EnumDomain(Domain):
    """
    A domain of discrete, explicitly defined elements. It only supports the
    EqualityCondition.
    """

    def __init__(self, values):
        self.values = set(values)

    def checkCoverage(self, args):
        # This check should probably be done at addCondition time.
        for arg in args:
            if not isinstance(arg, EqualityCondition):
                raise UnsupportedCondition(EnumDomain, type(arg))
        other_values = [x.value for x in args]
        return [EqualityCondition(x) for x in self.values - set(other_values)]


class BoolDomain(EnumDomain):
    def __init__(self):
        EnumDomain.__init__(self, [True, False])


def sortConditions(conds):
    real_conds = []
    for cond in conds:
        # Since InequalityCondition covers a disjoint set, it can't be
        # ordered. So replace it with two contiguous sets.
        if isinstance(cond, InequalityCondition):
            real_conds.append(LessThanCondition(cond.value))
            real_conds.append(GreaterThanCondition(cond.value))
        else:
            real_conds.append(cond)

    return sorted(real_conds, key=lambda x: x.sort_key)


class IntDomain(Domain):
    """
    The integer domain. Supports <, <=, =, ranges, >=, and >.
    """
    def checkCoverage(self, args):
        """
        The basic strategy here is
        1. if there is no </<=, then add one.
        2. If there is no >/>=, then add one.
        3. Fill in any gaps in the middle with ranges.
        """
        
        conditions = sortConditions(args)
        gaps = []
        pre_gap = None
        post_gap = None


        # We introspect the condition to determine what the "nice" inverse
        # would be, where "nice" means "referring to the same number". So,
        # the inverse of > X is <= X, instead of < X+1.
        if conditions[0].lowest() != None:
            if isinstance(conditions[0], GreaterThanCondition):
                pre_gap = LessThanOrEqualToCondition(conditions[0].lowest() - 1)
            else:
                pre_gap = LessThanCondition(conditions[0].lowest())

        if conditions[-1].highest() != None:
            if isinstance(conditions[-1], LessThanCondition):
                post_gap = GreaterThanOrEqualToCondition(conditions[-1].highest() + 1)
            else:
                post_gap = GreaterThanCondition(conditions[-1].highest())

        hypothetical_conditions = conditions[:]
        if pre_gap is not None:
            hypothetical_conditions.insert(0, pre_gap)
        if post_gap is not None:
            hypothetical_conditions.append(post_gap)
        highest_covered = hypothetical_conditions[0].highest()
        assert highest_covered != None, hypothetical_conditions[0]

        for condition in hypothetical_conditions[1:]:
            if highest_covered is None:
                break
            if condition.lowest() - 1 != highest_covered:
                if highest_covered + 1 == condition.lowest() - 1:
                    gaps.append(EqualityCondition(highest_covered + 1))
                else:
                    gaps.append(RangeCondition(highest_covered + 1, condition.lowest() - 1))
            highest_covered = condition.highest()

        if pre_gap is not None:
            gaps.insert(0, pre_gap)
        if post_gap is not None:
            gaps.append(post_gap)

        return gaps


class SimpleOperatorCondition(object):
    def __init__(self, value):
        self.value = value
        self.sort_key = value

    def matches(self, other):
        return self.operator(other, self.value)

    def format(self):
        return "%s %r" % (self.formatted_operator, self.value)

    def __eq__(self, other):
        return type(self) == type(other) and self.value == other.value and self.sort_key == other.sort_key

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.value)

    def __hash__(self):
        return hash((type(self), self.value, self.sort_key))


class GreaterThanCondition(SimpleOperatorCondition):
    operator = gt
    formatted_operator = ">"
    def lowest(self):
        return self.value + 1

    def highest(self):
        return None

GT = GreaterThanCondition


class LessThanCondition(SimpleOperatorCondition):
    operator = lt
    formatted_operator = "<"
    def lowest(self):
        return None

    def highest(self):
        return self.value - 1

LT = LessThanCondition


class GreaterThanOrEqualToCondition(SimpleOperatorCondition):
    operator = ge
    formatted_operator = ">="
    def lowest(self):
        return self.value

    def highest(self):
        return None

GTE = GreaterThanOrEqualToCondition


class LessThanOrEqualToCondition(SimpleOperatorCondition):
    operator = le
    formatted_operator = "<="
    def lowest(self):
        return None

    def highest(self):
        return self.value

LTE = LessThanOrEqualToCondition


class RangeCondition(object):
    def __init__(self, min, max):
        assert min <= max, "%r <= %r" % (min, max)
        self.min = min
        self.max = max
        self.sort_key = min

    def lowest(self):
        return self.min

    def highest(self):
        return self.max

    def matches(self, other):
        return other >= self.min and other <= self.max

    def format(self):
        return "%r - %r" % (self.min, self.max)

    def __eq__(self, other):
        return type(self) == type(other) and self.min == other.min and self.max == other.max and self.sort_key == other.sort_key

    def __hash__(self):
        return hash((type(self), self.min, self.max, self.sort_key))

    def __repr__(self):
        return "RangeCondition(%r, %r)" % (self.min, self.max)


class EqualityCondition(SimpleOperatorCondition):
    operator = eq
    formatted_operator = "=="

    def highest(self):
        return self.value

    def lowest(self):
        return self.value

EQ = EqualityCondition


class InequalityCondition(SimpleOperatorCondition):
    operator = ne
    formatted_operator = "!="

    def highest(self):
        return None

    def lowest(self):
        return None

NE = InequalityCondition


class Variable(object):
    def __init__(self, name, domain):
        self.name = name
        self.domain = domain

    def __repr__(self):
        return "Variable(%r, %r)" % (self.name, self.domain)


class Row(object):

   def __init__(self, conditions, result):
       self.conditions = conditions
       self.result = result


class TruthTable(object):
    def __init__(self, **columns):
        self.columns = [Variable(k, v) for k, v in columns.iteritems()]
        self._table = []

    def addCondition(self, values, result):
        assert set(values.keys()) == set([x.name for x in self.columns])
        self._table.append(Row(values, result))

    def evaluate(self, values):
        # Optimize this. Here's an idea.
        # Instead of taking 'values' directly, take a set of functions
        # which can produce inputs, along with a set of 'costs' for those
        # functions. Retrieve the lowest-cost input. Throw out the parts
        # of the table that don't match that input. Find the next-lowest-cost
        # input that's referenced by what remains in the table (as something
        # other than IrrelevantCondition or FullDomainCondition). And so
        # on until a result is found. This will allow avoiding completely
        # some inputs that aren't needed for a particular case.

        # But that's still a pretty naive approach. It ignores cases where
        # given inputs A (cost 0), B (cost 10) and C (cost 100), C is *always*
        # necessary, but B is not. Or does it? I need to trace this out.
        for row in self._table:
            for key in row.conditions.keys():
                if not row.conditions[key].matches(values[key]):
                    break
            else:
                return row.result

    def format(self):
        s = ''
        for column in self.columns:
            s += '%10s |' % (column.name,)
        s += '%10s\n' % ('result',)
        s += '-' * 11 * (len(self.columns) + 1) + '\n'
        for row in self._table:
            for column in self.columns:
                s += '%10s |' % (row.conditions[column.name].format(),)
            s += '%10r\n' % (row.result,)
        return s

    def findGaps(self):
        gaps = []
        for column in self.columns:
            this_column_values = [x.conditions[column.name] for x in self._table]
            this_column_gaps = column.domain.checkCoverage(this_column_values)
            for condition in this_column_values + this_column_gaps:
                combinations = [row.conditions for row in self._table if row.conditions[column.name] == condition]
                for other_column in self.columns:
                    if other_column == column:
                        continue
                    other_column_values = [row[other_column.name] for row in  combinations]
                    print "all values of %s where %s is %s: %s" % (other_column.name, column.name, condition, other_column_values)
                    other_column_gaps = other_column.domain.checkCoverage(other_column_values)
                    print "having gaps", other_column_gaps
#                for other_column in self.columns:
#                    if other_column == column:
#                        continue
#                    other_column_values = [row for row in self._table if row.conditions[column.name] == condition]
#                    pass
                #print "combinations with", column.name, condition, combinations
            gaps.append({column.name: this_column_gaps})
        return gaps


if __name__ == '__main__':
    tt = TruthTable(a=BoolDomain(), c=IntDomain())
    tt.addCondition({'a': EQ(True), 'c': LT(6)}, 'woo')
    tt.addCondition({'a': EQ(False),'c': RangeCondition(6, 10)}, 'werb')
    tt.addCondition({'a': EQ(True), 'c': NE(8)}, 'werby')
    print tt.format()


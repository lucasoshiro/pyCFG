"""
pyCFG - Python context free grammar(CFG) parser library and application

Version : 1.0.0
Author : Hamidreza Mahdavipanah
Repository: http://github.com/mahdavipanah/pyCFG
License : MIT License
"""
import re
from copy import deepcopy, copy


def strings_contain_each_other(first_str, second_str):
    if (type(first_str) is not str
        or type(second_str) is not str):
        raise TypeError("strings_contain_each_other() arguments must be strings")

    first_count = second_str.count(first_str)
    second_count = first_str.count(second_str)

    are_containing = bool(first_count + second_count)

    if not bool(second_count) and are_containing:
        first_str, second_str = second_str, first_str

    return are_containing, first_str, second_str


def string_contains_space(string):
    if type(string) is not str:
        raise TypeError("string_contains_space() argument must be string not {}".format(type(string).__name__))

    for char in string:
        if char.isspace():
            return True

    return False


class RuleNode(object):
    def __init__(self, value=None):
        self.value = value

    def children(self, pattern):
        for i in range(len(self.value)):
            if pattern.fullmatch(self.value[i][0]) and not self.value[i][1]:
                first_value = deepcopy(self.value)
                first_value[i][1] = True
                second_value = deepcopy(self.value)
                del second_value[i]
                return RuleNode(first_value), RuleNode(second_value)


class CFG(object):
    def __init__(self, variables, terminals, rules, start_variable, null_character):
        self.variables = variables
        self.terminals = terminals
        self.start_variable = start_variable
        self.null_character = null_character
        self.accepts_null = None
        self.rules = rules
        self._is_chamsky = None
        self._cnf = None

    @property
    def variables(self):
        return self._variables

    @variables.setter
    def variables(self, new_variables):
        if type(new_variables) is not set:
            raise TypeError("CFG variables must be a set, not '{}'".format(type(new_variables).__name__))

        for variable in new_variables:
            if type(variable) is not str:
                raise TypeError("CFG variables must be strings, not '{}'".format(type(variable).__name__))

        for variable in new_variables:
            if string_contains_space(variable):
                raise ValueError("Variables cannot contain white spaces : '{}'".format(variable))

        new_variables_list = list(new_variables)
        for i in range(len(new_variables_list) - 1):
            for j in range(i + 1, len(new_variables_list)):
                contain_each_other, first_str, second_str = strings_contain_each_other(new_variables_list[i],
                                                                                       new_variables_list[j])
                if contain_each_other:
                    raise ValueError("Variables cannot contain each other, '{}' contains '{}'"
                                     .format(first_str, second_str))

        self._variables = frozenset(new_variables)
        self._is_chamsky = False

    @property
    def terminals(self):
        return self._terminals

    @terminals.setter
    def terminals(self, new_terminals):
        if type(new_terminals) is not set:
            raise TypeError("CFG terminals must be a set, not '{}'".format(type(new_terminals).__name__))

        for terminal in new_terminals:
            if type(terminal) is not str:
                raise TypeError("CFG terminals must be strings, not '{}'".format(type(terminal).__name__))

        for terminal in new_terminals:
            if string_contains_space(terminal):
                raise ValueError("Variables cannot contain white spaces : '{}'".format(terminal))

        new_terminals_list = list(new_terminals)
        for i in range(len(new_terminals_list) - 1):
            for j in range(i + 1, len(new_terminals_list)):
                contain_each_other, first_str, second_str = strings_contain_each_other(new_terminals_list[i],
                                                                                       new_terminals_list[j])
                if contain_each_other:
                    raise ValueError("Terminals cannot contain each other, '{}' contains '{}'"
                                     .format(first_str, second_str))

        self._terminals = frozenset(new_terminals)
        self._is_chamsky = False

    @property
    def rules(self):
        return self._rules

    @rules.setter
    def rules(self, new_rules):
        if type(new_rules) is not set:
            raise TypeError("CFG rules must be a set, not '{}'".format(type(new_rules).__name__))

        for rule in new_rules:
            if type(rule) is not tuple:
                raise TypeError("CFG rules must be 2-tuples, not '{}'".format(type(rule).__name__))
            if len(rule) != 2:
                raise TypeError("CFG rules must be 2-tuples")
            if type(rule[0]) is not str or type(rule[1]) is not str:
                raise TypeError("CFG rules must contain strings")
            if string_contains_space(rule[0]) or string_contains_space(rule[1]):
                raise ValueError("Rule cannot contain white spaces : '{} -> {}'".format(rule[0], rule[1]))

        escaped_vars_and_rules = {re.escape(item) for item in self.variables | self.terminals}

        pattern = re.compile('({})+'.format('|'.join(escaped_vars_and_rules)))

        for rule in new_rules:
            if rule[0] not in self.variables:
                raise ValueError("Unknown Variable '{p0}' in '{p0} -> {p1}'".format(
                    p0=rule[0],
                    p1=rule[1]
                ))
            if not pattern.fullmatch(rule[1]):
                raise ValueError("Rule must contain combination of variables and terminals : {}".format(rule[1]))

        self._rules = frozenset(new_rules)
        self._is_chamsky = False
        if (self.start_variable, self.null_character) in self._rules:
            self.accepts_null = True

    @property
    def start_variable(self):
        return self._start_variable

    @start_variable.setter
    def start_variable(self, new_start_variable):
        if type(new_start_variable) is not str:
            raise TypeError("CFG start variable must be string, not '{}'".format(type(new_start_variable).__name__))

        if new_start_variable not in self.variables:
            raise ValueError("Start variable must be in variables set")

        self._start_variable = new_start_variable
        self._is_chamsky = False

    @property
    def null_character(self):
        return self._null_character

    @null_character.setter
    def null_character(self, new_null_character):
        if type(new_null_character) is not str:
            raise TypeError("CFG null character must be string, not '{}'".format(type(new_null_character).__name__))

        if new_null_character not in self.terminals:
            raise ValueError("Null character must be in terminals set")

        self._null_character = new_null_character
        self._is_chamsky = False

    def remove_null_rules(self):
        nullable_vars = {rule[0] for rule in self.rules if rule[1] == self.null_character}
        while True:
            is_nullable = re.compile('({})+'.format('|'.join(nullable_vars)))
            new_nullable_vars = {rule[0] for rule in self.rules if is_nullable.fullmatch(rule[1])}
            new_set = nullable_vars | new_nullable_vars
            if new_set == nullable_vars:
                break
            nullable_vars = new_set

        if not nullable_vars:
            return

        contains_nullable = re.compile('({})'.format('|'.join(nullable_vars)))

        new_rules = set()

        for rule in self.rules:
            if rule[1] == self.null_character:
                continue
            splits = contains_nullable.split(rule[1])
            if splits[0] != rule[1]:
                splits = [[x, False] for x in splits if x != '']

                def tree_search(node):
                    if not node.value:
                        return
                    children = node.children(contains_nullable)
                    if not children:
                        new_rules.add((rule[0], (''.join((val[0] for val in node.value)))))
                    else:
                        for child in children:
                            tree_search(child)

                tree_search(RuleNode(splits))
            new_rules.add(rule)

        self._rules = frozenset(new_rules)

    def _var_none_unit_rules(self, var):
        is_unit_rule = re.compile('({})'.format('|'.join(self.variables)))
        return {rule[1] for rule in self.rules
                if rule[0] == var and
                not is_unit_rule.fullmatch(rule[1])}

    def _var_unit_rules(self, var):
        return {rule[1] for rule in self.rules if rule[0] == var} - self._var_none_unit_rules(var)

    def remove_unit_rules(self):

        def get_related_unit_rules(var, var_related_unit_rules):
            prev_related_unit_rules = copy(var_related_unit_rules)
            var_unit_rules = self._var_unit_rules(var)
            var_related_unit_rules |= var_unit_rules
            for unit_var in var_unit_rules - prev_related_unit_rules:
                get_related_unit_rules(unit_var, var_related_unit_rules)

        related_unit_rules = dict([(var, set()) for var in self.variables])
        for var in self.variables:
            get_related_unit_rules(var, related_unit_rules[var])
            related_unit_rules[var] -= {var}

        non_unit_rules = {(var, rule) for var in self.variables for rule in self._var_none_unit_rules(var)}

        for var in self.variables:
            for related_var in related_unit_rules[var]:
                non_unit_rules |= {(var, related_var_non_unit_rule) for related_var_non_unit_rule
                                   in self._var_none_unit_rules(related_var)}

        self._rules = frozenset(non_unit_rules)

    def reduct(self):
        # Phase 1
        v1 = set()
        while True:
            v1_union_t = v1 | self.terminals
            pattern = re.compile('({})+'.format('|'.join(v1_union_t)))
            prev_v1 = copy(v1)
            for var in self.variables:
                if {rule for rule in self.rules if rule[0] == var and pattern.fullmatch(rule[1])}:
                    v1.add(var)
            if prev_v1 == v1:
                break
        p1 = {rule for rule in self.rules if pattern.fullmatch(rule[1])}

        is_rule = re.compile('({})'.format('|'.join(v1)))

        # Phase 2
        def get_related_vars(var, related_vars):
            var_related_vars = set()
            for rule in {rule[1] for rule in p1 if rule[0] == var}:
                var_related_vars |= set(is_rule.findall(rule))

            prev_related_vars = copy(related_vars)
            related_vars |= var_related_vars
            for related_var in var_related_vars - prev_related_vars:
                get_related_vars(related_var, related_vars)

        S_related_vars = set()
        get_related_vars(self.start_variable, S_related_vars)
        v1 = S_related_vars
        v1.add(self.start_variable)
        is_related_rule = re.compile('|'.join(v1))
        p1 -= {rule for rule in p1 if not is_related_rule.search(rule[0])}

        terminals_pattern = re.compile('|'.join(self.terminals))
        t1 = {self.null_character}
        for rule in p1:
            t1 |= set(terminals_pattern.findall(rule[1]))

        self._variables = frozenset(v1)
        self._rules = frozenset(p1)
        self._terminals = frozenset(t1)

    def simplify(self):
        self.remove_null_rules()
        self.remove_unit_rules()
        self.reduct()

    @staticmethod
    def _generate_var_names(variables, n, var_name=None):
        def next_var():
            nonlocal var_name
            z_index = -1
            for i in range(len(var_name)):
                if var_name[i] == 'Z':
                    z_index = i
            if z_index == len(var_name) - 1:
                var_name = ['A' for _ in range(z_index + 2)]
            else:
                var_name[z_index] = chr(ord(var_name[z_index]) + 1)
            return var_name

        var_names = []
        if not var_name:
            var_name = ['A']
        while True:
            contain_each_other = False
            var_str = ''.join(var_name)
            for var in variables:
                contain_each_other, _, _ = strings_contain_each_other(var, var_str)
                if contain_each_other:
                    break
            if contain_each_other:
                next_var()
            else:
                var_names.extend([var_str + str(i) for i in range(1, 10)])
                next_var()
                if len(var_names) >= n:
                    break

        return var_names[:n], var_name

    def chamsky(self):
        last_checked_variable = None
        free_variables = []

        def new_var():
            nonlocal free_variables
            nonlocal v1
            nonlocal last_checked_variable

            if len(free_variables) == 0:
                free_variables, last_checked_variable = CFG._generate_var_names(v1, 9, last_checked_variable)

            return free_variables.pop(0)

        # Phase 1
        self.simplify()
        v1 = set(self.variables)
        p1 = set()
        is_terminal = re.compile('|'.join(self.terminals))

        terminal_rules = {}
        for var in self.variables:
            var_rules = [rule[1] for rule in self.rules if rule[0] == var]
            if len(var_rules) == 1:
                if is_terminal.fullmatch(var_rules[0]):
                    terminal_rules[var_rules[0]] = var

        for rule in self.rules:
            if is_terminal.fullmatch(rule[1]):
                p1.add(rule)
            else:
                rule_terminals = is_terminal.findall(rule[1])
                if not rule_terminals:
                    p1.add(rule)
                    continue

                old_rule = rule[1]

                for rule_terminal in rule_terminals:
                    if not terminal_rules.get(rule_terminal, None):
                        new_variable = new_var()
                        terminal_rules[rule_terminal] = new_variable
                        p1.add((new_variable, rule_terminal))
                        v1.add(new_variable)
                    old_rule = old_rule.replace(rule_terminal, terminal_rules[rule_terminal])

                p1.add((rule[0], old_rule))
        # Phase 2
        variables = re.compile('|'.join(v1))
        p2 = set()
        for rule in p1:
            if is_terminal.fullmatch(rule[1]):
                p2.add(rule)
                continue

            rule_variables = variables.findall(rule[1])
            if len(rule_variables) == 2:
                p2.add(rule)
            else:
                new_vars = [new_var() for _ in range(len(rule_variables) - 2)]
                p2.add((rule[0], rule_variables.pop(0) + new_vars[-1]))
                for i in range(len(new_vars) - 2):
                    p2.add((new_vars[i], new_vars.pop(0) + new_vars[i + 1]))
                a = rule_variables.pop()
                b = rule_variables.pop()
                p2.add((new_vars[-1], b + a))
                v1 |= set(new_vars)

        self._variables = frozenset(v1)
        self._rules = frozenset(p2)
        self._is_chamsky = True

    def cyk(self, string):
        string = string.strip()

        if not self._is_chamsky:
            if not self._cnf:
                self._cnf = copy(self)
                self._cnf.chamsky()
            self = self._cnf

        if string == '':
            if self.accepts_null:
                return True
            return False
        if string == self.null_character:
            return False

        V = [[set() for _ in range(len(string))] for _ in range(len(string))]
        for i in range(len(string)):
            V[i][i] = {rule[0] for rule in self.rules if rule[1] == string[i]}

        variables_pattern = re.compile('|'.join(self.variables))

        def Vij(i, j):
            nonlocal V

            for k in range(i, j):
                for rule in self.rules:
                    rule_variables = variables_pattern.findall(rule[1])
                    if len(rule_variables) == 2:
                        if rule_variables[0] in V[i][k] and rule_variables[1] in V[k + 1][j]:
                            V[i][j].add(rule[0])

        for j in range(len(string) - 1):
            for i in range(len(string)):
                if i + 1 + j < len(string):
                    Vij(i, i + 1 + j)

        if self.start_variable in V[0][-1]:
            return True
        return False

    def str_rules(self, *, return_list=False, prepend='', line_splitter='\n'):
        rules_var = {}
        vars = set()
        for rule in self.rules:
            if not rules_var.get(rule[0], None):
                rules_var[rule[0]] = []

            rules_var[rule[0]].append(rule[1])
            if rule[0] != self.start_variable:
                vars.add(rule[0])

        for rules in rules_var.values():
            rules.sort()

        vars = list(vars)
        vars.sort()
        vars.insert(0, self.start_variable)

        if self.accepts_null:
            if not self.null_character in rules_var[self.start_variable]:
                rules_var[self.start_variable].append(self.null_character)

        str_lines = [prepend + '{} -> {}'.format(var, ' | '.join(rules_var[var])) for var in vars]

        if return_list:
            return str_lines

        return line_splitter.join(str_lines)

    def __str__(self):
        print_lines = []
        print_lines.append("Variables (V): {}".format(set(self.variables)))
        print_lines.append("Terminals (Σ): {}".format(set(self.terminals)))
        print_lines.append("Null character: {}".format(self.null_character))
        print_lines.append("Start variable (S): {}".format(self.start_variable))
        print_lines.append("Rules (R):")
        print_lines.extend(self.str_rules(return_list=True, prepend='\t'))

        return "\n".join(print_lines)

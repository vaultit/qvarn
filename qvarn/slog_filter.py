# slog_filter.py - structured logging filtering
#
# Copyright 2017  QvarnLabs Ab
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import re


class FilterRule(object):  # pragma: no cover

    def allow(self, log_obj):
        raise NotImplementedError()


class FilterAllow(FilterRule):

    def allow(self, log_obj):
        return True


class FilterDeny(FilterRule):

    def allow(self, log_obj):
        return False


class FilterHasField(FilterRule):

    def __init__(self, field_name):
        self._field_name = field_name

    def allow(self, log_obj):
        return self._field_name in log_obj


class FilterFieldHasValue(FilterRule):

    def __init__(self, field, value):
        self._field = field
        self._value = value

    def allow(self, log_obj):
        return self._field in log_obj and log_obj[self._field] == self._value


class FilterFieldValueRegexp(FilterRule):

    def __init__(self, field, pattern):
        self._field = field
        self._pattern = pattern

    def allow(self, log_obj):
        if self._field not in log_obj:
            return False
        value = str(log_obj[self._field])
        return re.search(self._pattern, value) is not None


class FilterInclude(FilterRule):

    def __init__(self, rule_dict, rule):
        self._rule = rule
        self._include = rule_dict.get('include', True)

    def allow(self, log_obj):
        allow = self._rule.allow(log_obj)
        return (self._include and allow) or (not self._include and not allow)


class FilterAny(FilterRule):

    def __init__(self, rules):
        self._rules = rules

    def allow(self, log_obj):
        return any(rule.allow(log_obj) for rule in self._rules)


def construct_log_filter(filters):
    if not filters:
        raise NoFilter()
    rules = []
    for spec in filters:
        rule = None
        if 'field' in spec:
            if 'value' in spec:
                rule = FilterFieldHasValue(spec['field'], spec['value'])
            elif 'regexp' in spec:
                rule = FilterFieldValueRegexp(
                    spec['field'], spec['regexp'])
            elif 'field' in spec:
                rule = FilterHasField(spec['field'])
            else:  # pragma: no cover
                rule = FilterAllow()
        if 'include' in spec:
            rule = FilterInclude(spec, rule)
        rules.append(rule)
    return FilterAny(rules)


class NoFilter(Exception):

    def __init__(self):
        super(NoFilter, self).__init__('No log filter specified')

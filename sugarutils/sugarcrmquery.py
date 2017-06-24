#!/usr/bin/env python

import functools

from sugarutils import AbstractListener, ChainInterpreter, GrammarError, SemiSQLGrammar, StateMachine


class ChainSugarCrmQuery(AbstractListener):
    class PreparedStmt(object):
        def __init__(self):
            self.table = ''
            self.stmt = ''
            self.fields = []

        def __str__(self):
            return "<{3}> Table: {0}, Fields: {1}, Statement: {2}".format(self.table, self.fields, self.stmt,
                                                                          self.__class__)

        def __repr__(self):
            return self.__str__()

        def empty(self):
            return not bool(self.table)

    class Translator(object):

        class TranslateTerminated(Exception):
            pass

        @classmethod
        def _prepare_default(cls, stmt, _):
            return stmt

        @classmethod
        def _prepare_select(cls, stmt, frame):
            if frame.args:
                stmt.fields.extend(frame.args[0])
            return stmt

        @classmethod
        def _prepare_from(cls, stmt, frame):
            stmt.table = frame.args[0]
            return stmt

        @classmethod
        def _prepare_where(cls, stmt, _):
            return stmt

        @classmethod
        def _prepare_op(cls, stmt, frame):
            _q = ''

            def esq(arg, isesq=False):
                if isesq:
                    return "'{0}'".format(arg)
                else:
                    return arg

            eq = functools.partial(esq, isesq=frame.kwargs.get('esq', False))
            if frame.ctx == 'in_':
                _q += ' ' + frame.args[0] + ' IN ({0})'.format(','.join(map(eq, frame.args[1])))
            elif frame.ctx == 'gt_':
                _q += ' ' + frame.args[0] + '>' + eq(frame.args[1])
            elif frame.ctx == 'lt_':
                _q += ' ' + frame.args[0] + '<' + eq(frame.args[1])
            elif frame.ctx == 'eq_':
                _q += ' ' + frame.args[0] + '=' + eq(frame.args[1])
            elif frame.ctx == 'neq_':
                _q += ' ' + frame.args[0] + '<>' + eq(frame.args[1])
            elif frame.ctx == 'bw_':
                _q += ' ' + frame.args[0] + ' BETWEEN ' + eq(frame.args[1][0]) + ' AND ' + eq(frame.args[1][1])
            else:
                raise GrammarError('How come, that we are here?!')
            stmt.stmt += _q
            return stmt

        @classmethod
        def _prepare_nterm(cls, stmt, frame):
            _q = ''
            if frame.ctx == 'and_':
                _q += ' ' + 'AND'
            else:
                _q += ' ' + 'OR'
            stmt.stmt += _q
            return stmt

        @classmethod
        def _prepare_term(cls, stmt, frame):
            raise cls.TranslateTerminated

        @classmethod
        def translate(cls, stmt, frame):
            _state_events = {'INIT': cls._prepare_default, 'SELECT': cls._prepare_select, 'FROM': cls._prepare_from,
                             'WHERE': cls._prepare_where, 'OP': cls._prepare_op, 'NON_TERM': cls._prepare_nterm,
                             'TERM': cls._prepare_term}
            return _state_events[frame.cmd](stmt, frame)

    def __init__(self, connection):
        self._machine = StateMachine.machine(SemiSQLGrammar)
        self._machine.add_listener(self)
        self._inter = ChainInterpreter.interpreter(self._machine)
        self._conn = connection
        self._prepared = []
        self._stmt = self.PreparedStmt()

    def handle_event(self, frame):
        try:
            self._stmt = self.Translator.translate(self._stmt, frame)
        except self.Translator.TranslateTerminated:
            self._prepared.append(self._stmt)
            self._stmt = self.PreparedStmt()

    def cursor(self):
        return self._inter

    def close(self):
        self._machine.reset()
        self._prepared = []

    def fetch_all(self):
        if not self._stmt.empty():
            raise GrammarError('Statement not terminated properly')
        for ps in self._prepared:
            ps_data = self._exec(ps)
            yield ps_data

    def fetch(self, set_id):
        return self._exec(self._prepared[set_id])

    def fields(self):
        for ps in self._prepared:
            yield ps.fields

    def recordset_count(self):
        return len(self._prepared)

    def _exec(self, stmt):
        func = 'get_entry_list'
        entries = self._conn.request(func, [self._conn._session, stmt.table, stmt.stmt, '', 0, stmt.fields, '', 1000])
        result = []
        for entry in entries['entry_list']:
            if not stmt.fields:
                flds = []
                for fld in entry['name_value_list']:
                    result.append(entry['name_value_list'][fld]['value'])
                    flds.append(fld)

                for ps in self._prepared:
                    if ps == stmt:
                        ps.fields = flds
            else:
                result.append([entry['name_value_list'][fld]['value'] for fld in stmt.fields])
        return tuple(result)

#!/usr/bin/env python

from functools import wraps


class GrammarError(Exception):
    pass


class SemiSQLGrammar(object):
    __GRAMMAR = {'INIT': ['INIT', 'SELECT', 'TERM'], 'SELECT': ['FROM'], 'FROM': ['WHERE', 'TERM'], 'WHERE': ['OP'],
                 'OP': ['TERM', 'NON_TERM'], 'NON_TERM': ['OP'], 'TERM': []}
    __ALIASES = {'INIT': [], 'SELECT': ['select_'], 'FROM': ['from_'], 'WHERE': ['where_'],
                 'OP': ['in_', 'gt_', 'lt_', 'eq_', 'neq_', 'bw_'], 'NON_TERM': ['and_', 'or_'],
                 'TERM': ['exec_', 'end_']}

    @classmethod
    def init_state(cls):
        return 'INIT'

    @classmethod
    def next_state(cls, state):
        try:
            return cls.__GRAMMAR[state]
        except KeyError:
            raise GrammarError('Unknown state %s' % state)

    @classmethod
    def states(cls):
        return cls.__GRAMMAR.keys()

    @classmethod
    def get_alias(cls, state):
        return cls.__ALIASES.get(state, [])


class StackFrame(object):
    def __init__(self, command, ctx, args, kwargs):
        self._cmd = command
        self._context = ctx
        self._args = args
        self._kwargs = kwargs

    @property
    def cmd(self):
        return self._cmd

    @property
    def args(self):
        return self._args

    @property
    def kwargs(self):
        return self._kwargs

    @property
    def ctx(self):
        return self._context


class AbstractListener(object):
    def handle_event(self, frame):
        pass


class StateMachine(object):
    @staticmethod
    def frame(cmd, ctx, args, kwargs):
        return StackFrame(cmd, ctx, args, kwargs)

    @classmethod
    def machine(cls, grammar):
        return StateMachine(grammar)

    def __init__(self, grammar=None):
        self._grammar = grammar
        self._state = grammar.init_state()
        self._line = 0
        self._listeners = []

    def reset(self):
        self._state = self._grammar.init_state()
        self._line = 0

    def add_listener(self, listener):
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener):
        self._listeners = [l for l in self._listeners if l != listener]

    @property
    def grammar(self):
        return self._grammar

    @property
    def state(self):
        return self._state

    def __line_no(self):
        while True:
            self._line += 1
            yield self._line

    def _notify(self, state, ctx, args, kwargs):
        for l in self._listeners:
            l.handle_event(self.frame(state, ctx, args, kwargs))

    def enter_state(self, entering_state, ctx, args, kwargs):
        states = self._grammar.next_state(self._state)
        if entering_state not in states:
            raise GrammarError("Invalid jump from %s to %s, %s expected" % (self._state, entering_state, states))
        self._state = entering_state
        self._notify(entering_state, ctx, args, kwargs)
        if not self._grammar.next_state(entering_state):
            self._state = self._grammar.init_state()


class AbstractInterpreter(object):
    @classmethod
    def interpreter(cls, machine):
        pass


class ChainInterpreter(AbstractInterpreter):
    @classmethod
    def interpreter(cls, machine):
        return ChainInterpreter(machine)

    def state_method(self, func, entering_state, method):
        @wraps(func)
        def wrapper(*args, **kwargs):
            self._sm.enter_state(entering_state, method, args, kwargs)
            return func(*args, **kwargs)

        return wrapper

    def __init__(self, machine):
        self._sm = machine
        for state in self._sm.grammar.states():
            for method in machine.grammar.get_alias(state):
                def f(*args, **kwargs):
                    return self

                f.__name__ = method
                self.__dict__[method] = self.state_method(f, state, method)


class StackListener(AbstractListener):
    def __init__(self):
        self._stack = []

    def handle_event(self, frame):
        self._stack.append(frame)

    def stack_trace(self):
        for s in self._stack:
            yield s


if __name__ == "__main__":
    machine = StateMachine.machine(SemiSQLGrammar)
    lsnr = StackListener()
    machine.add_listener(lsnr)
    inter = ChainInterpreter.interpreter(machine)

    inter.select_('test').from_('table').where_(delayed=False).in_('user', ['a', 'b'], where=None).exec_(1).select_(
        2).from_(3).exec_()
    for k, frame in enumerate(lsnr.stack_trace()):
        print 'Line:{0} {1} <{2}> with {3}'.format(k, frame.cmd, frame.ctx, frame.args or frame.kwargs)
    print machine.state

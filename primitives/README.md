Primitive collections and classes
==================================

chaininterpret.py
-----------------
Simple pseudo-language to build up chained constructions like:

do().something().in_().some().chain()

Grammar consists of *states* and *aliases*. Each state can be associated with one or more aliases
Example of simple pseudo-sql grammar:
`__GRAMMAR = {'INIT': ['INIT', 'SELECT', 'TERM'],
             'SELECT': ['FROM'],
             'FROM': ['WHERE', 'TERM'],
             'WHERE': ['OP'],
             'OP': ['TERM', 'NON_TERM'],
             'NON_TERM': ['OP'],
             'TERM': []}`
Means, that *INIT* can be followed by *SELECT* that can be followed by *FROM* that can be followed by either
*WHERE* or *TERM* and so on. *TERM* is the final state as it does not provide any further states
Aliases from the other side mean real class methods representing states
`__ALIASES = {'INIT': [],
                 'SELECT': ['select_'],
                 'FROM': ['from_'],
                 'WHERE': ['where_'],
                 'OP': ['in_', 'gt_', 'lt_', 'eq_', 'neq_', 'bw_'],
                 'NON_TERM': ['and_', 'or_'],
                 'TERM': ['exec_', 'end_']}`
In this case *select_* method will represent *SELECT* state, when *OP* state is represented by many methods (aka SQL
IN, >, < , =, !=, BETWEEN

There are also helper clasess for  dialing with interpreter. For example let's create the grammar above and parse
some simple statements.

Creating primitive listener that will just print statements and environment:

    class StackListener(AbstractListener):
             def __init__(self):
             self._stack = []`

             def handle_event(self, frame):
                self._stack.append(frame)

             def stack_trace(self):
                 for s in self._stack:
                   yield s

    if __name__ == "__main__":
      machine = StateMachine.machine(SimpleGrammar)
      lsnr = StackListener()
      machine.add_listener(lsnr)
      inter = ChainInterpreter.interpreter(machine)

     inter.select_('test').from_('table').where_(delayed=False).in_('user', ['a', 'b'], where=None).exec_(1).select_(
         2).from_(3).exec_()
     for k, frame in enumerate(lsnr.stack_trace()):
         print 'Line:{0} {1} <{2}> with {3}'.format(k, frame.cmd, frame.ctx, frame.args or frame.kwargs)
      print machine.state

And here is the result:


Line:0 SELECT <select_> with ('test',)

Line:1 FROM <from_> with ('table',)

Line:2 WHERE <where_> with {'delayed': False}

Line:3 OP <in_> with ('user', ['a', 'b'])

Line:4 TERM <exec_> with (1,)

Line:5 SELECT <select_> with (2,)

Line:6 FROM <from_> with (3,)

Line:7 TERM <exec_> with {}

INIT

Chains can be combined together so more than one statement can be executed at the same line.

observer.py
--------------------
Simple decorator-based observer implementation. Can be applied to any object that needs to be observed and tracked. There are
some difficulties with standard methods like *__get_item__*.
Example:
Let's assume we have simple class to observe:

     class TestClass(object):
        def __init__(self):
            self.test = False

        def test1(self, value=True):
            self.test = value
            print "From test1", value

        def test2(self):
            self.test = False
            print "From test2"

And two observes:

    class TestObserver(BasicObserver):
        def notify(self, sender, *m_args, **m_kwargs):
            print "From Observer1"
            print m_args, m_kwargs
            print sender

    class TestObserver2(BasicObserver):
        def notify(self, sender, *m_args, **m_kwargs):
            print "From Observer2"
            print m_args, m_kwargs
            print sender


Creating dispatcher and both observers:

    c = TestClass()
    disp = Dispatcher()
    o = TestObserver()
    o2 = TestObserver2()

Registering events with dispatcher, now *TestClass* instance will provide information about execution of *test1* and
   *test2* methods.

    disp.register_event(c, 'test1')
    disp.register_event(c, 'test2')

So subscribers can subscribe:

    disp.subscribe(o, c, 'test1')
    disp.subscribe(o2, c, 'test2')
    disp.subscribe(o, c, 'test2')

Some information about subscribers to the particular method:

    disp.get_subscribers(c, 'test2')

Execution of *test1* or *test2* methods will automatically call appropriate subscribers' method
    c.test1(value=False)
    c.test2()

We can also cancel subscription:
    disp.unsubscribe(o, c, 'test1')


    c.test1(value=False)
    c.test2()

Exception will raise when subscribing to a non-registered event

    try:
        for s in disp.get_subscribers(c, 'test2'):
            print s.__class__.__name__
    except EventNotRegistered as e:
        print e

Internal method showing who is monitored:

    print disp._monitored
    disp.unregister_event(c, 'test1')
    print disp._monitored

LazyDict
------------------------
Laxy dict is a simple dictionary calling *__batch_update__* method each time key with empty value is accessed. Can
be used to collect item just in case they are really required.

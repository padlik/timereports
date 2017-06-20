#!/bin/env python

import inspect
from functools import wraps


class BasicObserver(object):
    def notify(self, sender, *m_args, **m_kwargs):
        pass


class EventNotRegistered(Exception):
    pass


class Dispatcher(object):
    """
     Dispatch subscriptions on methods by observers
     Example:
     Monitor method "Method_Name" of class instance "Object_Instance"
     dispatcher.register_event(Object_Instance, Method_Name)
     subscribe Observer on "Method_Name" of class instance "Object_Instance" execution
     dispatcher.subscribe(Observer, Object_Instance, Method_Name)
     execute event
     Object_Instance.Method_Name(args)
     recive notification to notify method of Observer
     unsubscribe
     dispatcher.unsubscribe(Observer, Object_Instance, Method_Name)
     in case if monitoring is no longer required clear event registration
     dispatcher.unregister_event(Object_Instance, Method_Name)
     other functions are for information purpose one
     Please note, that once event is not registered Exception will be raised
     on any attempt to call methods with it.

    """

    def __init__(self):
        self._monitored = {}
        self._mon_obj_info = {}

    @staticmethod
    def _make_hash(instance, func_name):
        return "{}_{}".format(id(instance), func_name)

    def _notify_observers(self, sender, *args, **kwargs):
        o_hash = self._make_hash(sender[0], sender[1])
        for observer in self._monitored[o_hash]:
            observer.notify(sender, *args, **kwargs)

    def _wrap_observer(self, func):

        sender = (func.__self__, func.__name__)

        @wraps(func)
        def wrapper(*args, **kwargs):
            self._notify_observers(sender, *args, **kwargs)
            func(*args, **kwargs)

        return wrapper

    @staticmethod
    def _get_inst_members(instance, method):
        return [(k, v) for k, v in inspect.getmembers(instance) if k == method and inspect.isroutine(v)]

    def register_event(self, instance, method):
        members = self._get_inst_members(instance, method)
        for k, real_method in members:
            m_hash = self._make_hash(instance, method)
            if m_hash not in self._monitored:
                self._monitored[m_hash] = []
                self._mon_obj_info[m_hash] = (instance.__class__.__name__, method, real_method)
                real_method = self._wrap_observer(real_method)
                setattr(instance, method, real_method)

    def unregister_event(self, instance, method):
        m_hash = self._make_hash(instance, method)
        if m_hash in self._mon_obj_info:
            del self._monitored[m_hash]
            setattr(instance, method, self._mon_obj_info[m_hash][2])
            del self._mon_obj_info[m_hash]

    def subscribe(self, observer, instance, method):
        m_hash = self._make_hash(instance, method)
        if m_hash in self._monitored:
            if observer not in self._monitored[m_hash]:
                self._monitored[m_hash].append(observer)
        else:
            raise EventNotRegistered("{}.{} is not registered".format(instance.__class__.__name__, method))

    def unsubscribe(self, observer, instance, method):
        m_hash = self._make_hash(instance, method)
        if m_hash in self._monitored:
            self._monitored[m_hash] = [v for v in self._monitored[m_hash] if v != observer]
        else:
            raise EventNotRegistered("{}.{} is not registered".format(instance.__class__.__name__, method))

    def get_subscription(self, observer):
        subscription = []
        for k, v in self._monitored.iteritems():
            if observer in v:
                subscription.append(self._mon_obj_info[k])
        return subscription

    def get_subscribers(self, instance, method):
        m_hash = self._make_hash(instance, method)
        subscribers = []
        if m_hash in self._monitored:
            subscribers.extend(self._monitored[m_hash])
        else:
            raise EventNotRegistered("{}.{} is not registered".format(instance.__class__.__name__, method))
        return subscribers

from abc import ABCMeta, abstractmethod
import colorama
import six

from .. import LOG as _LOG
from ..entity import *
from ..util import *

LOG = _LOG.getChild('orchestrator.event_callback')
        
@six.add_metaclass(ABCMeta)
class EventCallbackBase(object):
    """
    EC: event->action wrapper
    """
    def __init__(self, event):
        self.event = event
        self.action = None

    @abstractmethod
    def to_jsondict(self):
        pass
    
    def __repr__(self):
        return '<EC %s>' % repr(self.event)

    def __str__(self):
        return repr(self)

    def __hash__(self):
        return hash(repr(self))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __call__(self, orchestrator):
        orchestrator.send_action(self.action)


@six.add_metaclass(ABCMeta)
class _DeferredEventCallback(EventCallbackBase):
    def __init__(self, event):
        self.event = event
        self.action = PassDeferredEventAction.from_event(self.event)        
        
    def to_jsondict(self):
        return {
            'abstract_event' : self.event.option,
            'abstract_action' : self.action.__class__.__name__
        }


class PacketEventCallback(_DeferredEventCallback):    
    def __repr__(self):
        return '<PEC %s(%s)>' % (repr(self.action.__class__.__name__), repr(self.event.option))


class FunctionCallEventCallback(_DeferredEventCallback):    
    def __repr__(self):
        return '<FCEC %s(%s)>' % (repr(self.action.__class__.__name__), repr(self.event.option))



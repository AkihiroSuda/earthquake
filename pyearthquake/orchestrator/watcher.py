from abc import ABCMeta, abstractmethod
import colorama
import copy
import six
import time
import uuid

from .. import LOG as _LOG
from ..entity import *
from ..entity.event import *
from ..entity.action import *
from ..util import *
from .event_callback import *

LOG = _LOG.getChild('orchestrator.watcher')

@six.add_metaclass(ABCMeta)
class WatcherBase(object):
    def __init__(self):
        self.oc = None

    def set_orchestrator(self, oc):
        self.oc = oc

    @abstractmethod
    def handles(self, event):
        pass

    @abstractmethod
    def on_event(self, state, event):
        """
        returns list of EC
        """
        pass

    def on_terminal_state(self, terminal_state):
        pass

    def on_reset(self):
        pass

        
class DefaultWatcher(WatcherBase):
    
    def handles(self, event):
        raise RuntimeError('Do not call handles() for DefaultWatcher.' + 
                           'DefaultWatcher handles the event if no watcher handles it.')

    def on_event(self, state, event):
        if event.deferred:
            LOG.warn('DefaultWatcher passing %s', event)
            action = PassDeferredEventAction.from_event(event)
            self.oc.send_action(action)
        else:
            LOG.warn('DefaultWatcher ignoring %s', event)
        return []



class ProcessWatcher(WatcherBase):

    def __init__(self, process_id):
        super(ProcessWatcher, self).__init__()
        self.process = process_id

    def handles(self, event):
        return event.process == self.process

    def on_event(self, state, event):
        ecs = []
        ## TODO: move the logic to somewhere else
        if isinstance(event, PacketEvent):
            ecs.append(PacketEventCallback(event))
        elif isinstance(event, FunctionCallEvent):
            ecs.append(FunctionCallEventCallback(event))            
        else:
            raise RuntimeError('Unknown event %s' % event)
        return ecs

    def on_reset(self):
        LOG.info('Please restart process %s manually', self.process)

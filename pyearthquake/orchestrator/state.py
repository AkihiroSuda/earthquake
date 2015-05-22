from abc import ABCMeta, abstractmethod
import copy
import six
import time

from .. import LOG as _LOG
from ..entity import *
from ..util import *
from .event_callback import *

LOG = _LOG.getChild('orchestrator.state')
    
@six.add_metaclass(ABCMeta)
class StateBase(object):
    TERMINAL_STATE_STAYING_SECS = 5

    def __init__(self):
        self._event_callback_sequence = []
        self._last_transition_time = 0
        
    def __repr__(self):
        return '<S %s>' % repr(self._event_callback_sequence)

    def __str__(self):
        """
        human-readable representation
        """
        return self.__repr__()

    def is_terminal_state(self):
        now = time.time()
        elapsed = now - self._last_transition_time
        if elapsed > self.TERMINAL_STATE_STAYING_SECS and \
           len(self._event_callback_sequence) > 0:
            LOG.debug('StateBase.is_terminal_state() considers this is a terminal state, as elapsed=%f > %d', elapsed, self.TERMINAL_STATE_STAYING_SECS)
            return True
        return False
        
    def __hash__(self):
        """
        needed for networkx
        """
        return hash((self.__class__, tuple(self._event_callback_sequence)))

    def __eq__(self, other):
        """
        needed for networkx
        """
        return hash(self) == hash(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def make_copy(self):
        try:
            copied = copy.copy(self)
            copied._event_callback_sequence = copy.copy(self._event_callback_sequence)
            return copied
        except Exception as e:
            LOG.error('make_copy() failed for %s', self)
            raise e

    def append_event_callback(self, ec):
        assert isinstance(ec, EventCallbackBase)
        self._event_callback_sequence.append(ec)
        self._last_transition_time = time.time()

    def get_event_callback_sequence(self):
        for ec in self._event_callback_sequence: yield ec

from abc import ABCMeta, abstractmethod
import copy
import six
import time

from .. import LOG as _LOG
from ..entity import *
from ..util import *
from .digestible import *

LOG = _LOG.getChild('orchestrator.detector')
    
@six.add_metaclass(ABCMeta)
class TerminationDetectorBase(object):
    def init_with_orchestrator(self, orchestrator):
        self.oc = orchestrator
        
    @abstractmethod
    def is_terminal_state(self, state):
        pass


class IdleForWhileDetector(TerminationDetectorBase):
    def __init__(self, msecs=5000):
        self.threshold_msecs = msecs
        
    def is_terminal_state(self, state):
        now = time.time()
        elapsed_secs = now - state.last_transition_time
        elapsed_msecs = elapsed_secs * 1000
        if elapsed_msecs > self.threshold_msecs and  len(state.digestible_sequence) > 0:
            LOG.debug('%s detected termination, as elapsed_msecs=%f > %d', self.__class__.__name__, elapsed_msecs, self.threshold_msecs)
            return True
        return False


class InspectionEndDetector(TerminationDetectorBase):
    """
    detect termination when InspectionEndEvent observed
    """
    def is_terminal_state(self, state):
        raise NotImplementedError

from abc import ABCMeta, abstractmethod
import copy
import six
import time

from .. import LOG as _LOG
from ..entity import *
from ..util import *
from .digestible import *

LOG = _LOG.getChild('orchestrator.state')
    
@six.add_metaclass(ABCMeta)
class StateBase(object):
    def __init__(self):
        self.digestible_sequence = []
        self.init_time = time.time()
        self.last_transition_time = 0
        
    def __repr__(self):
        return '<S %s>' % repr(self.digestible_sequence)

    def __str__(self):
        """
        human-readable representation
        """
        return self.__repr__()
        
    def __hash__(self):
        """
        needed for networkx
        """
        return hash((self.__class__, tuple(self.digestible_sequence)))

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
            copied.digestible_sequence = copy.copy(self.digestible_sequence)
            return copied
        except Exception as e:
            LOG.error('make_copy() failed for %s', self)
            raise e

    def append_digestible(self, ec):
        assert isinstance(ec, DigestibleBase)
        self.digestible_sequence.append(ec)
        self.last_transition_time = time.time()


class BasicState(StateBase):
    pass


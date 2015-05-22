## FIXME: remove unused imports
from abc import ABCMeta, abstractmethod
import colorama
import copy
import eventlet
from eventlet.greenthread import sleep
from eventlet.semaphore import Semaphore
from eventlet.timeout import Timeout
from eventlet.queue import *
from greenlet import GreenletExit
import matplotlib.pyplot
import networkx as nx
import six
import time
import random
import uuid

from .. import LOG as _LOG
from ..entity import *
from ..util import *

from .state import *
from .watcher import *
from .event_callback import *

LOG = _LOG.getChild('orchestrator.explorer')

class Graph(object):
    """
    MOVE ME TO LIBEARTHQUAKE.SO
    """
    def __init__(self, initial_state):
        self._g = nx.DiGraph()
        self.visit_node(initial_state)

    def draw(self):
        nx.draw(self._g)
        matplotlib.peclot.show()
        
    def get_leaf_nodes(self):
        return [n for n,d in self._g.out_degree().items() if d==0]

    def _print_nodes(self):
        leaf_nodes = self.get_leaf_nodes()
        LOG.debug('* Nodes (%d): %s', len(self._g.nodes()), [str(x) for x in self._g.nodes()])
        LOG.debug('* Leaf Nodes (%d): %s', len(leaf_nodes), [str(x) for x in leaf_nodes])

    def visit_node(self, state):
        assert isinstance(state, StateBase)
        count = self._g.node[state]['count'] if self._g.has_node(state) else 0
        # LOG.debug('Visit state %s, count=%d->%d', state, count, count+1)
        self._g.add_node(state, count=count+1)
        
    def visit_edge(self, state, next_state, ec):
        assert isinstance(state, StateBase)
        assert isinstance(next_state, StateBase)
        assert isinstance(ec, EventCallbackBase)
        self.visit_node(state)
        self.visit_node(next_state)
        self._g.add_edge(state, next_state, ec=ec)
        # self._print_nodes()


@six.add_metaclass(ABCMeta)
class ExplorerBase(object):
    def __init__(self):
        self.graph = None
        self._event_q = Queue()
        self.oc = None
        self.state = None
        self.initial_state = None
        self.watchers = []
        self.visited_terminal_states = {} #key: state, value: count

    def set_orchestrator(self, oc, initial_state):
        self.oc = oc
        self.initial_state = initial_state
        self.state = self.initial_state.make_copy()
        LOG.debug(colorama.Back.CYAN +
                  'set initial state=%s' +
                  colorama.Style.RESET_ALL, self.state)
        self.graph = Graph(self.state)

    def regist_watcher(self, w):
        ## NOTE: this makes circular references (Orchestrator->Explorer->Watcher->Orchestrator->..)
        w.set_orchestrator(self.oc)
        self.watchers.append(w)

    def send_event(self, event):
        assert isinstance(event, EventBase)
        self._event_q.put(event)
        
    def recv_events(self, timeout_msecs):
        events = []
        timeout = Timeout(timeout_msecs / 1000.0)
        try:
            while True:
                event = self._event_q.get()
                events.append(event)
        except Timeout:
            pass
        except Exception as e:
            raise e
        finally:
            timeout.cancel()
        return events


    def _worker__print_events_and_callbacks(self, ecs, new_events, new_ecs):
        if ecs:
            LOG.debug('Before state %s, the following OLD %d callbacks had been yielded', self.state, len(ecs))
            for ec in ecs: LOG.debug('* %s', ec)
        LOG.debug('In state %s, the following %d events happend', self.state, len(new_events))
        for e in new_events:
            try: LOG.debug('* %f: %s', e.recv_timestamp, e.abstract_msg)
            except Exception: LOG.debug('* %s', e)
        LOG.debug('In state %s, the following NEW %d callbacks were yielded for the above %d events', self.state, len(new_ecs), len(new_events))
        for new_ec in new_ecs: LOG.debug('* %s', new_ec)
            
    def worker(self):
        ecs = []
        while True:
            if self.state.is_terminal_state(): self.state = self.on_terminal_state()
            new_events = self.recv_events(timeout_msecs=self.oc.time_slice)
            if not new_events and not ecs: continue

            new_ecs = []
            for e in new_events:
                e_handled = False
                for w in self.watchers:
                    if w.handles(e): new_ecs.extend(w.on_event(self.state, e)); e_handled = True
                if not e_handled: new_ecs.extend(self.oc.default_watcher.on_event(self.state, e))
            self._worker__print_events_and_callbacks(ecs, new_events, new_ecs)
            ecs.extend(new_ecs)
            if not ecs: LOG.warn('No EC, THIS MIGHT CAUSE FALSE DEADLOCK, state=%s', self.state)

            next_state, ecs = self.do_it(ecs)
            if not ecs: LOG.warn('No EC, THIS MIGHT CAUSE FALSE DEADLOCK, next_state=%s', next_state)

            LOG.debug('transit from %s to %s', self.state, next_state)
            self.state = next_state

    def do_it(self, ecs):
        """
        select a ec from ecs and do it in the state.
        returns: (next_state, other_ecs)
        FIXME: rename me!
        """
        if not ecs: return self.state, []
        chosen_ec = self.choose_ec(ecs)
        assert(any(ec.event.uuid == chosen_ec.event.uuid for ec in ecs))
        ecs.remove(chosen_ec)
        other_ecs = ecs

        if chosen_ec:
            next_state = self.do_transition(chosen_ec)
        else:
            LOG.warn('No EC chosen, THIS MIGHT CAUSE FALSE DEADLOCK, state=%s', self.state)
            next_state = self.state
        
        ## NOTE: as other ecs are also enabled in the NEXT state, we return other ecs here.
        ## the worker will handle other ecs in the next round.
        return next_state, other_ecs

    @abstractmethod
    def choose_ec(self, ecs):
        pass

    def do_transition(self, ec):
        assert isinstance(ec, EventCallbackBase)
        LOG.debug(colorama.Back.CYAN +
                  'Invoking the callback at state=%s, ec=%s' +
                  colorama.Style.RESET_ALL, self.state, ec)
        ec(orchestrator=self.oc)
        next_state = self.state.make_copy()
        next_state.append_event_callback(ec)
        LOG.debug(colorama.Back.CYAN +
                  'State Transition: %s->%s' +
                  colorama.Style.RESET_ALL, self.state, next_state)        

        self.graph.visit_edge(self.state, next_state, ec)
        ## NOTE: worker sets self.state to next_state
        return next_state

    def stat_on_terminal_state(self, past_all_states, past_visit_count, past_visit_count_sum):
        if past_visit_count == 0:
            banner = 'TERMINAL STATE(FRONTIER)'
            new_all_states = past_all_states + 1
        else:
            banner = 'TERMINAL STATE(REVISITED)'
            new_all_states = past_all_states
        LOG.info(colorama.Back.RED + '%s state %s, count=%d->%d, count_sum=%d->%d, all_states=%d->%d' + colorama.Style.RESET_ALL,
                 banner,
                 self.state,
                 past_visit_count, past_visit_count + 1,
                 past_visit_count_sum, past_visit_count_sum + 1,
                 past_all_states, new_all_states)
        
    def on_terminal_state(self):
        assert self.state.is_terminal_state()
        LOG.debug(colorama.Back.RED +
                  '*** REACH TERMINAL STATE (%s) ***' +
                  colorama.Style.RESET_ALL, self.state)

        ## make stat
        all_states = len(self.visited_terminal_states)
        visit_count_sum = sum(self.visited_terminal_states.values())
        if self.state in self.visited_terminal_states:
            visit_count = self.visited_terminal_states[self.state]
        else:
            visit_count = 0
            self.visited_terminal_states[self.state] = 0
        self.stat_on_terminal_state(all_states, visit_count, visit_count_sum)
        self.visited_terminal_states[self.state] += 1

        ## notify termination to watchers
        for w in self.watchers: w.on_terminal_state(self.state)

        ## Reset
        next_state = self.initial_state.make_copy()        
        LOG.debug('Reset to %s', next_state)
        ## notify reset to watchers
        for w in self.watchers: w.on_reset()
        return next_state
        


class RandomExplorer(ExplorerBase):
    def choose_ec(self, ecs):
        assert (ecs)
        r = random.randint(0, len(ecs)-1)
        chosen_ec = ecs[r]
        return chosen_ec


class DumbExplorer(ExplorerBase):        
    def choose_ec(self, ecs):
        assert (ecs)
        return ecs[0]


from networkx.algorithms.traversal.depth_first_search import dfs_tree
class GreedyExplorer(ExplorerBase):
    def get_subtrees(self, ecs):
        d = {}        
        frontier_ecs = list(ecs) # this is a shallow copy
        g = self.graph._g ## FIXME: should not access others' private vars  
        assert self.state in g.edge        
        for next_state in g.edge[self.state]:
            ## NOTE: even if ec==edge_ec, event_uuid can differ. Do NOT return edge_ec.
            edge_ec = g.edge[self.state][next_state]['ec']
            ecs_matched = [ec for ec in ecs if ec == edge_ec]
            if not ecs_matched: continue
            ec = ecs_matched[0]
            frontier_ecs.remove(ec)
            subtree = dfs_tree(g, next_state)
            d[ec] = subtree
        for ec in frontier_ecs:
            d[ec] = None
        return d

    def evaluate_ec_subtree(self, ec, subtree):
        assert(ec) # subtree may be None
        if not subtree: 
            metric = 1.0
        else:
            subtree_nodes = subtree.number_of_nodes()
            metric = 1.0 / subtree_nodes if subtree_nodes > 0 else 1.0
        rand_factor = random.randint(9, 11) / 10.0
        metric *= rand_factor
        return metric
    
    def choose_ec(self, ecs):
        assert (ecs)        
        ec_metrics = {}
        for ec, subtree in self.get_subtrees(ecs).items():
            metric = self.evaluate_ec_subtree(ec, subtree)
            LOG.debug('Evaluated: metric=%f, ec=%s', metric, ec)
            ec_metrics[ec] = metric
        chosen_ec = max(ec_metrics, key=ec_metrics.get)
        return chosen_ec

from abc import ABCMeta, abstractmethod
import colorama
import copy
import ctypes
import eventlet
from eventlet import wsgi
from eventlet.queue import *
from flask import Flask, request, jsonify
import json
import six
import sys
import time
import uuid


from .. import LOG as _LOG
from ..entity import *
from ..entity.entity import *
from ..util import *

from .explorer import *
from .state import *
from .watcher import *

LOG = _LOG.getChild('orchestrator.orchestrator')


@six.add_metaclass(ABCMeta)
class OrchestratorBase(object):
    def __init__(self, config):
        self._init_load_config(config)
        self._init_load_libearthquake()        
        self._init_regist_explorer()
        self._init_regist_watchers()
        
    def _init_load_config(self, config):
        self.listen_port = int(config['globalFlags']['orchestrator']['listenTCPPort'])
        self.time_slice = int(config['globalFlags']['orchestrator']['search']['timeSlice'])
        # search policy is ignored right now (available: Dumb, Random, Greedy)
        self.processes = {}
        for p in config['processes']:
            pid = p['id']
            queue = Queue()
            self.processes[pid] = { 'queue': queue }

        LOG.info('Time Slice: %d', self.time_slice)
        LOG.info('Processes: %s', self.processes)
        self.config = config
        
    def _init_load_libearthquake(self):
        self.libearthquake = ctypes.CDLL('libearthquake.so')
        config_json_str = json.dumps(self.config)
        self.libearthquake.EQInitCtx(config_json_str)

    def _init_regist_explorer(self):
        state = StateBase()
        self.explorer = DumbExplorer()
        LOG.info('Explorer: %s', self.explorer.__class__.__name__)        
        self.explorer.set_orchestrator(self, initial_state=state)

    def _init_regist_watchers(self):
        self.default_watcher = DefaultWatcher()
        for p in self.processes:
            self.regist_watcher(ProcessWatcher(p))
        
    def start(self):
        explorer_worker_handle = eventlet.spawn(self.explorer.worker)
        
        flask_app = Flask(__name__)
        flask_app.debug = True
        self.regist_flask_routes(flask_app)
        server_sock = eventlet.listen(('localhost', self.listen_port))
        wsgi.server(server_sock, flask_app)
        
#        explorer_worker_handle.wait()
        raise RuntimeError('should not reach here!')

    def regist_flask_routes(self, app):
        LOG.debug('registering flask routes')
        @app.route('/')
        def root():
            return 'Hello Earthquake!'
        
        @app.route('/api/v1', methods=['POST'])
        def api_v1_post():
            ## get event
            ev_jsdict = request.get_json(force=True)

            ## check process id (TODO: check dup)
            process_id = ev_jsdict['process']
            assert process_id in self.processes.keys(), 'unknown process %s. check the config.' % (process_id)

            ## send to explorer
            ev = EventBase.dispatch_from_jsondict(ev_jsdict)
            LOG.debug('API ==> event: %s', ev)
            ev.recv_timestamp = time.time()
            self.explorer.send_event(ev)

            ## wait for action
            act = self.processes[process_id]['queue'].get()
            LOG.debug('API <== action: %s', ev)
            act_jsdict = act.to_jsondict()
            return jsonify(act_jsdict)
    
    def send_action(self, act):
        process_id = act.process
        self.processes[process_id]['queue'].put(act)
        
    def regist_watcher(self, w):
        return self.explorer.regist_watcher(w)


class BasicOrchestrator(OrchestratorBase):
    pass


def main():
    assert len(sys.argv) > 1, "arg is required (config path)"
    config_path = sys.argv[1]
    config_file = open(config_path)
    config_str = config_file.read()
    config_file.close()
    config = json.loads(config_str)
    oc = BasicOrchestrator(config)
    oc.start()
    

if __name__ == "__main__":
    main()

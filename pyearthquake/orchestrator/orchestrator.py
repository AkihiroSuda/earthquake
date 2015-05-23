from abc import ABCMeta, abstractmethod
import colorama
import copy
import ctypes
import eventlet
from eventlet import wsgi
from eventlet.queue import *
from flask import Flask, request, Response, jsonify
import json
import six
import subprocess
import sys
import time
import uuid


from .. import LOG as _LOG
from ..entity import *
from ..entity.entity import *
from .digestible import *
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
        self.watchers = []
        self.default_watcher = DefaultWatcher(orchestrator=self)

        
    def start(self):
        explorer_worker_handle = eventlet.spawn(self.explorer.worker)
        flask_app = Flask(__name__)
        flask_app.debug = True
        self.regist_flask_routes(flask_app)
        server_sock = eventlet.listen(('localhost', self.listen_port))
        wsgi.server(server_sock, flask_app)
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
            LOG.debug('API ==> %s', ev_jsdict)            

            ## check process id (TODO: check dup)
            process_id = ev_jsdict['process']
            assert process_id in self.processes.keys(), 'unknown process %s. check the config.' % (process_id)

            ## send event to explorer
            ev = EventBase.dispatch_from_jsondict(ev_jsdict)
            ev.recv_timestamp = time.time()
            self.explorer.send_event(ev)
            return jsonify({})


        @app.route('/api/v1/<process_id>', methods=['GET'])
        def api_v1_get(process_id):
            assert process_id in self.processes.keys(), 'unknown process %s. check the config.' % (process_id)
             
            ## wait for action from explorer
            action = self.processes[process_id]['queue'].get()

            ## return action
            action_jsdict = action.to_jsondict()
            LOG.debug('API <== %s', action_jsdict)
            return jsonify(action_jsdict)
    
    def send_action(self, action):
        """
        explorer calls this
        """
        process_id = action.process
        self.processes[process_id]['queue'].put(action)
        
    def regist_watcher(self, w):
        self.watchers.append(w)

    def execute_command(self, command):
        rc = subprocess.call(command, shell=True)
        return rc

    @abstractmethod
    def call_action(self, action):
        """
        it may be interesting to override this
        """
        pass

    @abstractmethod
    def make_digestible_pair(self, event, action):
        """
        it may be interesting to override this
        """
        pass


class BasicOrchestrator(OrchestratorBase):

    def _init_regist_watchers(self):
        super(BasicOrchestrator, self)._init_regist_watchers()
        # you can override BasicProcessWatchers to add ExecuteCommandActions on events
        for p in self.processes:
            self.regist_watcher(BasicProcessWatcher(orchestrator=self, process_id=p))
    
    def call_action(self, action):
        assert isinstance(action, ActionBase)
        action.call(orchestrator=self)

    def make_digestible_pair(self, event, action):
        digestible = BasicDigestible(event, action)
        return digestible



def main():
    """
    orchestrator loader
    """
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

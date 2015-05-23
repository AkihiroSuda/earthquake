from .entity import ActionBase, action_class
from .. import LOG as _LOG
LOG = _LOG.getChild('entity.action')

@action_class()
class NopAction(ActionBase):
    pass

@action_class()
class PassDeferredEventAction(ActionBase):
    @classmethod
    def from_event(cls, event):
        assert event.deferred
        inst = cls._from_event_uuid(event.uuid)
        inst.process = event.process
        return inst
    
    @classmethod
    def _from_event_uuid(cls, event_uuid):
        inst = cls()
        inst.option = {'event_uuid': event_uuid}        
        return inst

    def digest(self):    
        return (self.__class__.__name__)


@action_class()
class ExecuteCommandOnInspectorAction(ActionBase):
    def __init__(self):
        raise NotImplementedError


@action_class()
class ExecuteCommandOnOrchestratorAction(ActionBase):
    """
    Execute the command on orchestrator, not on inspector.

    This action is recommended for fault injection that kills the inspector.
    
    """
    @classmethod
    def from_command(cls, command):
        inst = cls()
        inst.option = {'command': command}        
        return inst

    def call(self, orchestrator):
        command = self.option['command']
        LOG.debug('%s: execute command"%s"', __name__, command)
        rc = orchestrator.execute_command(command)
        LOG.debug('%s: return command="%s", rc=%d', __name__, command, rc)

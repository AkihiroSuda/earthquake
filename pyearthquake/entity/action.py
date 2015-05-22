from .entity import ActionBase, action_class
from .. import LOG as _LOG
LOG = _LOG.getChild('entity.action')

class _EventActionBase(ActionBase):
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

    
@action_class()
class NopAction(_EventActionBase):
    pass


@action_class()
class PassDeferredEventAction(_EventActionBase):
    pass

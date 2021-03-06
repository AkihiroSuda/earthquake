#!/usr/bin/env python

import os
# TODO: eliminate port specification
TCP_PORT=9999

ZMQ_ADDR=os.getenv('EQ_ETHER_ZMQ_ADDR')

from scapy.all import *
import pyearthquake
from pyearthquake.inspector.ether import *
from pyearthquake.signal.signal import *
from pyearthquake.signal.event import *
from pyearthquake.signal.action import *
import hexdump

LOG = pyearthquake.LOG.getChild(__name__)

class SamplePacket(Packet):
    name = 'SamplePacket'
    longname = 'SamplePacket (tcp-ex)'
    fields_desc=[ StrFixedLenField('type', '[NUL]', 5),
                  StrStopField('msg', '(NULL)', '\r\n') ]
    
    def post_dissect(self, s):
        try:
            m = re.compile('worker=w([0-9]+), *msg=msg([0-9]+)').search(self.msg)
            if m is None or len(self.msg.splitlines()) > 1:
                raise ValueError("bad msg: \"%s\"" % self.msg)
            msg = {'w_no': int(m.group(1), 10),
                   'msg_no': int(m.group(2), 10),
                   'is_res': 'RES' in self.type}
            src_entity = 'server' if msg['is_res'] else 'client-w%d' % msg['w_no']
            dst_entity =  'client-w%d' % msg['w_no'] if msg['is_res'] else 'server'
            self.event = PacketEvent.from_message(src_entity, dst_entity, msg)
        except Exception as e:
            LOG.exception(e)
            
    def mysummary(self):
        """
        human-readable summary
        """
        try:
            msg = self.event.option['message']
            src_entity = self.event.option['src_entity']
            dst_entity = self.event.option['dst_entity']
            return self.sprintf('%s ==> %s SamplePacket w%d,msg%d' % \
                                (src_entity, dst_entity,
                                 msg['w_no'], msg['msg_no']))
        except Exception as e:
            LOG.exception(e)
            return self.sprintf('ERROR')

        
class SampleInspector(EtherInspectorBase):
    def __init__(self):
        super(SampleInspector, self).__init__(zmq_addr=ZMQ_ADDR)
        self.regist_layer_on_tcp(SamplePacket, TCP_PORT)

    def map_packet_to_event(self, pkt):
        """
        return None if this packet is NOT interesting at all.
        """
        if pkt.haslayer(SamplePacket):
            LOG.debug('%s packet: %s', self.__class__.__name__, pkt[SamplePacket].mysummary())            
            event = pkt[SamplePacket].event
            LOG.debug('mapped event=%s', event)
            return event
        else:
            # LOG.debug('%s unknown packet: %s', self.__class__.__name__, pkt.mysummary())
            # hexdump.hexdump(str(pkt))
            return None


if __name__ == '__main__':
    d = SampleInspector()
    d.start()

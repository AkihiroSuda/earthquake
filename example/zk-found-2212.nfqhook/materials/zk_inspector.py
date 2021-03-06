#!/usr/bin/env python
import os

ZMQ_ADDR = os.getenv('EQ_ETHER_ZMQ_ADDR')

import pyearthquake
from pyearthquake.inspector.zookeeper import ZkEtherInspector

LOG = pyearthquake.LOG.getChild(__name__)


class Zk2212Inspector(ZkEtherInspector):

    def __init__(self, zmq_addr):
        super(Zk2212Inspector, self).__init__(zmq_addr, ignore_pings=True)

if __name__ == '__main__':
    d = Zk2212Inspector(zmq_addr=ZMQ_ADDR)
    d.start()

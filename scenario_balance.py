from xaal.lib import Device,Engine,tools,Message,helpers
from xaal.monitor import Monitor,Notification
import platform
from functools import partial
import sys
import os
import logging


ADDR = tools.str_to_uuid('14e05692-d4bf-11eb-8d10-0800272eacd7')

PACKAGE_NAME="xaal.Scenario_balance"
logger = logging.getLogger(PACKAGE_NAME)

def UUID(uuids):
    r = []
    for k in uuids:
        r.append(tools.get_uuid(k))
    return r


BALANCE = UUID(['120193bc-d043-11eb-890d-d6bd5fe18736'])

LED = [tools.str_to_uuid('110193bc-d043-11eb-890d-d6bd5fe18736')]

MONITORING_DEVICES = BALANCE

weight = 0.5

class Devices:
    def __init__(self):
        self.balance = None
        
    @property
    def list(self):
        return [self.balance]
    
    def check(self):
        for k in self.list:
            if k == None: return False
            if len(k.attributes.keys()) == 0: return False
        return True
    
    def used(self,dev):
        for k in self.list:
            if k==dev: return True
        return False

devices = Devices()

def send(targets,action,body=None):
    global device
    device.engine.send_request(device,targets,action,body)              

def filter_msg(msg):
    if msg.source in MONITORING_DEVICES:
        return True
    return False

def on_event(event,dev):
    if event == Notification.new_device:
        if [dev.address] == BALANCE :
            devices.balance = dev
    
    if event == Notification.attribute_change:
        logger.info(dev.attributes)
        if dev == devices.balance:
            if dev.attributes['Weight'] < weight :
                send(LED,'on')
            if dev.attributes['Weight'] > weight :
                send(LED,'off')


def main():
    global mon,device
    device = Device('scenario.basic',ADDR)
    state=device.new_attribute('state')
    state.value = "Init"
    device.info = '%s@%s' % (PACKAGE_NAME,platform.node())
    device.dump()
    engine = Engine()
    engine.add_device(device)
    mon = Monitor(device,filter_func = filter_msg)
    mon.subscribe(on_event)
    engine.run()
    
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Bye bye')

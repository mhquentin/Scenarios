from xaal.lib import Device,Engine,tools,Message,helpers
from xaal.monitor import Monitor,Notification
from datetime import datetime
import sys
import os
import logging
import platform
import locale

locale.setlocale(locale.LC_TIME,'')

import time

from enum import Enum

ADDR = tools.str_to_uuid('14e05693-d4bf-11eb-8d10-0800272eacd7')

os.chdir("/home/user/xaal_svn_branches/0.7/scripts/")

PACKAGE_NAME="xaal.Scenario_soir"
logger = logging.getLogger(PACKAGE_NAME)

def UUID(uuids):
    r = []
    for k in uuids:
        r.append(tools.get_uuid(k))
    return r

#strftime("%H:%M:%S", datetime.now())

BORDSDULIT = UUID(['e7f60ee3-d583-11eb-9cd5-b54f7b90f500'])
EVERYWHERE = UUID(['e7f60ee4-d583-11eb-9cd5-b54f7b90f5000'])
PORTE = UUID(['e7f60ee5-d583-11eb-9cd5-b54f7b90f500'])
CHAMBRE = UUID(['e7f60ee6-d583-11eb-9cd5-b54f7b90f500'])
COULOIR = UUID(['e7f60ee7-d583-11eb-9cd5-b54f7b90f500'])
TOILETTE = UUID(['e7f60ee8-d583-11eb-9cd5-b54f7b90f500'])
LUM_COULOIR = UUID(['93e09006-708e-11e8-956e-00fec8f7138c'])
LUM_CHAMBRE = UUID(['93e09003-708e-11e8-956e-00fec8f7138c'])
VOLET_CHAMBRE = UUID(['93e09050-708e-11e8-956e-00fec8f7138c'])
RADIO_CHAMBRE = UUID(['c36fba66-e35a-11e9-9c14-b827eb756001'])

# ------ RECUPERATION NOTIFICATION ET TRAITEMENT DU SCENARIO ------ #             

def on_devices():
    send(VOLET_CHAMBRE,'up')
    send(LUM_CHAMBRE,'turn_off')
    send(LUM_COULOIR,'turn_off')
    send(RADIO_CHAMBRE,'turn_off')

def off_devices():
    send(VOLET_CHAMBRE,'down')
    send(LUM_CHAMBRE,'turn_on')
    send(LUM_COULOIR,'turn_off')
    send(RADIO_CHAMBRE,'turn_on')

# ------ ENVOI DES MESSAGES SUR LE BUS ------ #        

def send(targets,action,body=None):
    global device
    device.engine.send_request(device,targets,action,body)

# ------ CREATION DEVICE SCENARIO ------ #

def main():
    global mon,device,target,state
    target = False
    device = Device('scenario.basic',ADDR)
    state=device.new_attribute('state')
    state.value = "Init"
    device.info = '%s@%s' % (PACKAGE_NAME,platform.node())
    device.dump()

    def on():
        state.value = True
        print("%s ON" % device)
        os.system('./alexa_remote_control.sh -d "Echo MaD" -e speak:"Le scénario soir est activé"')
        off_devices()

    def off():
        state.value = False
        print("%s OFF" % device)
        os.system('./alexa_remote_control.sh -d "Echo MaD" -e speak:"Le scénario soir est désactivé"')
        on_devices()


    device.add_method('on',on)
    device.add_method('off',off)
    engine = Engine()
    engine.add_device(device)
    engine.run()
    
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Bye bye')

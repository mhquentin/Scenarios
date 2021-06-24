from xaal.lib import Device,Engine,tools,Message,helpers
from xaal.monitor import Monitor,Notification
from datetime import datetime
import time
import sys
import logging
import platform

from enum import Enum

ADDR = tools.str_to_uuid('14e05692-d4bf-11eb-8d10-0800272eacd7')

PACKAGE_NAME="xaal.Scenario"
logger = logging.getLogger(PACKAGE_NAME)

def UUID(uuids):
    r = []
    for k in uuids:
        r.append(tools.get_uuid(k))
    return r

#strftime("%H:%M:%S", datetime.now())

BORDSDULIT = UUID(['7ce24829-d4bb-11eb-8d10-0800272eac00'])
EVERYWHERE = UUID(['7ce2482a-d4bb-11eb-8d10-0800272eac00'])
PORTE = UUID(['7ce2482b-d4bb-11eb-8d10-0800272eac00'])
CHAMBRE = UUID(['7ce2482c-d4bb-11eb-8d10-0800272eac00'])
COULOIR = UUID(['7ce2482d-d4bb-11eb-8d10-0800272eac00'])
TOILETTE = UUID(['7ce2482e-d4bb-11eb-8d10-0800272eac00'])

MQTT = [tools.str_to_uuid('505e1614-ce9d-11eb-9335-080027dd8560')]
MONITORING_DEVICES = BORDSDULIT + EVERYWHERE + PORTE + CHAMBRE + COULOIR + TOILETTE


# ------ PEUT ETRE UTILE PLUS TARD ------ #

class Devices:
    def __init__(self):
        self.bordsdulit = None
        self.everywhere = None
        self.porte = None
        self.chambre = None
        self.toilette = None
        self.couloir = None
        
    @property
    def list(self):
        return [self.bordsdulit,self.everywhere,self.porte,self.chambre,self.toilette,self.couloir]
    
    def check(self):
        for k in self.list:
            if k == None: return False
            if len(k.attributes.keys()) == 0: return False
        return True
    
    def used(self,dev):
        for k in self.list:
            if k==dev: return True
        return False

# ------ INITIALISATION DES VARIABLES ------ #

device = None
previous_state = None
devices = Devices()
#print(strftime("%Y-%m-%d %H:%M:%S", datetime.now()))

# ------ FONCTIONS AFFICHAGE DES DALLES------ # 

def display_init():
    all_up_size(8)
    all_right()
    send(MQTT,'droit',{'topic':'/topic/qos0'})

def all_up_size(size):
    i=0
    while(i<size):
        send(MQTT,'plus',{'topic':'/topic/qos0'})
        i=i+1

def all_down_size(size):
    i=0
    while(i<size):
        send(MQTT,'moins',{'topic':'/topic/qos0'})
        i=i+1

def all_off():
    send(MQTT,'droit',{'topic':'/topic/qos0'})

def all_right():
    send(MQTT,'droite',{'topic':'/topic/qos0'})

def all_left():
    send(MQTT,'gauche',{'topic':'/topic/qos0'})

def up_size(topic,size):
    i=0
    while(i<size):
        send(MQTT,'plus',{'topic':topic})
        i=i+1

def down_size(topic,size):
    i=0
    while(i<size):
        send(MQTT,'moins',{'topic':topic})
        i=i+1

def off(topic):
    send(MQTT,'droit',{'topic':topic})

def right(topic):
    send(MQTT,'droite',{'topic':topic})

def left(topic):
    send(MQTT,'gauche',{'topic':topic})


# ------ RECUPERATION MESSAGE ET TRAITEMENT DU SCENARIO ------ #

def handle_msg(msg):
    global previous_state
    if not msg.is_notify():
        return

    if msg.is_attributes_change():
        # Au bord du lit
        print(type(msg.source))
        print(type(BORDSDULIT))
        print(type(BORDSDULIT[0]))
        if [msg.source] == BORDSDULIT:
            print("IN")
            now = datetime.now()
            time_h = now.strftime("%H")
            today8am = now.replace(hour=8, minute=0, second=0, microsecond=0)

            # Aller
            if (now > today8am and msg.body['Presence']==True and not(previous_state == "porte")):
                all_up_size(8)
                right("esp32_1")
                right("esp32_2")
                left("esp32_3")                            
                previous_state = "bordsdulit"
                return
            
            # Retour
            if (previous_state == "porte" and msg.body['Presence']==True):
                all_off()
                previous_state = "bordsdulit"
                return

        # Dans la porte
        if msg.source == PORTE:

            # Aller
            if (previous_state == "bordsdulit" and msg.body['Presence']==True):
                all_down_size(3)
                previous_state = "porte"
                return

            # Retour
            if (previous_state == "couloir" and msg.body['Presence']==True): ## faut traiter le chevauchement des zones vcouloirs et porte              
                all_down_size(3)
                previous_state = "porte"
                return   

        # Dans le couloir
        if msg.source == COULOIR:
            
            # Aller
            if (previous_state == "porte" and msg.body['Presence']==True):
                all_down_size(2)
                previous_state = "couloir"
                return

            # Retour            
            if (previous_state == "toilette" and msg.body['Presence']==True):
                all_left()
                all_up_size(10)
                left("esp32_1")
                previous_state = "couloir"
                return                  

        # Dans les toilettes
        if msg.source == TOILETTE:
            if (previous_state == "couloir" and msg.body['Presence']==True):
                all_off()
                previous_state = "toilette"
                return                

def on_event(event,dev):
##    print(event)
##    print(dev)
    if event == Notification.new_device:
        global previous_state
        print(dev.address)
        print(BORDSDULIT)
        print(type(dev.address))
        print(type(BORDSDULIT))
        if dev.address == BORDSDULIT : devices.bordsdulit = dev
        if dev.address == PORTE : devices.porte = dev
        if dev.address == COULOIR : devices.couloir = dev
        if dev.address == EVERYWHERE : devices.everywhere = dev
        if dev.address == TOILETTE : devices.toilette = dev
        if dev.address == CHAMBRE : devices.chambre = dev

    if event == Notification.attribute_change:
##        print(dev.attributes)
##        print(dev)
##        print("PORTE : ",devices.porte)
        logger.info(dev.attributes)
        if dev == devices.bordsdulit:
            now = datetime.now()
            time_h = now.strftime("%H")
            today8am = now.replace(hour=8, minute=0, second=0, microsecond=0)

            # Aller
            if (now > today8am and dev.attributes['Presence']==True and not(previous_state == "porte")):
                all_up_size(8)
                right("esp32_1")
                right("esp32_2")
                left("esp32_3")                            
                previous_state = "bordsdulit"
                return
            
            # Retour
            if (previous_state == "porte" and dev.attributes['Presence']==True):
                all_off()
                previous_state = "bordsdulit"
                return

        # Dans la porte
        if dev == devices.porte:

            # Aller
            if (previous_state == "bordsdulit" and dev.attributes['Presence']==True):
                all_down_size(3)
                previous_state = "porte"
                return

            # Retour
            if (previous_state == "couloir" and dev.attributes['Presence']==True): ## faut traiter le chevauchement des zones vcouloirs et porte              
                all_down_size(3)
                previous_state = "porte"
                return   

        # Dans le couloir
        if dev == devices.couloir:
            
            # Aller
            if (previous_state == "porte" and dev.attributes['Presence']==True):
                all_down_size(2)
                previous_state = "couloir"
                return

            # Retour            
            if (previous_state == "toilette" and dev.attributes['Presence']==True):
                all_left()
                all_up_size(10)
                left("esp32_1")
                previous_state = "couloir"
                return                  

        # Dans les toilettes
        if dev == devices.toilette:
            if (previous_state == "couloir" and dev.attributes['Presence']==True):
                all_off()
                previous_state = "toilette"
                return                

# ------ ENVOI DES MESSAGES SUR LE BUS ------ #        

def send(targets,action,body=None):
    global device
    device.engine.send_request(device,targets,action,body)

def filter_msg(msg):
    if msg.source in MONITORING_DEVICES:
        return True
    return False

# ------ CREATION DEVICE SCENARIO ------ #

def main():
    global mon,device
    device = Device('scenario.basic',ADDR)
    state=device.new_attribute('state')
    state.value = "Init"
    device.info = '%s@%s' % (PACKAGE_NAME,platform.node())
    device.dump()

    def on():
        state.value = True
        print("%s ON" % device)

    def off():
        state.value = False
        print("%s OFF" % device)

    device.add_method('on',on)
    device.add_method('off',off)
    engine = Engine()
    engine.add_device(device)
##    engine.add_rx_handler(handle_msg)
    mon = Monitor(device,filter_func = filter_msg)
    mon.subscribe(on_event)
    display_init()
    engine.run()
    
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Bye bye')

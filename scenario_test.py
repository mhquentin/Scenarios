from xaal.lib import Device,Engine,tools,Message,helpers
from xaal.monitor import Monitor,Notification
from datetime import datetime
import time
import sys
import logging
import platform

from enum import Enum

now =datetime.now()

PACKAGE_NAME="xaal.Scenario"
logger = logging.getLogger(PACKAGE_NAME)

#strftime("%H:%M:%S", datetime.now())

BORDSDULIT = 'a62c3184-d262-11eb-ab39-0800272eac00'
EVERYWHERE = 'a62c3185-d262-11eb-ab39-0800272eac00'
PORTE = 'a62c3186-d262-11eb-ab39-0800272eac00'
CHAMBRE = 'a62c3187-d262-11eb-ab39-0800272eac00'
COULOIR = 'a62c3188-d262-11eb-ab39-0800272eac00'
TOILETTE = 'a62c3189-d262-11eb-ab39-0800272eac00'

MQTT = [tools.str_to_uuid('505e1614-ce9d-11eb-9335-080027dd8560')]
MONITORING_DEVICES = [BORDSDULIT,EVERYWHERE,PORTE,CHAMBRE,COULOIR,TOILETTE]


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

def all_left():s
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
        if str(msg.source) == BORDSDULIT:
            time_h =now.strftime("%H")
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
        if str(msg.source) == PORTE:

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
        if str(msg.source) == COULOIR:
            
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
        if str(msg.source) == TOILETTE:
            if (previous_state == "couloir" and msg.body['Presence']==True):
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
    cfg = tools.load_cfg(PACKAGE_NAME)
    if cfg == None:
        print(cfg)
        logger.info('New config file')
        cfg = tools.new_cfg(PACKAGE_NAME)
        cfg.write()
    device = Device('scenario.basic')
    device.address=tools.str_to_uuid(cfg['config']['addr'])
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
    engine.add_rx_handler(handle_msg)
    mon = Monitor(device,filter_func = filter_msg)
    mon.subscribe(handle_msg)
    display_init()
    engine.run()
    
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Bye bye')

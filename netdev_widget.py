

import time

from pytlm import Widget
from pytlm import Container
from pytlm import cm
from pytlm import StatusLabel


class NetworkDevice(Container) :

    def __init__(self, x: int, y: int, width: int, height: int, **kwargs) :

        super().__init__(x, y, width, height, **kwargs)

        self.device        = kwargs.get("device",   "eth0")
        self.interval      = kwargs.get("interval", 1.0)        

        self.normal_fg    = kwargs.get("normal_foreground",  "white")
        self.normal_bg    = kwargs.get("normal_background",  "default")
        self.normal_att   = kwargs.get("normal_attribute",   "default")
        self.normal_color = None
        
        self.last_tick     = 0
        self.last_interval = 0
        self.value         = "none"        
        self.data          = {}

        #
        # DEVICE_NAME :
        #   TX:0123456789  0123456789  0123456789   0123456789   0123456789
        #   RX:0123456789  0123456789  0123456789   0123456789   0123456789
        #
        
        self.label_name = self.add_widget(StatusLabel(0, 0, 10, value="dev_name"))

        self.label_rxb  = self.add_widget(StatusLabel( 0, 1, 10, value="rx_bytes"))
        self.label_rxp  = self.add_widget(StatusLabel(12, 1, 10, value="rx_packets"))        

        self.label_txb  = self.add_widget(StatusLabel( 0, 2, 10, value="tx_bytes"))        
        self.label_txp  = self.add_widget(StatusLabel(12, 2, 10, value="tx_packets"))        

        
    def save_paint(self, win) :

        pass
    
        #if self.normal_color == None :
        #    self.normal_color = cm(self.normal_fg, self.normal_bg, self.normal_att)
        
        #try :
            #win.addstr(self.y, self.x, value, self.normal_color)
        #except :
        #    pass

        
    def handle_tick(self) :
                
        time_now = time.monotonic()
        interval_now = time_now - self.last_tick

        # Update the NIC data 
        if interval_now >= self.interval :            
           self.update_stats(self.device)
           self.last_tick = time_now
           self.last_interval = interval_now
           self.request_repaint()            


    def update_stats(self, name) :
                
        with open("/proc/net/dev", "r") as f :
            lines = f.readlines()
        
        if len(lines) > 2 :
            for line in lines[2:]:
                stats = self.parse_line(line)
                if stats['name'] == self.device :
                    self.data = stats

        self.label_name.set_value(self.data['name'])
        self.label_rxb.set_value(self.data['rx_bytes'])
        self.label_rxp.set_value(self.data['rx_packets'])
        self.label_txb.set_value(self.data['tx_bytes'])
        self.label_txp.set_value(self.data['tx_packets'])        
                    
    def parse_line(self, line:str) :
                
        line = line.strip()
        parts = line.split()
        parts[0] = parts[0].replace(":", "")
    
        keys = ["name",
                "rx_bytes", "rx_packets", "rx_errors", "rx_err_dropped", "rx_err_fifo", "rx_err_frame",
                "rx_compressed", "rx_multicast",

                "tx_bytes", "tx_packets",
                "tx_errors", "tx_err_dropped", "tx_err_fifo", "tx_err_collisions"]

        return dict(zip(keys, parts))


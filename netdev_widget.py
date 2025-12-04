

import time

from pytlm import Widget
from pytlm import Container
from pytlm import cm
from pytlm import StatusLabel

# Inter-| Receive                                                    |  Transmit
# face |  bytes    packets errs drop fifo frame compressed multicast | bytes    packets  errs  drop  fifo  colls  carrier  compressed
#   lo:  358765    3674    0    0    0     0     0         0           358765   3674     0     0     0     0      0        0
# enp0s31f6:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
# wlp1s0: 544546315  897314    0    9    0     0          0         0 65607729  630227    0    0    0     0       0          0



class NetworkDevice(Container) :

    def __init__(self, x: int, y: int, width: int, height: int, **kwargs) :

        super().__init__(x, y, width, height, **kwargs)

        self.device      = kwargs.get("device",   "eth0")
        self.interval    = kwargs.get("interval", 1.0)        

        self.label_fg    = kwargs.get("label_foreground",  "cyan")
        self.label_bg    = kwargs.get("label_background",  "black")
        self.label_att   = kwargs.get("label_attribute",   "normal")
        self.label_color = None
        
        self.last_tick     = 0
        self.last_interval = 0
        self.value         = "none"        
        self.data          = {}

        #    00         10        20        30        40        50        60          
        #    0123456789|123456789|123456789|123456789|123456789|123456789|123456789
        #   +=======================================================================  
        # 0 |HOST / NIC :  
        # 1 |  TX: 000.000 Xb/s  00000 p/s  00000 Errs  00000 Drop  00000 Fifo  
        # 2 |  RX: 000.000 Xb/s  00000 p/s  00000 Errs  00000 Drop  00000 Fifo    
        # 3 |  MC:   00000  p/s  00000 car  00000 Frms  00000 coll
        # 4 |
        # 5 | 
        
        self.host_dev = self.add_widget(StatusLabel( 0, 0, 15))

        self.rx_bps   = self.add_widget(StatusLabel( 6, 1, 7))
        self.tx_bps   = self.add_widget(StatusLabel( 6, 2, 7))
        self.rx_mcs   = self.add_widget(StatusLabel( 6, 3, 7))
        
        self.rx_pps   = self.add_widget(StatusLabel(20, 1, 5))
        self.tx_pps   = self.add_widget(StatusLabel(20, 2, 5))
        self.rx_carr  = self.add_widget(StatusLabel(20, 3, 5))
        
        self.rx_errs  = self.add_widget(StatusLabel(31, 1, 5))
        self.tx_errs  = self.add_widget(StatusLabel(31, 2, 5))
        self.rx_fram  = self.add_widget(StatusLabel(31, 3, 5))
        
        self.rx_drop  = self.add_widget(StatusLabel(43, 1, 5))
        self.tx_drop  = self.add_widget(StatusLabel(43, 2, 5))
        self.tx_coll  = self.add_widget(StatusLabel(43, 3, 5))

        self.rx_fifo  = self.add_widget(StatusLabel(55, 1, 5))
        self.tx_fifo  = self.add_widget(StatusLabel(55, 2, 5))
            
    
    def paint(self, win) :

        if self.label_color == None :
            self.label_color = cm(self.label_fg, self.label_bg, self.label_att)
        
        super().paint(win)

        X = self.x
        Y = self.y
        
        #win.hline(Y, X, "-", self.width)
        #win.hline(Y + self.height, X, "-", self.width)
        #win.vline(Y, X, "|", self.height)
        #win.vline(Y, X + self.width, "|", self.height)
        
        win.addstr(Y + 1, X + 2, "TX:", self.label_color)
        win.addstr(Y + 2, X + 2, "RX:", self.label_color)
        win.addstr(Y + 3, X + 2, "MC:", self.label_color)

        win.addstr(Y + 1, X + 26, "p/s", self.label_color)
        win.addstr(Y + 2, X + 26, "p/s", self.label_color)
        win.addstr(Y + 3, X + 26, "p/s", self.label_color)

        win.addstr(Y + 1, X + 37, "Errs", self.label_color)
        win.addstr(Y + 2, X + 37, "Errs", self.label_color)
        win.addstr(Y + 3, X + 37, "Frms", self.label_color)

        win.addstr(Y + 1, X + 49, "Drop", self.label_color)
        win.addstr(Y + 2, X + 49, "Drop", self.label_color)
        win.addstr(Y + 3, X + 49, "Coll", self.label_color)
        
        win.addstr(Y + 1, X + 61, "Fifo", self.label_color)
        win.addstr(Y + 2, X + 61, "Fifo", self.label_color)
                
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

        self.host_dev.set_value(self.data['name'])
        
        self.rx_bps.set_value(self.data['rx_bytes'])
        self.rx_pps.set_value(self.data['rx_packets'])
        self.rx_errs.set_value(self.data['rx_errors'])
        self.rx_drop.set_value(self.data['rx_dropped'])
        self.rx_fifo.set_value(self.data['rx_fifo'])
        self.rx_fram.set_value(self.data['rx_frame'])        
        self.rx_mcs.set_value(self.data['rx_multicast'])
        
        self.tx_bps.set_value(self.data['tx_bytes'])
        self.tx_pps.set_value(self.data['tx_packets'])
        self.tx_errs.set_value(self.data['tx_errors'])
        self.tx_drop.set_value(self.data['tx_dropped'])
        self.tx_fifo.set_value(self.data['tx_fifo'])        

        
    def parse_line(self, line:str) :
                
        line = line.strip()
        parts = line.split()
        parts[0] = parts[0].replace(":", "")
    
        keys = ["name",
                "rx_bytes",  "rx_packets",    "rx_errors",     "rx_dropped",
                "rx_fifo",   "rx_frame",      "rx_compressed", "rx_multicast",
                "tx_bytes",  "tx_packets",    "tx_errors",     "tx_dropped",
                "tx_fifo",   "tx_collisions", "tx_carrier",    "tx_compressed"]

        return dict(zip(keys, parts))


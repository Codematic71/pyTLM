
import time
import curses
import logging

from pytlm import Widget
from pytlm import Container
from pytlm import cm
from pytlm import StatusLabel

logger = logging.getLogger("NetworkDevice")

class NetworkDevice(Container) :

    def __init__(self, x: int, y: int, width: int, height: int, **kwargs) :

        super().__init__(x, y, width, height, **kwargs)

        self.base_background  = "black"
        self.base_foreground  = "cyan"
        self.base_attribute   = "normal"
        
        self.device      = kwargs.get("device",   "eth0")
        self.interval    = kwargs.get("interval", 1.0)        

        self.label_fg    = kwargs.get("label_foreground",  "cyan")
        self.label_bg    = kwargs.get("label_background",  "black")
        self.label_att   = kwargs.get("label_attribute",   "normal")
        self.label_color = None

        self.last_tick     = 0
        self.last_interval = 0
        self.value         = "none"        

        self.last_data     = {}
        self.data          = {}

        #    00         10        20        30        40        50        60          
        #    0123456789|123456789|123456789|123456789|123456789|123456789|123456789
        #   +=======================================================================  
        # 0 |HOST / NIC :  
        # 1 |  TX: 000.00 Xbps  00000 p/s  00000 Errs  00000 Drop  00000 Fifo  
        # 2 |  RX: 000.00 Xbps  00000 p/s  00000 Errs  00000 Drop  00000 Fifo    
        # 3 |  MC:  00000 Xps   00000 car  00000 Frms  00000 coll
        # 4 |
        # 5 | 

        self.host_dev = self.add_widget(StatusLabel( 1, 0, 15,
                                                     normal_foreground="white",
                                                     normal_background="black"))

        ###############################
 
        self.tx_bps   = self.add_widget(StatusLabel( 7, 1, 11, format=">6.2f",
                                                     normal_background="black",
                                                     normal_foreground="green",
                                                     units_background="black"))

        self.rx_bps   = self.add_widget(StatusLabel( 7, 2, 11, format=">6.2f",
                                                     threshold=90.0,
                                                     comparison=">=",
                                                     fault_background="red",
                                                     fault_foreground="white",
                                                     normal_background="black",
                                                     normal_foreground="green",
                                                     units_background="black"))
                                                     
        self.rx_mcs   = self.add_widget(StatusLabel( 7, 3, 11, format=">6.2f",
                                                     normal_background="black",
                                                     normal_foreground="green",
                                                     units_background="black"))

        ###############################
 
        self.tx_pps   = self.add_widget(StatusLabel(20, 1, 11, format=">6.2f",
                                                    normal_background="black",
                                                    normal_foreground="green",
                                                    units_background="black"))
                                                    
        self.rx_pps   = self.add_widget(StatusLabel(20, 2, 11, format=">6.2f",
                                                    normal_background="black",
                                                    normal_foreground="green",
                                                    units_background="black"))
        ###############################
                
        self.rx_errs  = self.add_widget(StatusLabel(33, 1, 6, format=">6",
                                                    units=" Errs",
                                                    value=0,
                                                    normal_background="black",
                                                    normal_foreground="green",
                                                    units_background="black"))
        
        self.tx_errs  = self.add_widget(StatusLabel(33, 2, 6, format=">6",
                                                    units=" Errs",
                                                    value=0,
                                                    normal_background="black",
                                                    normal_foreground="green",
                                                    units_background="black"))

        self.rx_carr  = self.add_widget(StatusLabel(33, 3, 6, format=">6",
                                                    units=" Carr",
                                                    value=0,
                                                    normal_background="black",
                                                    normal_foreground="green",
                                                    units_background="black"))

        ###############################

        self.rx_drop  = self.add_widget(StatusLabel(46, 1, 5, format=">6",
                                                    units=" Drop",
                                                    value=0,
                                                    normal_background="black",
                                                    normal_foreground="green",
                                                    units_background="black"))
                                                    
        self.tx_drop  = self.add_widget(StatusLabel(46, 2, 5, format=">6",
                                                    units=" Drop",
                                                    value=0,
                                                    normal_background="black",
                                                    normal_foreground="green",
                                                    units_background="black"))

        self.rx_fram  = self.add_widget(StatusLabel(46, 3, 5, format=">6",
                                                    units=" Frms",
                                                    value=0,
                                                    normal_background="black",
                                                    normal_foreground="green",
                                                    units_background="black"))
        
        ###############################
        
        self.rx_fifo  = self.add_widget(StatusLabel(59, 1, 5, format=">6",
                                                    units=" Fifo",
                                                    value=0,
                                                    normal_background="black",
                                                    normal_foreground="green",
                                                    units_background="black"))
        
        self.tx_fifo  = self.add_widget(StatusLabel(59, 2, 5, format=">6",
                                                    units=" Fifo",
                                                    value=0,
                                                    normal_background="black",
                                                    normal_foreground="green",
                                                    units_background="black"))
                                                            
        self.tx_coll  = self.add_widget(StatusLabel(59, 3, 5, format=">6",
                                                    units=" Coll",
                                                    value=0,
                                                    normal_background="black",
                                                    normal_foreground="green",
                                                    units_background="black"))

        
    def paint(self, win) :

        if self.label_color == None :
            self.label_color = cm(self.label_fg, self.label_bg, self.label_att)
        
        X = self.x
        Y = self.y

        super().paint(win)
                
        win.addstr(Y + 1, X + 2, "TX:", self.label_color)
        win.addstr(Y + 2, X + 2, "RX:", self.label_color)
        win.addstr(Y + 3, X + 2, "MC:", self.label_color)

                
    def handle_tick(self) :
                
        time_now = time.monotonic()
        interval_now = time_now - self.last_tick

        # Update the NIC data 
        if interval_now >= self.interval :            
           self.read_stats(self.device)
           self.last_tick = time_now
           self.last_interval = interval_now
           self.request_repaint()


    #
    #  Bandwidth Calculation : 
    #   
    #            (final_bytes - Initial_Bytes) * 8
    #  BW_bps = ------------------------------------
    #              (time_stop - Time_start)
    #
    
    def calc_bw(self, name) -> tuple[float, str]:

        if name in self.last_data :
            
            data_d = (self.data[name] - self.last_data[name])
            time_d = (self.data['time_ms'] - self.last_data['time_ms'])

            bw_bps = (data_d * 8) / time_d

            return self.humanize_number(bw_bps)
                      
        else :
                      
            return 0, ""

    def humanize_number(self, value) -> tuple[float, str] :
                      
        units = [' ','K','M','G','T']
        unit_index = 0

        count = float(value)
                      
        while count >= 1000 and unit_index < len(units) :
            count /= 1000
            unit_index += 1

        return count, units[unit_index] 

    #
    #
    #
    #
    #

    def bw_stat(self, name, units, label) :

        value = 0.0
        scale = ""
        
        value, scale = self.calc_bw(name)
        
        label.set_value(float(value))
        label.set_units(f" {scale}{units}")

        
    def read_stats(self, name) :
                
        with open("/proc/net/dev", "r") as f :
            lines = f.readlines()
        
        if len(lines) > 2 :
            for line in lines[2:]:
                stats = self.parse_line(line)
                if stats['name'] == self.device :
                    self.last_data = self.data
                    self.data = stats
                    self.update_stats()
                    

    def update_stats(self) :

        logger.info(f"Stats : {self.data}")
        
        self.host_dev.set_value(self.data['name'])        

        self.bw_stat('tx_bytes',     "bps", self.tx_bps)        
        self.bw_stat('rx_bytes',     "bps", self.rx_bps)        
        self.bw_stat('rx_multicast', "bps", self.rx_mcs)
        
        self.bw_stat('tx_packets', "pps", self.tx_pps)               
        self.bw_stat('rx_packets', "pps", self.rx_pps) 
        
        #self.rx_bps.set_value(self.calc_bw('rx_bytes'))
        #self.rx_pps.set_value(self.data['rx_packets'])
        self.rx_errs.set_value(self.data['rx_errors'])
        self.rx_drop.set_value(self.data['rx_dropped'])
        self.rx_fifo.set_value(self.data['rx_fifo'])
        self.rx_fram.set_value(self.data['rx_frame'])        
        
        #self.tx_bps.set_value(self.data['tx_bytes'])
        #self.tx_pps.set_value(self.data['tx_packets'])
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

        # Ensure data is integers and not strings.
        
        for s in range(1, len(keys)) :
            parts[s] = int(parts[s])
        
        # combine the data.
        
        result = dict(zip(keys, parts))
        result['time_ms'] = time.time()
            
        return result


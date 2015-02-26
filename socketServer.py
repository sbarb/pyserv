import logging
import sys
import SocketServer
from collections import OrderedDict
import errno
import os

logging.basicConfig(level=logging.DEBUG,
                    format='%(name)s: %(message)s',
                    )
   
############################################
# Pi helper functions
# mapping of physical pin (and human readable name) to the internal GPIO pin numbering
# ie: {name: data}
_unordered_pins = {
  'pin1': { 'pin': 7, 'name' : 'Lamp', 'state': False, 'weight': 1 },
  'pin2': { 'pin': 11, 'name' : 'LED 1', 'state': False, 'weight': 2 },
  'pin3': { 'pin': 13, 'name' : 'LED 2', 'state': False, 'weight': 3 },
  'pin4': { 'pin': 15, 'name' : 'LED 3', 'state': False, 'weight': 4 },
  'pin5': { 'pin': 12, 'name' : 'LED 4', 'state': False, 'weight': 5 },
  'pin6': { 'pin': 16, 'name' : 'LED 5', 'state': False, 'weight': 6 },
  'pin7': { 'pin': 18, 'name' : 'LED 6', 'state': False, 'weight': 7 },
  'pin8': { 'pin': 22, 'name' : 'LED 7', 'state': False, 'weight': 8 },
  'pin9': { 'pin': 24, 'name' : 'LED 8', 'state': False, 'weight': 9 },
  'pin10': { 'pin': 26, 'name' : 'LED 9', 'state': False, 'weight': 10 },
  'pin11': { 'pin': 19, 'name' : 'LED 10', 'state': False, 'weight': 11 }
}
# guarantees order during iteration based on the weight key
pins = OrderedDict(sorted(_unordered_pins.items(), key=lambda t: t[1]['weight']))
# determins if the host is a RPi or not
def notAPi(body):
    print "This is not a running on a pi. Skipping a pi feature: " + body

def makeDebugString(pin_tuple):
    return "/ "+ pin_tuple[0] +" = " + pin_tuple[1]
# converts string '1' or '0' to bool True or False
def toBoolean(boolStr):
    if str(boolStr) == "1":
        return True
    elif str(boolStr) == "0":
        return False
    else: # Any input that is not '1' or '0' will return None
        return None
# Tell 'pinName' to be in state 'state'
def writePin(pinName, state):
    if state is None:
        print "Not doing anything. Someone requesting something absurd."
        return
    global pins
    # updates global state
    pins[pinName]['state'] = state
    if not isPi:
        notAPi("Write " + str(state) + " on pin "+pinName+" #" + str(pins[pinName]['pin']))
        return
    GPIO.output(pins[pinName]['pin'], state)
# Write High for 'pinName'
def writeHigh(pinName):
    writePin(pinName, True)
# Write Low for 'pinName'
def writeLow(pinName):
    writePin(pinName, False)
# Write 'state' for ALL pins
def writeAll(state):
    for name, data in pins.iteritems():
        # if data['state'] != state:
        writePin(name, state)
# Cut off and cleanup (remove) all gpio pins 
def cleanUp():
    global pins
    # turn off all the pins
    writeAll(False)
    GPIO.cleanup() # cleanup all gpio 
# If this host is a RPi this will initialize the gpio pins
# and set start the program with all pins OFF
def initPi():
    if not isPi:
        notAPi("init pi")
        return
    #setup gpio pinout using BOARD numbering
    GPIO.setmode(GPIO.BOARD)
    #ignore warnings
    GPIO.setwarnings(False)
    #setup pin for output
    for name, data in pins.iteritems():
        GPIO.setup(data['pin'], GPIO.OUT)
    writeAll(False)

# Configure if the program is running as a Raspberry pi
# expected value is 0 or 1
#### this is where the environment variable is processed
if 'PI' in os.environ:
    isPi = toBoolean(os.environ['PI'])
else:
    isPi = False

if isPi:
    import RPi.GPIO as GPIO
    initPi()
# End Pi helper functions
############################################
# socket data helper functions
class TCPHandler(SocketServer.StreamRequestHandler):

    def __init__(self, request, client_address, server):
        self.logger = logging.getLogger('TCPHandler')
        self.logger.debug('__init__')
        SocketServer.StreamRequestHandler.__init__(self, request, client_address, server)
        return

    def setup(self):
        self.logger.debug('setup')
        return SocketServer.StreamRequestHandler.setup(self)

    def handle(self):
        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls
        self.data = self.rfile.readline().strip()
        
        pinName = self.data.split(" ")[0]
        state = self.data.split(" ")[1]

        print "{} wrote:".format(self.client_address[0])
        print "Pin Name {}".format(pinName)
        print "State {}".format(state)
        # Likewise, self.wfile is a file-like object used to write back
        # to the client
        self.wfile.write(self.data)
        if pinName in pins:
            print "***IF EXECUTED***"
            writePin(pinName, toBoolean(state))
        elif str(pinName) in ("all", "ALL", "All", "aLL", "alL", "aLl"):
            print "***ELIF (ALL) EXECUTED***"
            writeAll(toBoolean(state))
        else:
            print "*** SOMETHING ISN'T RIGHT ***"
    # def finish(self):
    #     try:
    #         self.logger.debug('finish')
    #         return SocketServer.StreamRequestHandler.finish(self)
    #     except socket.error, v:
    #         errorcode=v[0]
    #         if errorcode == errno.ECONNREFUSED:
    #             print "Connection Refused"
    #         elif errorcode == errno.EPIPE: 
    #             print "Broken Pipe"
# End socket data helper functions
############################################

############################################

# set the socket host and port addresses
socketHost, socketPort = "192.168.1.111", 9999

# Create the server, binding to socketHost on socketPort 
socketServer = SocketServer.TCPServer((HOST, PORT), TCPHandler)
# socketServer = SocketServer.TCPServer(address, TCPHandler)
# Start the program
if __name__ == "__main__":
    global socketServer
    try:
        logger = logging.getLogger('Socket Server')
        logger.info('Socket Server running on %s:%s', socketHost, socketPort)

        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        socketServer.serve_forever()

        # # list of pin name and state as a string ("pin1", "True")
        # pins_info = [(name, str(data['state'])) for name, data in pins.iteritems()]
        # # transform into a list of strings
        # pin_strings = [makeDebugString(pin_obj) for pin_obj in pins_info]
        # # print the strings one line at a time
        # print "\n".join(pin_strings)
        # # raise KeyboardInterrupt  
   
    except KeyboardInterrupt as stop:    
        print "\nClosing Socket."
        # close the socket
        socketServer.socket.close()
        print "\n\n\nServer Run Complete."
    
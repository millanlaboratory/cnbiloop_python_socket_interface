from tobi import pylibtobiic, pylibtobiid, pylibtobicore, pytpstreamer
import atexit
from socket import *

class BciInterface:
    def __init__(self, connect_ip='localhost', id_port_bus=8126, id_port_dev = 8127):
        # Setup TOBI interfaces iC and iD
        # set up IC objects
        #self.ic_msg = pylibtobiic.ICMessage()
        #self.ic_serializer = pylibtobiic.ICSerializer(self.ic_msg, True)

        # set up ID objects
        self.id_msg_bus = pylibtobiid.IDMessage()
        self.id_msg_bus.SetBlockIdx(100)
        self.id_msg_bus.SetDescription("Drone")
        self.id_msg_bus.SetFamilyType(0)
        self.id_msg_dev = pylibtobiid.IDMessage()
        self.id_msg_dev.SetBlockIdx(100)
        self.id_msg_dev.SetDescription("Drone")
        self.id_msg_dev.SetFamilyType(0)

        self.id_serializer_bus = pylibtobiid.IDSerializer(self.id_msg_bus, True)
        self.id_serializer_dev = pylibtobiid.IDSerializer(self.id_msg_dev, True)

        # Bind sockets for iC and iD, hardcoded thanks to the new loop.
        # I could retrieve it from the nameserver in the future
        if connect_ip is 'localhost':
            connect_ip = '127.0.0.1'
        elif connect_ip is 'pk':
            connect_ip = '169.254.123.102'
        print 'BCI interface will connect:', connect_ip
        self.iDIP_bus = connect_ip
        self.iDport_bus = id_port_bus
        self.iDIP_dev = connect_ip
        self.iDport_dev = id_port_dev

        #self.icStreamer = pytpstreamer.TPStreamer()
        self.idStreamer_bus = pytpstreamer.TPStreamer()
        self.idStreamer_dev = pytpstreamer.TPStreamer()
        print "Successfully set streamer..."
        self.iDsock_bus = socket(AF_INET, SOCK_STREAM)
        self.iDsock_bus.connect((self.iDIP_bus, self.iDport_bus))
        self.iDsock_dev = socket(AF_INET, SOCK_STREAM)
        self.iDsock_dev.connect((self.iDIP_dev, self.iDport_dev))
        print 'Successfully set sockets...'

        print 'Protocol is listening for iD event data on ip %s, port %d' % (self.iDIP_bus, self.iDport_bus)
        print 'Protocol is listening for iD command data on ip %s, port %d' % (self.iDIP_dev, self.iDport_dev)
        self.iDsock_bus.setblocking(0)
        self.iDsock_dev.setblocking(0)
        atexit.register(self.iDsock_bus.close) # close socket on program termination, no matter what!
        atexit.register(self.iDsock_dev.close) # close socket on program termination, no matter what!
        print 'BCI interface is successfully set'

    def close(self):
        self.iDsock_bus.close()
        self.iDsock_dev.close()

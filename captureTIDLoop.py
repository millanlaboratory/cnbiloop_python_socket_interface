# initialize BCI interface
import pygame
from BCI import BciInterface
import socket
import time

# variables for setting
videoMode = False

# variables for debug
fakeData = [i for i in range(10)]
idxFakeData = 0
print fakeData[0]

# Arguments
terminateKey = 'c'  # to terminate this loop
ip_protocol = '127.0.0.1'  # '169.254.123.101'
ip_cnbiloop = '192.198.1.1'
port_protocol = 9999
BufferSize = 1024
socket.setdefaulttimeout(1)


def handle_tobiid_input(bci):
    data = None
    try:
        data = bci.iDsock_bus.recv(512)
        data = parseData(data)
        # print "A = ",data
        # bci.idStreamer_dev.Append(data)
    except:
        # bci.nS = False
        # bci.dec = 0
        pass
    return data


def parseData(data):
    try:
        idx1 = data.find('event=\"')
        n = len('event=\"')
        # print 'idx1', idx1
        # print 'substr', data[idx1+n:]
        idx2 = data[idx1+n:].find('\"')
        # print 'idx2', idx2
        # print 'substr2', data[idx1+n:idx1+n+idx2]

        # data must be sent in a string format
        # value = int(data[idx1+n:idx1+n+idx2])
        value = data[idx1 + n:idx1 + n + idx2] + '.' # period (.) is the ending of an event
        # print 'value', value
    except:
        print 'failed to parse data!!!'
        value = -9999
    return value


def waitForConnection(sockHost, terminateKey):
    print 'Waiting for clients...'
    while True:
        try:
            s, addr = sockHost.accept()
        except socket.timeout:
            s = None
            addr = None
        if s is not None:
            print addr, ' is connected.'
            return s, addr, False, time.time()
        for event in pygame.event.get():
            if event.type is pygame.KEYDOWN:
                key = pygame.key.name(event.key)
                print key + " pressed"
                if key == terminateKey:
                    return s, addr, True, time.time()


def createServer(serverAddress):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(serverAddress)
    s.listen(1)
    return s


# initialize pygame for quitting loop
pygame.init()
screen = pygame.display.set_mode((60, 60))
pygame.display.set_caption('Pygame Keyboard Test')

# Host a server
serverAddress = (ip_protocol, port_protocol)
sockHost = createServer(serverAddress)
# Wait for connection
sockClient, clientAddress, flag, establishedTime = waitForConnection(sockHost, terminateKey)
print clientAddress
#sockClient.sendall('99.')
bci = BciInterface(connect_ip=ip_cnbiloop)
nData = 0
while not flag:
    # receive TiD Event
    data = handle_tobiid_input(bci)

    # if data:
    #    print data
    # transmit TiD Event if input buffer is not empty
    if data is not None:
        '''
        # Debug
        data = str(fakeData[idxFakeData])
        data = data + "."
        idxFakeData = idxFakeData + 1
        if idxFakeData >= len(fakeData):
            idxFakeData = 0
        '''
        try:
            nData = nData + 1
            #print data
            curTime = time.time()
            elapsedTime = curTime - establishedTime
            if elapsedTime > 0.0 and not videoMode:
                #print elapsedTime
                print data, nData/elapsedTime

            sockClient.sendall(data)
            '''
            #sockHost.sendall(data)
            #sockHost.sendto(data, (ip_protocol, port_protocol))
            #sockHost.sendto(data, sockHost)
            #sockHost.sendto(data, clientAddress)
            #sockHost.sendto(data, sockClient)
            '''
        except socket.error:
            print 'Failed to send data...reconnecting...'
            bci.close()
            sockClient, clientAddress, flag, establishedTime = waitForConnection(sockHost, terminateKey)
            bci = BciInterface()

            nData = 0
            #sockClient.sendall('99.')
    ''' Not working...
    # detect potential connection lost
    try:
        readyToRead, readyToWrite, inError = \
            select.select([], [sockClient], [], 0.01)
        if readyToWrite is None:
            sockClient, clientAddress = waitForConnection(sockHost)
    except select.error:
        sockClient, clientAddress = waitForConnection(sockHost)
    '''
    # to terminate the infinite loop
    for event in pygame.event.get():
        if event.type is pygame.KEYDOWN:
            key = pygame.key.name(event.key)
            print key + " pressed"
            if key == terminateKey:
                print "Terminating the program"
                flag = True
                break
            else:
                print 'press ' + terminateKey + ' if you want to terminate'
    if flag:
        break
    continue

bci.close()
sockHost.close()
pygame.quit()
print 'socket terminated!'
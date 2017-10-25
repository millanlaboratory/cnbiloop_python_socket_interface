import pygame
from BCI import BciInterface
import socket
import time
import multiprocessing as mp
import atexit

def handle_tobiid_input(bci):
    data = None
    try:
        data = bci.iDsock_bus.recv(512)
        data = parse_data(data)
        # print "A = ",data
        # bci.idStreamer_dev.Append(data)
    except:
        # bci.nS = False
        # bci.dec = 0
        pass
    return data


def parse_data(data):
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


def wait_for_connection(sock_host, terminate_key):
    print 'Waiting for clients...'
    while True:
        try:
            s, addr = sock_host.accept()
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
                if key == terminate_key:
                    return s, addr, True, time.time()


def create_server(server_address):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(server_address)
    s.listen(1)
    return s


class BidirectionalInterface:
    def __init__(self, ip_cnbiloop='192.168.1.1', port_tid_from_cnbiloop=9999,
                 ip_python='192.168.1.1', port_tid_to_cnbiloop=9990,
                 from_cnbiloop=True, to_cnbiloop=True, manual_trigger=False):
        pygame.init()
        screen = pygame.display.set_mode((60, 60))
        pygame.display.set_caption('Pygame Keyboard Test')

        self.finish = False
        self.bci = BciInterface(connect_ip=ip_cnbiloop)
        self.ip_cnbiloop = ip_cnbiloop
        self.ip_python = ip_python
        self.port_tid_to_protocol = port_tid_from_cnbiloop
        self.port_tid_from_protocol = port_tid_to_cnbiloop
        self.to_cnbiloop = to_cnbiloop
        self.from_cnbiloop = from_cnbiloop
        self.terminateKey = 'c'
        self.videoMode = False

        # Host servers
        if self.from_cnbiloop:
            server_address = (ip_python, port_tid_from_cnbiloop)
            self.sockHostToProtocol = create_server(server_address)
        if self.to_cnbiloop:
            server_address = (ip_python, port_tid_to_cnbiloop)
            self.sockHostFromProtocol = create_server(server_address)

        # Wait for connection
        if self.from_cnbiloop:
            self.sockClientToProtocol, self.clientAddress, self.finish, self.established_time = \
                wait_for_connection(self.sockHostToProtocol, self.terminateKey)
            print 'connected to: ', self.clientAddress
        if self.to_cnbiloop:
            self.sockClientFromProtocol, self.clientAddressFromProtocol, self.finish, self.established_time = \
                wait_for_connection(self.sockHostFromProtocol, self.terminateKey)
            print 'connected to: ', self.clientAddressFromProtocol

        self.proc = []
        if to_cnbiloop:
            if manual_trigger:
                self.init_mp_process(self.send_manual_trigger_daemon())
            else:
                self.init_mp_process(self.send_tid_daemon())
        if from_cnbiloop:
            self.init_mp_process(self.receive_tid_daemon())
        atexit.register(self._close())  # close socket on program termination, no matter what!

    def _close(self):
        for i in range(0, len(self.proc)):
            self.proc[i].join()
        self.bci.close()
        if self.from_cnbiloop:
            self.sockHostToProtocol.close()
        if self.to_cnbiloop:
            self.sockHostFromProtocol.close()
        # self.sockClientFromProtocol.close()
        # self.sockClientToProtocol.close()

    def init_mp_process(self, target_func):
        self.proc.append(mp.Process(group=None, target=target_func))
        self.proc[-1].start()

    def send_manual_trigger_daemon(self):
        while True:
            try:
                data = int(raw_input('Trigger value (1-255)? ').strip())
                assert 1 <= data <= 255
                self.bci.id_msg_bus.SetEvent(data)
                self.bci.iDsock_bus.sendall(self.bci.id_serializer_bus.Serialize())
                print('Sent', data)
            except KeyboardInterrupt:
                self.finish = True
                break

    def send_tid_daemon(self):
        while not self.finish:
            # data = receive(self.sockHostFromProtocol)
            data = []
            try:
                msg = self.sockClientFromProtocol.recv(1024)
                # print 'msg', msg
                data = msg.split(',')
                # print 'data split', data
                if len(data) >= 2:
                    data = data[-2]  # take the last one with number, if just last one, it will be an empty string
                else:
                    self.sockClientFromProtocol, self.clientAddressFromProtocol, self.finish, self.established_time = \
                        wait_for_connection(self.sockHostFromProtocol, self.terminateKey)
                    data = []
            except socket.error as e:
                # print e
                pass

            # send to tid
            # print len(data)
            if len(data) is not 0:
                data = (int)(data)
                print 'sending: ', data
                self.bci.id_msg_bus.SetEvent(data)
                self.bci.iDsock_bus.sendall(self.bci.id_serializer_bus.Serialize())

    def is_ndf_event(self, data):
        # should convert to num or check in string format...
        return True

    def receive_tid_daemon(self):
        n_data = 0
        while True:
            # receive TiD Event
            data = handle_tobiid_input(self.bci)
            # if data:
            #    print data
            # transmit TiD Event if input buffer is not empty
            if data is not None:
                try:
                    n_data = n_data + 1
                    # print data
                    cur_time = time.time()
                    elapsed_time = cur_time - self.established_time
                    if elapsed_time > 0.0 and not self.videoMode:
                        # print elapsedTime
                        print data, n_data / elapsed_time
                    if self.is_ndf_event(data):
                        self.sockClientToProtocol.sendall(data)
                except socket.error:
                    print 'Failed to send data...reconnecting...'
                    self.bci.close()
                    self.sockClientToProtocol, self.clientAddress, self.finish, self.established_time = \
                        wait_for_connection(self.sockHostToProtocol, self.terminateKey)
                    self.bci = BciInterface(self.ip_cnbiloop)
                    n_data = 0
            if self.finish:
                break
            continue
        self._close()
        print 'Interface terminated!'
        pygame.quit()
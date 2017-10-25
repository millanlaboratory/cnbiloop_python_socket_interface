'''
This program allows sending TID  events manually
Author: Ping-Keng Jao
'''
from BCI import BciInterface

if __name__ == "__main__":
    # bci = BciInterface(connect_ip='localhost')
    bci = BciInterface(connect_ip='pk')
    while True:
        try:
            data = int(raw_input('Trigger value (1-255)? ').strip())
            if not (1 <= data <= 255):
                break
            bci.id_msg_bus.SetEvent(data)
            bci.iDsock_bus.sendall(bci.id_serializer_bus.Serialize())
            print('Sent', data)
        except KeyboardInterrupt:
            break
bci.close()
print 'Program Finished Successfully!'
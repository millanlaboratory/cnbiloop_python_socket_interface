''''''
# initialize BCI interface
import bidirectionalInterface as bi
import socket

# Arguments
ip_python = '192.168.1.1'  # '169.254.123.101'
ip_cnbiloop = '127.0.0.1' # '192.168.1.1'
port_tid_to_protocol = 9999
port_tid_from_protocol = 9990
socket.setdefaulttimeout(1)


if __name__ == "__main__":
    b_inf = bi.BidirectionalInterface(ip_python=ip_python, ip_cnbiloop=ip_cnbiloop,
                                      port_tid_from_cnbiloop=port_tid_to_protocol, port_tid_to_cnbiloop=port_tid_from_protocol,
                                      to_cnbiloop=True, from_cnbiloop=True, manual_trigger=False)
    while not b_inf.finish:
        pass

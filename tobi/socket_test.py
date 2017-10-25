import socket
s = socket.socket()
host = socket.gethostname()
port = 12397
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((host, port))

print "a"
s.listen(1)
print "b"
while True:
    print "c"
    c, addr = s.accept()
    print "d"
    print "Got connection from", addr
    c.snd("Thank you for connecting!")
    c.close()
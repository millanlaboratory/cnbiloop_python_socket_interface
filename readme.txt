The default value is for PK's drone experiment.
The python program should be executed on the Linux machine which runs cnbiloop.

There are 4 main files can be executed with the following commnads:
	python bidirection_loop.py # This handles TID values from/to protocol to/from the ndf MATLAB file.
	python captureTIDLoop.py   # This feeds TID values from ndf MATLAB file to the protocol
	python sendTIDLoop.py      # This captures TID values from the protocol.
	python send_trigger.py     # This allows manual sedning TID values to the loop.
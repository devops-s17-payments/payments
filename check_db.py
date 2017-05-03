import socket, time, argparse, os
""" Check if port is open, avoid docker-compose race condition """


if 'VCAP_SERVICES' in os.environ:
	print("Using Bluemix storage service!")
else:
	parser = argparse.ArgumentParser(description='Check if port is open')
	parser.add_argument('--ip', required=True)
	parser.add_argument('--port', required=True)

	args = parser.parse_args()

	# Get arguments
	port = int(args.port)
	ip = str(args.ip)

	# Infinite loop
	while True:
	    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	    result = sock.connect_ex((ip, port))
	    if result == 0:
	        print("{0} port is open!".format(ip))
	        break
	    else:
	        print("{0} port is not open! Checking again soon,".format(ip))
	        time.sleep(3)

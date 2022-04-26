import operator
import re
import SocketServer
import socket
import threading
import sys

def calcchecksum(nmea_str):
	return reduce(operator.xor, map(ord, nmea_str), 0)

def readNMEA(nmea_str):
	
	NMEApattern = re.compile('''
		^[^$]*\$?
		(?P<nmea_str>
			(?P<talker>\w{2})
			(?P<sentence_type>\w{3}),
			(?P<data>[^*]+)
		)(?:\\*(?P<checksum>[A-F0-9]{2}))
		[\\\r\\\n]*
		''', re.X | re.IGNORECASE)
	match = NMEApattern.match(nmea_str)
	if not match:
		raise ValueError('could not parse data: %r' % nmea_str)
	nmea_dict = {}	
	nmea_str      				= match.group('nmea_str')
	nmea_dict['talker']         = match.group('talker').upper()
	nmea_dict['sentence_type']  = match.group('sentence_type').upper()
	nmea_dict['data']           = match.group('data').split(',')
	checksum					= match.group('checksum')
	cs1 = int(checksum, 16)
	cs2 = calcchecksum(nmea_str)
	if cs1 != cs2:
		raise ValueError('checksum does not match: %02X != %02X' %
			(cs1, cs2))	
	return nmea_dict

def parseHeartbeat(message):

	if len(message['data']) != 8:
		raise ValueError('Incorrect number of elements in sentence')
	print "Valid Heartbeat"
	print "Team ID: ", message['data'][5]
	print "Vehicle time", message['data'][0], "Vehicle at ", message['data'] [1], message['data'] [2], message['data'] [3],message['data'] [4]
	if message['data'][6] == '1':
		print "Vehicle under RC mode"
	elif message['data'][6] == '2':
		print "Vehicle under Autonomous Mission Mode"
	else:
		raise ValueError('Unknown mode reported')
	if message['data'][7]:
		print "Reported current task", message['data'][7]
	else:
		print "Current task not reported"

def parseSearchTask(message):

	if len(message['data']) != 7:
		raise ValueError('Incorrect number of elements in sentence')
	print "Answer to Underwater Search and Report given"
	print "Team ID: ", message['data'][1]
	print "Vehicle time: ", message['data'][0]
	print "Reported Pinger Location: ", message['data'] [2], message['data'] [3], message['data'] [4],message['data'] [5]
	if message['data'][6]:
		print "Reported pinger depth: ", message['data'][6]
	else:
		print "No pinger depth reported"	
	
def parseLightTask(message):

	if len(message['data']) != 3:
		raise ValueError('Incorrect number of elements in sentence')
	print "Answer to Observe and Report given"
	print "Team ID: ", message['data'][1]
	print "Vehicle time: ", message['data'][0] 
	print "Reported light sequency from first to last: ",
	for a in message['data'] [2]:
		if a == 'R':
			print 'Red '
		elif a == 'G':
			print 'Green '
		elif a == 'B':
			print 'Blue '
		else:
			print 'Razz-a-ma-tazz'
	
class MyTCPHandler(SocketServer.StreamRequestHandler):
	
	def handle(self):
		while True:
			# self.rfile is a file-like object created by the handler;
			# We can now use e.g. readline() instead of raw recv() calls
			self.data = self.rfile.readline().strip()
			if self.data == '':
				break
			try:
				message = readNMEA(self.data)
				if message['talker'] != 'RX':
					raise ValueError('Invalid Talker, got %r' % message['talker'])
				if message['sentence_type'] == 'HRT':
					parseHeartbeat(message)
				elif message['sentence_type'] == 'SEA':
					parseSearchTask(message)
				elif message['sentence_type'] == 'LIT':
					parseLightTask(message)
				else:
					raise ValueError('Invalid Sentence Type, got %r' % message['sentence_type'])
			except ValueError as e:
				print "Error parsing message:" 
				print e

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

if __name__ == "__main__":
    
	# Create the server, binding to localhost on port 12345
	HOST, PORT = "localhost", 12345
	#server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)
	server = ThreadedTCPServer((HOST, PORT), MyTCPHandler)
	
	# Start a thread with the server.
	# That thread will then start one more thread for each request.
	server_thread = threading.Thread(target=server.serve_forever)
	server_thread.daemon = True
	server_thread.start()
	print "Server running"
	print "Server Address:", socket.gethostbyname(socket.gethostname()) 
	print "Connect to server on port:", PORT
	
	while True:
		command = raw_input("type 'quit' to exit program  ")
		if command == 'quit':
			sys.exit()
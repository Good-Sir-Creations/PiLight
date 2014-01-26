#!/usr/bin/env python
import socket, threading, time#, RPi.GPIO as GPIO

readCommand = ""
host = "0.0.0.0"
port = 9001
choices = []
choiceCommands = []
pins = []
rgba = []
gpio = []

class ClientThread(threading.Thread):
	def __init__(self, ip, port, socket):
		threading.Thread.__init__(self)
		self.ip = ip
		self.port = port
		self.socket = socket
		#print "[+] New thread started for "+ip+":"+str(port)
	def run(self):
		#print"Connection from : "+ip+":"+str(port)
		data = self.socket.recv(1024).replace('\n','')
		print "Client sent:\"" + data + "\""
		if data.lower().startswith("init"):
			self.socket.send(str(join(choices)) + "\n")
		elif data.lower().startswith("get:"):
			tmp = data.split(":")[1]
			if tmp.lower().startswith("all"):
				if not rgbaEqual():
					resetRGBA()
					#resetPins()
				self.socket.send(rgba[0] + "\n")
			else:
				self.socket.send(tmp + ":" + getChoiceRGBA(tmp) + "\n")
		elif data.lower().startswith("set:"):
			tmp = data.split("/")
			choice = tmp[0].split(":")[1]
			setRGBA(choice, tmp[1])
			#resetPins()
			self.socket.send("done\n")
class FileHandler(threading.Thread):
	def run(self):
		while True:
			f = open("default.config", 'r+')
			print "Doing file things..."
			f.close()
			time.sleep(1)

def join(arr):
	tmp = ""
	for i in range(0, len(arr)-1):
		tmp += arr[i] + ","
	tmp += arr[len(arr)-1]
	return tmp
def rgbaEqual():
	tmp = rgba[0]
	for i in range(1, len(rgba)):
		if not tmp == rgba[i]:
			return False
	return True
def getChoiceRGBA(choice):
	for i in range(0, len(choices)):
		if choice==choiceCommands[i]:
			return rgba[i]
def setRGBA(choice, newrgba):
	if choice=="all":
		for tmp in rgba:
			tmp = newrgba
	else:
		for i in range(0, len(choices)):
			if choice==choiceCommands[i]:
				rgba[i]=newrgba
				break
def resetRGBA():
	for tmp in rgba:
		tmp = "255 255 255 50"
def initFile():
	f = open("default.config")
	for line in f:
		if line[0] != '\t':
			if "Init" in line:
				readCommand = "init"
			elif "LED Areas and Pins" in line:
				readCommand = "pins"
			elif "Default Values" in line:
				readCommand = "vals"
		else:
			if readCommand=="init"	:
				tmp = line.replace('\t','').split(':')
				if tmp[0]=="port":
					port = int(tmp[1])
			elif readCommand=="pins":
				tmp = line.replace('\t','').split(':')
				choices.append(tmp[0])
				choiceCommands.append(tmp[0].lower().replace(' ', ''))
				pins.append(tmp[1].split(' '))
				rgba.append("")
			elif readCommand=="vals":
				tmp = line.replace('\t','').split(':')
				for i in range(0, len(choices)):
					if choices[i]==tmp[0]:
						rgba[i] = tmp[1]
				for i in range(0, len(choices)):
					if rgba[i]=="":
						rgba[i]="255 255 255 50"
	f.close()
def initPins():
	print "stuff"
	#reset the pins here
	#GPIO.setmode(GPIO.BCM)

def resetPins():
	print "stuff"
	#reset the pins here

def initConfigFile():
	print "default.config not found... loading config\n"
	port = raw_input("Port Number: ")
	ledStrips = int(raw_input("Number of LED Strips: "))
	choices = [None] * ledStrips
	choiceCommands = [None] * ledStrips
	pins = [None] * ledStrips
	rgba = [None] * ledStrips
	for i in range(0, ledStrips):
		choices[i] = raw_input("Enter the LED Strip Area: ")
		choiceCommand[i] = choices[i].lower().replace(' ', '')
		tmpPins = ""
		tmpPins += (raw_input("Enter the pin for RED: ") + " ")
		tmpPins += (raw_input("Enter the pin for GREEN: ") + " ")
		tmpPins += raw_input("Enter the pin for BLUE: ")
		pins[i] = tmpPins
		rgba[i] = "255 255 255 50"
	f = open("default.config", 'w')
	f.write("Init:")
	f.write('\t' + str(port) + '\n')
	f.write("LED Areas and Pins:\n")
	for i in range(0, ledStrips):
		f.write(choices[i] + ":" + pins[i])
	f.write("Default Values:")
	for i in range(0, ledStrips):
		f.write(choices[i] + ":" + rgba[i])
try:
	with open("default.config"):
		initFile()
except IOError:
	initConfigFile()
#intiPins()
#resetPins()
FileHandler().start()
tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcpsock.bind((host, port))
while True:
	tcpsock.listen(4)
	(clientsock, (ip, port)) = tcpsock.accept()
	newthread = ClientThread(ip, port, clientsock)
	newthread.start()
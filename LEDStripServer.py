#!/usr/bin/env python
import socket, threading, signal, RPi.GPIO as GPIO
from time import sleep

#Getting that input
readCommand = ""

#Starting them servers
host = "0.0.0.0"
port = 9001

#All of the arrays for storing info for the LEDs
choices = []
choiceCommands = []
pins = []
rgba = []
gpio = []
presets = []
fadeType = []

fadeSpeed = 0.02
fadeSpeedSlow = 0.02
fadeSpeedFast = 0.002

cFade = "colorFade"

#Tell the threads to die... eventually
running = True

############################################
#              Client Thread               #
############################################
# The  Client Thread  handles all incoming #
# sockets and  determines  which LED Strip #
# or LED Strips will be lit.   It also has #
# the ability to initialize  preset fading #
# functions that  will  automatically fade #
# the LEDs  according  each  of the preset #
# fade types.                              #
############################################
# @param socket  -  the  socket  that  the #
#        current thread is  using  to send #
#        and receive data.                 #
############################################
class ClientThread(threading.Thread):
	#Initialize dat thread!
	def __init__(self, socket):
		threading.Thread.__init__(self)
		self.socket = socket
	#Run dat thread!
	def run(self):
		data = self.socket.recv(1024).replace('\n','')    # Receives the data from the client
		if data.lower().startswith("init"):               # Checks if it needs the initial info and then sends the initial info
			self.socket.send(str(join(choices)) + "\n")
		elif data.lower().startswith("get:"):             # Checks if it needs an update
			tmp = data.split(":")[1]
			if tmp.lower().startswith("all"):             # Checks if it is for one or all of them
				if not rgbaEqual():                       # If everything is not already equal, then make it so!  Then send data
					resetRGBA()
				self.socket.send(rgba[0] + "\n")
			else:
				self.socket.send(tmp + ":" + getChoiceRGBA(tmp) + "\n") # Or just send the data for the item it is asking for
		elif data.lower().startswith("set:"):             # Check to see if we need to set the LEDs
			tmp = data.split("/")
			choice = tmp[0].split(":")[1]
			setRGBA(choice, tmp[1])                       # Oh snap, we do!  Better split them strings up and set them LEDs
		elif data.lower().startswith("pre:"):             # Check to see if the request is for a preset Fader
			#uh, ionno.  ABORT ABORT!!!
			print "hooray!"

############################################
#           Light Handler Thread           #
############################################
# The  Light Handler Thread is  constantly #
# updating a single LED Strip with its RGB #
# values to make sure  everything is going #
# as quickly as possible.    It also has a #
# check to make sure  the GPIO isn't being #
# set if there isnt any  change in the RGB #
# Values.                                  #
############################################
class LightHandler(threading.Thread):
	def __init__(self, s, r, g, b):
		threading.Thread.__init__(self)
		self.rgbStrip = s
		self.lastR = self.rPin = r
		self.lastG = self.gPin = g
		self.lastB = self.bPin = b

	def run(self):
		while running: # Make sure we are still good to go!  Then check if anything has changed.  If so, reset the lastRGB to the current RGB and reset the pins Duty Cycle
			#print "\"" + str(float(self.lastR*2.55)) + "\""  + " " + "\""  + str(float(rgba[self.rgbStrip].split(' ')[1])) + "\""
			if (float(self.lastR*2.55))!=(float(rgba[self.rgbStrip].split(' ')[0])) or (float(self.lastG*2.55))!=(float(rgba[self.rgbStrip].split(' ')[1])) or (float(self.lastB*2.55))!=(float(rgba[self.rgbStrip].split(' ')[2])):
				self.lastR = (float(rgba[self.rgbStrip].split(' ')[0])/255)*100
				self.lastG = (float(rgba[self.rgbStrip].split(' ')[1])/255)*100
				self.lastB = (float(rgba[self.rgbStrip].split(' ')[2])/255)*100
				gpio[((self.rgbStrip)*3)].ChangeDutyCycle(self.lastR)     # this is where the pins data gets set.
				gpio[((self.rgbStrip)*3)+1].ChangeDutyCycle(self.lastG)   # All of the colors!
				gpio[((self.rgbStrip)*3)+2].ChangeDutyCycle(self.lastB)
				sleep(fadeSpeed)
				#print (int(float(self.lastR*2.55)+1)!=(int(float(rgba[self.rgbStrip].split(' ')[0]))))


############################################
#           File Handler Thread            #
############################################
# The  File  Handler   Thread  efficiently #
# updates the default.config file with the #
# most current values  and  presets on the #
# device.   It  also  makes  sure  not  to #
# rewrite the file too many times, for the #
# sake of the poor SD card.                #
############################################
class FileHandler(threading.Thread):
	def run(self):
		while running:
			f = open("default.config", 'r+')
			#print "Doing file things..."
			f.close()
			sleep(1)

def join(arr):
	tmp = ""
	for i in range(0, len(arr)-1):
		tmp += arr[i] + ' '
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
		tmp = "255 255 255 100"


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
			if readCommand=="init":
				tmp = line.replace('\t','').split(':')
				if tmp[0]=="port":
					port = int(tmp[1])

			elif readCommand=="pins":
				tmp = line.replace('\t','').split(':')
				choices.append(tmp[0])
				choiceCommands.append(tmp[0].lower().replace(' ', ''))

				pins.append(tmp[1])
				rgba.append("")

			elif readCommand=="vals":
				tmp = line.replace('\t','').split(':')
				for i in range(0, len(choices)):
					if choices[i]==tmp[0]:
						rgba[i] = tmp[1]

				for i in range(0, len(choices)):
					if rgba[i]=="":
						rgba[i]="255 255 255 100"
	f.close()



def initPins():
	tmpPin = 0
	tmpP = 0
	GPIO.setmode(GPIO.BCM)                           # Initializes the GPIO pins
	for p in pins:
		GPIO.setup(int(p.split(' ')[0]), GPIO.OUT)   # Sets the required pins to output data
		GPIO.setup(int(p.split(' ')[1]), GPIO.OUT)
		GPIO.setup(int(p.split(' ')[2]), GPIO.OUT)
	for pin in pins:
		for i in pin.split():
			gpio.append(GPIO.PWM(int(i), 100))       # Add PWM controllers to an array for easy access
	tmpRGB = 0
	tmpC = 0
	for tmp in gpio:
		tmp.start((float(rgba[tmpRGB].split(' ')[tmpC])/255)*100)
		tmpC+=1
		if tmpC==4:
			tmpRGB+=1
			tmpC = 0

def initLEDThreads():
	for i in range(0, len(pins)):
		tmp = LightHandler(i, int(pins[i].split(' ')[0]), int(pins[i].split(' ')[1]), int(pins[i].split(' ')[2]))
		tmp.start()

def initPresetThreads():
	print "not yet"

def cleanup():
	for tmp in gpio:
		tmp.stop()
	GPIO.cleanup()
	tcpsock.close()

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
		rgba[i] = "255 255 255 100"
	f = open("default.config", 'w')
	f.write("Init:")
	f.write('\t' + str(port) + '\n')
	f.write("LED Areas and Pins:\n")
	for i in range(0, ledStrips):
		f.write(choices[i] + ":" + pins[i])
	f.write("Default Values:")
	for i in range(0, ledStrips):
		f.write(choices[i] + ":" + rgba[i])

def init():
	initPins()
	initLEDThreads()
	initPresetThreads()
	FileHandler().start()

try:
	with open("default.config"):
		initFile()
except IOError:
	initConfigFile()
init()
tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcpsock.bind((host, port))

try:
	while True:
		tcpsock.listen(4)
		(clientsock, (ip, port)) = tcpsock.accept()
		newthread = ClientThread(clientsock)
		newthread.start()
except KeyboardInterrupt:
    cleanup()
    running = False
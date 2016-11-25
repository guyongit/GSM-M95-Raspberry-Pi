# Import of libraries
import picamera
import RPi.GPIO as GPIO # GPIO library
import serial
import time # library used for sleep() function
import os

# constants defining Rpi I/O pins (in board numbers!)
pwrPin = 3
BellButton = 7
DoorOpener = 5

# dimensions of the photo in pixels
# don't make it too large, takes longer to send and may cause extra charges
camWIDTH =160
camHEIGHT = 120

#The following constants must be changed for your provider and phone number
ThisNumber="+31612345678"                 #this SIM card's phone number
ThatNumber="+31687654321"                 #number of the phone receiving the MMS
APN = "portalmmm.nl"                    #your provider's APN, in this case KPN
#APN = "office.vodafone.nl"              #your provider's APN, in this case Vodafone
MMSC="http://mp.mobiel.kpn/mmsc"        #your provider's MMSC, KPN
#MMSC = "http://mmsc.mms.vodafone.nl"    #your provider's MMSC, Vodafone
MMSproxy="10.10.100.20"                 #your provider's MMS proxy server, KPN
MMSport="5080"                          # and its port
#MMSproxy = "192.168.251.150"		#your provider's MMS proxy server, Vodafone
#MMSport = "8799"				# and its port

# Password for remote door opener
Very_Secret="1234"

# Adjustment of speaker volume level
SpeakerLevel = '50' #0-100 (low-hi)
# Adjustment of microphone gain
MicGain = '8' #0-15 (low-high)

# This function is used to determine file size of the photo
#JPG is a compressed format, size may vary depending on pictures content
def getsize(filename):
        st = os.stat(filename)
        return st.st_size

# Initialisation of the serial port for communication
# between Rpi and M95 GSM-module
port = serial.Serial("/dev/ttyAMA0", baudrate = 115200, timeout = 3.0)
#IMPORTANT!!! Uncomment the next line if you are using Raspbian #version older than Jessie
#
#port.open()

# setup digital I/Os of the Rpi
GPIO.setmode(GPIO.BOARD)
GPIO.setup(pwrPin,GPIO.OUT)             # PWRKEY signal to toggle GSM module on/off
GPIO.output(pwrPin,GPIO.LOW)
GPIO.setup(BellButton,GPIO.IN)          # input for doorbell button
GPIO.setup(DoorOpener,GPIO.OUT)         # output for door opener
GPIO.setup(DoorOpener,GPIO.LOW)
#next command switches the GSM module off, just in case it's already switched on
#otherwise the following toggle of PWRKEY will switch it off
port.write('AT+QPOWD=0\r')
time.sleep(1)

#toggle PWRKEY of the GSM module to wake it up
GPIO.output(pwrPin,GPIO.HIGH) 
time.sleep(1)
GPIO.output(pwrPin,GPIO.LOW)
print "power on"
time.sleep(5)

port.write("AT\r")
time.sleep(0.5) # sleep
line =port.readline()
port.write('AT\r')
time.sleep(0.5) # sleep
port.write('AT\r')
time.sleep(0.5) # sleep


# switch audio channel to the microphone in and speaker out
port.write('AT+QAUDCH=2\r')

# set speaker volume level 0-100 (low-hi)
port.write('AT+CLVL='+SpeakerLevel+'\r')
time.sleep(1)

# set microphone gain 0-15 (low-hi)
print"Micro gain"
port.write('AT+QMIC=0,'+MicGain+'\r')

# some settings of the Rpi cam
# may need adjustment
camera = picamera.PiCamera()
camera.vflip = False
camera.hflip = False
camera.brightness = 60
camera.resolution=(camWIDTH,camHEIGHT)
time.sleep(1)

#uncomment the next two lines if SIM card is protected with PIN number
# and change 0000 to the PIN of your SIM card
#port.write('AT+CPIN=0000\r')
#time.sleep(0.5) # sleep

port.write('AT+CPMS="SM"\r')       #storage for text messages on SIM card
time.sleep(0.5) # sleep

# set phone off hook after second ring
port.write('ATS0=2\r')
time.sleep(0.5)


#set the modem to text mode for SMS messages
port.write('AT+CMGF=1\r')
time.sleep(0.5)
port.write('ATE0\r')            #set echo off
time.sleep(0.5)
port.write('AT+CMGD=0,4\r')     # delete all received SMS messages
time.sleep(0.5)


try:
        while 1:
                port.flushInput()
                port.write('AT+CMGR=1\r')
                time.sleep(0.2)
                line=port.readline()    #skip first response line (it's empty)
                time.sleep(0.2)
                line=port.readline()
                if "REC READ" in line:          #if the text message is already read, delete it
                       port.write('AT+CMGD=0,4\r')     # delete all received SMS messages 
                else:
                        if ThatNumber in line:          #only accept message from correct cell phone nr.
                                print"Phone number correct"
                                time.sleep(0.5)
                                line=port.readline()
                                time.sleep(0.5)
                                line=line.strip()
                                if (line==Very_Secret): #check the password
                                        print 'Open Door'
                                        GPIO.output(DoorOpener,GPIO.HIGH) #toggle dooropener
                                        time.sleep(1)
                                        GPIO.output(DoorOpener,GPIO.LOW)
                print "waiting...."
                if (GPIO.input(BellButton)):
                        
                        print "RING!!!"
                        
                        camera.capture('test1.jpg')
                        print "Picture saved"
                        
                        #line =port.readline()
                        #print line
                        #time.sleep(0.2)
                        #line =port.readline()

        
                        #provider's APN        
                        port.write('AT+QICSGP=1,"'+APN+'"\r')
                        time.sleep(0.2) # sleep
                        #provider's MMSC       
                        port.write('AT+QMMURL="'+MMSC+'"\r')
        
                        time.sleep(0.2) # sleep
        
                        # MMS proxy + port       
                        port.write('AT+QMMPROXY=1,"'+MMSproxy+'",'+MMSport+'\r')
        
                        time.sleep(0.2) # sleep

                        port.write('AT+QFDEL="RAM:picture.jpg"\r')
                        time.sleep(0.2) # sleep
        
                        port.write('AT+QMMSW=0\r')
                        time.sleep(0.2) # sleep
        
                        port.write('AT+QMMSW=1,1,"'+ThatNumber+'"\r')
                        time.sleep(0.2) # sleep
        
                        port.write('AT+QMMSCS="UTF8",1\r')
                        time.sleep(0.2) # sleep
        
                        port.write('AT+QMMSW=4,1\r')
                        time.sleep(0.2) # sleep
                        port.write('You have a visitor!. Dial '+ThisNumber+' to speak to him or her')
                        time.sleep(0.5) # sleep
                        port.write(chr(26))
        
                        time.sleep(1) # sleep
                        test = open("test1.jpg", "r")

        
                        #time.sleep(0.5)
                        file1 = test.read()
                        size=getsize('test1.jpg')
                        print size
                        port.write('AT+QFUPL="RAM:picture.jpg",'+str(size)+'\r')
                        time.sleep(0.5) # sleep
                        port.write(file1)
                        time.sleep(0.5) # sleep
                        port.write('AT+QMMSW=5,1,"RAM:picture.jpg"\r')
                        time.sleep(0.5) # sleep
                        line = port.readline()
                        print 'wait'+line
                        
                        port.write('AT+QMMSEND=1\r')
                        time.sleep(30)
                        
        
except KeyboardInterrupt:
        GPIO.output(pwrPin,GPIO.HIGH) #toggle PWRKEY of the GSM module to switch it off
        time.sleep(1)
        GPIO.output(pwrPin,GPIO.LOW)
        print "power off"
        
        GPIO.cleanup()

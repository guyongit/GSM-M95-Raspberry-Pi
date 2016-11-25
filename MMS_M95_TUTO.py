# Importation des librairies.
import picamera
import RPi.GPIO as GPIO # librairie pour utiliser le port GPIO.
import serial
import time # librairie pour créer pause en secondes.
import os

# constantes pour définir les pins utilisées du port GPIO.
pwrPin = 29  # pour marche arrêt du module M95 (PWRKEY).
Bouton = 33  # pour envoyer une phto par MMS.
SortieLed = 35 # pour controler une sortie du GPIO en receptionnant un
               # SMS depuis un téléphone.

# dimensions de la photo avec PiCamera.
# Attention à la taille de l'image.
camWIDTH = 320  #160 par défaut.
camHEIGHT = 240 #120 par défaut.


# Paramétres de configuration du fournisseur téléphonique.
# A modifier selon votre opérateur. Ici Bouygues Telecom.
ThisNumber="+336XXXXXXXX"      # Numéro de téléphone de la carte SIM.
ThatNumber="+336XXXXXXXX"  #Numéro de téléphone qui receptionnera les MMS.
APN = "mmsbouygtel.com"     # APN du fournisseur.

MMSC="http://mms.bouyguestelecom.fr/mms/wapenc"   #your provider's MMSC
MMSproxy="62.201.129.226"             #Proxy MMS server,
MMSport="8080"                        # et son port.

# Code secret pour valider la SortieLed reçu par SMS, afin de sécuriser
# la sortie du GPIO.
Very_Secret="1234"

# Adjustment of speaker volume level
SpeakerLevel = '50' #0-100 (low-hi)
# Adjustment of microphone gain
MicGain = '8' #0-15 (low-high)

# Cette fonction détermine la taille de l'image enregistrée,
# nécessaire pour l'envoi du MMS.
def getsize(filename):
        st = os.stat(filename)
        return st.st_size

# Initialisation du port série relié entre la raspberry
# et le GSM-module M95 .
port = serial.Serial("/dev/ttyAMA0", baudrate = 115200, timeout = 3.0)
#IMPORTANT!!! Uncomment the next line if you are using Raspbian #version older than Jessie
#
#port.open()


# setup digital I/Os of the Rpi

GPIO.setmode(GPIO.BOARD)         # pins par numéro sur CI.
GPIO.setup(pwrPin,GPIO.OUT)      # PWRKEY signal to toggle GSM module on/off.
GPIO.output(pwrPin,GPIO.LOW)

GPIO.setup(Bouton,GPIO.IN)       # Bouton configuré en entrée.
GPIO.setup(SortieLed,GPIO.OUT)   # SortieLed configuré en sortie.
GPIO.setup(SortieLed,GPIO.LOW)

#next command switches the GSM module off, just in case it's already switched on
#otherwise the following toggle of PWRKEY will switch it off
port.write('AT+QPOWD=0\r')
time.sleep(1)

#toggle PWRKEY of the GSM module to wake it up
GPIO.output(pwrPin,GPIO.HIGH) 
time.sleep(1)
GPIO.output(pwrPin,GPIO.LOW)
print "M95 allumé"
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
port.write('AT+QMIC=0,'+
MicGain+'\r')

# Paramétrages de la Caméra :
camera = picamera.PiCamera()
camera.vflip = False
camera.hflip = False
camera.brightness = 60
camera.resolution=(camWIDTH,camHEIGHT)
time.sleep(1)

#Les 2 lignes suivantes si la carte SIM contient un code PIN.
# remplacer les 0000 par le code pin de la SIM.
port.write('AT+CPIN=0000\r')
time.sleep(0.5) # sleep

port.write('AT+CPMS="SM"\r')     #storage for text messages on SIM card
time.sleep(0.5) # sleep

# nombre de sonneries avant de répondre automatiquement à l'appel ici 2.
port.write('ATS0=2\r')
time.sleep(0.5)



port.write('AT+CMGF=1\r')# 1 = messages en mode texte.
time.sleep(0.5)
port.write('ATE0\r')            # set echo off.
time.sleep(0.5)

port.write('AT+CMGD=0,4\r')     # effacer tout les messages.
time.sleep(0.5)


try:
        while 1:
                port.flushInput()
                port.write('AT+CMGR=1\r') #lecture message SMS (3 lectures).
                time.sleep(0.2)
                line=port.readline()    #on passe la première réponse.
                time.sleep(0.2)
                # la premiére ligne contient REC UNREAD ou READ, numéro
                # de téléphone, date et heure d'envoi :
                line=port.readline()    
                if "REC READ" in line:    #Si le message est déja lu, on efface.
                       port.write('AT+CMGD=0,4\r') # effacer tout les SMS messages.
                else:
                        if ThatNumber in line:   #on vérifie le numéro de téléphone du SMS
                                print"Numéro de téléphone correct"
                                time.sleep(0.5)
                                line=port.readline() #contient le message.
                                time.sleep(0.5)
                                line=line.strip()  #on enleve tout les caractéres spéciaux.
                                if (line==Very_Secret): #Ok si message est égal au code secret.
                                        print 'Led allumé'
                                        GPIO.output(SortieLed,GPIO.HIGH) #toggle SortieLed
                                        time.sleep(2)
                                        GPIO.output(SortieLed,GPIO.LOW)
                                        print 'Led eteinte'
                                        
                                        # Envoyer un SMS :
                                        port.write('AT+CMGF=1\r')
                                        time.sleep(0.5)
                                        port.write('AT+CSCS="GSM"\r')
                                        time.sleep(0.5)
                                        port.write('AT+CMGS="'+ThatNumber+'"\r')
                                        time.sleep(0.2)
                                        port.write("Recu SMS, led allumé 2 secondes") # Message à transmettre.
                                        time.sleep(0.5)
                                        port.write(chr(26)) # Ctrl+Z
                                        time.sleep(1)
                                        # fin instruction envoyer SMS.
                                        
                print "waiting...."
                if (GPIO.input(Bouton)): # si on appui sur le bouton,
										 # on envoi un MMS !	
                        print "On a appuyé sur le Bouton"
                        
                        camera.capture('test1.jpg')
                        print "Image enregistrée"
                        
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

                        port.write('On a appuyé sur le bouton !. Dial '+ThisNumber+' voici la photo ')
                        time.sleep(0.5) # sleep

                        port.write(chr(26))   # Ctrl+Z
        
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
        print "Arret"
        
        GPIO.cleanup()

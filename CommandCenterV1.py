# by patrick Pinard, 30 nov. 2018
# Objet : Command Center V1 
# Mesure de la température, pression et humidité avec capteurs GrovePI sur Raspebrry et affichage sur InfluxDB
# Commande au travers d'une interface graphique créée avec GLADE
#!/usr/bin/python
# Python 3.7
# -*- coding: utf-8 -*-

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from grovepi import *
from grove_rgb_lcd import *
from gi.repository import GObject
import sys, time

#Variables Globales 
temperature        = 0
humidity           = 0
DEBUG              = True
TimeToRefreshValue = 5  #temps de rafraichissement des mesures

#InfluxDB access information
influxDBADDRESS = 'adresse IP serveur InfluxDB'
influxDBUSERNAME = 'username'
influxDBPASSWORD = 'password'
influxDBPORT = 8086
influxDBDATABASE = 'InfluxDB DB name'


#Glade information
GladeName        = "CommandCenterV1.glade"
GladeWindow      = "fenetre"

#information sur capteur pour InfluxDB
measurement = "capteur DHT"
location = "atelier"
GPSCoord = "25°N,45°S"
sensorType = "Raspberry Pi 3 with Grove PI"


class MyWindow:
    global GladeName, GladeWindow    

    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(GladeName)
        self.builder.connect_signals(Handler())
        window = self.builder.get_object(GladeWindow)
        window.show_all()
        
    def main(self):
         Gtk.main()
        
        
class Handler():
    global temperature, humidity  

    def on_graph_clicked(self,widget):
        print("Graph des mesures")
    
    def on_rafraichir_clicked(self, button):
        # Read and refresh display light, temperature & humidity
        displayMesures()      
            
    def on_switch1_activated(self,widget,param):
        if widget.get_state():
            print("switch is set to ON")
            setText("ALL LED are ON")
            digitalWrite(4,1)
            digitalWrite(3,1) 
            digitalWrite(2,1)
        else:
            print("switch is set to OFF")
            setText("ALL LED are OFF")
            digitalWrite(4,0)
            digitalWrite(3,0)
            digitalWrite(2,0)
                          
    def on_switch2_activated(self,widget,param):
        if widget.get_state():
            print("switch RELAI 1 to ON")
            setText("Relai 1 is ON")
            digitalWrite(7,1)
        else:
            print("switch RELAI 1to OFF")
            setText("Relai 1 is OFF")
            digitalWrite(7,0)
            
    def on_checkbutton1_toggled(self, widget):
        if widget.get_active():
            print("button is set to ON for LED bleu")
            digitalWrite(4,1)
        else:
            print("button is set to OFF for LED bleu")
            digitalWrite(4,0)
            
    def on_checkbutton2_toggled(self, widget):
        if widget.get_active():
            print("button is set to ON for LED rouge")
            digitalWrite(3,1)
        else:
            print("button is set to OFF for LED rouge")
            digitalWrite(3,0)
            
    def on_checkbutton3_toggled(self, widget):
        if widget.get_active():
            print("button is set to ON for LED verte")
            digitalWrite(2,1)
        else:
            print("button is set to OFF for LED verte")
            digitalWrite(2,0)
       
    def on_Quitter_activate(self, widget):
        print("au revoir")
        Gtk.main_quit()
        sys.exit(0)

       
def displayMesures(): 

    # Read and display temperature and humidity mesures
    temperature, humidity = readDHTmesure()
    display_time = time.strftime(" %d %b %Y à %H:%M:%S")
    
    # display mesure on window
    MyApp.builder.get_object("DisplayLastMesureTime").set_text(display_time)
    MyApp.builder.get_object("DisplayTemperature").set_text(str(temperature))
    MyApp.builder.get_object("DisplayHumidity").set_text(str(humidity))
                
    # Read and display light mesure
    light = readLIGHTmesure()
    MyApp.builder.get_object("DisplayLightMesure").set_text(str(light))

    mesuretime = int(time.time())*1000
    InjectDataToInfluxDB(temperature, humidity,light,mesuretime)

    if DEBUG: 
        print("---------------------------------------------------")
        print("Valeurs envoyées à InfluxDB : ")
        print("   Date        : ", time.strftime("%d %b %Y"))
        print("   Heure       : ", time.strftime("%H:%M:%S"))
        print("   Température : ", temperature)
        print("   Humidité    : ", humidity)
        print("   Luminosité  : ", light)
        print("---------------------------------------------------")


 
def readDHTmesure():

    sensor = 8  # The Sensor goes on digital port D8
    blue = 0    # The Blue colored sensor.
    white = 1   # The White colored sensor.

    curr_time = time.strftime(" %d %b %Y à %H:%M:%S") 
    [temperature,humidity] = dht(sensor,white)
    
    try:
        if math.isnan(temperature) == False and math.isnan(humidity) == False:
            setRGB(0,64,0) 
            setText("temp= %.02f C \nhum = %.02f %%" %(temperature, humidity))   
            return temperature, humidity
        else:
            setText("erreur lecture Temp & Hum...")
            return -1, -1
    except(ValueError, ZeroDivisionError):
        print("Oops, something went wrong!")

def readLIGHTmesure():  
    # Connect the Grove Light Sensor to analog port A0
    light_sensor = 0
    pinMode(light_sensor,"INPUT")
    # Get sensor value (min = 0, max = 65535)  ???
    light = analogRead(light_sensor)
    try:
        if math.isnan(light) == False :
            setRGB(0,64,0) 
            setText("Light= %.02" %(light))   
            return light
        else:
            setText("erreur lecture Luminosité !")
            return -1
    except(ValueError, ZeroDivisionError):
        print("Oops, something went wrong!")

def OpenInfluxDB():

    #Login (host, port, user, pwd, dbname)
    client =  InfluxDBClient(influxDBADDRESS, influxDBPORT, influxDBUSERNAME, influxDBPASSWORD, influxDBDATABASE)  
    
    # create database if doesn't exist
    client.create_database(influxDBDATABASE)    

def InjectDataToInfluxDB(t,h,l,d):
    
    global measurement, location, GPSCoord, sensorType
     
    data=[
        {
          "measurement": measurement,
              "tags": {
                  "location": location,
                  "GPS coord": GPSCoord,
                  "Type capteur": sensorType,
              },
              "time": d,
              "fields": {
                  "temperature" : t,
                  "humidity": h,
                  "light": l
              }
          }
        ]
    if DEBUG:
        print(data)
    try:
        client.write_points(data, time_precision='ms')
    except(ValueError, ZeroDivisionError):
        print("Oops, something went wrong with InfluxDB ... ! ")
    
   

if __name__ == '__main__':
   
    setRGB(0,64,0) 
    setText("         Bienvenue !       ")
    setText("...ouverture de InfluxDB...") 
    time.sleep(2)

    OpenInfluxDB()
    
    setText("Thread de mesure démarre...")
    time.sleep(1)
    t = threading.Timer(TimeToRefreshValue, displayMesures)
    t.start()

    MyApp=MyWindow()
    MyApp.main()
   
    
           
   

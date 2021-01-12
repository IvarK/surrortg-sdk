import time
import serial
import socketio
import asyncio
from dataclasses import dataclass

"""
General:
 - Python version 3.7
 - use python-socketio's async client for the communication:
 https://python-socketio.readthedocs.io/en/latest/api.html#asyncclient-class
 https://github.com/miguelgrinberg/python-socketio
 - pyserial and pyserial-asyncio could be beneficial if serial communication is required
 (if i2c is better use that) 
 https://github.com/pyserial/pyserial-asyncio
"""

@dataclass
class GPSData:
    """Represents data form the sensors
    
    Can include also speed, acceleration, angles etc.
    This is just an example.
    """
    lat: float
    lon: float
    alt: float

class GPSArea:
    def __init__(self, gps_area):
            self.gps_area = gps_area

    def in_valid_area(self, location):
        """Returns True if inside the valid area, False if not"""
        return True

class GPSSensor:
    """Do not implement __init__, as this is more convinient for the users
    """
    #Global keyword for testing receiving data from server
    global sio
    sio = socketio.Client()

    async def connect(self, polling_rate=1, pins="SOME_DEFAULT_PINS", robot_id=123456):
        """Connect and start polling data from the sensor to on_location method

        Any required parameters can be passed to __init__ also (pins, etc.).
        Optionally allow specifying the polling rate to some appropriate value

        (use async methods to allow calling on_location in a non-blocking way)
        """
        self.robot_id = robot_id
        sio.connect('http://165.227.146.155:3002?type=robot')
        x = {
                "robot_id":  robot_id,
                "alt": 0, 
                "lat":   0,
                "long": 0 
            }
        """Callback to receive area data from the server"""
        #data = await self.sio.emit('retrieve_data', x)
        #self.gps_area = GPSArea(data)
        self.gps_area = GPSArea(1)
        self.ser = serial.Serial(
            port='/dev/ttyS0', 
            baudrate = 9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1
        )

    async def get_data(self):
        """Returns a GPSData object

        After connect, this method should be called according to the polling rate
        (can be async def if needed)
        """
        while True:
            gpsData=str(self.ser.readline())
            if "$GPGGA" in gpsData:
                try:
                    gpsList = gpsData.split(",")

                    latitude = gpsList[2]
                    latChar = gpsList[3]
                    degreeLat = int(float(latitude)/100)
                    secondLat = float(latitude) - degreeLat * 100
                    latDec = degreeLat + secondLat/60
                    if (latChar == "S"):
                        latDec = -latDec

                    longitude = gpsList[4]
                    longChar = gpsList[5]
                    degreeLong = int(float(longitude)/100)
                    secondLong = float(longitude) - degreeLong * 100
                    longDec = degreeLong + secondLong/60
                    if(longChar == "W"):
                        longDec = -longDec

                    alt = gpsList[9]

                #print("Latitude: " + str(latDec) + ", Longitude: " + str(longDec) + ", Altitude: " + alt)
                    #print("WORKS")
                    return GPSData(latDec, longDec, alt)
                except ValueError:
                    #print("Value Error")
                    return GPSData(0, 0, -10000)

    
    async def run(self, polling_rate):
        while True:
            loc = await self.get_data()
            """Check if inside valid area and send coordinates to server"""
            #in_valid_area(loc)
            x = {
                        "robot_id":  self.robot_id,
                        "alt": loc.alt, 
                        "lat":   loc.lat,
                        "long": loc.lon 
                }
            #if ( loc.alt != -10000) 
            sio.emit('update_location', x)
            print(x)
            await asyncio.sleep(1)

    
    async def on_data(self, data):
        """Users should override this method to keep up with changes
        
        For example they could pass the GPSData to GPSArea.in_valid_area
        """
        pass

    async def disconnect(self):
        """Stop polling, connections, release resources"""
        sio.disconnect()

#Receive area data from the server
@sio.on('boundary_data')
def boundary_data(data):
    print("RECEIVED DATA FROM THE SERVER: ")
    print(data)
    self.gps_area = GPSArea(data)
    #return "OK", 123

if __name__ == "__main__":
    # Example usage:

    # create custom gps sensor with callback
    class MyGPSSensor(GPSSensor):

        async def on_data(self, data):
            if self.gps_area.in_valid_area(data):
                print("In valid area!")
            else:
                print("Was outside the valid area")

    async def main():
        print("running")
        # create GPSSensor
        gps_sensor = MyGPSSensor()
        # connect
        await gps_sensor.connect(polling_rate=10)
        task = asyncio.create_task(gps_sensor.run(1))
        print("sleeping")
        # get GPS updates for 30s according to the set polling rate
        await asyncio.sleep(45)
        print("sleep ended")
        task.cancel()
        await gps_sensor.disconnect()
        
    asyncio.run(main())

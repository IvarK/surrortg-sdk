import time
import serial
import socketio
import asyncio
from dataclasses import dataclass

from shapely.geometry import Point, Polygon, LinearRing
from shapely.ops import nearest_points
from math import radians, cos, sin, asin, sqrt

"""
General:
 - Python version 3.7
 - Socketio version 4.6.1
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
    This is just for position
    """
    lat: float
    lon: float
    alt: float

class GPSArea:

    """Handles the calculations for the boundary data"""

    def __init__(self, gps_area):
    	self.gps_area = gps_area

    def in_valid_area(self, location):
    	boundary_area = Polygon(self.gps_area)
    	loc = Point(location)
    	"""Returns True if inside the valid area, False if not"""
    	return boundary_area.contains(loc)

    def distance_to_border(self, location):
        border = LinearRing(self.gps_area)
        loc = Point(location)
        p1, _ = nearest_points(border, loc)

        def haversine(lon1, lat1, lon2, lat2):
            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371000
            return c * r

        distance = haversine(loc.x, loc.y, p1.x, p1.y)
        return distance


class gpsSocket:

    sio = socketio.AsyncClient()

    def __init__(self, robot_id):
        self.robot_id = robot_id

    @sio.event
    def boundary_data(data):
        print('boundary data received: ', data)

    async def send_data(self, data):
        x = {
                "robot_id":  self.robot_id,
                "alt": data.alt, 
                "lat":   data.lat,
                "long": data.lon 
            }
        #print("SENDING DATA!")
        await self.sio.emit('update_location', x)

    async def connect(self):
        #For testing locally
        await self.sio.connect('http://localhost:5000')
        #await self.sio.connect('http://165.227.146.155:3002?type=robot&game_id=0&robot_id=123456')

    async def disconnect(self):
        await self.sio.disconnect()

class GPSSensor:
    """Do not implement __init__, as this is more convinient for the users
    """

    async def connect(self, polling_rate=1, pins="SOME_DEFAULT_PINS"):
        """Connect and start polling data from the sensor to on_location method

        Any required parameters can be passed to __init__ also (pins, etc.).
        Optionally allow specifying the polling rate to some appropriate value

        """

        self.ser = serial.Serial(
            port='/dev/ttyS0', 
            baudrate = 9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1
        )

    def get_data(self):
        """Returns a GPSData object

        After connect, this method should be called according to the polling rate
        (can be async def if needed)
        """
        return GPSData(0, 0, -10000)
        while True:
            gpsData=str(self.ser.readline())
            if "$GPGGA" in gpsData:
                try:

                    """Parse the data from the sensor and convert the elements to a correct format"""
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

                    return GPSData(latDec, longDec, alt)
                except ValueError:
                    return GPSData(0, 0, -10000)

    async def on_data(self, data):
        """Users should override this method to keep up with changes
        
        For example they could pass the GPSData to GPSArea.in_valid_area
        """
        pass

    async def disconnect(self):
        """Stop polling, connections, release resources"""
        pass

if __name__ == "__main__":
    # Example usage:

    # create custom gps sensor
    class MyGPSSensor(GPSSensor):
        
        def __init__(self, socket):
            self.socket = socket

        async def pre_run(self):
            await self.socket.connect()

        async def post_run(self):
            await self.socket.disconnect()

        async def run(self, polling_rate):
            await self.pre_run()
            while True:
                loc = self.get_data()
                await self.socket.send_data(loc)
                await asyncio.sleep(1)

    async def main():
        print("running")
        #Create SocketIO and GPSSensor
        socket = gpsSocket(123456)
        gps_sensor = MyGPSSensor(socket)

        #Create new task and add it to the event loop
        event_loop = asyncio.get_event_loop()
        task = event_loop.create_task(gps_sensor.run(1))
        
        # get GPS updates for 30s according to the set polling rate
        await asyncio.sleep(30)
        await gps_sensor.post_run()
        print("main loop ended")
        
        await gps_sensor.disconnect()
        
    asyncio.run(main())

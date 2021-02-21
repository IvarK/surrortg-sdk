import time
import serial
import socketio
import asyncio
import jwt
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
 -Shapely 1.7
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
        loc = Point([location.lon, location.lat])
        """Returns True if inside the valid area, False if not"""
        return boundary_area.contains(loc)

    def distance_to_border(self, location):
        border = LinearRing(self.gps_area)
        loc = Point([location.lon, location.lat])
        p1, _ = nearest_points(border, loc)

        def haversine(lon1, lat1, lon2, lat2):
            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * asin(sqrt(a))
            r = 6371000
            return c * r

        distance = haversine(loc.x, loc.y, p1.x, p1.y)
        return distance

class GPSSocket:

    sio = socketio.AsyncClient()
    secret = "asd"

    def __init__(self, url, robot_id, game_id):
        self.url = url
        self.robot_id = robot_id
        self.game_id = game_id
        self.gps_area = GPSArea([(25.04076,60.293783),(25.0414252,60.2937299),(25.0406528,60.2932992),(25.0407493,60.2937033)])

    
    @sio.event(namespace='/robot')
    def boundary_data(self, data):
        print("Received data: ", data)
        self.gps_area = GPSArea(data['points'])
    
    def get_query_url(self, url):
        data = {
                "role" : 'location',
                "gameId" : self.game_id,
                "robotId":  self.robot_id
                }
        encoded_jwt = jwt.encode(data, self.secret, algorithm="HS256")
        self.url += (
            f"?token={encoded_jwt}"
        )

    async def send_data(self, data):
        x = {
                "robot_id":  self.robot_id,
                "alt": data.alt, 
                "lat":   data.lat,
                "long": data.lon
            }
        print("sending: ", x)
        await self.sio.emit('location_data', x, namespace='/robot')

    async def connect(self):
        # Link the handler to the GPSSocket class, allows the use of 'self'
        #hold = {'_id': '602408525910da0d98ab2780', 'game_id': '0', 'points': [[-11.40594059405937, 27.54411672839069], [-60.59405940594056, -10.828519650211135], [49.54455445544556, 5.848726834192107], [-11.40594059405937, 27.54411672839069]]}
        self.sio.on("boundary_data", self.boundary_data, namespace='/robot')

        # For testing locally
        if "localhost" not in self.url:
            self.get_query_url(self.url)
        print(self.url)
        await self.sio.connect(self.url, namespaces=['/robot'])

    async def disconnect(self):
        await self.sio.disconnect()


class GPSSensor:
    """Do not implement __init__, as this is more convinient for the users"""

    testing = True

    async def connect(self, pins="SOME_DEFAULT_PINS"):
        """Connect and start polling data from the sensor to on_location method

        Any required parameters can be passed to __init__ also (pins, etc.).
        Optionally allow specifying the polling rate to some appropriate value

        """

        self.ser = serial.Serial(
            port="/dev/ttyS0",
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1,
        )

    def get_data(self):
        """Returns a GPSData object

        After connect, this method should be called according to the polling rate
        (can be async def if needed)
        """
        if self.testing:
            return GPSData(25.0410908, 60.2934853, -10000)
        while True:
            gpsData = str(self.ser.readline())
            if "$GPGGA" in gpsData:
                try:

                    """Parse the data from the sensor and convert the elements to a correct format"""
                    gpsList = gpsData.split(",")

                    latitude = gpsList[2]
                    latChar = gpsList[3]
                    degreeLat = int(float(latitude) / 100)
                    secondLat = float(latitude) - degreeLat * 100
                    latDec = degreeLat + secondLat / 60
                    if latChar == "S":
                        latDec = -latDec

                    longitude = gpsList[4]
                    longChar = gpsList[5]
                    degreeLong = int(float(longitude) / 100)
                    secondLong = float(longitude) - degreeLong * 100
                    longDec = degreeLong + secondLong / 60
                    if longChar == "W":
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
            self.testing = True
            await self.socket.connect()

        async def post_run(self):
            await self.socket.disconnect()

        async def run(self, polling_rate):
            await self.pre_run()
            while True:
                loc = self.get_data()
                await self.socket.send_data(loc)
                await asyncio.sleep(polling_rate)

    async def main():
        print("running")
        # Create SocketIO and GPSSensor
        # "http://165.227.146.155:3002"
        socket = GPSSocket("http://localhost:9090", 123456, 0)
        gps_sensor = MyGPSSensor(socket)

        # Create new task and add it to the event loop
        event_loop = asyncio.get_event_loop()
        task = event_loop.create_task(gps_sensor.run(1))

        # get GPS updates for 30s according to the set polling rate
        await asyncio.sleep(10)
        await gps_sensor.post_run()
        print("main loop ended")

        await gps_sensor.disconnect()

    asyncio.run(main())

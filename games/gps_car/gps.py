import time
import serial
import socketio
import asyncio
import jwt
from dataclasses import dataclass
from .area.game_areas import GameArea, StopArea
from .area.area_methods import inside_area_effect, distance_to_border


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


class GPSSocket:

    sio = socketio.AsyncClient()
    secret = "asd"

    def __init__(self, url, robot_id, game_id):
        self.url = url
        self.robot_id = robot_id
        self.game_id = game_id
        self.game_areas = []
        self.stop_areas = []

    @sio.event(namespace='/robot')
    def boundary_data(self, data):
        print("Received data: ", data)
        if ( area['type'] == 'StopArea'):
            print("New Stop Area")
            self.stop_areas.append(StopArea(area))
        else:
            print("New Game Area")
            self.game_areas.append(GameArea(area))

    @sio.event(namespace='/robot')
    def all_boundary_data(self, data):
        print("Received data: ", data)
        for area in data:
            if ( area['type'] == 'StopArea'):
                print("New Stop Area")
                self.stop_areas.append(StopArea(area))
            else:
                print("New Game Area")
                self.game_areas.append(GameArea(area))
    
    @sio.event(namespace='/robot')
    def remove_boundary(self, data):
        for area in self.game_areas:
            if ( area.area_id == data['id']):
                self.game_areas.remove(area)
                break
        for area in self.stop_areas:
            if ( area.area_id == data['id']):
                self.stop_areas.remove(area)
                break
    
    @sio.event(namespace='/robot')
    def distance_to_area(self, data):
        area = self.get_area(data)
        if area :
            dist = distance_to_border(area, loc)
            self.sio.emit('distance_to_area', dist, namespace='/robot')
    
    @sio.event(namespace='/robot')
    def inside_area(self, data):
        area = self.get_area(data)
        if area :
            effect = inside_area_effect(area, loc)
            self.sio.emit('distance_to_area', effect, namespace='/robot')

    def get_area(self, data):
        for area in self.game_areas:
            if ( area.area_id == data['id']):
                return area
        for area in self.stop_areas:
            if ( area.area_id == data['id']):
                return area
        return False

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
        self.sio.on("boundary_data", self.boundary_data, namespace='/robot')
        self.sio.on("all_boundary_data", self.all_boundary_data, namespace='/robot')
        self.sio.on("remove_boundary", self.remove_boundary, namespace='/robot')
        self.sio.on("distance_to_area", self.distance_to_area, namespace='/robot')
        self.sio.on("inside_area", self.inside_area, namespace='/robot')

        # For testing locally
        if "localhost" not in self.url:
            self.get_query_url(self.url)
        print(self.url)
        await self.sio.connect(self.url, namespaces=['/robot'])

    async def disconnect(self):
        await self.sio.disconnect()


class GPSSensor:
    """Do not implement __init__, as this is more convinient for the users"""

    testing = False

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
            return GPSData(5, 15, -10000)
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
                except (ValueError, IndexError) as e:
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
        # "http://localhost:9090"
        socket = GPSSocket("http://localhost:9010", 123456, "0")
        gps_sensor = MyGPSSensor(socket)

        # Create new task and add it to the event loop
        event_loop = asyncio.get_event_loop()
        task = event_loop.create_task(gps_sensor.run(1))

        # get GPS updates for 30s according to the set polling rate
        await asyncio.sleep(30)
        await gps_sensor.post_run()
        print("main loop ended")

        await gps_sensor.disconnect()

    asyncio.run(main())

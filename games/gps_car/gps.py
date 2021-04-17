import serial
import socketio
import asyncio
from dataclasses import dataclass
from .area.game_areas import GameArea
from .area.area_methods import inside_area_effect, distance_to_border


"""
General:
 - Python version 3.7
 - Socketio version 4.6.1
 - use python-socketio's async client for the communication:
 https://python-socketio.readthedocs.io/en/latest/api.html#asyncclient-class
 https://github.com/miguelgrinberg/python-socketio
 -pyserial
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

    lon: float
    lat: float
    alt: float


class GPSSocket:

    sio = socketio.AsyncClient()
    secret = "asd"

    def __init__(self, url, robot_id, game_id):
        self.url = url
        self.robot_id = robot_id
        self.game_id = game_id
        self.game_areas = []

    @sio.event(namespace="/robot")
    def boundary_data(self, data):
        # if area id exists, update
        print("Received single data: ", data)
        for area in self.game_areas:
            if area.area_id == data["uuid"]:
                print("Override old area: ", area.area_id)
                self.game_areas.remove(area)
        self.game_areas.append(GameArea(data))

    @sio.event(namespace="/robot")
    def all_boundary_data(self, data):
        print("Received data: ", data)
        for area in data:
            self.game_areas.append(GameArea(area))

    @sio.event(namespace="/robot")
    def remove_boundary(self, id):
        for area in self.game_areas:
            if area.area_id == id:
                print(
                    "Remove area: ", area.area_id, " and label: ", area.label
                )
                self.game_areas.remove(area)
                break

    # Not used
    @sio.event(namespace="/robot")
    def distance_to_area(self, id):
        for area in self.game_areas:
            if area.area_id == id:
                print("Distance to area!")
                dist = distance_to_border(area, self.latest_loc)
                self.sio.emit("distance_to_area", dist, namespace="/robot")
                break

    # Not used
    @sio.event(namespace="/robot")
    def inside_area(self, id):
        for area in self.game_areas:
            if area.area_id == id:
                print("Inside an area!")
                effect = inside_area_effect(area, self.latest_loc)
                self.sio.emit("inside_area", effect, namespace="/robot")
                break

    async def get_query_url(self, url):
        """
        data = {
            "role": "location",
            "gameId": self.game_id,
            "robotId": self.robot_id,
        }
        encoded_jwt = jwt.encode(data, self.secret, algorithm="HS256")
        """
        self.url += f"?token={self.token}"

    async def send_data(self, data):
        x = {
            "robot_id": self.robot_id,
            "alt": data.alt,
            "long": data.lon,
            "lat": data.lat,
        }
        await self.sio.emit("location_data", x, namespace="/robot")

    async def connect(self):
        # Link the handler to the GPSSocket class, allows the use of 'self'
        self.sio.on("boundary_data", self.boundary_data, namespace="/robot")
        self.sio.on(
            "all_boundary_data", self.all_boundary_data, namespace="/robot"
        )
        self.sio.on(
            "remove_boundary", self.remove_boundary, namespace="/robot"
        )
        self.sio.on(
            "distance_to_area", self.distance_to_area, namespace="/robot"
        )
        self.sio.on("inside_area", self.inside_area, namespace="/robot")

        # For testing locally
        if "localhost" not in self.url:
            await self.get_query_url(self.url)

        await self.sio.connect(self.url, namespaces=["/robot"])

    async def disconnect(self):
        await self.sio.disconnect()


class GPSSensor:
    """Do not implement __init__, as this is more convenient for the users"""

    testing = False
    gps_fix_lost = False
    num_of_errors = 0
    latest_loc = GPSData(1000, 1000, 1000)

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

        After connect, this method should be called
        according to the polling rate (can be async def if needed)
        """
        if self.testing:
            return GPSData(5, 15, -10000)

        while True:
            # TEST what happens when you remove gps module during game.
            gpsData = str(self.ser.readline())
            if len(gpsData) < 5:
                print("GPS Problem")
                raise RuntimeError("GPS Problem")
            if "$GPGGA" in gpsData:
                try:

                    """Parse the data from the sensor and convert the elements
                    to a correct format"""
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
                    self.latest_loc = GPSData(latDec, longDec, alt)
                    self.num_of_errors = 0

                    return GPSData(latDec, longDec, alt)
                except (ValueError, IndexError):
                    self.num_of_errors += 1
                    if self.num_of_errors < 5 and self.latest_loc:
                        return self.latest_loc
                    else:
                        return GPSData(1000, 1000, 1000)

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

        socket = GPSSocket("https://gps.surrogate.tv:3002", 123456, "0")
        gps_sensor = MyGPSSensor(socket)

        # Create new task and add it to the event loop
        event_loop = asyncio.get_event_loop()
        event_loop.create_task(gps_sensor.run(1))

        # get GPS updates for 30s according to the set polling rate
        await asyncio.sleep(10)
        await gps_sensor.post_run()
        print("main loop ended")

        await gps_sensor.disconnect()

    asyncio.run(main())

import asyncio
import socketio
from aiohttp import web

# import jwt
# Test server for a gps game
sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)
NAMESPACE = "/robot"

secret = "asd"

props1 = {"prop1": "empty", "slowing_factor": "3"}

props2 = {"prop1": "empty", "disables_inputs": True}

dataJSON = {
    "uuid": "1",
    "label": "test_area",
    "type": "StopArea",
    "area": [
        [60.168811, 24.774154],
        [60.168569, 24.774197],
        [60.168445, 24.774725],
        [60.169048, 24.774696],
    ],
    "props": props1,
}

dataJSONTWO = {
    "uuid": "2",
    "label": "test_area2",
    "type": "GameArea",
    "area": [
        [60.169265, 24.775230],
        [60.168509, 24.775541],
        [60.168579, 24.776485],
        [60.169150, 24.776109],
    ],
    "props": props2,
}
all_data = [dataJSON, dataJSONTWO]


@sio.event(namespace=NAMESPACE)
def connect(sid, environ):
    print("connect ", sid)
    asyncio.run_coroutine_threadsafe(
        sio.emit("all_boundary_data", all_data, namespace=NAMESPACE),
        asyncio.get_event_loop(),
    )


@sio.event(namespace=NAMESPACE)
async def location_data(sid, data):
    print(f"received data :{data}")


@sio.event(namespace=NAMESPACE)
def disconnect(sid):
    print("disconnect ", sid)


if __name__ == "__main__":
    web.run_app(app, port=9010)

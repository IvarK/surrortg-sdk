import asyncio
import socketio
import jwt
from aiohttp import web

#Test server for a gps game
sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)

secret = "asd"
dataJSON = {
    'uuid': "1337",
    'label': 'test_area',
    'area': [[0,0],[0, 10], [10,10], [10,0]],
    'props': 'no_props'
}

@sio.event(namespace='/robot')
def connect(sid, environ):
    print('connect ', sid)
    asyncio.run_coroutine_threadsafe(
        sio.emit('boundary_data', {'data': dataJSON}, namespace='/robot'),
        asyncio.get_event_loop(),
    )

@sio.event(namespace='/robot')
async def location_data(sid, data):
    print(f"received data :{data}")

@sio.event(namespace='/robot')
def disconnect(sid):
    print('disconnect ', sid)

if __name__ == "__main__":
    web.run_app(app, port=9090)

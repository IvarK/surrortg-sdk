import asyncio
import socketio
from aiohttp import web

#Test server for a gps game
sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)

areaData = [(1,1),(-1, 1), (-1,-1), (1,-1)]

@sio.event
def connect(sid, environ):
    print('connect ', sid)
    asyncio.run_coroutine_threadsafe(
        sio.emit('boundary_data', {'data': areaData}),
        asyncio.get_event_loop(),
    )

@sio.event
async def update_location(sid, data):
    print(f"received data :{data}")

@sio.event
def disconnect(sid):
    print('disconnect ', sid)

if __name__ == "__main__":
    web.run_app(app, port=9090)

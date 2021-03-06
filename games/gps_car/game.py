from games.gps_car.gps import GPSSocket
from games.gps_car.gps import GPSSensor
from games.gps_car.area.area_methods import inside_area_effect
from surrortg import Game  # First we need import the Game
from surrortg.inputs import LinearActuator  # and our preferred input(s)
import pigpio
import logging
import asyncio

MOTOR_PIN = 16
SERVO_PIN = 12


class PwmActuator(LinearActuator):
    """PwmActuator acts as controller for ESC and
    steering servo that take standard pwm servo input

    It receives values -1 ... 1 and maps that to matching
    pwm pulsewidth value where 0 input maps to 1500 pulsewidth.
    This correlates to middle position on servos, and 0 on a
    ESC.

    :param pi: instance of pigpio gpio control class
    :param pin: GPIO pin number to output the pwm signal
    :type pin: int
    :param: delta_max: Maximum value of pulsewidth dirrence
        from the middle (1500) position. Default value of 300
        translates to range of 1200 ... 1800. Be careful with this
        value as overturning servo might cause physical damage to
        the servo or the device it is attached to.
    :type delta_max: int
    :param calibration: Pulsewidth value that modifies the
        middle position used for operating. Default value 0 does
        not alter the 1500 middle position. This value can be used
        to fine tune the steering servo so that the wheels of the car
        are straight with the middle value.

    :var middle: Middle position used for 0 input mapping.
        Defaults to 1500 and adds the calibration value to itself.
    :var current_delta: Active value that is used to control
        the actuator. Defaults to half of delta_max, and can be
        modified with increase_delta and reduce_delta methods.
    """

    def __init__(self, pi, pin, delta_max=300, calibration=0):
        self.middle = 1500 + calibration
        self.delta_max = delta_max
        self.current_delta = delta_max / 2
        # Store and initialize pigpio for the control pin
        self.latest_val = 0
        self.pi = pi
        self.pin = pin
        self.pi.set_mode(self.pin, pigpio.OUTPUT)
        self.pi.set_servo_pulsewidth(self.pin, self.middle)
        """  You can also change the pwm frequency
            if your use case requires it. More at:
            http://abyz.me.uk/rpi/pigpio/python.html#set_PWM_frequency """
        # self.pi.set_PWM_frequency(self.pin, <value>)

    async def drive_actuator(self, val, seat=0):
        """This function is called when input is received.
        It maps -1 ... 1 value to corresponding pulsewidth
        value. For example value -1 translates to 1500 (middle)
        minus current_delta which would be 1350 with default values.

        :param val: float value from ranging -1 to 1. If keyboard
            input is used it will be -1, 0 or 1.
        """
        self.latest_val = val
        new_val = self.middle + (val * self.current_delta)
        self.pi.set_servo_pulsewidth(self.pin, new_val)

    async def increase_delta(self, inc):
        """Method that is called from ShiftGear class to
        increase throttle or steering value. Changing the
        value will take effect only, after the input is
        cycled off-on once (release and press key).

        :param inc: Amount to increase the current_delta value
        type: inc: int"""
        if (self.current_delta + inc) <= self.delta_max:
            self.current_delta += inc
            logging.info(
                f"current gear ratio {self.current_delta/self.delta_max}"
            )

    async def reduce_delta(self, inc):
        """Method that is called from ShiftGear class to
        decrease throttle or steering value. Changing the
        value will take effect only, after the input is
        cycled off-on once (release and press key).

        :param: inc: Amount to decrease the current_delta value
        :type: inc: int"""
        if (self.current_delta - inc) > 0:
            self.current_delta -= inc
            logging.info(
                f"current gear ratio {self.current_delta/self.delta_max}"
            )


class ShiftGear(LinearActuator):
    """Virtual actuator class that implements shifting gears or
    adjusting the amount of steering.

    :param: actuator: Instance of PwmActuator to be modified
    :param: inc: Amount of pulsewidth to modify with each shifting.
        Defaults to 10.
    :type: inc: Int
    """

    def __init__(self, actuator, inc=10):
        self.actuator = actuator
        self.increment = inc

    async def drive_actuator(self, val, seat=0):
        """Driving this virtual actuator increases the value
        of the connected actuator if the input is positive value,
        and decreases the value if it is negative. Off position
        (0) does nothing."""
        if val < 0:
            await self.actuator.reduce_delta(self.increment)
        elif val > 0:
            await self.actuator.increase_delta(self.increment)


class MyGPSSensor(GPSSensor):
    def __init__(self, gps_socket, io, motor):
        self.gps_socket = gps_socket
        self.io = io
        self.motor = motor
        self.inputs_enabled = (
            True  # call enable/disable inputs only when needed
        )
        self.gear = 0  # counter for slowing down/speeding back up

    async def on_data(self, data):

        """Loop over the Game areas"""
        player_speed_modified = False
        player_inputs_disabled = False
        print("ROBOT LOCATION: ", data.lat, data.lon)
        for game_area in self.gps_socket.game_areas:
            effects_robot = inside_area_effect(game_area, data)
            if effects_robot:
                await game_area.player_in_area(self)
                if game_area.slowing_factor > 0:
                    player_speed_modified = True
                if self.gear > -game_area.slowing_factor:
                    await ShiftGear(self.motor).drive_actuator(-1, seat=0)
                    self.gear -= 1
                    # player_speed_modified = True
                    print("Player speed decreasing!")
                    # If player enters area for the first time
                    if not game_area.player_inside:
                        await self.motor.drive_actuator(
                            self.motor.latest_val * 0.75, seat=0
                        )
                        game_area.player_inside = True

                if game_area.disables_inputs:
                    player_inputs_disabled = True

                if game_area.disables_inputs and self.inputs_enabled:
                    self.io.disable_input(0)  # disables inputs
                    await self.motor.drive_actuator(0, seat=0)  # stop the car
                    self.inputs_enabled = False

            else:
                # Player is outside the area effect, reset boolean to False
                game_area.player_inside = False

        """Player is not effected by input disabling area, enable inputs"""
        if (
            not self.inputs_enabled
            and not player_inputs_disabled
            and not self.gps_fix_lost
        ):
            self.io.enable_input(0)  # enables inputs
            self.inputs_enabled = True

        """Player speed is not modified, raise speed to normal"""
        if not player_speed_modified and self.gear < 0:
            print("Player speed increasing!")
            await ShiftGear(self.motor).drive_actuator(1, seat=0)
            await self.motor.drive_actuator(self.motor.latest_val, seat=0)
            self.gear += 1

    async def pre_run(self):
        """
        Sleep for 2 so the game class has time to set up on_config and
        the socket connection can get the JWT token from the GE.
        This should probably be replaced with something else with other
        games, in case the game specific config takes longer to load.
        """
        await asyncio.sleep(2)
        await self.gps_socket.connect()
        await self.connect()

    async def post_run(self):
        await self.gps_socket.disconnect()

    async def run(self, polling_rate):
        await self.pre_run()
        while True:
            loc = self.get_data()
            if loc.lat == 1000 and loc.lon == 1000:
                self.gps_fix_lost = True
            else:
                self.gps_fix_lost = False

            if self.gps_fix_lost and self.inputs_enabled:
                print("gps fix lost, disabling inputs")
                self.io.disable_input(0)  # disables inputs
                await self.motor.drive_actuator(0, seat=0)  # stop the car
                self.inputs_enabled = False
                # Maybe emit message that robot has lost gps fix
            else:
                await self.gps_socket.send_data(loc)
                await self.on_data(loc)

            await asyncio.sleep(polling_rate)


class CarGame(Game):
    async def on_init(self):

        """First initialize the pigpio class. For this you have to have
        pigpio installed on your system and the pigpiod daemon running!"""
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("Could not connect to pigpio")

        """Here we initialize our actuators with correct gpio pins
        and values.
        motor controls 1 ESC with 1 pwm signal
        steering controls 1 servo with 1 pwm signal
        throttle_shifting modifies the used speed (pwm signal) of the motor
        steering_shifting modifies the used turning angle (pwm signal) of the
        servo
        """
        self.motor = PwmActuator(self.pi, MOTOR_PIN, 250)
        self.steering = PwmActuator(self.pi, SERVO_PIN, 400)
        self.throttle_shifting = ShiftGear(self.motor)
        self.steering_shifting = ShiftGear(self.steering)
        """ During the Game initialization callback register your motor
        and steering so the Game Engine knows where to send the user input
        during the games. As we want to use also the shifting functionality
        in the game we must register those inputs to be used from the game
        as well. """
        self.io.register_inputs(
            {
                "motor": self.motor,
                "steering": self.steering,
                "throttle_shifting": self.throttle_shifting,
                "steering_shifting": self.steering_shifting,
            }
        )

        # create gpsSocket and custom GPSSensor
        # http://localhost:9090'
        # print("GAME ID OF CONFIG: ", self.io._config["game_engine"]["id"])

        self.gps_socket = GPSSocket(
            "https://gps.surrogate.tv:3002",
            self.io._config["device_id"],
            self.io._config["game_engine"]["id"],
        )  # pass all required parameters here
        self.gps_sensor = MyGPSSensor(self.gps_socket, self.io, self.motor)
        # Create new task
        self.task = asyncio.create_task(self.gps_sensor.run(1))
        # Add a done callback
        self.task.add_done_callback(self.run_done_cb)

    async def on_config(self):

        # Get the JWT token for GPSSocket class
        self.gps_socket.token = self._configs.get("locationServiceToken")

    async def run_done_cb(self, fut):
        # make program end if GPSSensor's run() raises errors
        if not fut.cancelled() and fut.exception() is not None:
            import traceback
            import sys

            # If the game ends stop the motor manually
            # Otherwise car keeps on driving
            await self.motor.drive_actuator(0, seat=0)
            e = fut.exception()
            logging.error(
                "".join(traceback.format_exception(None, e, e.__traceback__))
            )
            sys.exit(1)

    async def on_exit(self, reason, exception):
        self.task.cancel()
        await self.gps_sensor.disconnect()
        await self.gps_socket.post_run()
        await self.motor.shutdown()
        await self.steering.shutdown()
        self.pi.stop()


# And now you are ready to play!
if __name__ == "__main__":
    CarGame().run()

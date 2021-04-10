""""
Methods in these classes should have access to the motor object in order to
change the speed of the robot.
Individual instances of this class need a 'label' attribute.
"""


class GameArea:

    """
    Attributes:
        -id
        -label
        -coordinates
        -Props
    """

    def __init__(self, data):
        self.area_id = data["uuid"]
        self.label = data["label"]
        self.area = data["area"]
        self.player_inside = False
        self.helper(data.get("props", {}))
        print("Game Area id: ", self.area_id)
        print("Game Area attributes: ", self.slowing_factor, self.reversed)

    def __eq__(self, other):
        return self.area_id == other.area_id

    def helper(self, properties):
        """look over the properties and add them"""
        self.reversed = properties.get("reversed", False)
        self.slowing_factor = properties.get("slowing_factor", 0)
        self.disables_inputs = properties.get("disables_inputs", False)

    async def player_in_area(self, custom_gps):
        """
        Method to decrease or increase the robot speed,
        give points to the player, etc.
        Can be called every cycle.
        """
        """
        if custom_gps.gear > -self.slowing_factor:
            await ShiftGear(custom_gps.motor).drive_actuator(-1, seat=0)
            custom_gps.gear -= 1

        if self.disables_inputs and custom_gps.inputs_enabled:
            custom_gps.io.disable_input(0)  # disables inputs
            await custom_gps.motor.drive_actuator(0, seat=0)  # stop the car
            custom_gps.inputs_enabled = False
        """


class CustomArea(GameArea):

    """
    Attributes:
        -id
        -label
        -coordinates
        -reversed (boolean)
    """

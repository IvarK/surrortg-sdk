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
        -reversed (boolean)
        -slowing factor
    """

    def __init__(self, data):
        self.area_id = data["uuid"]
        self.label = data["label"]
        self.area = data["area"]
        self.helper(data["props"])
        print("Game Area attributes: ", self.slowing_factor, self.reversed)

    def __eq__(self, other):
        return self.area_id == other.area_id

    def helper(self, properties):
        """look over the properties and add them"""
        self.reversed = properties.get("reversed", False)
        self.slowing_factor = properties.get("slowing_factor", 0)

    def player_in_area(self, socket):

        """
        Method to decrease or increase the robot speed,
        give points to the player, etc.
        Will be called every cycle.
        """
        pass


class StopArea(GameArea):

    """
    Attributes:
        -id
        -label
        -coordinates
        -reversed (boolean)
    """

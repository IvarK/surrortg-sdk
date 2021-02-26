
""""
Methods in these classes should have access to the motor object in order to change the speed of the robot.
Individual instances of this class need a 'label' attribute.
"""

class StopArea():

    """
    Attributes:
        -id
        -label
        -coordinates
        -reversed (boolean)
    """
    def __init__(self, data):
        self.area_id = data['uuid']
        self.label = data['label']
        self.area = data['area']
        self.reversed = False
        self.helper(data['props'])
        print("Stop Area attributes: ", self.reversed)

    def __eq__(self, other):
        return self.area_id == other.area_id

    def helper(self, properties):
        print(properties)
        try:
            if (properties['reversed'] == 'true'):
                self.reversed = True
        except KeyError:
            pass


    def player_in_area(self, socket):
        """
        Method to decrease or increase the robot speed, give points to the player, etc.
        Will be called every cycle.
        """
        pass

class GameArea():

    """
    Attributes:
        -id
        -label
        -coordinates
        -reversed (boolean)
        -slowing factor
    """

    def __init__(self, data):
        self.area_id = data['uuid']
        self.label = data['label']
        self.area = data['area']
        self.reversed = False
        self.slowing_factor = 0
        self.helper(data['props'])
        print("Game Area attributes: ", self.slowing_factor, self.reversed)

    def __eq__(self, other):
        return self.area_id == other.area_id

    def helper(self, properties):
        """look over the properties and add them"""
        print(properties)
        try:
            if (properties['reversed'] == 'true'):
                self.reversed = True
        except KeyError:
            print('KeyError')
            pass
        try:
            if (properties['slowing_factor']):
                self.slowing_factor = int(properties['slowing_factor'])
        except KeyError:
            print('KeyError')
            pass

    def player_in_area(self, socket):
        
        """
        Method to decrease or increase the robot speed, give points to the player, etc.
        Will be called every cycle.
        """
        pass


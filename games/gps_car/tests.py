import unittest
from .area.game_areas import GameArea
from .area.area_methods import inside_area_effect, distance_to_border
from .gps import GPSData

"""Simple unittests using Töölönlahti as area"""
test_area = [
    [24.9310255, 60.1786389],
    [24.9311113, 60.1784895],
    [24.931798, 60.1777852],
    [24.9326992, 60.1773157],
    [24.9339437, 60.1771876],
    [24.9352741, 60.1773797],
    [24.9366045, 60.1779346],
    [24.937892, 60.1789377],
    [24.9379349, 60.1801328],
    [24.9366045, 60.1810504],
    [24.9357462, 60.1817973],
    [24.93536, 60.1828643],
    [24.9351883, 60.1838885],
    [24.9344158, 60.184614],
    [24.9331284, 60.1842726],
    [24.932313, 60.1837605],
    [24.9321842, 60.1829496],
    [24.9318838, 60.1819254],
    [24.9314117, 60.1804742],
    [24.9317122, 60.1794285],
    [24.9310255, 60.1786389],
]

testArea = {
    "uuid": "1",
    "label": "unit_test",
    "type": "GameArea",
    "area": test_area,
}

test_location_true = GPSData(24.9344587, 60.1799407, 0)
test_location_true2 = GPSData(24.9343729, 60.1841233, 0)
test_location_false = GPSData(24.9311543, 60.1794712, 0)

area = GameArea(testArea)

paris = GPSData(2.3522, 48.8566, 0)
brisbane = GPSData(153.021072, -27.470125, 0)


props1 = {"slowing_factor": 3}
props2 = {"slowing_factor": 2, "reversed": True}
props3 = {"disables_inputs": True, "reversed": True}
props4 = {"disables_inputs": True, "reversed": False}


data_one = {
    "uuid": "1",
    "label": "test_area",
    "type": "Area slows when inside",
    "area": [[0, 0], [0, 5], [5, 5], [5, 0]],
    "props": props1,
}

data_two = {
    "uuid": "2",
    "label": "test_area2",
    "type": "Area slows when outside",
    "area": [[-10, -10], [-10, 10], [10, 10], [10, -10]],
    "props": props2,
}

data_three = {
    "uuid": "3",
    "label": "test_area2",
    "type": "Area disables inputs when outside",
    "area": [[-20, -20], [-20, 20], [20, 20], [20, -20]],
    "props": props3,
}

data_four = {
    "uuid": "4",
    "label": "test_area2",
    "type": "Area disables inputs when inside",
    "area": [[5, 5], [5, 10], [10, 10], [10, 5]],
    "props": props4,
}

area_one = GameArea(data_one)
area_two = GameArea(data_two)
area_three = GameArea(data_three)
area_four = GameArea(data_four)

location_false = GPSData(50, 50, 0)
location_one = GPSData(2.5, 2.5, 0)
location_two = GPSData(7.5, 7.5, 0)


class TestGPSArea(unittest.TestCase):
    def test_in_valid_area(self):
        self.assertEquals(inside_area_effect(area, test_location_true), True)
        self.assertEquals(inside_area_effect(area, test_location_true2), True)
        self.assertEquals(inside_area_effect(area, test_location_false), False)

    def test_distance_to_border(self):
        self.assertAlmostEqual(
            distance_to_border(area, paris), 1909000, delta=5000
        )
        self.assertAlmostEqual(
            distance_to_border(area, brisbane), 14705000, delta=5000
        )

    def test_area_one(self):
        self.assertEquals(area_one.disables_inputs, False)
        self.assertEquals(area_one.reversed, False)
        self.assertEquals(area_one.slowing_factor, 3)
        self.assertEquals(inside_area_effect(area_one, location_false), False)
        self.assertEquals(inside_area_effect(area_one, location_one), True)

    def test_area_two(self):
        self.assertEquals(area_two.disables_inputs, False)
        self.assertEquals(area_two.reversed, True)
        self.assertEquals(area_two.slowing_factor, 2)
        self.assertEquals(inside_area_effect(area_two, location_false), True)
        self.assertEquals(inside_area_effect(area_two, location_one), False)

    def test_area_three(self):
        self.assertEquals(area_three.disables_inputs, True)
        self.assertEquals(area_three.reversed, True)
        self.assertEquals(area_three.slowing_factor, 0)
        self.assertEquals(inside_area_effect(area_three, location_false), True)
        self.assertEquals(inside_area_effect(area_three, location_one), False)

    def test_area_four(self):
        self.assertEquals(area_four.disables_inputs, True)
        self.assertEquals(area_four.reversed, False)
        self.assertEquals(area_four.slowing_factor, 0)
        self.assertEquals(inside_area_effect(area_four, location_false), False)
        self.assertEquals(inside_area_effect(area_four, location_one), False)
        self.assertEquals(inside_area_effect(area_four, location_two), True)


if __name__ == "__main__":
    unittest.main()

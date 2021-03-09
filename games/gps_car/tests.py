import unittest
from area.game_areas import GameArea
from area.area_methods import inside_area_effect, distance_to_border
from gps import GPSData

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


if __name__ == "__main__":
    unittest.main()

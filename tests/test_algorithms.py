import unittest
import pandas as pd
from algorithms.parser import parse_and_validate_dataset
from algorithms.greedy import run_greedy_allocation
from algorithms.knapsack import run_knapsack_allocation, solve_knapsack_for_slot

class TestAlgorithms(unittest.TestCase):
    
    def setUp(self):
        # Sample valid standard dataset
        self.valid_data = (
            "AdvertisementID,Duration,Budget,Priority,PreferredSlot\n"
            "AD001,30,5000,8,Morning\n"
            "AD002,45,8500,9,PrimeTime\n"
            "AD003,60,12000,7,Evening\n"
            "AD004,20,3500,5,Morning\n"
        )

    def test_parser_valid(self):
        df = parse_and_validate_dataset(self.valid_data)
        self.assertEqual(len(df), 4)
        self.assertIn('AdvertisementID', df.columns)
        self.assertIn('Duration', df.columns)
        self.assertIn('Budget', df.columns)
        
    def test_parser_invalid_columns(self):
        bad_data = "AdID,Dur,Bud\nAD001,30,500"
        with self.assertRaises(ValueError):
            parse_and_validate_dataset(bad_data)
            
    def test_parser_negative_values(self):
        bad_data = (
            "AdvertisementID,Duration,Budget,Priority,PreferredSlot\n"
            "AD001,-30,5000,8,Morning\n"
        )
        with self.assertRaises(ValueError):
            parse_and_validate_dataset(bad_data)
            
    def test_parser_duplicate_ids(self):
        bad_data = (
            "AdvertisementID,Duration,Budget,Priority,PreferredSlot\n"
            "AD001,30,5000,8,Morning\n"
            "AD001,45,8500,9,PrimeTime\n"
        )
        with self.assertRaises(ValueError):
            parse_and_validate_dataset(bad_data)


    def test_greedy_algorithm(self):
        df = parse_and_validate_dataset(self.valid_data)
        result = run_greedy_allocation(df)
        self.assertIn('ads', result)
        self.assertIn('metrics', result)
        # Check that we got allocations
        self.assertGreater(result['metrics']['allocated_count'], 0)
        
    def test_knapsack_solver(self):
        # standard simple knapsack check
        weights = [10, 20, 30]
        values = [60.0, 100.0, 120.0]
        capacity = 50
        max_val, indices = solve_knapsack_for_slot(weights, values, capacity)
        self.assertEqual(max_val, 220.0)
        self.assertEqual(set(indices), {1, 2}) # 20 and 30 weight items selected

    def test_knapsack_algorithm(self):
        df = parse_and_validate_dataset(self.valid_data)
        result = run_knapsack_allocation(df)
        self.assertIn('ads', result)
        self.assertIn('metrics', result)
        self.assertGreater(result['metrics']['allocated_count'], 0)


if __name__ == '__main__':
    unittest.main()

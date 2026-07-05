import unittest
import pandas as pd
from algorithms.parser import parse_and_validate_dataset, parse_time_to_minutes
from algorithms.greedy import run_greedy_allocation
from algorithms.knapsack import run_knapsack_allocation, solve_knapsack_for_slot
from algorithms.interval import run_interval_allocation, solve_weighted_interval_scheduling

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
        
        # Sample interval dataset
        self.interval_data = (
            "AdvertisementID,Duration,Budget,Priority,PreferredSlot,StartTime,EndTime\n"
            "AD001,30,5000,8,Morning,09:00,09:30\n"
            "AD002,45,8500,9,PrimeTime,21:00,21:45\n"
            "AD003,20,3500,5,Morning,09:20,09:40\n"
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

    def test_time_parsing(self):
        self.assertEqual(parse_time_to_minutes("09:30"), 570)
        self.assertEqual(parse_time_to_minutes("00:00"), 0)
        self.assertEqual(parse_time_to_minutes("24:00"), 1440)
        self.assertIsNone(parse_time_to_minutes("invalid-time"))

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

    def test_interval_scheduling_solver(self):
        # test compatibility resolving
        intervals = [
            {'start_min': 0, 'end_min': 10, 'budget': 50},
            {'start_min': 5, 'end_min': 15, 'budget': 100}, # overlaps
            {'start_min': 10, 'end_min': 20, 'budget': 50}
        ]
        # Sort by end times
        intervals.sort(key=lambda x: x['end_min'])
        selected = solve_weighted_interval_scheduling(intervals)
        # Optimal should select index 0 and 2 (total budget = 100) instead of index 1 (budget = 100)
        # because 0 and 2 do not overlap and sum to 100, wait. Both options give 100 budget.
        # But if index 1 had budget 90, 0 & 2 would be strictly better.
        # Let's change weights to make 0 and 2 strictly better:
        intervals[0]['budget'] = 60
        intervals[1]['budget'] = 100
        intervals[2]['budget'] = 60
        selected = solve_weighted_interval_scheduling(intervals)
        self.assertEqual(len(selected), 2)
        # The indices in sorted list:
        # intervals[0] (end 10) -> index 0
        # intervals[1] (end 15) -> index 1
        # intervals[2] (end 20) -> index 2
        # selected indices should be 0 and 2
        self.assertEqual(set(selected), {0, 2})

    def test_interval_algorithm(self):
        df = parse_and_validate_dataset(self.interval_data)
        result = run_interval_allocation(df)
        self.assertIn('ads', result)
        self.assertIn('metrics', result)
        self.assertGreater(result['metrics']['allocated_count'], 0)

if __name__ == '__main__':
    unittest.main()

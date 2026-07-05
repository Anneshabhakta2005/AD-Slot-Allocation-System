import time
from typing import Dict, Any
from .greedy import run_greedy_allocation
from .knapsack import run_knapsack_allocation
from .interval import run_interval_allocation

def run_allocation(ads_df, algorithm: str) -> Dict[str, Any]:
    """
    Orchestrates the running of the selected algorithm.
    Measures execution time and runs benchmarking for comparison.
    """
    algorithm = algorithm.lower().strip()
    
    # 1. Run the main selected algorithm and measure time
    start_time = time.perf_counter()
    if algorithm == 'greedy':
        result = run_greedy_allocation(ads_df)
    elif algorithm == 'knapsack':
        result = run_knapsack_allocation(ads_df)
    elif algorithm == 'interval':
        result = run_interval_allocation(ads_df)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    end_time = time.perf_counter()
    
    execution_time_ms = (end_time - start_time) * 1000.0
    result['metrics']['execution_time_ms'] = execution_time_ms
    result['metrics']['algorithm_name'] = algorithm.capitalize()
    
    # 2. Run the other algorithms in background for comparison metrics
    comparisons = {}
    
    # Greedy comparison
    if algorithm == 'greedy':
        comparisons['greedy'] = {
            'revenue': result['metrics']['total_revenue'],
            'time_ms': execution_time_ms,
            'allocated': result['metrics']['allocated_count'],
            'rejected': result['metrics']['rejected_count'],
            'unused_mins': result['metrics']['total_unused_time']
        }
    else:
        st = time.perf_counter()
        g_res = run_greedy_allocation(ads_df)
        et = time.perf_counter()
        comparisons['greedy'] = {
            'revenue': g_res['metrics']['total_revenue'],
            'time_ms': (et - st) * 1000.0,
            'allocated': g_res['metrics']['allocated_count'],
            'rejected': g_res['metrics']['rejected_count'],
            'unused_mins': g_res['metrics']['total_unused_time']
        }
        
    # Knapsack comparison
    if algorithm == 'knapsack':
        comparisons['knapsack'] = {
            'revenue': result['metrics']['total_revenue'],
            'time_ms': execution_time_ms,
            'allocated': result['metrics']['allocated_count'],
            'rejected': result['metrics']['rejected_count'],
            'unused_mins': result['metrics']['total_unused_time']
        }
    else:
        st = time.perf_counter()
        k_res = run_knapsack_allocation(ads_df)
        et = time.perf_counter()
        comparisons['knapsack'] = {
            'revenue': k_res['metrics']['total_revenue'],
            'time_ms': (et - st) * 1000.0,
            'allocated': k_res['metrics']['allocated_count'],
            'rejected': k_res['metrics']['rejected_count'],
            'unused_mins': k_res['metrics']['total_unused_time']
        }
        
    # Interval comparison
    if algorithm == 'interval':
        comparisons['interval'] = {
            'revenue': result['metrics']['total_revenue'],
            'time_ms': execution_time_ms,
            'allocated': result['metrics']['allocated_count'],
            'rejected': result['metrics']['rejected_count'],
            'unused_mins': result['metrics']['total_unused_time']
        }
    else:
        st = time.perf_counter()
        i_res = run_interval_allocation(ads_df)
        et = time.perf_counter()
        comparisons['interval'] = {
            'revenue': i_res['metrics']['total_revenue'],
            'time_ms': (et - st) * 1000.0,
            'allocated': i_res['metrics']['allocated_count'],
            'rejected': i_res['metrics']['rejected_count'],
            'unused_mins': i_res['metrics']['total_unused_time']
        }
        
    result['comparisons'] = comparisons
    return result

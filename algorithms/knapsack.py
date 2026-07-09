from typing import List, Dict, Any
# pyrefly: ignore [missing-import]
import numpy as np
from .parser import SLOT_CONFIGS

def solve_knapsack_for_slot(weights: List[int], values: List[float], capacity: int):
    """
    Solves the 0/1 Knapsack problem using dynamic programming.
    Returns: (max_value, list of selected indices)
    """
    n = len(weights)
    if n == 0 or capacity == 0:
        return 0.0, []

    # Initialize DP matrix. Row: items, Col: capacity.
    # We round values to floats or cast to float, but using float values in DP is fine.
    # The DP state dp[i][w] represents max value using first i items with weight limit w.
    dp = np.zeros((n + 1, capacity + 1), dtype=float)

    for i in range(1, n + 1):
        w_i = weights[i-1]
        v_i = values[i-1]
        for w in range(1, capacity + 1):
            if w_i <= w:
                dp[i][w] = max(dp[i-1][w], v_i + dp[i-1][w - w_i])
            else:
                dp[i][w] = dp[i-1][w]

    # Traceback to find selected items
    selected_indices = []
    w = capacity
    for i in range(n, 0, -1):
        # We use a small epsilon tolerance to compare floating point budgets
        if dp[i][w] > dp[i-1][w] + 1e-5:
            selected_indices.append(i-1)
            w -= weights[i-1]

    # Return max value and selected indices (reversed to match original order)
    return float(dp[n][capacity]), selected_indices[::-1]


def run_knapsack_allocation(ads_df) -> Dict[str, Any]:
    """
    Runs the 0/1 Knapsack dynamic programming algorithm on the input DataFrame.
    Solves for each slot separately to maximize total revenue.
    """
    df = ads_df.copy()
    
    # Initialize allocation columns
    df['AllocatedSlot'] = 'None'
    df['Status'] = 'Rejected'
    df['AllocatedStartTime'] = 'N/A'
    df['AllocatedEndTime'] = 'N/A'

    slot_utilization = {slot: 0 for slot in SLOT_CONFIGS}
    slot_unused_time = {slot: config['capacity'] for slot, config in SLOT_CONFIGS.items()}
    total_revenue = 0

    # Process each slot independently
    for slot, config in SLOT_CONFIGS.items():
        capacity = config['capacity']
        start_min = config['start_min']
        
        # Filter ads that prefer this slot
        slot_ads = df[df['PreferredSlot'] == slot].copy()
        
        if slot_ads.empty:
            continue
            
        # Convert durations and budgets to lists
        # We cast durations to integers to index the DP table correctly
        durations = slot_ads['Duration'].round().astype(int).tolist()
        budgets = slot_ads['Budget'].astype(float).tolist()
        ad_indices = slot_ads.index.tolist()
        
        max_val, selected_local_indices = solve_knapsack_for_slot(durations, budgets, capacity)
        
        # Mark selected ads
        current_time_offset = 0
        for local_idx in selected_local_indices:
            global_idx = ad_indices[local_idx]
            duration = durations[local_idx]
            
            ad_start_min = start_min + current_time_offset
            ad_end_min = ad_start_min + duration
            
            start_h = ad_start_min // 60
            start_m = ad_start_min % 60
            end_h = ad_end_min // 60
            end_m = ad_end_min % 60
            
            start_time_str = f"{start_h:02d}:{start_m:02d}"
            end_time_str = f"{end_h:02d}:{end_m:02d}"
            
            df.at[global_idx, 'AllocatedSlot'] = slot
            df.at[global_idx, 'Status'] = 'Allocated'
            df.at[global_idx, 'AllocatedStartTime'] = start_time_str
            df.at[global_idx, 'AllocatedEndTime'] = end_time_str
            
            current_time_offset += duration
            total_revenue += budgets[local_idx]
            
        slot_utilization[slot] = current_time_offset
        slot_unused_time[slot] = capacity - current_time_offset

    processed_ads = df.to_dict(orient='records')
    
    return {
        'ads': processed_ads,
        'metrics': {
            'total_revenue': float(total_revenue),
            'slot_utilization': slot_utilization,
            'slot_unused_time': slot_unused_time,
            'total_unused_time': int(sum(slot_unused_time.values())),
            'allocated_count': int(df[df['Status'] == 'Allocated'].shape[0]),
            'rejected_count': int(df[df['Status'] == 'Rejected'].shape[0])
        }
    }

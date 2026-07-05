import hashlib
from typing import List, Dict, Any
from .parser import SLOT_CONFIGS, parse_time_to_minutes

def deterministic_hash_int(s: str) -> int:
    """Returns a deterministic integer hash for a string to seed interval generation."""
    return int(hashlib.md5(s.encode('utf-8')).hexdigest(), 16)

def generate_deterministic_intervals(df):
    """
    Checks if StartTime and EndTime columns exist and are fully populated.
    If not, deterministically generates plausible overlapping start/end times
    for ads based on their duration and preferred slot constraints.
    """
    df = df.copy()
    
    if 'StartTime' not in df.columns:
        df['StartTime'] = 'N/A'
    if 'EndTime' not in df.columns:
        df['EndTime'] = 'N/A'
        
    for idx, row in df.iterrows():
        st = row['StartTime']
        et = row['EndTime']
        
        # Check if we need to generate times
        if (st == 'N/A' or et == 'N/A' or 
            st == 'nan' or et == 'nan' or 
            not isinstance(st, str) or not isinstance(et, str) or
            st.strip() == '' or et.strip() == '' or st.strip().lower() == 'nan'):
            
            ad_id = row['AdvertisementID']
            slot = row['PreferredSlot']
            duration = int(round(row['Duration']))
            
            config = SLOT_CONFIGS[slot]
            slot_capacity = config['capacity']
            start_min = config['start_min']
            
            # If the duration exceeds slot capacity, we caps it
            if duration > slot_capacity:
                duration = slot_capacity
                df.at[idx, 'Duration'] = duration
                
            # Deterministic pseudo-random start offset
            h_val = deterministic_hash_int(ad_id)
            max_offset = slot_capacity - duration
            
            if max_offset > 0:
                # Add some variety so ads overlap. Using modulo arithmetic on the hash.
                start_offset = h_val % max_offset
            else:
                start_offset = 0
                
            ad_start_min = start_min + start_offset
            ad_end_min = ad_start_min + duration
            
            start_h = ad_start_min // 60
            start_m = ad_start_min % 60
            end_h = ad_end_min // 60
            end_m = ad_end_min % 60
            
            df.at[idx, 'StartTime'] = f"{start_h:02d}:{start_m:02d}"
            df.at[idx, 'EndTime'] = f"{end_h:02d}:{end_m:02d}"
            
    return df

def find_largest_compatible(intervals: List[Dict[str, Any]], index: int) -> int:
    """
    Finds the largest index j < index such that intervals[j] finishes
    before intervals[index] starts. Uses binary search for efficiency O(log N).
    Returns -1 if no such interval exists.
    """
    low = 0
    high = index - 1
    target_start = intervals[index]['start_min']
    
    ans = -1
    while low <= high:
        mid = (low + high) // 2
        if intervals[mid]['end_min'] <= target_start:
            ans = mid
            low = mid + 1
        else:
            high = mid - 1
            
    return ans

def solve_weighted_interval_scheduling(intervals: List[Dict[str, Any]]) -> List[int]:
    """
    Runs the classic Weighted Interval Scheduling dynamic programming algorithm.
    Intervals list must be pre-sorted by end_min.
    Returns: List of selected indices in the sorted intervals list.
    """
    n = len(intervals)
    if n == 0:
        return []
        
    # p[i] stores the index of the last compatible interval before interval i
    p = [-1] * n
    for i in range(n):
        p[i] = find_largest_compatible(intervals, i)
        
    # DP table: M[i] stores the max weight using subset of intervals 0..i
    M = [0.0] * n
    M[0] = float(intervals[0]['budget'])
    
    for i in range(1, n):
        val_with = float(intervals[i]['budget'])
        if p[i] != -1:
            val_with += M[p[i]]
            
        val_without = M[i-1]
        
        M[i] = max(val_with, val_without)
        
    # Backtrack to reconstruct the optimal set of intervals
    selected_indices = []
    
    def backtrack(i):
        if i < 0:
            return
        if i == 0:
            selected_indices.append(0)
            return
            
        val_with = float(intervals[i]['budget'])
        if p[i] != -1:
            val_with += M[p[i]]
            
        # If including interval i yields a larger/equal value than excluding it
        if val_with >= M[i-1] - 1e-5:
            selected_indices.append(i)
            backtrack(p[i])
        else:
            backtrack(i-1)
            
    backtrack(n - 1)
    
    # Reverse selected indices to preserve sorted order
    return selected_indices[::-1]

def run_interval_allocation(ads_df) -> Dict[str, Any]:
    """
    Main entry point for Weighted Interval Scheduling.
    Pre-processes data, runs scheduling per slot, and returns formatted metrics.
    """
    # 1. Fill in start and end times deterministically if not present
    df = generate_deterministic_intervals(ads_df)
    
    # Initialize columns
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
        
        # Filter ads that prefer this slot
        slot_ads = df[df['PreferredSlot'] == slot].copy()
        
        if slot_ads.empty:
            continue
            
        # Parse times to minutes and build interval objects
        intervals = []
        for idx, row in slot_ads.iterrows():
            st_min = parse_time_to_minutes(row['StartTime'])
            et_min = parse_time_to_minutes(row['EndTime'])
            intervals.append({
                'global_idx': idx,
                'id': row['AdvertisementID'],
                'start_min': st_min,
                'end_min': et_min,
                'duration': et_min - st_min,
                'budget': float(row['Budget']),
                'start_str': row['StartTime'],
                'end_str': row['EndTime']
            })
            
        # Sort intervals by end time (crucial requirement for Weighted Interval Scheduling)
        intervals.sort(key=lambda x: x['end_min'])
        
        # Solve
        selected_local_indices = solve_weighted_interval_scheduling(intervals)
        
        # Mark as allocated
        current_used_duration = 0
        for local_idx in selected_local_indices:
            interval = intervals[local_idx]
            g_idx = interval['global_idx']
            
            df.at[g_idx, 'AllocatedSlot'] = slot
            df.at[g_idx, 'Status'] = 'Allocated'
            df.at[g_idx, 'AllocatedStartTime'] = interval['start_str']
            df.at[g_idx, 'AllocatedEndTime'] = interval['end_str']
            
            current_used_duration += interval['duration']
            total_revenue += interval['budget']
            
        slot_utilization[slot] = current_used_duration
        slot_unused_time[slot] = capacity - current_used_duration

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

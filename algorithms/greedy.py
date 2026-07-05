from typing import List, Dict, Any
from .parser import SLOT_CONFIGS

def run_greedy_allocation(ads_df) -> Dict[str, Any]:
    """
    Runs the Greedy scheduling algorithm on the input DataFrame.
    Sorts by: Priority (descending) -> Budget (descending) -> Duration (ascending).
    Fits ads into their preferred slots.
    """
    # Make a copy of the dataframe
    df = ads_df.copy()
    
    # Initialize allocation results columns
    df['AllocatedSlot'] = 'None'
    df['Status'] = 'Rejected'
    df['AllocatedStartTime'] = 'N/A'
    df['AllocatedEndTime'] = 'N/A'

    # Results to return
    allocation_results = []
    slot_utilization = {slot: 0 for slot in SLOT_CONFIGS}
    slot_unused_time = {slot: config['capacity'] for slot, config in SLOT_CONFIGS.items()}
    total_revenue = 0
    
    # Process each slot individually
    for slot, config in SLOT_CONFIGS.items():
        capacity = config['capacity']
        start_min = config['start_min']
        
        # Filter ads that prefer this slot
        slot_ads = df[df['PreferredSlot'] == slot].copy()
        
        # Sort by: Priority desc, Budget desc, Duration asc
        slot_ads.sort_values(
            by=['Priority', 'Budget', 'Duration'], 
            ascending=[False, False, True], 
            inplace=True
        )
        
        current_time_offset = 0 # Minutes from slot start
        
        for idx, row in slot_ads.iterrows():
            duration = row['Duration']
            budget = row['Budget']
            
            # Check if this ad fits in the remaining capacity
            if current_time_offset + duration <= capacity:
                # Allocate
                ad_id = row['AdvertisementID']
                
                # Calculate start and end absolute times
                ad_start_min = start_min + current_time_offset
                ad_end_min = ad_start_min + duration
                
                start_h = ad_start_min // 60
                start_m = ad_start_min % 60
                end_h = ad_end_min // 60
                end_m = ad_end_min % 60
                
                start_time_str = f"{start_h:02d}:{start_m:02d}"
                end_time_str = f"{end_h:02d}:{end_m:02d}"
                
                # Update DataFrame
                df.at[idx, 'AllocatedSlot'] = slot
                df.at[idx, 'Status'] = 'Allocated'
                df.at[idx, 'AllocatedStartTime'] = start_time_str
                df.at[idx, 'AllocatedEndTime'] = end_time_str
                
                current_time_offset += duration
                total_revenue += budget
            else:
                # Doesn't fit in the remaining capacity, status remains 'Rejected'
                df.at[idx, 'AllocatedSlot'] = 'None'
                df.at[idx, 'Status'] = 'Rejected'
                
        slot_utilization[slot] = current_time_offset
        slot_unused_time[slot] = capacity - current_time_offset

    # Return summary dict and processed list of ads
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

import io
import pandas as pd
import numpy as np

# Slot limits and time ranges
SLOT_CONFIGS = {
    'Morning': {
        'capacity': 180,  # minutes
        'start_time': '09:00',
        'end_time': '12:00',
        'start_min': 540,
        'end_min': 720
    },
    'Afternoon': {
        'capacity': 180,
        'start_time': '12:00',
        'end_time': '15:00',
        'start_min': 720,
        'end_min': 900
    },
    'Evening': {
        'capacity': 240,
        'start_time': '17:00',
        'end_time': '21:00',
        'start_min': 1020,
        'end_min': 1260
    },
    'PrimeTime': {
        'capacity': 180,
        'start_time': '21:00',
        'end_time': '24:00',
        'start_min': 1260,
        'end_min': 1440
    }
}

def parse_and_validate_dataset(file_content: str):
    """
    Parses the dataset text content, validates against rules, and returns a Pandas DataFrame.
    Raises ValueError on validation failure.
    """
    if not file_content.strip():
        raise ValueError("The uploaded dataset is empty.")
    
    # Read the text file as a CSV/TXT
    try:
        # Use StringIO to read file content into pandas
        df = pd.read_csv(io.StringIO(file_content), skipinitialspace=True)
    except Exception as e:
        raise ValueError(f"Failed to parse file. Ensure it is a valid comma-separated text file. Error: {str(e)}")

    # Check for empty dataframe
    if df.empty:
        raise ValueError("The uploaded dataset contains no rows or data.")

    # Standardize column names (strip spaces, case insensitivity)
    rename_dict = {}
    for col in df.columns:
        norm = col.strip().lower()
        if norm == 'advertisementid' or norm == 'adid':
            rename_dict[col] = 'AdvertisementID'
        elif norm == 'duration':
            rename_dict[col] = 'Duration'
        elif norm == 'budget':
            rename_dict[col] = 'Budget'
        elif norm == 'priority':
            rename_dict[col] = 'Priority'
        elif norm == 'preferredslot' or norm == 'slot':
            rename_dict[col] = 'PreferredSlot'

    df.rename(columns=rename_dict, inplace=True)

    # Required columns check
    required_cols = {'AdvertisementID', 'Duration', 'Budget', 'Priority', 'PreferredSlot'}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in dataset: {', '.join(missing)}")

    # Data cleaning and type conversions
    df['AdvertisementID'] = df['AdvertisementID'].astype(str).str.strip()
    
    # Check for duplicate AdvertisementIDs
    duplicates = df[df.duplicated('AdvertisementID', keep=False)]['AdvertisementID'].unique()
    if len(duplicates) > 0:
        raise ValueError(f"Duplicate Advertisement IDs found: {', '.join(duplicates[:10])}")

    # Validate numbers
    try:
        df['Duration'] = pd.to_numeric(df['Duration'])
        df['Budget'] = pd.to_numeric(df['Budget'])
        df['Priority'] = pd.to_numeric(df['Priority'])
    except Exception:
        raise ValueError("Duration, Budget, and Priority must be numeric values.")

    # Check for negative or zero duration/budget/priority
    negative_duration = df[df['Duration'] <= 0]
    if not negative_duration.empty:
        invalid_ids = negative_duration['AdvertisementID'].tolist()
        raise ValueError(f"Duration must be greater than 0. Invalid IDs: {', '.join(invalid_ids[:10])}")

    negative_budget = df[df['Budget'] < 0]
    if not negative_budget.empty:
        invalid_ids = negative_budget['AdvertisementID'].tolist()
        raise ValueError(f"Budget cannot be negative. Invalid IDs: {', '.join(invalid_ids[:10])}")

    negative_priority = df[df['Priority'] < 0]
    if not negative_priority.empty:
        invalid_ids = negative_priority['AdvertisementID'].tolist()
        raise ValueError(f"Priority cannot be negative. Invalid IDs: {', '.join(invalid_ids[:10])}")

    # Check PreferredSlot validity
    valid_slots = set(SLOT_CONFIGS.keys())
    df['PreferredSlot'] = df['PreferredSlot'].astype(str).str.strip()
    
    # Normalize slot casing (e.g. primetime -> PrimeTime)
    slot_map = {s.lower(): s for s in valid_slots}
    invalid_slots = []
    
    for idx, row in df.iterrows():
        slot_val = row['PreferredSlot'].lower()
        if slot_val in slot_map:
            df.at[idx, 'PreferredSlot'] = slot_map[slot_val]
        else:
            invalid_slots.append(f"{row['AdvertisementID']}({row['PreferredSlot']})")

    if invalid_slots:
        raise ValueError(f"Invalid PreferredSlot value(s). Must be one of Morning, Afternoon, Evening, PrimeTime. Invalid records: {', '.join(invalid_slots[:10])}")

    return df

# Data Report

## Data Loading

**Handled by:** `load_csv_data` function

### Considerations: Choosing a Data Structure

I opted for a **list of dictionaries** to store the data. This structure is convenient for later data validation since we can easily access each dictionary’s keys and their respective values. Each row is represented as a dictionary, like so:

```python
row = {
    'timestamp': line[0].strip(),
    'price': line[1].strip(),
    'size': line[2].strip()
}
```

### Problem: Slow Execution Time (~22s)

### Solution:
Initially, I used Python’s `threading` module to create individual threads for each file and store the results in a `Queue` object. However, I later learned that `ThreadPoolExecutor` is a better alternative, as it handles thread management automatically. This is how I implemented it:

```python
with ThreadPoolExecutor() as executor:
    results = list(executor.map(read_csv, csv_files))
```

---

## Data Cleaning

### Errors Found:
1. **Negative Prices**
2. **Missing Prices**
3. **Incorrect Decimal Points**
4. **Duplicate Timestamps**

### Solutions:
#### Handling Errors 1, 2, and 3:
Initially, I set a `min_price` (400.0) and `max_price` (500.0) and filtered out data where price was out of this range. However, this approach was too simplistic, as manually setting a fixed range is not statistically robust. Instead, I calculated **lower and upper bounds** for prices using the **interquartile range (IQR):**

```python
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR
```

#### Handling Error 4:
To remove duplicate timestamps, I used Python's `Counter` module to count occurrences of each timestamp and filtered out any rows where the timestamp appeared more than once. I chose not to store even the first occurrence of any duplicate, as it's unclear which timestamp contains the valid price data.

```python
from collections import Counter

timestamp_counter = Counter(row["timestamp"] for row in data if "timestamp" in row)
```

### Problem:
Since we want to filter out data outside of trading hours, converting each timestamp to **datetime objects** is slow.

### Potential Solutions:
- Utilize optimized **date-time parsing libraries** designed for large datasets (e.g., `pandas.to_datetime()` or `ciso8601`).

---

## Data Interface Development

### User Input for Timeframes
I implemented **helper functions** to prompt the user for:
- **Start Time**
- **End Time**
- **Intervals**

These functions use **regex and while loops** to ensure that the user’s input is in the correct format.

**Limitation:** The current design assumes that the user is well-informed about the data. For example, the **start time and end time must be provided down to the millisecond**. The user should also be aware that only time ranges within trading hours is allowed.

---

## OHLCV Generation

### Steps:
1. **Sort the data** by timestamp.

    ```python
    data.sort(key=lambda x: x['timestamp'])
    ```

2. Perform a **binary search** to find the indices for the **start time** and **end time**.

    ```python
    import bisect
    
    start_index = bisect.bisect_left(timestamps, start_time)
    end_index = bisect.bisect_right(timestamps, end_time)
    ```

3. Use a **nested while loop**:
   - The loop continues as long as `start_time < end_time` and `start_index < end_index`.
   - Within the loop, we check if the timestamp at `start_index` is **less than** `interval_end_time`, and increment accordingly.

    ```python
    while start_time < end_time:
        interval_data = []
        while start_index < end_index and start_time <= data[start_index]["timestamp"] < interval_end_time:
            # Process interval data
    ```

---

## Future Improvements:
1. Optimize **timestamp conversion** for performance.
2. Allow **user input** to decide whether to filter data outside trading hours.
3. Implement **faster search algorithms** for better efficiency in data lookups.

---

### **End of Report**

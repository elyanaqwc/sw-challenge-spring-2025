Data Loading 

Handled by load_csv_date function

Considerations: Which data structure to store our data?

I opted for a list of dictionaries to store the data. This structure is convenient for later data validation since we can easily access each dictionary’s keys and their respective values. Each row is represented as a dictionary, like so:

row = {
   'timestamp': line[0].strip(),
    'price': line[1].strip(),
    'size': line[2].strip()
       }

Problem: Initial execution time took very long  (~22s)

Solution: Initially, I used Python’s threading module to create individual threads for each file and store the results in a Queue object. However, I later learned that ThreadPoolExecutor is a better alternative, as it handles thread management automatically. This is how I implemented it:

with ThreadPoolExecutor() as executor:
    results = list(executor.map(read_csv, csv_files))



Data Cleaning 

This calls the load_csv_data function; Execution time  5-6s

Errors Found:
1. Negative Prices
2. Missing prices
3. Incorrect decimal point
4. Duplicate timestamps

Solutions for Error 1, 2, 3:
Initially, I set a min_price (400.0) and max_price (500.0) and filtered out data where price was out of this range. However, I thought that this way of approaching price data was too simplistic because setting a fixed range manually is not based on statistical methods. So, I calculated a lower bound and upper bound for the prices using the interquartile range of the prices: 

lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

Solution for Error 4:
To handle duplicate timestamps, I used Python's Counter module to count occurrences of each timestamp. I then filtered out any rows where the timestamp appeared more than once. I chose not to store the first occurrence of any duplicate because I am not sure which timestamp contains the valid price data.

timestamp_counter = Counter(row["timestamp"] for row in data if "timestamp" in row)

**NOTE: I did not filter out data outside of trading hours because there was a significant amount of it that might be useful for analysis. Improvements for future: Seek for user input on whether or not they want data outside of trading hours to be included


Data Interface Development
User input for timeframes: I implemented helper functions to prompt the user for the start time, end time, and intervals. These functions use regex and while loops to ensure that the user’s input is in the correct format.
Limitation: The current design assumes that the user is well-informed about the data. For example, the start time and end time must be provided down to the millisecond. 
OHLCV Generation:

I convert each timestamp into datetime objects and sort them.
for row in data:
    row['timestamp'] = self.__convert_timestamp(row['timestamp'])
data.sort(key=lambda x: x['timestamp'])

I then perform a binary search to find the starting index (for start time) and the ending index (for end time).
start_index = bisect.bisect_left(timestamps, start_time)
end_index = bisect.bisect_right(timestamps, end_time)

After identifying the indices, I use a nested while loop: The loop continues as long as start_time < end_time and start_index < end_index.
 while start_time < end_time:
       interval_data = []
       while start_index < end_index and start_time <= data[start_index]["timestamp"] < interval_end_time:

Within the loop, I ensure that the timestamp at the start index is less than the interval end time, and both the start_index and interval_end_time are incremented.

Problem: Converting each timestamp to datetime objects is slow. 

Potential Solutions: Utilize optimized libraries designed for fast date-time parsing, especially for large datasets.

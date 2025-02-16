import os
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
import re
from datetime import datetime, timedelta, time
import csv
import bisect 

class DataParser:
    def __init__(self, dir_path):
        self.dir_path = dir_path
        self.filtered_data = []

    def load_csv_data(self):
        # helper function, parses each line in a file into a dictionary that stores timestamp,
        # price, and size as keys as well as their respective values
        def read_csv(file_path):
            unfiltered_data = []
            try:
                with open(os.path.join(self.dir_path, file_path), 'r') as file:
                    csv_reader = csv.reader(file)
                    next(csv_reader) 
                    for line in csv_reader:
                        if len(line) == 3:
                            row = {
                                'timestamp': line[0].strip(),
                                'price': line[1].strip(),
                                'size': line[2].strip()
                            }
                            unfiltered_data.append(row)
            except (FileNotFoundError, OSError) as e:
                print(f"Error reading file {file_path}: {e}")
            return unfiltered_data

        # list of csv file paths
        csv_files = [file for file in os.listdir(self.dir_path) if file.endswith('.csv')]

        # fixed pool of threads to map our read_csv function to each file in our list of csv_files
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(read_csv, csv_files))

        # flatten the list because currently, results is a list of lists, where each sublist contains
        # dictionaries from a single file
        return [item for sublist in results for item in sublist]
    
    def validate_data(self):
        # define trading hours
        trading_start = time(9, 30)
        trading_end = time(16, 0)
        
        data = self.load_csv_data()

        prices = []

        # loop through unfiltered data to store prices so that we can perform iqr calculation
        for row in data:
            price_str = row.get("price", "").strip()
            try:
                price = float(price_str)
                prices.append(price)
            except ValueError:
                continue
        if prices:
            # here we sort the prices, get the indexes for Q1 and Q3 and initialize their values
            sorted_prices = sorted(prices)
            n = len(sorted_prices)

            q1_index = int(0.25 * n)
            Q1 = sorted_prices[q1_index]

            q3_index = int(0.75 * n)
            Q3 = sorted_prices[q3_index]

            IQR = Q3 - Q1

            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
        else:
            lower_bound, upper_bound = 0, 0  

        # store timestamps and their respective counts in a Counter object
        timestamp_counter = Counter(row["timestamp"] for row in data if "timestamp" in row)

        self.filtered_data = []

        for row in data:
            # retrieve price, size, timestamp values in each row and removes any whitespace
            # if any of the values are missing, it defaults to an empty string
            price_str = row.get("price", "").strip()
            size_str = row.get("size", "").strip()
            timestamp_str = row.get("timestamp", "")

            # if any of the values are empty, we move to the next row
            if not price_str or not size_str or not timestamp_str:
                continue
            
            # convert price into float, size into int, and timestamp into datetime object
            try:
                price = float(price_str)
                size = int(size_str)
                timestamp = self.__convert_timestamp(timestamp_str)
                if timestamp is None:
                    continue
            except ValueError:
                continue  
            
            # only store rows where timestamp is unique, price is between the bounds we calculated,
            # valid size, and timestamp is between trading hours    
            if (
                timestamp_counter[timestamp_str] == 1   
                and lower_bound <= price <= upper_bound  
                and size > 0  
                and trading_start <= timestamp.time() <= trading_end
            ):
                self.filtered_data.append({"timestamp": timestamp, "price": price, "size": size})
        return self.filtered_data

    # helper function to convert a timestamp string into a datetime object
    def __convert_timestamp(self, timestamp):
        try:
            return datetime.fromisoformat(timestamp)
        except ValueError:
            return None

    # helper function to get start time and end time from user
    def __get_user_time_range(self):
        # define regex pattern for our timestamp
        timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}'
        
        # ensure that self.filtered_data is not empty 
        if not self.filtered_data:
            print("No data available. Cannot determine a valid time range.")
            return None  

        last_timestamp = self.filtered_data[-1]['timestamp']
        
        while True:
            start_time = input("Enter start time (e.g. 2024-09-19 20:47:02.535): ")

            # ensure that user input matches our regex pattern
            if not re.fullmatch(timestamp_pattern, start_time):
                print("Invalid start time format. Try again.")
                continue

            start_time_converted = self.__convert_timestamp(start_time)

            end_time = input("Enter end time (e.g. 2024-09-20 20:47:02.535): ")
            if not re.fullmatch(timestamp_pattern, end_time):
                print("Invalid end time format. Try again.")
                continue

            end_time_converted = self.__convert_timestamp(end_time)

            # ensure that the start time is less than the end time
            if start_time_converted >= end_time_converted:
                print("Start time must be before end time. Try again.")
                continue

            # ensure that the end time is less than or equal the last timestamp in our filtered data
            if end_time_converted > last_timestamp:
                print("End time must be within available data range. Try again.")
                continue

            return start_time_converted, end_time_converted

    # helper function to get intervals from user 
    def __get_intervals(self):
        total_seconds = 0

        # define regex pattern for interval
        interval_pattern = r'^(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$'       
        conversion = {'d': 86400, 'h': 3600, 'm': 60, 's': 1} 
        while True:
            user_interval = input("Enter a valid interval (e.g. 1h30m): ")
            if not re.fullmatch(interval_pattern, user_interval):
                print('Invalid interval. Please try again.')
                continue
        
            # list of tuples, each tuple contains a value and a unit e.g. ('1' , 'd')
            matches = re.findall(r'(\d+)([dhms])', user_interval) 

            # iterates over each tuple (value, unit) and, multiply value by its corresponding 
            # conversion factor from our conversion dictionary
            total_seconds = sum(int(value) * conversion[unit] for value, unit in matches)

            if total_seconds <= 0:
                print("Interval must be greater than 0 seconds. Try again.")
                continue
            
            return total_seconds
        

    def generate_ohlcv(self):
        start_end_times = self.__get_user_time_range()
        interval = self.__get_intervals()

        if not start_end_times:
            print("Invalid time range.")
            return []

        start_time, end_time = start_end_times
        data = self.filtered_data

        if not data:
            print("No data found in the specified time range.")
            return []

        # sort data by timestamp 
        data.sort(key=lambda x: x['timestamp'])

        # store all timestamps in a list
        timestamps = [row['timestamp'] for row in data]

        # finds the leftmost index where if start time is present in timestamps, it returns its index
        # if not, it returns the index where it should be inserted
        start_index = bisect.bisect_left(timestamps, start_time)

        # same logic as above, but finds the rightmost index for end time instead
        end_index = bisect.bisect_right(timestamps, end_time)

        ohlcv_list = []

        # loop continues as long as there are timestamps left within the time range
        while start_index < end_index:
            interval_data = [] # reset the list to store next interval's data
            first_timestamp = data[start_index]["timestamp"]  # set the first timestamp in this interval
            interval_start_time = first_timestamp  # reset interval start time
            interval_end_time = interval_start_time + timedelta(seconds=interval)   # reset interval end time

            # if current timestamp is less than the interval end time, it belongs to this interval
            while data[start_index]["timestamp"] < interval_end_time:
                interval_data.append(data[start_index])
                start_index += 1

            # only until after a timestamp exceeds or is equal to the interval end time, we break out
            # of the inner loop and generate ohlcv data for the current interval
            if interval_data:
                ohlcv_list.append({
                    'timestamp': first_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],  
                    'open': interval_data[0]['price'],
                    'high': max(d['price'] for d in interval_data),
                    'low': min(d['price'] for d in interval_data),
                    'close': interval_data[-1]['price'],
                    'volume': sum(d['size'] for d in interval_data)
                })

        return ohlcv_list
    
    # improvements for future: dynamic file naming convention based on time range and interval
    def generate_csv(self):
        csv_name = '1d_interval.csv'
        try:
            with open(csv_name, 'w', newline='') as csvfile:
                columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                writer = csv.DictWriter(csvfile, fieldnames=columns )
                writer.writeheader()
                writer.writerows(self.generate_ohlcv())        
        except Exception as e:
            print(f'Error occured: {e}')


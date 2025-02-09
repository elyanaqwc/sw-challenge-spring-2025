import os
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
import re
from datetime import datetime, timedelta
import csv
import bisect 

class DataParser:
    def __init__(self, dir_path):
        self.dir_path = dir_path
        self.filtered_data = []

    '''
    This function uses a ThreadPoolExecutor object to map our read_csv function to all the files in our
    csv_files list 
    '''
    def load_csv_data(self):
        ''' 
        Target function to be used by ThreadPoolExecutor(), parses each line into dictionary with keys
        timestamp, price, and size. row (dictionary) is then appended to our unfiltered_data list
        '''
        def read_csv(file_path):
            unfiltered_data = []
            try:
                with open(os.path.join(self.dir_path, file_path), 'r') as file:
                    csv_reader = csv.reader(file)
                    next(csv_reader) # here we skip the header row
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

        csv_files = [file for file in os.listdir(self.dir_path) if file.endswith('.csv')]

        # Here we create a ThreadPoolExecutor object, creating a fixed pool of threads
        # We then use the object's map function to map our target function read.csv to each file
        # in our list of csv_files. The object distributes the tasks among the threads 
        # Improvements for future: explore the object's parameters such as max_workers,
        # and map function parameters such as chunk_size to optimize efficiency   
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(read_csv, csv_files))

        # here we flatten the list because each read_csv call returns a list of dictionaries, so right now
        # results is a list of lists, where each sublist is the data of a single csv file
        return [item for sublist in results for item in sublist]
    
    ''' 
    Errors found: 
    1) negative price data
    2) missing price data
    3) incorrect decimal point (eg 40.0 instead of 400.0)
    4) duplicate timestamps

    - for errors 1, 2, and 3, we calculate a lower bound and upper bound using interquartile range
    - this allows us to only store data that is within this range
    - for error 4, we use the Counter module, which stores hashable onjects and their counts,
    then later on we only store rows where its timestamp count is 1
    **NOTE: I was unsure on whether or not to filter out timestamps outside of trading hours. Ultimately,
    I chose not to because there is a significant amount of data outside trading hours that might be useful for 
    analysis. Future improvements: ask user for input on whether or not they want to include data outside
    of trading hours and filter based on that
    '''
    def validate_data(self):
        data = self.load_csv_data() #retrieve unfiltered data by calling our load_csv_data function

        prices = []
        # use for loop to store valid price values, and then sort the prices to perform iqr calculations
        for row in data:
            price_str = row.get("price", "").strip()
            try:
                price = float(price_str)
                prices.append(price)
            except ValueError:
                continue
        if prices:
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

        # here we intialize a Counter object that stores each timestamp and their counts
        timestamp_counter = Counter(row["timestamp"] for row in data if "timestamp" in row)

        self.filtered_data = []

        # use for loop to iterate through data and only append rows where
        # 1) all fields are present
        # 2) price and size values are in valid format to be converted from string to float, int
        # 3) timestamp is unique
        # 4) price is within the lower bound and upper bound which we calculated using iqr
        # 5) size is more than 0
        for row in data:
            price_str = row.get("price", "").strip()
            size_str = row.get("size", "").strip()
            timestamp = row.get("timestamp")

            if not price_str or not size_str or not timestamp:
                continue
            
            try:
                price = float(price_str)
                size = int(size_str)
            except ValueError:
                continue  

            if (
                timestamp_counter[timestamp] == 1   #ensures that we only store unique timestamps
                and lower_bound <= price <= upper_bound  
                and size > 0  
            ):
                self.filtered_data.append({"timestamp": timestamp, "price": price, "size": size})
        print(lower_bound, upper_bound)

        
    ''' 
    private helper function to convert a single string timestamp to a datetime object 
    improvements for future: this is kinda too slow. tried using regex but requires very strict exception
    handling. maybe can use external library like pandas :')
    '''
    def __convert_timestamp(self, timestamp):
        return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")

    ''' 
    private helper function to get start time and end time from user, using regex for input validation
    '''
    def __get_user_time_range(self):
        timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}'
        
        # ensure that the filtered data list is not empty because we need it to get the last_timestamp
        if not self.filtered_data:
            print("No data available. Cannot determine a valid time range.")
            return None  

        last_timestamp = self.__convert_timestamp(self.filtered_data[-1]['timestamp'])  
        
        # use while loop to get user input, if invalid then print error message and ask user to input again
        while True:
            start_time = input("Enter start time (e.g. 2024-09-19 20:47:02.535): ")
            if not re.fullmatch(timestamp_pattern, start_time):
                print("Invalid start time format. Try again.")
                continue

            start_time_converted = self.__convert_timestamp(start_time)

            end_time = input("Enter end time (e.g. 2024-09-20 20:47:02.535): ")
            if not re.fullmatch(timestamp_pattern, end_time):
                print("Invalid end time format. Try again.")
                continue

            end_time_converted = self.__convert_timestamp(end_time)

            if start_time_converted > end_time_converted:
                print("Start time must be before end time. Try again.")
                continue

            if end_time_converted > last_timestamp:
                print("End time must be within available data range. Try again.")
                continue

            return start_time_converted, end_time_converted

    '''
    private helper function to get intervals from user, converts user input into total seconds
    '''
    def __get_intervals(self):
        total_seconds = 0
        interval_pattern = r'^\d+[dhms](\d+[dhms])*$'        
        conversion = {'d': 86400, 'h': 3600, 'm': 60, 's': 1} 
        while True:
            user_interval = input("Enter a valid interval (e.g. 1h30m): ")
            if not re.fullmatch(interval_pattern, user_interval):
                print('Invalid interval. Please try again.')
                continue
        
            matches = re.findall(r'(\d+)([dhms])', user_interval) #list of tuples
            total_seconds = sum(int(value) * conversion[unit] for value, unit in matches)

            if total_seconds <= 0:
                print("Interval must be greater than 0 seconds. Try again.")
                continue
            
            return total_seconds
        
    '''
    1) convert each timestamp to datetime object and sort data based on timestamp
    2) get index of start time and end time 
    3) run nested while loop to generate ohlcv in sections: we increment the index, start_time becomes 
    end_time, and end_time is incremented by interval
    '''
    def generate_ohlcv(self):
        start_end_times = self.__get_user_time_range()
        interval = self.__get_intervals()

        ohlcv_list = []
        if not start_end_times:
            print("Invalid time range.")
            return []

        start_time, end_time = start_end_times
        data = self.filtered_data        

        for row in data:
           row['timestamp'] = self.__convert_timestamp(row['timestamp'])
        data.sort(key=lambda x: x['timestamp'])

        if not data:
            print("No data found in the specified time range.")
            return []

        timestamps = [row['timestamp'] for row in data]

        # here we use python's bisect module to perform a binary search from the left to find the index of the 
        # timestamp that is >= the start time and from the right to find the index that is <= the end time
        start_index = bisect.bisect_left(timestamps, start_time)
        end_index = bisect.bisect_right(timestamps, end_time)
        interval_end_time = start_time + timedelta(seconds=interval)

        while start_time < end_time:
            interval_data = []

            # collect data for this interval
            while start_index < end_index and start_time <= data[start_index]["timestamp"] < interval_end_time:
                interval_data.append(data[start_index])
                start_index += 1  # move to the next data point

            # process data only if there are entries in the interval
            if interval_data:
                ohlcv_list.append({
                    'timestamp': datetime.strftime(interval_data[0]['timestamp'], "%Y-%m-%d %H:%M:%S.%f"),
                    'open': interval_data[0]['price'],
                    'high': max(d['price'] for d in interval_data),
                    'low': min(d['price'] for d in interval_data),
                    'close': interval_data[-1]['price'],
                    'volume': sum(d['size'] for d in interval_data)
                })

            # move to the next interval
            start_time = interval_end_time
            interval_end_time = start_time + timedelta(seconds=interval)
        return ohlcv_list
    
    '''
    improvements for future: dynamic file naming convention based on the start time, end time, and interval
    '''
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

dir_path = r"C:\Users\quahe\Documents\sw-challenge-spring-2025\data" #maybe store this in an .env file
#start = time.time()

parser = DataParser(dir_path)
parser.validate_data()  #loading files + validating data: execution time ~ 5-6s
parser.generate_csv() # execution time varies because based on user input for getting time range and intervals

#end = time.time()
#print(end-start)

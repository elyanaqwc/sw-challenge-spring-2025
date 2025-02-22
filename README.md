## Introduction

The **DataParser** class is designed to streamline the process of handling financial tick data. It performs the following key tasks:

- **Data Loading**: Efficiently loads CSV files containing tick data from a specified directory, utilizing multithreading to speed up the process.
- **Data Cleaning**: Parses invalid data such as negative prices, missing prices, duplicate timestamps, 
and extreme outliers.
- **Data Interface**: Accepts user-defined time intervals and ranges, then generates a CSV file containing OHLCV bars for the specified time frames.
### Setup

1. **Clone the repository**:
   To clone this repository to your local machine, run the following command in your terminal:
   
   ```bash
   git clone https://github.com/elyanaqwc/sw-challenge-spring-2025.git
   ```

### Usage

2. **Import the DataParser module**:
   ```python
   from data_parser import DataParser
   
3. **Create an instance of the DataParser**:
   The DataParser class accepts the path to your data directory as a parameter.
    ```python
    parser = DataParser(dir_path)

4. **Call the validate_data function and generate_csv function**:
   You can call both functions in sequence to validate the data and generate the CSV file.
    ```python
    parser.validate_data()
    parser.generate_csv()

5. **User Inputs**: 
    When calling generate_csv, you will be prompted to enter a start time:
    ```ruby
    Enter start time (e.g. 2024-09-19 20:47:02.535): 
    ```
    and an end time:
    ```ruby
    Enter end time (e.g. 2024-09-20 20:47:02.535)
    ```
    where both start time and end time have to match the format:
    ```ruby
    YYYY-MM-DD HH:MM:SS.sss
    ```

    
   **Validation Rules**:
    - The start time must not exceed or equate to the end time.
    - The end time must not exceed the last timestamp in the data.
    - Both time ranges must be within trading hours (9:30 AM to 4:00 PM EST).
     
    You will be prompted to enter an interval:
    ```ruby
    Enter a valid interval (e.g. 1h30m):
    ```

    
    whereby the interval must match the following pattern:
    ```ruby
    ^\d+[dhms](\d+[dhms])*$
    ```
   **Examples of valid intervals**:
   ```ruby
   1d 
   1d1h1m1s
   2h30m
   30s
   ```
  
   **Examples of invalid intervals**:
   ```ruby
   2d 3h (There should be no space between units)
   1h1d (Units should follow correct order: Days -> Hours -> Minutes -> Seconds)
   ```
    
    
### Assumptions
- Outlier Filtering: The class filters out outliers based on the Interquartile Range (IQR) method before processing the data.

- Time Range Format: Users are expected to input the time range in the correct format, ensuring that the start and end times are valid for the data being processed.

- Trading Hours: Only data within the trading hours (9:30 AM to 4:00 PM) is included; any data outside of this range is excluded from processing.

### Limitations
- Processing Speed: Depending on the size of the dataset, processing might take time (~7-9s for data loading and validation combined), especially with large amounts of tick data. Optimizations for speed may be necessary for larger datasets.

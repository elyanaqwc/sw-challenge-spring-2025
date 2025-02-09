## Introduction

### Setup

1. **Clone the repository**:
   Clone the repository to your local environment.

2. **Import the DataParser module**:
   ```python
   from data_parser import DataParser
   
3. **Create an instance of the DataParser**:
   The DataParser class accepts the path to your data directory as a parameter.
    ```python
    parser = DataParser(dir_path)

4. **Call the validate_data function**:
    This function will prompt you for a time range and interval.
    ```python
    parser.validate_data()

5. **User Inputs**: 
    You will be prompted to enter a start time:
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
     
    You will be prompted to enter an interval:
    ```ruby
    Enter a valid interval (e.g. 1h30m):
    ```
    
    whereby the interval must match the following pattern:
    ```ruby
    ^\d+[dhms](\d+[dhms])*$
    ```
    
    **Validation Rules**:
    - The start time must not exceed the end time.
    - The end time must not exceed the last timestamp in the data.
    - Both time ranges must be within trading hours (9:30 - 4:00)
    
6. **Generate CSV:**
   After validation, you can generate the CSV file with:
   ```python
   parser.generate_csv()

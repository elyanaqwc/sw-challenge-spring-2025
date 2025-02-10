from data_parser import DataParser
#import time

dir_path = r"C:\Users\quahe\Documents\sw-challenge-spring-2025\data" 

parser = DataParser(dir_path)
#start = time.time()
parser.validate_data() # ~ 7-9s
#end = time.time()
#print(end-start)
parser.generate_csv() 



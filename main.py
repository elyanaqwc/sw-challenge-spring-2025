from data_parser import DataParser

dir_path = r"C:\Users\quahe\Documents\sw-challenge-spring-2025\data" 

parser = DataParser(dir_path)
parser.validate_data()
parser.generate_csv() 



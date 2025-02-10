from datetime import datetime 

start_time = datetime.fromisoformat("2024-09-20 09:25:00.106000")
print(start_time.replace(microsecond=0))
import requests
import time

API = "http://127.0.0.1:5000"
USER_ID = "user123"
N_REQUESTS = 100

latencies = []

for i in range(N_REQUESTS):
    start = time.time()
    r = requests.get(f"{API}/recommendations/{USER_ID}", params={"algo":"user_based","limit":10})
    end = time.time()
    latency = end - start
    latencies.append(latency)
    if r.status_code != 200:
        print(f"Request {i} failed: {r.status_code}")

print(f"Performed {N_REQUESTS} requests")
print(f"Average latency: {sum(latencies)/len(latencies):.3f} sec")
print(f"Min latency: {min(latencies):.3f} sec")
print(f"Max latency: {max(latencies):.3f} sec")

import json
import requests
import concurrent.futures
import time
import numpy as np


headers = {
    'Authorization': 'Basic YWRtaW46YWRtaW4='
}

def process_input_file(file_path, num_buckets):
    with open(file_path, "r") as file:
        lines = file.readlines()
        # print("total lines:", len(lines))
        lines_per_bucket = len(lines) // num_buckets
    # Create a list of lists to store the buckets
    buckets = []

    # Split lines into buckets
    for i in range(num_buckets):
        start = i * lines_per_bucket
        end = start + lines_per_bucket
        # print("start is:" + start + ",end is:" + end)
        bucket = lines[start:end]
        buckets.append(bucket)

    # If there are any remaining lines, add them to the last bucket
    if len(lines) % num_buckets > 0:
        remaining_lines = lines[num_buckets * lines_per_bucket:]
        buckets[-1].extend(remaining_lines)

    return buckets

def a_task(bucket):
    print("peeking the first row:" + bucket[0])
    total_len = len(bucket)
    calculation = []
    while len(bucket) > 0:
        input = bucket.pop()
        embedding = get_embedding_result(input)
        start_time = time.time() * 1000
        knn_query(embedding)
        end_time = time.time() * 1000
        print("progress:{}%".format((1 - len(bucket) / total_len) * 100))
        calculation.append(end_time - start_time)
    return calculation

def knn_query(embedding):
    query_body = {
        "size": 10,
        "query": {
            "knn": {
                "text_knn": {
                    "vector": embedding,
                    "k": 10
                }
            }
        }
    }
    url = "http://localhost:9200/my-index/_search"
    try:
        response = requests.post(url, headers=headers, json=query_body)
        if response.status_code == 200:
            data = response.text
            return data
        else:
            print("error when querying")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the request: {e}")
        return None

def start_threads(buckets):
    # Create a ThreadPoolExecutor with the desired number of threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(buckets)) as executor:
        # Submit tasks to the executor using the `submit` method
        future_result = {executor.submit(a_task, buckets[i]): i for i in range(0, len(buckets))}
        final_result = []
        # Optionally, gather the results of the tasks using `as_completed` method
        for future in concurrent.futures.as_completed(future_result):
            res = future_result[future]
            try:
                result = future.result()
                final_result.extend(result)
            except Exception as e:
                print(f"Task {a_task} raised an exception: {e}")
    return final_result

def calculate_final_result(final_result):
    print("length of result list is:", len(final_result))
    p90 = np.percentile(final_result, 90)
    p99 = np.percentile(final_result, 99)
    print("P90:", p90)
    print("P99:", p99)

def get_embedding_result(input):
    input_map = json.loads(input)
    query = input_map['text']
    embedding_req = {
        "text_docs": [
            query
        ],
        "return_number": True,
        "target_response": [
            "sentence_embedding"
        ]
    }
    url = "http://localhost:9200/_plugins/_ml/_predict/TEXT_EMBEDDING/VCPIhokBXWGkUR5E4nP5"
    try:
        response = requests.post(url, headers=headers, json=embedding_req)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # The content of the response is typically in bytes, so you might need to decode it to a string
            data = response.text
            data_map = json.loads(data)
            vector = data_map['inference_results'][0]['output'][0]['data'] 
            # print(vector)
            return vector
        else:
            print(f"Request failed with status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the request: {e}")
        return None

if __name__ == "__main__":
    buckets = process_input_file("/Users/zaniu/Downloads/msmarco/first_6k.jsonl", 10)
    final_result = start_threads(buckets)
    calculate_final_result(final_result)
import time
import httplib2
import json

def json_writer(json_queue):
   while True:
      item_time, chksum_is, type, temp1, temp2 = json_queue.get()
      millis = int(round(time.time() * 1000))
      set = {"created": millis, "checksum": chksum_is, "temperature_1": temp1, "temperature_2": temp2}
      http = httplib2.Http()
      print(set)
      headers = {'Content-type': 'application/json'}
      response, content = http.request("http://localhost:9200/bbq/reading", 'POST', headers=headers, body=json.dumps(set))
      print(response)
      print(content)
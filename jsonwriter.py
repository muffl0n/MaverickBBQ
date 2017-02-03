import json
import os
import random
import string

def get_random_filename(filename):
    return filename + '_' + ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(12))

def json_writer(json_queue):
   unit = '°C'
   while True:
      item_time, chksum_is, type, temp1, temp2 = json_queue.get()
      set = {'time': item_time, 'checksum': chksum_is, 'type' : type, 'unit': unit, 'temperature_1' : temp1, 'temperature_2' : temp2}
      print(set)
      tmp_filename = get_random_filename("output.json")
      with open(tmp_filename, 'w') as json_file:
          json_file.write(json.dumps(set))
          json_file.flush()
          os.fsync(json_file.fileno())
          json_file.close()
          os.rename(tmp_filename, "output.json")
      json_queue.task_done()
from influxdb import InfluxDBClient

INFLUX_DB = {
    'host': 'openhabianpi',
    'port': 8086,
    'username': 'admin',
    'password': 'openhab',
    'database': 'openhab_db'
}


def writer(queue):
    influx = InfluxDBClient(**INFLUX_DB)
    while True:
        item_time, chksum_is, type, temp1, temp2 = queue.get()
        points = list()
        points.append({
            'measurement': 'maverick',
            'tags': {
                'id': 'temp1'
            },
            'fields': {
                'value': temp1
            }
        })
        points.append({
            'measurement': 'maverick',
            'tags': {
                'id': 'temp2'
            },
            'fields': {
                'value': temp2
            }
        })

        print(points)
        influx.write_points(points)
    #log.info('inserted {} points'.format(len(points)))

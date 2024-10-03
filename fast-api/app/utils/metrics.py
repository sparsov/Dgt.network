
from influxdb_client import InfluxDBClient as NewInfluxDBClient
from influxdb import InfluxDBClient
import json
import os
from app.core.config import settings 
from urllib.parse import urlparse

# Настройка подключения к InfluxDB
if True:
    # old
    url = urlparse(settings.OPENTSDB_URL)
    client = InfluxDBClient(
                  host=url.hostname,
                  port=url.port,
                  username=settings.OPENTSDB_UNAME,
                  password=settings.OPENTSDB_PASSW,
                  database=settings.OPENTSDB_DB
             )
    
else:
    client = NewInfluxDBClient(url=settings.OPENTSDB_URL,username=settings.OPENTSDB_UNAME,password=settings.OPENTSDB_PASSW,database=settings.OPENTSDB_DB)
    query_api = client.query_api()


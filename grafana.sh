docker run -d -p 8086:8086 \
    -v /var/lib/influx-data:/var/lib/influxdb \
    -e INFLUXDB_DB=metrics \
    -e INFLUXDB_HTTP_AUTH_ENABLED=true \
    -e INFLUXDB_ADMIN_USER="admin" \
    -e INFLUXDB_ADMIN_PASSWORD="pwadmin" \
    -e INFLUXDB_USER="lrdata" \
    -e INFLUXDB_USER_PASSWORD="pwlrdata" \
    --name bgx-stats-influxdb influxdb

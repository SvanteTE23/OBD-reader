import obd

# Skapa anslutning till din OBD-II WiFi-adapter (ersätt med din IP och port)
connection = obd.OBD("192.168.0.10", 35000)

def read_obd_data(command):
    response = connection.query(command)
    if response.is_null():
        return None
    return response.value
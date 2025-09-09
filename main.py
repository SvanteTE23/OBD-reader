import obd

# Skapa anslutning till din OBD-II WiFi-adapter (ersätt med din IP och port)
connection = obd.OBD("192.168.0.10", 35000)

# Välj en sensor, t.ex. hastighet
cmd = obd.commands.SPEED
response = connection.query(cmd)

print(response.value)
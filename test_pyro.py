from Pyrometer import Pyrometer
import time

pyrometer = Pyrometer('/dev/cu.usbserial-B00378DF')

# Set emissivity (0.95 is more realistic than 1.0)
pyrometer.set_emissivity(0.95)

# Use default measurement (no channel parameter) - this works

while True:
    temp = pyrometer.measure_temperature()
    print(f"Temperature: {temp}°C")
    time.sleep(1)




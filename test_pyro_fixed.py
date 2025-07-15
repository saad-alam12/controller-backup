from Pyrometer import Pyrometer
import time

pyrometer = Pyrometer('/dev/cu.usbserial-B00378DF')

# Clear any leftover data in the buffer
pyrometer.ser.reset_input_buffer()
pyrometer.ser.reset_output_buffer()

# Set emissivity (0.95 is more realistic than 1.0)
pyrometer.set_emissivity(0.95)

# Wait a bit and clear buffer again
time.sleep(0.5)
pyrometer.ser.reset_input_buffer()

# Now measure temperature
temp = pyrometer.measure_temperature()
print(f"Temperature: {temp}°C")

# Try a few more measurements
for i in range(3):
    time.sleep(1)
    temp = pyrometer.measure_temperature()
    print(f"Temperature {i+2}: {temp}°C")
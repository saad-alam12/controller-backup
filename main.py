import time
import serial
from TDKLambda import TDKLambda
from Pyrometer import Pyrometer
from PID import PIDController

# Replace with your actual serial ports
PYROMETER_PORT = "/dev/ttyUSB0"  
PSU_PORT = "/dev/ttyUSB1"     

# Initialize devices
pyrometer = Pyrometer(PYROMETER_PORT)
PSU = TDKLambda(PSU_PORT)

# Control parameters
max_current = 6
min_current = 0.0  
control_interval = 1.0  # Time between control iterations 
temperature_tolerance = 1

# Setpoint
target_temp = float(input("Enter target temperature (°C): "))

# adjust parameters 
print("\nDefault PID parameters: Kp=1.0, Ki=0.1, Kd=0.01")
adjust_pid = input("Do you want to adjust PID parameters? (y/n): ").lower()
if adjust_pid == 'y':
    kp = float(input("Enter Kp value: "))
    ki = float(input("Enter Ki value: "))
    kd = float(input("Enter Kd value: "))
else:
    kp, ki, kd = 1.0, 0.1, 0.01

# Initialize PID controller with target temperature
pid = PIDController(kp, ki, kd, target_temp)
print(f"PID parameters: Kp={kp}, Ki={ki}, Kd={kd}")

# Start the loop
print(f"\nStarting temperature control loop to reach {target_temp}°C")

# Turn on the power supply output
PSU.output_on()

# Set initial current to minimum
PSU.set_current(min_current)

iteration = 0
max_iterations = 100
last_time = time.time()

try:
    while iteration < max_iterations:
        # Measure current temperature
        current_temperature = pyrometer.measure_temperature()
        
        # Skip iteration if temperature reading failed
        if current_temperature is None:
            print("Failed to read temperature, retrying...")
            time.sleep(control_interval)
            continue
        
        # Calculate time delta for PID controller
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time
        
        # Check if target temperature is reached within tolerance
        if abs(current_temperature - target_temp) <= temperature_tolerance:
            print(f"Target temperature reached: {current_temperature}°C")
            break
        
        # Compute PID output (current adjustment)
        pid_output = pid.compute(current_temperature, dt)
        
        # Get current current setting
        current_current = PSU.get_set_current()
        
        # Calculate new current value
        new_current = pid_output
        
        # Clamp current to valid range
        new_current = max(min_current, min(max_current, new_current))
        
        # Set the new current
        PSU.set_current(new_current)
        
        print(f"Iteration {iteration}: Temperature={current_temperature}°C, "
              f"Current={new_current:.3f}A, Error={target_temp - current_temperature:.2f}°C")
        
        # Wait for the next control iteration
        time.sleep(control_interval)
        iteration += 1
    
    if iteration >= max_iterations:
        print(f"Maximum iterations ({max_iterations}) reached without converging to target temperature")

except KeyboardInterrupt:
    print("Control loop interrupted by user")
except Exception as e:
    print(f"Error in control loop: {e}")
finally:
    # Turn off the power supply output
    PSU.output_off()
    print("Power supply output turned off")


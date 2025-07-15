# tune.py
import time
import serial
import matplotlib.pyplot as plt
from TDKLambda import TDKLambda
from Pyrometer import Pyrometer
from PID import PIDController 



PYROMETER_PORT = "/dev/ttyUSB0"  
PSU_PORT = "/dev/ttyUSB1"     

# Control parameters
max_current = 6  # Ampere
min_current = 0.0  
control_interval = 0.5  # Time between control iterations in seconds 
temperature_tolerance = 0.5  # Temperature tolerance in degrees Celsius

# device initialization

try:
    pyrometer = Pyrometer(PYROMETER_PORT)
    PSU = TDKLambda(PSU_PORT)
    pyrometer.set_emissivity(0.95) 
except serial.SerialException as e:
    print(f"Error initializing serial devices: {e}")
    print("Check ports and device connections.")
    exit()
except Exception as e:
    print(f"An unexpected error occurred during device initialization: {e}")
    exit()


# Setpoint
try:
    target_temp = float(input("Enter target temperature (°C): "))
except ValueError:
    print("Invalid temperature entered. Exiting.")
    exit()

# adjust parameters
print("\nDefault PID parameters: Kp=1.0, Ki=0.1, Kd=0.01")
adjust_pid = input("Do you want to adjust PID parameters? (y/n): ").lower()
if adjust_pid == 'y':
    try:
        kp = float(input("Enter Kp value: "))
        ki = float(input("Enter Ki value: "))
        kd = float(input("Enter Kd value: "))
    except ValueError:
        print("Invalid PID value entered. Using defaults.")
        kp, ki, kd = 1.0, 0.1, 0.01
else:
    kp, ki, kd = 1.0, 0.1, 0.01

# PID Initialization 

pid = PIDController(kp, ki, kd, target_temp)
pid.set_output_limits(min_current, max_current)

print(f"PID parameters: Kp={kp}, Ki={ki}, Kd={kd}")

# Plot Initialization 
plt.ion()  
fig, ax = plt.subplots()
temp_line, = ax.plot([], [], 'r-', label='Temperature (°C)')
current_line, = ax.plot([], [], 'b--', label='Set Current (A)') 
# Add a horizontal line for the setpoint
setpoint_line, = ax.plot([], [], 'g--', label=f'Target: {target_temp}°C')
ax2 = ax.twinx() 
ax2.set_ylabel('Set Current (A)', color='b')
ax2.tick_params(axis='y', labelcolor='b')
ax2.set_ylim(min_current - 0.1, max_current + 0.1) 

ax.set_xlabel('Time (s)')
ax.set_ylabel('Temperature (°C)', color='r')
ax.tick_params(axis='y', labelcolor='r')
ax.set_title(f'PID Tuning: Target Temp = {target_temp}°C')
ax.legend(loc='upper left')
ax.grid(True)

time_data = []
temp_data = []
current_data = []
start_loop_time = time.time() # For relative time axis

# --- Control Loop ---
print(f"\nStarting temperature control loop to reach {target_temp}°C")

# Make sure Korad commands are corrected as discussed previously!
try:
    PSU.output_on()
    PSU.set_current(min_current) # Set initial current
except Exception as e:
    print(f"Error communicating with Korad during setup: {e}")
    exit()


iteration = 0

# max_iterations = 100
last_time = time.time()

try:
    # while iteration < max_iterations:
    while True: 
        current_loop_time = time.time()
        elapsed_time = current_loop_time - start_loop_time

        #Measure temp 
        current_temperature = pyrometer.measure_temperature()

        # Skip iteration if temperature reading failed
        if current_temperature is None:
            print("Failed to read temperature, retrying...")
            # Optionally plot a NaN or skip plotting for this point
            time.sleep(control_interval)
            continue # Skip PID and plotting for this iteration

        #PID Calculation
        dt = current_loop_time - last_time
        if dt <= 0:
             time.sleep(control_interval) 
             continue

        last_time = current_loop_time

        pid_output = pid.compute(current_temperature, dt)

    
        # Clamp PID output to valid current range
        new_current = max(min_current, min(max_current, pid_output))

        # Set the new current 
       
        try:
            PSU.set_current(new_current)
        except Exception as e:
             print(f"Error setting Korad current: {e}. Skipping actuation.")
             # Decide how to proceed - stop loop? Continue?

    
        time_data.append(elapsed_time)
        temp_data.append(current_temperature)
        current_data.append(new_current)

        temp_line.set_data(time_data, temp_data)
        current_line.set_data(time_data, current_data)
        # Update the setpoint line
        setpoint_line.set_data([time_data[0], time_data[-1]], [target_temp, target_temp])

        ax.relim() # Recalculate axis limits
        ax.autoscale_view(True, True, True) # Autoscale x and primary y
        ax2.relim() # Recalculate limits for secondary axis
        ax2.autoscale_view(True, False, True) # Autoscale secondary y

        fig.canvas.draw() 
        fig.canvas.flush_events()
        plt.pause(0.01) # Small pause to allow plot to update

        # --- Status Print ---
        print(f"Time: {elapsed_time:6.1f}s | Temp: {current_temperature:6.2f}°C | "
              f"Set Current: {new_current:5.3f}A | Error: {target_temp - current_temperature:6.2f}°C | "
              f"PID Int: {pid.integral:8.2f}") # Assuming pid has .integral attribute

        if abs(current_temperature - target_temp) <= temperature_tolerance:
            print(f"Target temperature reached: {current_temperature}°C")
            break # for continuous tuning

   
        processing_time = time.time() - current_loop_time
        sleep_time = max(0, control_interval - processing_time)
        time.sleep(sleep_time)

        iteration += 1

    # if iteration >= max_iterations:
    #     print(f"Maximum iterations ({max_iterations}) reached")

except KeyboardInterrupt:
    print("\nControl loop interrupted.")
except Exception as e:
    print(f"\nAn error occurred in the control loop: {e}")
finally:
    # --- Cleanup ---
    print("Turning off power supply output")
    try:
        PSU.output_off()
        print("Power supply output turned off.")
    except Exception as e:
        print(f"Error turning off Korad output: {e}")

    plt.ioff() 
    print("Final plot:")
    plt.show() 
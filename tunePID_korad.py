# tune_korad.py
import time
import serial
import matplotlib.pyplot as plt
from Korad import Korad
from Pyrometer import Pyrometer
from PID import PIDController
from ZieglerNicholsAutoTuner import ZieglerNicholsAutoTuner
from AdaptivePIDController import AdaptivePIDController
from InputHandler import InputHandler 



PYROMETER_PORT = "/dev/cu.usbserial-B00378DF"  
PSU_PORT = "/dev/cu.usbmodem00273B64024C1"     

# Control parameters
max_current = 10  # Ampere
min_current = 0
control_interval = 0.5 # Time between control iterations in seconds 
temperature_tolerance = 0.5  # Temperature tolerance in degrees Celsius

# device initialization

try:
    pyrometer = Pyrometer(PYROMETER_PORT)
    PSU = Korad(PSU_PORT)
    pyrometer.set_emissivity(1) 
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

# PID parameter selection
print("\nPID Parameter Options:")
print("1. Use default parameters (Kp=1.0, Ki=0.1, Kd=0.01)")
print("2. Manually enter parameters")
print("3. Auto-tune using Ziegler-Nichols method")
print("4. Adaptive PID with automatic re-tuning")

while True:
    try:
        choice = input("Select option (1/2/3/4): ").strip()
        if choice in ['1', '2', '3', '4']:
            break
        else:
            print("Please enter 1, 2, 3, or 4")
    except KeyboardInterrupt:
        print("\nExiting...")
        exit()

if choice == '1':
    # Use default parameters
    kp, ki, kd = 1.0, 0.1, 0.01
    print(f"Using default parameters: Kp={kp}, Ki={ki}, Kd={kd}")
    
elif choice == '2':
    # Manual parameter entry
    try:
        kp = float(input("Enter Kp value: "))
        ki = float(input("Enter Ki value: "))
        kd = float(input("Enter Kd value: "))
    except ValueError:
        print("Invalid PID value entered. Using defaults.")
        kp, ki, kd = 1.0, 0.1, 0.01
        
elif choice == '3':
    # Auto-tuning using Ziegler-Nichols
    print("\nStarting Ziegler-Nichols Auto-Tuning...")
    print("This process will:")
    print("1. Find the critical gain (Kc) where oscillations occur")
    print("2. Measure the oscillation period (Tc)")
    print("3. Calculate optimal PID parameters")
    print("4. This may take several minutes and will cause temperature oscillations")
    
    confirm = input("Continue with auto-tuning? (y/n): ").lower()
    if confirm != 'y':
        print("Auto-tuning cancelled. Using default parameters.")
        kp, ki, kd = 1.0, 0.1, 0.01
    else:
        # Run auto-tuning
        auto_tuner = ZieglerNicholsAutoTuner(
            pyrometer=pyrometer,
            psu=PSU,
            target_temp=target_temp,
            max_current=max_current,
            min_current=min_current
        )
        
        print("\n" + "="*50)
        print("STARTING AUTO-TUNING PROCESS")
        print("="*50)
        
        tuning_success = auto_tuner.run_auto_tuning()
        
        if tuning_success:
            results = auto_tuner.get_tuning_results()
            kp = results['kp']
            ki = results['ki']
            kd = results['kd']
            
            print("\n" + "="*50)
            print("AUTO-TUNING COMPLETED SUCCESSFULLY!")
            print("="*50)
            print(f"Critical Gain (Kc): {results['critical_gain']:.4f}")
            print(f"Critical Period (Tc): {results['critical_period']:.2f}s")
            print(f"Calculated PID Parameters:")
            print(f"  Kp = {kp:.4f}")
            print(f"  Ki = {ki:.4f}")
            print(f"  Kd = {kd:.4f}")
            
            # Ask user if they want to use these parameters
            use_tuned = input("\nUse these auto-tuned parameters? (y/n): ").lower()
            if use_tuned != 'y':
                print("Using default parameters instead.")
                kp, ki, kd = 1.0, 0.1, 0.01
        else:
            print("\n" + "="*50)
            print("AUTO-TUNING FAILED!")
            print("="*50)
            print("Using default parameters instead.")
            kp, ki, kd = 1.0, 0.1, 0.01

elif choice == '4':
    # Adaptive PID with automatic re-tuning
    print("\nAdaptive PID with Automatic Re-tuning")
    print("This mode will:")
    print("1. Start with auto-tuned parameters or defaults")
    print("2. Continuously monitor system performance")
    print("3. Automatically re-tune when performance degrades")
    print("4. Provide real-time status and logging")
    print("5. Support manual re-tuning trigger (press 'r' during operation)")
    
    use_initial_autotune = input("\nPerform initial auto-tuning? (y/n): ").lower()
    
    if use_initial_autotune == 'y':
        print("\nPerforming initial auto-tuning...")
        auto_tuner = ZieglerNicholsAutoTuner(
            pyrometer=pyrometer,
            psu=PSU,
            target_temp=target_temp,
            max_current=max_current,
            min_current=min_current
        )
        
        tuning_success = auto_tuner.run_auto_tuning()
        
        if tuning_success:
            results = auto_tuner.get_tuning_results()
            kp = results['kp']
            ki = results['ki']
            kd = results['kd']
            print(f"Initial auto-tuning successful: Kp={kp:.4f}, Ki={ki:.4f}, Kd={kd:.4f}")
        else:
            print("Initial auto-tuning failed. Using default parameters.")
            kp, ki, kd = 1.0, 0.1, 0.01
    else:
        kp, ki, kd = 1.0, 0.1, 0.01
        print("Using default parameters for adaptive PID start")
    
    # Create adaptive PID controller
    adaptive_pid = AdaptivePIDController(
        pyrometer=pyrometer,
        psu=PSU,
        target_temp=target_temp,
        max_current=max_current,
        min_current=min_current
    )
    
    # Initialize with parameters
    adaptive_pid.initialize_pid(kp, ki, kd)
    
    # Skip traditional PID setup and use adaptive controller
    use_adaptive_controller = True

# Traditional PID setup (only if not using adaptive controller)
if choice != '4':
    use_adaptive_controller = False

# PID Initialization 

if not use_adaptive_controller:
    pid = PIDController(kp, ki, kd, target_temp)
    pid.set_output_limits(min_current, max_current)

print(f"PID parameters: Kp={kp}, Ki={ki}, Kd={kd}")

# Plot Initialization 
plt.ion()  
fig, ax = plt.subplots()
temp_line, = ax.plot([], [], 'r-', label='Temperature (°C)')
# Add a horizontal line for the setpoint
setpoint_line, = ax.plot([], [], 'g--', label=f'Target: {target_temp}°C')
ax2 = ax.twinx() 
current_line, = ax2.plot([], [], 'b--', label='Set Current (A)') 
ax2.set_ylabel('Set Current (A)', color='b')
ax2.tick_params(axis='y', labelcolor='b')
ax2.set_ylim(min_current - 0.1, max_current + 0.1) 

ax.set_xlabel('Time (s)')
ax.set_ylabel('Temperature (°C)', color='r')
ax.tick_params(axis='y', labelcolor='r')
ax.set_title(f'PID Tuning: Target Temp = {target_temp}°C')

# Combine legends from both axes
lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
ax.grid(True)

time_data = []
temp_data = []
current_data = []
start_loop_time = time.time() # For relative time axis

# --- Control Loop ---
print(f"\nStarting temperature control loop to reach {target_temp}°C")

# Initialize Korad PSU
try:
    # Set voltage first (important for heating elements)
    PSU.set_voltage(30.0)  # Set appropriate voltage for your heating element
    PSU.set_current(min_current)  # Set initial current
    PSU.output_on()
except Exception as e:
    print(f"Error communicating with Korad during setup: {e}")
    exit()


iteration = 0

# max_iterations = 100
last_time = time.time()

# Setup input handler for manual re-tuning
input_handler = None
if use_adaptive_controller:
    input_handler = InputHandler()
    input_handler.start()
    print("Manual re-tuning available: Type 'r' + Enter during operation")

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

        if use_adaptive_controller:
            # Check for manual re-tuning command
            if input_handler and input_handler.has_command():
                command = input_handler.get_command()
                if command and command.lower() == 'r':
                    print("Manual re-tuning requested...")
                    success, message = adaptive_pid.manual_retune()
                    print(f"Manual re-tuning: {message}")
            
            # Use adaptive PID controller
            new_current = adaptive_pid.compute_control_output(current_temperature, dt)
            
            # Check if re-tuning is needed
            adaptive_pid.check_retune_needed()
            
            # Check system health
            if not adaptive_pid.is_system_healthy():
                print("System health check failed. Stopping.")
                break
                
        else:
            # Use traditional PID controller
            pid_output = pid.compute(current_temperature, dt)
            new_current = pid_output

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
        # Update the setpoint line (only if we have data)
        if len(time_data) > 0:
            setpoint_line.set_data([time_data[0], time_data[-1]], [target_temp, target_temp])

        ax.relim() # Recalculate axis limits
        ax.autoscale_view(True, True, True) # Autoscale x and primary y
        ax2.relim() # Recalculate limits for secondary axis
        ax2.autoscale_view(True, False, True) # Autoscale secondary y

        fig.canvas.draw() 
        fig.canvas.flush_events()
        plt.pause(0.01) # Small pause to allow plot to update

        # --- Status Print ---
        if use_adaptive_controller:
            # Enhanced status display for adaptive PID
            if iteration % 10 == 0:  # Every 10 iterations (about 5 seconds)
                status_lines = adaptive_pid.get_status_display()
                print("\n" + "="*60)
                for line in status_lines:
                    print(line)
                print("="*60)
                print("Press 'r' + Enter for manual re-tuning | Ctrl+C to exit")
        else:
            # Traditional status display
            print(f"Time: {elapsed_time:6.1f}s | Temp: {current_temperature:6.2f}°C | "
                  f"Set Current: {new_current:5.3f}A | Error: {target_temp - current_temperature:6.2f}°C | "
                  f"PID Int: {pid.integral:8.2f}") # Assuming pid has .integral attribute

        if abs(current_temperature - target_temp) <= temperature_tolerance:
            if iteration % 2 == 0:  # Print status every 10 iterations when at target
                print(f"✓ Maintaining target temperature: {current_temperature}°C")

   
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
    
    # Cleanup adaptive PID if used
    if use_adaptive_controller:
        print("Cleaning up adaptive PID controller...")
        adaptive_pid.cleanup()
        
    # Cleanup input handler
    if input_handler:
        input_handler.stop()

    plt.ioff() 
    print("Final plot:")
    plt.show() 
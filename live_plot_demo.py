#!/usr/bin/env python3
"""
Live updating plot demonstration
"""

import matplotlib.pyplot as plt
import numpy as np
import time

def live_plot_demo():
    """Demonstrate live updating dual-axis plot"""
    print("Starting live plot demo...")
    print("Press Ctrl+C to stop")
    
    # Setup live plotting
    plt.ion()  # Turn on interactive mode
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # Temperature on primary axis (left)
    temp_line, = ax1.plot([], [], 'r-', linewidth=2, label='Temperature (°C)')
    target_line, = ax1.plot([], [], 'g--', linewidth=2, label='Target: 50°C')
    
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Temperature (°C)', color='r')
    ax1.tick_params(axis='y', labelcolor='r')
    ax1.set_title('Live PID Control Simulation')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 30)
    ax1.set_ylim(15, 60)
    
    # Current on secondary axis (right)
    ax2 = ax1.twinx()
    current_line, = ax2.plot([], [], 'b-', linewidth=2, label='Current (A)')
    ax2.set_ylabel('Current (A)', color='b')
    ax2.tick_params(axis='y', labelcolor='b')
    ax2.set_ylim(0, 7)
    
    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    # Data storage
    time_data = []
    temp_data = []
    current_data = []
    
    # Simulation parameters
    target_temp = 50.0
    current_temp = 20.0
    start_time = time.time()
    
    try:
        while True:
            # Update simulation
            elapsed = time.time() - start_time
            
            # Simple heating simulation
            error = target_temp - current_temp
            heating_power = min(6.0, max(0.0, error * 0.2))  # Simple P controller
            
            # Temperature physics (simplified)
            heat_rate = heating_power * 2.0  # Heat from current
            cooling_rate = (current_temp - 20) * 0.1  # Heat loss to ambient
            current_temp += (heat_rate - cooling_rate) * 0.1
            
            # Add some noise
            measured_temp = current_temp + np.random.normal(0, 0.3)
            measured_current = heating_power + np.random.normal(0, 0.05)
            
            # Store data
            time_data.append(elapsed)
            temp_data.append(measured_temp)
            current_data.append(measured_current)
            
            # Keep only last 300 points (30 seconds at 0.1s intervals)
            if len(time_data) > 300:
                time_data = time_data[-300:]
                temp_data = temp_data[-300:]
                current_data = current_data[-300:]
            
            # Update plot data
            temp_line.set_data(time_data, temp_data)
            current_line.set_data(time_data, current_data)
            
            # Update target line
            if len(time_data) > 1:
                target_line.set_data([time_data[0], time_data[-1]], [target_temp, target_temp])
            
            # Update x-axis to show rolling window
            if len(time_data) > 1:
                ax1.set_xlim(max(0, elapsed - 30), elapsed + 1)
            
            # Refresh the plot
            fig.canvas.draw()
            fig.canvas.flush_events()
            
            # Print status
            if len(time_data) % 20 == 0:  # Every 2 seconds
                print(f"Time: {elapsed:5.1f}s | Temp: {measured_temp:5.1f}°C | "
                      f"Current: {measured_current:4.1f}A | Error: {error:5.1f}°C")
            
            # Sleep to control update rate
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nStopping live demo...")
    
    plt.ioff()
    print("Demo complete. Close the plot window to exit.")
    plt.show(block=True)

if __name__ == "__main__":
    live_plot_demo()
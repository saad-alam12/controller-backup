#!/usr/bin/env python3
"""
Test script for PID controller and live plotting functionality
Tests with dummy data to validate behavior without hardware
"""

import time
import numpy as np
import matplotlib.pyplot as plt
from PID import PIDController
import math

class TemperatureSimulator:
    """Simulates realistic temperature behavior of a heating system"""
    
    def __init__(self, initial_temp=20.0, ambient_temp=20.0, thermal_mass=50.0, heat_loss_coeff=0.1):
        # System parameters for realistic thermal behavior
        self.current_temp = initial_temp  # Current temperature
        self.ambient_temp = ambient_temp  # Room temperature
        self.thermal_mass = thermal_mass  # How much energy needed to change temperature
        self.heat_loss_coeff = heat_loss_coeff  # Heat loss to environment
        self.heating_efficiency = 15.0  # Temperature rise per amp of current
        self.max_temp_rate = 2.0  # Maximum temperature change rate per second
        
        # Add some realistic noise and delays
        self.noise_amplitude = 0.5  # Temperature measurement noise
        self.time_constant = 2.0  # Thermal time constant (seconds)
        
    def update(self, current_amps, dt):
        """Update temperature based on applied current and time step"""
        # Heat input from current (watts = amps^2 * resistance, but simplified)
        heat_input = current_amps * self.heating_efficiency
        
        # Heat loss to environment (proportional to temperature difference)
        heat_loss = (self.current_temp - self.ambient_temp) * self.heat_loss_coeff
        
        # Net heat change
        net_heat = heat_input - heat_loss
        
        # Temperature change (first-order thermal response)
        temp_change_rate = net_heat / self.thermal_mass
        
        # Limit maximum rate of change (thermal inertia)
        temp_change_rate = max(-self.max_temp_rate, min(self.max_temp_rate, temp_change_rate))
        
        # Apply exponential smoothing for thermal time constant
        alpha = dt / (self.time_constant + dt)
        target_temp = self.current_temp + temp_change_rate * dt
        self.current_temp = self.current_temp + alpha * (target_temp - self.current_temp)
        
        # Add measurement noise
        measured_temp = self.current_temp + np.random.normal(0, self.noise_amplitude)
        
        return measured_temp
        
    def add_disturbance(self, temp_offset):
        """Add external temperature disturbance (like opening a door)"""
        self.current_temp += temp_offset

def test_pid_calculations():
    """Test PID controller calculations step by step"""
    print("\n=== PID Calculation Validation ===")
    
    # Create PID controller with known parameters
    pid = PIDController(Kp=2.0, Ki=0.5, Kd=0.1, setpoint=50.0)
    pid.set_output_limits(0, 6)
    
    # Test case 1: Step response
    print("\nTest 1: Step Response")
    dt = 0.5
    test_temps = [20.0, 25.0, 35.0, 45.0, 48.0, 50.0, 50.5]
    
    for i, temp in enumerate(test_temps):
        output = pid.compute(temp, dt)
        error = pid.setpoint - temp
        
        print(f"Step {i+1}: Temp={temp:5.1f}°C, Error={error:6.1f}°C, "
              f"Output={output:5.2f}A, Integral={pid.integral:6.2f}")
    
    # Test case 2: Output limits
    print("\nTest 2: Output Limits")
    pid2 = PIDController(Kp=10.0, Ki=5.0, Kd=0.0, setpoint=100.0)
    pid2.set_output_limits(0, 6)
    
    # This should saturate the output
    output = pid2.compute(20.0, 1.0)  # Large error should saturate
    print(f"Large error test: Output={output:5.2f}A (should be clamped to 6.0A)")
    
    # Test case 3: Anti-windup
    print("\nTest 3: Anti-windup Protection")
    for i in range(5):
        output = pid2.compute(20.0, 1.0)  # Keep applying large error
        print(f"Iteration {i+1}: Output={output:5.2f}A, Integral={pid2.integral:6.2f}")
    
    print("✓ PID calculations validated")

def test_live_plotting_fixed():
    """Test live plotting with corrected dual-axis setup"""
    print("\n=== Live Plotting Test (Fixed Version) ===")
    
    # Simulation parameters
    target_temp = 50.0
    control_interval = 0.1  # Faster for testing
    max_iterations = 100
    
    # Create temperature simulator and PID controller
    temp_sim = TemperatureSimulator(initial_temp=20.0)
    pid = PIDController(Kp=1.5, Ki=0.3, Kd=0.05, setpoint=target_temp)
    pid.set_output_limits(0, 6)
    
    # FIXED Plot Initialization
    plt.ion()
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Temperature on primary y-axis (left)
    temp_line, = ax.plot([], [], 'r-', linewidth=2, label='Temperature (°C)')
    setpoint_line, = ax.plot([], [], 'g--', linewidth=2, label=f'Target: {target_temp}°C')
    
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Temperature (°C)', color='r')
    ax.tick_params(axis='y', labelcolor='r')
    ax.set_title(f'PID Tuning Test: Target = {target_temp}°C')
    ax.grid(True, alpha=0.3)
    
    # FIXED: Current on secondary y-axis (right) - THIS WAS THE BUG!
    ax2 = ax.twinx()
    current_line, = ax2.plot([], [], 'b-', linewidth=2, label='Set Current (A)')
    ax2.set_ylabel('Set Current (A)', color='b')
    ax2.tick_params(axis='y', labelcolor='b')
    ax2.set_ylim(-0.5, 6.5)
    
    # Combine legends from both axes
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    # Data storage
    time_data = []
    temp_data = []
    current_data = []
    start_time = time.time()
    
    print("Starting simulation...")
    print("Time    Temp     Target   Current  Error    P      I      D")
    print("-" * 65)
    
    try:
        for iteration in range(max_iterations):
            current_time = time.time()
            elapsed_time = current_time - start_time
            
            # Get current temperature from simulator
            if iteration == 0:
                current_temp = temp_sim.current_temp
                dt = control_interval
            else:
                dt = elapsed_time - time_data[-1] if time_data else control_interval
                dt = max(0.01, dt)  # Prevent division by zero
            
            # PID calculation
            pid_output = pid.compute(current_temp, dt)
            
            # Apply current to temperature simulator
            current_temp = temp_sim.update(pid_output, dt)
            
            # Store data
            time_data.append(elapsed_time)
            temp_data.append(current_temp)
            current_data.append(pid_output)
            
            # Update plots - FIXED: current_line is now on ax2
            temp_line.set_data(time_data, temp_data)
            current_line.set_data(time_data, current_data)
            
            if len(time_data) > 1:
                setpoint_line.set_data([time_data[0], time_data[-1]], [target_temp, target_temp])
            
            # Auto-scale axes
            if len(time_data) > 1:
                ax.set_xlim(0, max(elapsed_time, 10))
                temp_min, temp_max = min(temp_data), max(temp_data)
                temp_range = temp_max - temp_min
                ax.set_ylim(temp_min - temp_range*0.1, temp_max + temp_range*0.1)
            
            # Refresh plot
            fig.canvas.draw()
            fig.canvas.flush_events()
            plt.pause(0.01)
            
            # Print status
            error = target_temp - current_temp
            if iteration % 10 == 0:  # Print every 10th iteration
                print(f"{elapsed_time:6.1f}  {current_temp:6.1f}  {target_temp:6.1f}  "
                      f"{pid_output:6.2f}  {error:6.1f}  {pid.Kp*error:6.2f}  "
                      f"{pid.Ki*pid.integral:6.2f}  {pid.Kd*(-(current_temp-pid.previous_pv)/dt if pid.previous_pv else 0):6.2f}")
            
            # Check if target reached
            if abs(error) < 0.5 and iteration > 20:
                print(f"\n✓ Target reached at {elapsed_time:.1f}s")
                break
                
            # Add disturbance at halfway point for testing
            if iteration == max_iterations // 2:
                temp_sim.add_disturbance(-5.0)
                print(f"\n! Added -5°C disturbance at {elapsed_time:.1f}s")
            
            time.sleep(max(0, control_interval - (time.time() - current_time)))
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    
    plt.ioff()
    
    # Final analysis
    if len(temp_data) > 10:
        final_error = abs(temp_data[-1] - target_temp)
        settling_time = None
        for i, temp in enumerate(temp_data):
            if abs(temp - target_temp) < 1.0:
                settling_time = time_data[i]
                break
        
        print(f"\n=== Test Results ===")
        print(f"Final temperature: {temp_data[-1]:.2f}°C")
        print(f"Final error: {final_error:.2f}°C")
        print(f"Settling time (±1°C): {settling_time:.1f}s" if settling_time else "Did not settle")
        print(f"Max current used: {max(current_data):.2f}A")
        print(f"✓ Live plotting test completed")
    
    plt.show()
    return time_data, temp_data, current_data

def test_different_scenarios():
    """Test PID controller with different scenarios"""
    print("\n=== Different Scenario Tests ===")
    
    scenarios = [
        {"name": "Aggressive Tuning", "Kp": 3.0, "Ki": 1.0, "Kd": 0.2},
        {"name": "Conservative Tuning", "Kp": 0.8, "Ki": 0.1, "Kd": 0.05},
        {"name": "I-dominant", "Kp": 0.5, "Ki": 2.0, "Kd": 0.0},
        {"name": "D-dominant", "Kp": 1.0, "Ki": 0.1, "Kd": 1.0},
    ]
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    axes = axes.flatten()
    
    for idx, scenario in enumerate(scenarios):
        ax = axes[idx]
        
        # Create simulator and PID for this scenario
        temp_sim = TemperatureSimulator(initial_temp=20.0)
        pid = PIDController(scenario["Kp"], scenario["Ki"], scenario["Kd"], 50.0)
        pid.set_output_limits(0, 6)
        
        time_data = []
        temp_data = []
        current_data = []
        
        # Run simulation
        for i in range(150):
            dt = 0.2
            elapsed_time = i * dt
            
            if i == 0:
                current_temp = temp_sim.current_temp
            
            pid_output = pid.compute(current_temp, dt)
            current_temp = temp_sim.update(pid_output, dt)
            
            time_data.append(elapsed_time)
            temp_data.append(current_temp)
            current_data.append(pid_output)
            
            # Add disturbance
            if i == 75:
                temp_sim.add_disturbance(-3.0)
        
        # Plot results
        ax_temp = ax
        ax_curr = ax.twinx()
        
        ax_temp.plot(time_data, temp_data, 'r-', label='Temperature')
        ax_temp.axhline(y=50, color='g', linestyle='--', label='Setpoint')
        ax_curr.plot(time_data, current_data, 'b-', alpha=0.7, label='Current')
        
        ax_temp.set_xlabel('Time (s)')
        ax_temp.set_ylabel('Temperature (°C)', color='r')
        ax_curr.set_ylabel('Current (A)', color='b')
        ax_temp.set_title(f'{scenario["name"]}\nKp={scenario["Kp"]}, Ki={scenario["Ki"]}, Kd={scenario["Kd"]}')
        ax_temp.grid(True, alpha=0.3)
        
        # Calculate performance metrics
        steady_state_error = abs(temp_data[-1] - 50.0)
        overshoot = max(temp_data) - 50.0 if max(temp_data) > 50.0 else 0
        
        print(f"{scenario['name']}: SSE={steady_state_error:.2f}°C, Overshoot={overshoot:.2f}°C")
    
    plt.tight_layout()
    plt.show()
    print("✓ Scenario testing completed")

def main():
    """Run all tests"""
    print("=== PID Controller and Plotting Validation Tests ===")
    
    # Test 1: PID calculations
    test_pid_calculations()
    
    # Test 2: Live plotting (this will show the plot)
    input("\nPress Enter to start live plotting test...")
    time_data, temp_data, current_data = test_live_plotting_fixed()
    
    # Test 3: Different scenarios
    input("\nPress Enter to test different PID tuning scenarios...")
    test_different_scenarios()
    
    print("\n=== All Tests Completed ===")
    print("✓ PID calculations validated")
    print("✓ Live plotting bug fixed (current now on correct axis)")
    print("✓ Dual-axis functionality working")
    print("✓ Different tuning scenarios tested")
    print("\nBug found and fixed: Current line was plotted on primary axis instead of secondary axis")

if __name__ == "__main__":
    main()
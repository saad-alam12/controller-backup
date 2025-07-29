#!/usr/bin/env python3
"""
Test Mode 4 (Adaptive PID) without real hardware
This script simulates the complete Mode 4 experience
"""

import time
import numpy as np
import matplotlib.pyplot as plt
from AdaptivePIDController import AdaptivePIDController

class MockPyrometer:
    """Simulates a pyrometer with realistic thermal behavior"""
    def __init__(self, target_temp):
        self.target_temp = target_temp
        self.current_temp = 25.0  # Room temperature start
        self.thermal_mass = 0.1   # Thermal response speed
        self.noise_level = 0.5    # Temperature reading noise
        self.disturbance = 0.0    # External disturbances
        
    def measure_temperature(self):
        """Simulate temperature measurement with noise"""
        noise = np.random.normal(0, self.noise_level)
        return self.current_temp + noise + self.disturbance
        
    def update_temperature(self, current_input, dt):
        """Update temperature based on heater current"""
        # Simple thermal model
        heat_input = current_input * 20  # 20°C per Ampere heating rate
        cooling_rate = (self.current_temp - 25) * 0.02  # Natural cooling
        
        temp_change = (heat_input - cooling_rate) * dt * self.thermal_mass
        self.current_temp += temp_change
        
    def add_disturbance(self, disturbance):
        """Add external disturbance (like door opening, airflow, etc.)"""
        self.disturbance = disturbance

class MockPSU:
    """Simulates a power supply unit"""
    def __init__(self):
        self.current_setting = 0.0
        self.voltage_setting = 30.0
        self.output_enabled = False
        
    def set_current(self, current):
        self.current_setting = max(0, min(10, current))  # 0-10A range
        
    def set_voltage(self, voltage):
        self.voltage_setting = voltage
        
    def output_on(self):
        self.output_enabled = True
        print("PSU Output ON")
        
    def output_off(self):
        self.output_enabled = False
        print("PSU Output OFF")

def simulate_mode4_operation():
    """Simulate complete Mode 4 operation"""
    print("🚀 Testing Mode 4: Adaptive PID with Automatic Re-tuning")
    print("="*60)
    
    # Create mock devices
    target_temp = 200.0
    pyrometer = MockPyrometer(target_temp)
    psu = MockPSU()
    
    # Create adaptive PID controller (same as Mode 4)
    adaptive_pid = AdaptivePIDController(
        pyrometer=pyrometer,
        psu=psu,
        target_temp=target_temp,
        max_current=10,
        min_current=0
    )
    
    print(f"🎯 Target Temperature: {target_temp}°C")
    print("🔧 Initializing adaptive PID controller...")
    
    # Initialize with default parameters (like Mode 4 without initial auto-tuning)
    adaptive_pid.initialize_pid(0.1, 0.05, 0.02)
    
    # Turn on PSU
    psu.output_on()
    
    # Simulation parameters
    dt = 0.5  # Control interval
    total_time = 300  # 5 minutes simulation
    iterations = int(total_time / dt)
    
    # Data storage for plotting
    time_data = []
    temp_data = []
    current_data = []
    stability_scores = []
    
    print("🔄 Starting control loop simulation...")
    print("   (This simulates what you'd see in Mode 4)")
    print()
    
    try:
        for i in range(iterations):
            current_time = i * dt
            
            # Update temperature based on PSU output
            pyrometer.update_temperature(psu.current_setting, dt)
            
            # Measure temperature
            temp = pyrometer.measure_temperature()
            
            # Compute control output (this is the core of Mode 4)
            control_output = adaptive_pid.compute_control_output(temp, dt)
            
            # Update PSU
            psu.set_current(control_output)
            
            # Check for re-tuning (automatic stability monitoring)
            adaptive_pid.check_retune_needed()
            
            # Store data
            time_data.append(current_time)
            temp_data.append(temp)
            current_data.append(control_output)
            
            # Get status
            status = adaptive_pid.get_control_status()
            stability_scores.append(status['stability']['stability_score'])
            
            # Add disturbances to test re-tuning
            if i == 120:  # 1 minute in
                print("⚠️  Adding disturbance (simulating door opening)...")
                pyrometer.add_disturbance(-5)  # Sudden cooling
                
            if i == 240:  # 2 minutes in
                print("⚠️  Adding another disturbance (simulating airflow)...")
                pyrometer.add_disturbance(3)   # Sudden heating
                
            # Display status like Mode 4 (every 10 seconds)
            if i % 20 == 0:
                status_lines = adaptive_pid.get_status_display()
                print(f"⏰ Time: {current_time:.0f}s")
                for line in status_lines:
                    print(f"   {line}")
                print()
                
            # Check system health
            if not adaptive_pid.is_system_healthy():
                print("❌ System health check failed!")
                break
                
            # Simulate manual re-tuning command at 3 minutes
            if i == 360:  # 3 minutes
                print("🔧 Simulating manual re-tuning command...")
                success, message = adaptive_pid.manual_retune()
                print(f"   {message}")
                
    except KeyboardInterrupt:
        print("\n⏹️  Simulation interrupted by user")
        
    finally:
        # Cleanup (like Mode 4 does)
        print("\n🔧 Cleaning up...")
        psu.output_off()
        adaptive_pid.cleanup()
        
        # Show final statistics
        final_status = adaptive_pid.get_control_status()
        print("\n📊 Final Results:")
        print(f"   Total runtime: {current_time:.0f}s")
        print(f"   Successful re-tunes: {final_status['successful_retunes']}")
        print(f"   Failed re-tunes: {final_status['failed_retunes']}")
        print(f"   Final stability score: {final_status['stability']['stability_score']:.1f}/100")
        print(f"   Final temperature: {temp:.1f}°C (target: {target_temp}°C)")
        print(f"   Final output: {control_output:.2f}A")
        
        # Plot results (like Mode 4 does)
        plt.figure(figsize=(12, 8))
        
        # Temperature plot
        plt.subplot(3, 1, 1)
        plt.plot(time_data, temp_data, 'r-', label='Temperature')
        plt.axhline(y=target_temp, color='g', linestyle='--', label=f'Target: {target_temp}°C')
        plt.ylabel('Temperature (°C)')
        plt.legend()
        plt.title('Mode 4 Simulation Results')
        plt.grid(True)
        
        # Current plot
        plt.subplot(3, 1, 2)
        plt.plot(time_data, current_data, 'b-', label='Output Current')
        plt.ylabel('Current (A)')
        plt.legend()
        plt.grid(True)
        
        # Stability score plot
        plt.subplot(3, 1, 3)
        plt.plot(time_data, stability_scores, 'purple', label='Stability Score')
        plt.axhline(y=70, color='orange', linestyle='--', label='Re-tuning Threshold')
        plt.ylabel('Stability Score')
        plt.xlabel('Time (s)')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        plt.show()
        
        print("\n✅ Mode 4 simulation completed successfully!")
        print("   This demonstrates all the features you'd get with real hardware.")

if __name__ == "__main__":
    simulate_mode4_operation()
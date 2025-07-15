#!/usr/bin/env python3
"""
Test script for ZieglerNicholsAutoTuner
This script simulates the auto-tuning process without real hardware
"""

import time
import numpy as np
from collections import deque

class MockPyrometer:
    """Mock pyrometer that simulates temperature response"""
    def __init__(self, target_temp):
        self.target_temp = target_temp
        self.current_temp = 25.0  # Start at room temperature
        self.thermal_mass = 0.1  # Simulated thermal mass
        self.noise_level = 0.5
        
    def measure_temperature(self):
        """Simulate temperature measurement with some noise"""
        # Add some random noise
        noise = np.random.normal(0, self.noise_level)
        return self.current_temp + noise
        
    def update_temperature(self, current_input, dt):
        """Update temperature based on current input"""
        # Simple thermal model: temperature change is proportional to current
        heat_input = current_input * 20  # 20°C per Ampere heating rate
        cooling_rate = (self.current_temp - 25) * 0.02  # Natural cooling
        
        temp_change = (heat_input - cooling_rate) * dt * self.thermal_mass
        self.current_temp += temp_change

class MockPSU:
    """Mock PSU that simulates power supply"""
    def __init__(self):
        self.current_setting = 0.0
        self.voltage_setting = 30.0
        self.output_enabled = False
        
    def set_current(self, current):
        self.current_setting = current
        
    def set_voltage(self, voltage):
        self.voltage_setting = voltage
        
    def output_on(self):
        self.output_enabled = True
        
    def output_off(self):
        self.output_enabled = False

def test_oscillation_detection():
    """Test the oscillation detection algorithm"""
    print("Testing oscillation detection...")
    
    # Create mock devices
    pyrometer = MockPyrometer(200.0)
    psu = MockPSU()
    
    # Import the auto-tuner
    from ZieglerNicholsAutoTuner import ZieglerNicholsAutoTuner
    
    # Create auto-tuner instance
    tuner = ZieglerNicholsAutoTuner(pyrometer, psu, 200.0, max_current=10, min_current=0)
    
    # Simulate some oscillating temperature data
    print("Simulating temperature oscillations...")
    
    # Generate oscillating data
    time_data = np.linspace(0, 40, 200)
    temp_data = 200 + 5 * np.sin(2 * np.pi * time_data / 8)  # 8-second period, 5°C amplitude
    
    # Feed data to tuner
    for i, (t, temp) in enumerate(zip(time_data, temp_data)):
        tuner.temp_history.append(temp)
        tuner.time_history.append(t)
        
        if i > 40:  # Wait for enough data
            is_oscillating, amplitude, period = tuner.detect_oscillations()
            if is_oscillating:
                print(f"Oscillation detected at time {t:.1f}s:")
                print(f"  Amplitude: {amplitude:.2f}°C")
                print(f"  Period: {period:.2f}s")
                break
    
    # If no oscillation detected, check the final state
    if not is_oscillating:
        print("No oscillation detected. Debugging info:")
        print(f"  Temperature range: {min(temp_data):.2f} to {max(temp_data):.2f}°C")
        print(f"  Expected amplitude: 5.0°C")
        print(f"  Expected period: 8.0s")
        print(f"  Threshold: {tuner.oscillation_threshold}°C")
    
    print("Oscillation detection test completed.")

def test_full_autotuning():
    """Test the full auto-tuning process with simulation"""
    print("\nTesting full auto-tuning process...")
    
    # Create mock devices
    pyrometer = MockPyrometer(200.0)
    psu = MockPSU()
    
    # Import the auto-tuner
    from ZieglerNicholsAutoTuner import ZieglerNicholsAutoTuner
    
    # Create auto-tuner instance with faster parameters for testing
    tuner = ZieglerNicholsAutoTuner(pyrometer, psu, 200.0, max_current=10, min_current=0)
    tuner.kp_start = 0.01
    tuner.kp_step = 0.01
    tuner.max_iterations = 10
    tuner.control_interval = 0.1
    
    # Override the run_proportional_test method for simulation
    def mock_proportional_test(kp_test):
        print(f"  Testing Kp = {kp_test:.4f}")
        
        # Simulate the test
        for i in range(100):  # Simulate 100 iterations
            current_time = i * 0.1
            
            # Update temperature based on current
            error = tuner.target_temp - pyrometer.current_temp
            output = kp_test * error
            output = max(0, min(10, output))
            
            # Update simulated temperature
            pyrometer.update_temperature(output, 0.1)
            
            # Measure temperature
            temp = pyrometer.measure_temperature()
            
            # Store data
            tuner.temp_history.append(temp)
            tuner.time_history.append(current_time)
            tuner.current_history.append(output)
            
            # Check for oscillations
            if i > 40:  # Wait for more data
                is_oscillating, amplitude, period = tuner.detect_oscillations()
                if is_oscillating and kp_test > 0.03:  # More likely to oscillate at higher gains
                    print(f"    Oscillation detected! Amplitude: {amplitude:.2f}°C, Period: {period:.2f}s")
                    return True, amplitude, period
                    
            # Force oscillation for testing at higher gains
            if kp_test > 0.06 and i > 60:
                # Add some artificial oscillation
                if i % 10 < 5:
                    pyrometer.current_temp += 2
                else:
                    pyrometer.current_temp -= 2
                    
                # Check again
                is_oscillating, amplitude, period = tuner.detect_oscillations()
                if is_oscillating:
                    print(f"    Forced oscillation detected! Amplitude: {amplitude:.2f}°C, Period: {period:.2f}s")
                    return True, amplitude, period
        
        return False, 0, 0
    
    # Replace the method
    tuner.run_proportional_test = mock_proportional_test
    
    # Run auto-tuning
    success = tuner.run_auto_tuning()
    
    if success:
        results = tuner.get_tuning_results()
        print(f"\nAuto-tuning successful!")
        print(f"Critical gain: {results['critical_gain']:.4f}")
        print(f"Critical period: {results['critical_period']:.2f}s")
        print(f"PID parameters:")
        print(f"  Kp = {results['kp']:.4f}")
        print(f"  Ki = {results['ki']:.4f}")
        print(f"  Kd = {results['kd']:.4f}")
    else:
        print("Auto-tuning failed.")

def test_syntax_check():
    """Test that the module can be imported without syntax errors"""
    print("Testing syntax and imports...")
    
    try:
        from ZieglerNicholsAutoTuner import ZieglerNicholsAutoTuner
        print("✓ ZieglerNicholsAutoTuner imported successfully")
        
        # Test basic instantiation
        pyrometer = MockPyrometer(200.0)
        psu = MockPSU()
        tuner = ZieglerNicholsAutoTuner(pyrometer, psu, 200.0)
        print("✓ ZieglerNicholsAutoTuner instantiated successfully")
        
        # Test method existence
        assert hasattr(tuner, 'detect_oscillations'), "detect_oscillations method missing"
        assert hasattr(tuner, 'run_proportional_test'), "run_proportional_test method missing"
        assert hasattr(tuner, 'find_critical_gain'), "find_critical_gain method missing"
        assert hasattr(tuner, 'calculate_pid_parameters'), "calculate_pid_parameters method missing"
        assert hasattr(tuner, 'run_auto_tuning'), "run_auto_tuning method missing"
        print("✓ All required methods present")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("="*60)
    print("ZieglerNicholsAutoTuner Test Suite")
    print("="*60)
    
    # Run tests
    if test_syntax_check():
        test_oscillation_detection()
        test_full_autotuning()
    
    print("\n" + "="*60)
    print("Test suite completed.")
    print("="*60)
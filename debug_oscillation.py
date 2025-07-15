#!/usr/bin/env python3
"""
Debug script to test oscillation detection algorithm
"""

import numpy as np
import matplotlib.pyplot as plt
from ZieglerNicholsAutoTuner import ZieglerNicholsAutoTuner

class MockPyrometer:
    def __init__(self, target_temp):
        self.target_temp = target_temp
        self.current_temp = 25.0
        
    def measure_temperature(self):
        return self.current_temp

class MockPSU:
    def __init__(self):
        self.current_setting = 0.0
        
    def set_current(self, current):
        self.current_setting = current
        
    def set_voltage(self, voltage):
        pass
        
    def output_on(self):
        pass
        
    def output_off(self):
        pass

def debug_oscillation_detection():
    """Debug the oscillation detection with known oscillating data"""
    
    # Create tuner
    pyrometer = MockPyrometer(200.0)
    psu = MockPSU()
    tuner = ZieglerNicholsAutoTuner(pyrometer, psu, 200.0)
    
    # Generate perfect oscillating data
    time_data = np.linspace(0, 40, 200)
    temp_data = 200 + 5 * np.sin(2 * np.pi * time_data / 8)  # 8-second period, 5°C amplitude
    
    print("Generated test data:")
    print(f"  Time range: {time_data[0]:.1f} to {time_data[-1]:.1f}s")
    print(f"  Temperature range: {temp_data.min():.1f} to {temp_data.max():.1f}°C")
    print(f"  Expected amplitude: {(temp_data.max() - temp_data.min())/2:.1f}°C")
    print(f"  Expected period: 8.0s")
    
    # Feed all data to tuner
    for t, temp in zip(time_data, temp_data):
        tuner.temp_history.append(temp)
        tuner.time_history.append(t)
    
    print(f"\nData fed to tuner: {len(tuner.temp_history)} points")
    
    # Test oscillation detection
    is_oscillating, amplitude, period = tuner.detect_oscillations()
    
    print(f"\nOscillation detection results:")
    print(f"  Is oscillating: {is_oscillating}")
    print(f"  Detected amplitude: {amplitude:.2f}°C")
    print(f"  Detected period: {period:.2f}s")
    print(f"  Threshold: {tuner.oscillation_threshold}°C")
    
    # Debug the detection algorithm step by step
    print("\nDetailed algorithm debugging:")
    
    # Get recent data
    recent_temps = list(tuner.temp_history)[-40:]
    recent_times = list(tuner.time_history)[-40:]
    
    print(f"  Recent data points: {len(recent_temps)}")
    print(f"  Mean temperature: {np.mean(recent_temps):.2f}°C")
    print(f"  Std deviation: {np.std(recent_temps):.2f}°C")
    
    # Test peak/valley detection
    peaks = []
    valleys = []
    
    for i in range(2, len(recent_temps) - 2):
        if (recent_temps[i] > recent_temps[i-1] and 
            recent_temps[i] > recent_temps[i+1] and
            recent_temps[i] > recent_temps[i-2] and
            recent_temps[i] > recent_temps[i+2]):
            peaks.append((recent_times[i], recent_temps[i]))
        elif (recent_temps[i] < recent_temps[i-1] and 
              recent_temps[i] < recent_temps[i+1] and
              recent_temps[i] < recent_temps[i-2] and
              recent_temps[i] < recent_temps[i+2]):
            valleys.append((recent_times[i], recent_temps[i]))
    
    print(f"  Peaks found: {len(peaks)}")
    print(f"  Valleys found: {len(valleys)}")
    
    if peaks:
        print(f"  Peak temperatures: {[p[1] for p in peaks]}")
    if valleys:
        print(f"  Valley temperatures: {[v[1] for v in valleys]}")
    
    # Test zero crossings
    mean_temp = np.mean(recent_temps)
    crossings = 0
    for i in range(1, len(recent_temps)):
        if ((recent_temps[i] - mean_temp) * (recent_temps[i-1] - mean_temp)) < 0:
            crossings += 1
    
    print(f"  Zero crossings: {crossings}")
    
    # Calculate amplitude from std
    amplitude_std = np.std(recent_temps) * 2
    print(f"  Amplitude from std: {amplitude_std:.2f}°C")
    
    # Test conditions
    has_peaks_valleys = len(peaks) >= 2 and len(valleys) >= 2
    has_crossings = crossings >= 4
    sufficient_amplitude = amplitude_std > tuner.oscillation_threshold
    
    print(f"\nCondition checks:")
    print(f"  Has peaks/valleys: {has_peaks_valleys}")
    print(f"  Has crossings: {has_crossings}")
    print(f"  Sufficient amplitude: {sufficient_amplitude}")
    
    # Try a simpler detection method
    print(f"\nSimpler detection method:")
    temp_range = temp_data.max() - temp_data.min()
    simple_amplitude = temp_range / 2
    print(f"  Simple amplitude: {simple_amplitude:.2f}°C")
    print(f"  Should detect: {simple_amplitude > tuner.oscillation_threshold}")

if __name__ == "__main__":
    debug_oscillation_detection()
import time
import numpy as np
from collections import deque
import math

class ZieglerNicholsAutoTuner:
    def __init__(self, pyrometer, psu, target_temp, max_current=10, min_current=0):
        self.pyrometer = pyrometer
        self.psu = psu
        self.target_temp = target_temp
        self.max_current = max_current
        self.min_current = min_current
        
        # Tuning parameters
        self.kp_start = 0.001  # Starting proportional gain
        self.kp_step = 0.001   # Step size for increasing Kp
        self.max_iterations = 100
        self.oscillation_threshold = 1.0  # Minimum oscillation amplitude to detect
        self.min_oscillation_periods = 3  # Minimum periods to measure
        self.control_interval = 0.5
        
        # Safety parameters
        self.max_temp_overshoot = 50  # Maximum temperature overshoot allowed
        self.max_tuning_time = 300    # Maximum tuning time in seconds
        
        # Data storage
        self.temp_history = deque(maxlen=200)
        self.time_history = deque(maxlen=200)
        self.current_history = deque(maxlen=200)
        
        # Results
        self.critical_gain = None
        self.critical_period = None
        self.final_kp = None
        self.final_ki = None
        self.final_kd = None
        self.tuning_successful = False
        
    def detect_oscillations(self, window_size=40):
        """Detect if system is oscillating around setpoint"""
        if len(self.temp_history) < window_size:
            return False, 0, 0
            
        # Get recent temperature data
        recent_temps = list(self.temp_history)[-window_size:]
        recent_times = list(self.time_history)[-window_size:]
        
        # Calculate mean temperature
        mean_temp = np.mean(recent_temps)
        
        # Find peaks and valleys with more relaxed criteria
        peaks = []
        valleys = []
        
        # Use a wider window for peak/valley detection
        for i in range(2, len(recent_temps) - 2):
            # Check if it's a peak (higher than neighbors)
            if (recent_temps[i] > recent_temps[i-1] and 
                recent_temps[i] > recent_temps[i+1] and
                recent_temps[i] > recent_temps[i-2] and
                recent_temps[i] > recent_temps[i+2]):
                peaks.append((recent_times[i], recent_temps[i]))
            # Check if it's a valley (lower than neighbors)
            elif (recent_temps[i] < recent_temps[i-1] and 
                  recent_temps[i] < recent_temps[i+1] and
                  recent_temps[i] < recent_temps[i-2] and
                  recent_temps[i] < recent_temps[i+2]):
                valleys.append((recent_times[i], recent_temps[i]))
        
        # Alternative method: check standard deviation and crossings
        std_temp = np.std(recent_temps)
        
        # Count zero crossings (temperature crossing the mean)
        crossings = 0
        for i in range(1, len(recent_temps)):
            if ((recent_temps[i] - mean_temp) * (recent_temps[i-1] - mean_temp)) < 0:
                crossings += 1
        
        # Calculate rough amplitude from standard deviation
        amplitude_std = std_temp * 2  # Approximate amplitude
        
        # Check for sustained oscillations using multiple criteria
        has_peaks_valleys = len(peaks) >= 2 and len(valleys) >= 2
        has_crossings = crossings >= 4  # At least 4 crossings indicate oscillation
        sufficient_amplitude = amplitude_std > self.oscillation_threshold
        
        if has_peaks_valleys:
            # Calculate amplitude from peaks and valleys
            peak_temps = [p[1] for p in peaks]
            valley_temps = [v[1] for v in valleys]
            amplitude = (np.mean(peak_temps) - np.mean(valley_temps)) / 2
            
            # Calculate period from peaks
            if len(peaks) >= 2:
                peak_times = [p[0] for p in peaks]
                periods = []
                for i in range(1, len(peak_times)):
                    periods.append(peak_times[i] - peak_times[i-1])
                period = np.mean(periods) if periods else 0
            else:
                period = 0
        else:
            # Use standard deviation method
            amplitude = amplitude_std
            # Estimate period from crossings
            if crossings > 0:
                time_span = recent_times[-1] - recent_times[0]
                period = 2 * time_span / crossings  # Approximate period
            else:
                period = 0
        
        # More relaxed oscillation detection
        is_oscillating = (sufficient_amplitude and 
                         (has_peaks_valleys or has_crossings) and
                         period > 2.0)  # Minimum period of 2 seconds
        
        return is_oscillating, amplitude, period
    
    def run_proportional_test(self, kp_test):
        """Run proportional-only control test with given Kp"""
        print(f"Testing Kp = {kp_test:.4f}")
        
        # Clear history for fresh test
        self.temp_history.clear()
        self.time_history.clear()
        self.current_history.clear()
        
        # Set initial current
        self.psu.set_current(self.min_current)
        
        start_time = time.time()
        test_duration = 60  # Test for 60 seconds
        
        while time.time() - start_time < test_duration:
            current_time = time.time() - start_time
            
            # Measure temperature
            temp = self.pyrometer.measure_temperature()
            if temp is None:
                time.sleep(self.control_interval)
                continue
                
            # Safety check
            if temp > self.target_temp + self.max_temp_overshoot:
                print(f"Safety stop: Temperature too high ({temp:.1f}°C)")
                self.psu.set_current(self.min_current)
                return False, 0, 0
            
            # Proportional control
            error = self.target_temp - temp
            output = kp_test * error
            
            # Clamp output
            output = max(self.min_current, min(self.max_current, output))
            
            # Set current
            self.psu.set_current(output)
            
            # Store data
            self.temp_history.append(temp)
            self.time_history.append(current_time)
            self.current_history.append(output)
            
            # Check for oscillations after some settling time
            if current_time > 20:  # Allow 20s for initial settling
                is_oscillating, amplitude, period = self.detect_oscillations()
                if is_oscillating:
                    print(f"Oscillation detected! Amplitude: {amplitude:.2f}°C, Period: {period:.2f}s")
                    return True, amplitude, period
            
            time.sleep(self.control_interval)
        
        return False, 0, 0
    
    def find_critical_gain(self):
        """Find critical gain where sustained oscillations occur"""
        print("Starting critical gain search...")
        
        kp_current = self.kp_start
        
        for iteration in range(self.max_iterations):
            print(f"\nIteration {iteration + 1}/{self.max_iterations}")
            
            # Run proportional test
            oscillating, amplitude, period = self.run_proportional_test(kp_current)
            
            if oscillating:
                print(f"Critical gain found: Kc = {kp_current:.4f}")
                self.critical_gain = kp_current
                self.critical_period = period
                return True
            
            # Increase gain for next iteration
            kp_current += self.kp_step
            
            # Prevent excessive gain
            if kp_current > 1.0:
                print("Maximum gain reached without oscillation")
                return False
        
        print("Maximum iterations reached without finding critical gain")
        return False
    
    def calculate_pid_parameters(self):
        """Calculate PID parameters using Ziegler-Nichols formulas"""
        if self.critical_gain is None or self.critical_period is None:
            return False
            
        # Ziegler-Nichols formulas for PID controller
        self.final_kp = 0.6 * self.critical_gain
        self.final_ki = 1.2 * self.critical_gain / self.critical_period
        self.final_kd = 0.075 * self.critical_gain * self.critical_period
        
        print(f"\nZiegler-Nichols PID Parameters:")
        print(f"Kp = {self.final_kp:.4f}")
        print(f"Ki = {self.final_ki:.4f}")
        print(f"Kd = {self.final_kd:.4f}")
        
        return True
    
    def run_auto_tuning(self):
        """Run complete auto-tuning process"""
        print("Starting Ziegler-Nichols Auto-Tuning...")
        print(f"Target temperature: {self.target_temp}°C")
        print(f"Current range: {self.min_current}A - {self.max_current}A")
        
        start_time = time.time()
        
        try:
            # Initialize PSU
            self.psu.set_voltage(30.0)
            self.psu.set_current(self.min_current)
            self.psu.output_on()
            
            # Step 1: Find critical gain
            if not self.find_critical_gain():
                print("Failed to find critical gain")
                return False
            
            # Step 2: Calculate PID parameters
            if not self.calculate_pid_parameters():
                print("Failed to calculate PID parameters")
                return False
            
            self.tuning_successful = True
            total_time = time.time() - start_time
            print(f"\nAuto-tuning completed successfully in {total_time:.1f} seconds")
            
            return True
            
        except Exception as e:
            print(f"Auto-tuning failed with error: {e}")
            return False
        
        finally:
            # Always turn off PSU
            try:
                self.psu.set_current(self.min_current)
                self.psu.output_off()
            except:
                pass
    
    def get_tuning_results(self):
        """Get the tuning results"""
        if not self.tuning_successful:
            return None
            
        return {
            'kp': self.final_kp,
            'ki': self.final_ki,
            'kd': self.final_kd,
            'critical_gain': self.critical_gain,
            'critical_period': self.critical_period
        }
    
    def get_tuning_data(self):
        """Get recorded tuning data for plotting"""
        return {
            'time': list(self.time_history),
            'temperature': list(self.temp_history),
            'current': list(self.current_history)
        }
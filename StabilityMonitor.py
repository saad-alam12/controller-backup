import time
import numpy as np
from collections import deque
import logging

class StabilityMonitor:
    """
    Monitor PID controller stability and performance metrics
    Detects when system needs re-tuning due to performance degradation
    """
    
    def __init__(self, target_temp, control_interval=0.5, window_size=100):
        self.target_temp = target_temp
        self.control_interval = control_interval
        self.window_size = window_size
        
        # Performance data storage
        self.temp_history = deque(maxlen=window_size)
        self.time_history = deque(maxlen=window_size)
        self.error_history = deque(maxlen=window_size)
        self.output_history = deque(maxlen=window_size)
        
        # Performance metrics
        self.settling_time = None
        self.overshoot = None
        self.steady_state_error = None
        self.oscillation_frequency = None
        self.stability_score = 100  # 0-100, higher is better
        
        # Stability thresholds
        self.max_steady_state_error = 2.0  # °C
        self.max_overshoot = 10.0  # °C
        self.max_settling_time = 120.0  # seconds
        self.max_oscillation_amplitude = 3.0  # °C
        self.min_stability_score = 70  # Trigger re-tuning below this
        
        # Monitoring state
        self.is_stable = True
        self.last_setpoint_change = None
        self.stability_check_interval = 30  # Check every 30 seconds
        self.last_stability_check = time.time()
        
        # Re-tuning control
        self.last_retune_time = None
        self.min_retune_interval = 300  # Minimum 5 minutes between re-tunings
        self.retune_count = 0
        self.max_retunes_per_hour = 3
        
        # Logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for stability monitoring"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('stability_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('StabilityMonitor')
        
    def add_measurement(self, temperature, control_output, current_time):
        """Add a new measurement to the monitoring system"""
        error = self.target_temp - temperature
        
        # Store data
        self.temp_history.append(temperature)
        self.time_history.append(current_time)
        self.error_history.append(error)
        self.output_history.append(control_output)
        
        # Check if it's time for stability assessment
        if current_time - self.last_stability_check > self.stability_check_interval:
            self.assess_stability()
            self.last_stability_check = current_time
            
    def calculate_settling_time(self):
        """Calculate settling time - time to reach within 2% of setpoint"""
        if len(self.temp_history) < 20:
            return None
            
        settling_tolerance = 0.02 * self.target_temp  # 2% of setpoint
        recent_temps = list(self.temp_history)[-50:]  # Last 50 readings
        recent_times = list(self.time_history)[-50:]
        
        # Find when temperature last entered settling band
        settling_start = None
        for i in range(len(recent_temps) - 10):  # Need at least 10 points after
            if abs(recent_temps[i] - self.target_temp) <= settling_tolerance:
                # Check if it stayed within band for next 10 points
                stayed_in_band = True
                for j in range(i + 1, min(i + 11, len(recent_temps))):
                    if abs(recent_temps[j] - self.target_temp) > settling_tolerance:
                        stayed_in_band = False
                        break
                if stayed_in_band:
                    settling_start = i
                    break
        
        if settling_start is not None:
            # Calculate settling time from start of window
            self.settling_time = recent_times[-1] - recent_times[settling_start]
        else:
            self.settling_time = None
            
        return self.settling_time
    
    def calculate_overshoot(self):
        """Calculate maximum overshoot from setpoint"""
        if len(self.temp_history) < 10:
            return None
            
        temps = list(self.temp_history)
        max_temp = max(temps)
        
        # Only consider overshoot if temperature went above setpoint
        if max_temp > self.target_temp:
            self.overshoot = max_temp - self.target_temp
        else:
            self.overshoot = 0
            
        return self.overshoot
    
    def calculate_steady_state_error(self):
        """Calculate steady-state error from recent measurements"""
        if len(self.temp_history) < 20:
            return None
            
        # Use last 20 measurements for steady-state
        recent_temps = list(self.temp_history)[-20:]
        self.steady_state_error = abs(np.mean(recent_temps) - self.target_temp)
        
        return self.steady_state_error
    
    def detect_oscillations(self):
        """Detect oscillations and calculate frequency"""
        if len(self.temp_history) < 30:
            return None, None
            
        recent_temps = list(self.temp_history)[-30:]
        recent_times = list(self.time_history)[-30:]
        
        # Calculate standard deviation
        temp_std = np.std(recent_temps)
        
        # Count zero crossings around mean
        mean_temp = np.mean(recent_temps)
        crossings = 0
        for i in range(1, len(recent_temps)):
            if ((recent_temps[i] - mean_temp) * (recent_temps[i-1] - mean_temp)) < 0:
                crossings += 1
        
        # Calculate oscillation frequency
        if crossings > 2:
            time_span = recent_times[-1] - recent_times[0]
            self.oscillation_frequency = crossings / (2 * time_span)  # Hz
        else:
            self.oscillation_frequency = 0
            
        return temp_std * 2, self.oscillation_frequency  # Amplitude, frequency
    
    def calculate_stability_score(self):
        """Calculate overall stability score (0-100)"""
        if len(self.temp_history) < 20:
            self.stability_score = 50  # Neutral score for insufficient data
            return self.stability_score
            
        score = 100
        
        # Penalize large steady-state error
        if self.steady_state_error is not None:
            error_penalty = min(30, (self.steady_state_error / self.max_steady_state_error) * 30)
            score -= error_penalty
            
        # Penalize overshoot
        if self.overshoot is not None:
            overshoot_penalty = min(25, (self.overshoot / self.max_overshoot) * 25)
            score -= overshoot_penalty
            
        # Penalize oscillations
        oscillation_amplitude, _ = self.detect_oscillations()
        if oscillation_amplitude is not None:
            osc_penalty = min(25, (oscillation_amplitude / self.max_oscillation_amplitude) * 25)
            score -= osc_penalty
            
        # Penalize slow settling
        if self.settling_time is not None:
            settling_penalty = min(20, (self.settling_time / self.max_settling_time) * 20)
            score -= settling_penalty
            
        self.stability_score = max(0, score)
        return self.stability_score
    
    def assess_stability(self):
        """Assess overall system stability"""
        # Calculate all metrics
        self.calculate_settling_time()
        self.calculate_overshoot()
        self.calculate_steady_state_error()
        self.detect_oscillations()
        self.calculate_stability_score()
        
        # Update stability status
        previous_stability = self.is_stable
        self.is_stable = self.stability_score >= self.min_stability_score
        
        # Log stability assessment
        self.logger.info(f"Stability Assessment:")
        self.logger.info(f"  Stability Score: {self.stability_score:.1f}/100")
        self.logger.info(f"  Steady-State Error: {self.steady_state_error:.2f}°C")
        self.logger.info(f"  Overshoot: {self.overshoot:.2f}°C")
        self.logger.info(f"  Settling Time: {self.settling_time:.1f}s" if self.settling_time else "  Settling Time: Not settled")
        self.logger.info(f"  Oscillation Freq: {self.oscillation_frequency:.3f}Hz" if self.oscillation_frequency else "  Oscillation Freq: 0 Hz")
        self.logger.info(f"  System Stable: {self.is_stable}")
        
        # Log stability change
        if previous_stability != self.is_stable:
            if self.is_stable:
                self.logger.info("✓ System stability RESTORED")
            else:
                self.logger.warning("⚠ System stability DEGRADED - Re-tuning may be needed")
                
    def should_retune(self):
        """Determine if system should be re-tuned"""
        current_time = time.time()
        
        # Check if system is unstable
        if self.is_stable:
            return False, "System is stable"
            
        # Check minimum time since last re-tuning
        if (self.last_retune_time is not None and 
            current_time - self.last_retune_time < self.min_retune_interval):
            return False, f"Too soon since last re-tuning ({current_time - self.last_retune_time:.0f}s ago)"
            
        # Check maximum re-tunings per hour
        if self.retune_count >= self.max_retunes_per_hour:
            return False, "Maximum re-tunings per hour reached"
            
        # System needs re-tuning
        return True, f"System unstable (score: {self.stability_score:.1f})"
    
    def notify_retune_started(self):
        """Notify monitor that re-tuning has started"""
        self.last_retune_time = time.time()
        self.retune_count += 1
        self.logger.info(f"🔄 Re-tuning initiated (#{self.retune_count})")
        
    def notify_retune_completed(self, success, new_params=None):
        """Notify monitor that re-tuning has completed"""
        if success:
            self.logger.info("✓ Re-tuning completed successfully")
            if new_params:
                self.logger.info(f"  New parameters: Kp={new_params['kp']:.4f}, Ki={new_params['ki']:.4f}, Kd={new_params['kd']:.4f}")
            # Reset stability score to give new parameters a chance
            self.stability_score = 90
            self.is_stable = True
        else:
            self.logger.error("✗ Re-tuning failed")
            
    def get_status_summary(self):
        """Get a summary of current system status"""
        oscillation_amplitude, _ = self.detect_oscillations()
        
        return {
            'is_stable': self.is_stable,
            'stability_score': self.stability_score,
            'steady_state_error': self.steady_state_error,
            'overshoot': self.overshoot,
            'settling_time': self.settling_time,
            'oscillation_amplitude': oscillation_amplitude,
            'oscillation_frequency': self.oscillation_frequency,
            'retune_count': self.retune_count,
            'last_retune_time': self.last_retune_time
        }
        
    def reset_counters(self):
        """Reset hourly counters (should be called every hour)"""
        self.retune_count = 0
        self.logger.info("Re-tuning counters reset")
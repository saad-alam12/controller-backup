import time
import threading
from PID import PIDController
from ZieglerNicholsAutoTuner import ZieglerNicholsAutoTuner
from StabilityMonitor import StabilityMonitor

class AdaptivePIDController:
    """
    Adaptive PID Controller that automatically re-tunes parameters when stability degrades
    Combines normal PID control with automatic Ziegler-Nichols re-tuning
    """
    
    def __init__(self, pyrometer, psu, target_temp, max_current=10, min_current=0):
        self.pyrometer = pyrometer
        self.psu = psu
        self.target_temp = target_temp
        self.max_current = max_current
        self.min_current = min_current
        
        # Control components
        self.pid_controller = None
        self.auto_tuner = None
        self.stability_monitor = StabilityMonitor(target_temp)
        
        # Current PID parameters
        self.current_kp = 1.0
        self.current_ki = 0.1
        self.current_kd = 0.01
        
        # Control state
        self.control_mode = 'normal'  # 'normal', 'retuning', 'failed'
        self.is_running = False
        self.last_temperature = None
        self.last_output = None
        self.last_time = None
        
        # Safety parameters
        self.emergency_stop = False
        self.max_consecutive_failures = 3
        self.consecutive_failures = 0
        
        # Threading for re-tuning
        self.retune_thread = None
        self.retune_lock = threading.Lock()
        
        # Status tracking
        self.total_runtime = 0
        self.successful_retunes = 0
        self.failed_retunes = 0
        
    def initialize_pid(self, kp, ki, kd):
        """Initialize PID controller with given parameters"""
        self.current_kp = kp
        self.current_ki = ki
        self.current_kd = kd
        
        # Create PID controller
        self.pid_controller = PIDController(kp, ki, kd, self.target_temp)
        self.pid_controller.set_output_limits(self.min_current, self.max_current)
        
        self.stability_monitor.logger.info(f"PID initialized with Kp={kp:.4f}, Ki={ki:.4f}, Kd={kd:.4f}")
        
    def update_pid_parameters(self, kp, ki, kd):
        """Update PID parameters during operation"""
        with self.retune_lock:
            self.current_kp = kp
            self.current_ki = ki
            self.current_kd = kd
            
            # Update existing controller
            if self.pid_controller:
                self.pid_controller.Kp = kp
                self.pid_controller.Ki = ki
                self.pid_controller.Kd = kd
                # Reset integral term to prevent windup
                self.pid_controller.reset_integral()
                
            self.stability_monitor.logger.info(f"PID parameters updated: Kp={kp:.4f}, Ki={ki:.4f}, Kd={kd:.4f}")
    
    def compute_control_output(self, current_temperature, dt):
        """Compute control output using current PID parameters"""
        if not self.pid_controller:
            return self.min_current
            
        with self.retune_lock:
            # Normal PID computation
            output = self.pid_controller.compute(current_temperature, dt)
            
            # Update stability monitor
            self.stability_monitor.add_measurement(
                current_temperature, 
                output, 
                time.time()
            )
            
            # Store for monitoring
            self.last_temperature = current_temperature
            self.last_output = output
            self.last_time = time.time()
            
            return output
    
    def check_retune_needed(self):
        """Check if re-tuning is needed and initiate if necessary"""
        if self.control_mode == 'retuning':
            return False  # Already re-tuning
            
        should_retune, reason = self.stability_monitor.should_retune()
        
        if should_retune:
            self.stability_monitor.logger.info(f"Re-tuning triggered: {reason}")
            self.initiate_retune()
            return True
            
        return False
    
    def initiate_retune(self):
        """Initiate re-tuning process in background thread"""
        if self.control_mode == 'retuning':
            return False
            
        self.control_mode = 'retuning'
        self.stability_monitor.notify_retune_started()
        
        # Start re-tuning in background thread
        self.retune_thread = threading.Thread(target=self._retune_worker)
        self.retune_thread.daemon = True
        self.retune_thread.start()
        
        return True
    
    def _retune_worker(self):
        """Background worker for re-tuning process"""
        try:
            self.stability_monitor.logger.info("🔄 Starting automatic re-tuning...")
            
            # Create auto-tuner
            auto_tuner = ZieglerNicholsAutoTuner(
                self.pyrometer,
                self.psu,
                self.target_temp,
                self.max_current,
                self.min_current
            )
            
            # Run auto-tuning
            tuning_success = auto_tuner.run_auto_tuning()
            
            if tuning_success:
                # Get new parameters
                results = auto_tuner.get_tuning_results()
                new_kp = results['kp']
                new_ki = results['ki']
                new_kd = results['kd']
                
                # Update PID parameters
                self.update_pid_parameters(new_kp, new_ki, new_kd)
                
                # Notify monitor
                self.stability_monitor.notify_retune_completed(True, results)
                self.successful_retunes += 1
                self.consecutive_failures = 0
                
                self.stability_monitor.logger.info("✓ Automatic re-tuning completed successfully")
                
            else:
                # Re-tuning failed
                self.stability_monitor.notify_retune_completed(False)
                self.failed_retunes += 1
                self.consecutive_failures += 1
                
                self.stability_monitor.logger.error("✗ Automatic re-tuning failed")
                
                # Check if too many consecutive failures
                if self.consecutive_failures >= self.max_consecutive_failures:
                    self.stability_monitor.logger.critical("🚨 Maximum consecutive re-tuning failures reached")
                    self.control_mode = 'failed'
                    return
                    
        except Exception as e:
            self.stability_monitor.logger.error(f"Re-tuning worker error: {e}")
            self.stability_monitor.notify_retune_completed(False)
            self.failed_retunes += 1
            self.consecutive_failures += 1
            
        finally:
            # Return to normal mode if not failed
            if self.control_mode != 'failed':
                self.control_mode = 'normal'
                self.stability_monitor.logger.info("Returned to normal control mode")
    
    def manual_retune(self):
        """Manually trigger re-tuning"""
        if self.control_mode == 'retuning':
            return False, "Re-tuning already in progress"
            
        self.stability_monitor.logger.info("Manual re-tuning requested")
        success = self.initiate_retune()
        
        if success:
            return True, "Manual re-tuning initiated"
        else:
            return False, "Failed to initiate re-tuning"
    
    def get_control_status(self):
        """Get current control system status"""
        stability_status = self.stability_monitor.get_status_summary()
        
        return {
            'control_mode': self.control_mode,
            'current_parameters': {
                'kp': self.current_kp,
                'ki': self.current_ki,
                'kd': self.current_kd
            },
            'last_temperature': self.last_temperature,
            'last_output': self.last_output,
            'stability': stability_status,
            'total_runtime': self.total_runtime,
            'successful_retunes': self.successful_retunes,
            'failed_retunes': self.failed_retunes,
            'consecutive_failures': self.consecutive_failures,
            'emergency_stop': self.emergency_stop
        }
    
    def get_status_display(self):
        """Get formatted status display for user"""
        status = self.get_control_status()
        stability = status['stability']
        
        display_lines = []
        display_lines.append(f"🎯 Target: {self.target_temp}°C | Current: {status['last_temperature']:.1f}°C")
        display_lines.append(f"⚡ Output: {status['last_output']:.2f}A")
        display_lines.append(f"🔧 Mode: {status['control_mode'].upper()}")
        display_lines.append(f"📊 Stability: {stability['stability_score']:.0f}/100 {'✓' if stability['is_stable'] else '⚠'}")
        display_lines.append(f"🔄 Re-tunes: {status['successful_retunes']} success, {status['failed_retunes']} failed")
        
        # Add performance metrics
        if stability['steady_state_error'] is not None:
            display_lines.append(f"📈 SS Error: {stability['steady_state_error']:.2f}°C")
        if stability['overshoot'] is not None:
            display_lines.append(f"📈 Overshoot: {stability['overshoot']:.2f}°C")
        if stability['oscillation_amplitude'] is not None:
            display_lines.append(f"📈 Oscillations: {stability['oscillation_amplitude']:.2f}°C")
            
        return display_lines
    
    def emergency_stop_system(self):
        """Emergency stop the entire system"""
        self.emergency_stop = True
        self.control_mode = 'failed'
        self.stability_monitor.logger.critical("🚨 EMERGENCY STOP ACTIVATED")
        
        # Turn off PSU
        try:
            self.psu.set_current(self.min_current)
            self.psu.output_off()
        except Exception as e:
            self.stability_monitor.logger.error(f"Error during emergency stop: {e}")
    
    def is_system_healthy(self):
        """Check if system is healthy and should continue running"""
        return (not self.emergency_stop and 
                self.control_mode != 'failed' and
                self.consecutive_failures < self.max_consecutive_failures)
    
    def cleanup(self):
        """Cleanup resources"""
        self.is_running = False
        
        # Wait for re-tuning thread to finish
        if self.retune_thread and self.retune_thread.is_alive():
            self.stability_monitor.logger.info("Waiting for re-tuning to complete...")
            self.retune_thread.join(timeout=30)
            
        # Final status
        final_status = self.get_control_status()
        self.stability_monitor.logger.info(f"System shutdown - Final statistics:")
        self.stability_monitor.logger.info(f"  Total runtime: {final_status['total_runtime']:.0f}s")
        self.stability_monitor.logger.info(f"  Successful re-tunes: {final_status['successful_retunes']}")
        self.stability_monitor.logger.info(f"  Failed re-tunes: {final_status['failed_retunes']}")
        
        self.stability_monitor.logger.info("Adaptive PID Controller shutdown complete")
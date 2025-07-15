class PIDController:
    def __init__(self, Kp, Ki, Kd, setpoint):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.integral = 0
        self.previous_pv = None  # Store previous process variable for derivative on measurement
        self.output_limits = (None, None)  # Default to no limits
        
    def set_output_limits(self, min_output, max_output):
        """Set the output limits for the controller."""
        self.output_limits = (min_output, max_output)
        
    def reset_integral(self):
        """Reset integral term - useful when setpoint changes."""
        self.integral = 0
        
    def compute(self, process_variable, dt):
        # Calculate error (how far measurement is off from setpoint)
        error = self.setpoint - process_variable
        
        # Proportional term
        P_out = self.Kp * error
        
        # Integral term with anti-windup
        self.integral += error * dt
        
        # Apply anti-windup protection for upper limit
        if self.output_limits[1] is not None:
            temp_I_out = self.Ki * self.integral
            if P_out + temp_I_out > self.output_limits[1]:
                if self.Ki != 0:
                    self.integral = (self.output_limits[1] - P_out) / self.Ki
                else:
                    self.integral = 0
        
        # Apply anti-windup protection for lower limit        
        if self.output_limits[0] is not None:
            temp_I_out = self.Ki * self.integral
            if P_out + temp_I_out < self.output_limits[0]:
                if self.Ki != 0:
                    self.integral = (self.output_limits[0] - P_out) / self.Ki
                else:
                    self.integral = 0
        
        # Calculate final integral output after anti-windup
        I_out = self.Ki * self.integral
        
        # Derivative term on measurement 
        if dt == 0 or self.previous_pv is None:
            derivative = 0
        else:
            # Derivative on measurement to reduce noise
            derivative = -(process_variable - self.previous_pv) / dt
        
        D_out = self.Kd * derivative
        
        # Calculate total output
        output = P_out + I_out + D_out 
        
        # Apply output limits if specified (final safety check)
        if self.output_limits[1] is not None:
            output = min(output, self.output_limits[1])
        if self.output_limits[0] is not None:
            output = max(output, self.output_limits[0])
        
        # Update previous values
        self.previous_pv = process_variable
        
        return output
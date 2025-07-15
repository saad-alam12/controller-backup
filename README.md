# Temperature Control System with Adaptive PID

A complete temperature control system with automatic PID parameter tuning and adaptive re-tuning capabilities.

## 📁 File Overview

### Core Control Files

#### `tunePID_korad.py` - Main Control Script
**What it does**: The main program you run to control temperature
- Provides 4 control modes: Default, Manual, Auto-tune, and Adaptive PID
- Handles device initialization (PSU and pyrometer)
- Runs the control loop with real-time plotting
- Manages user interface and input handling

**Key settings to adjust**:
```python
PYROMETER_PORT = "/dev/cu.usbserial-B00378DF"  # Change to your pyrometer port
PSU_PORT = "/dev/cu.usbmodem00273B64024C1"     # Change to your PSU port
max_current = 10  # Maximum current limit (Amperes)
control_interval = 0.5  # Control loop speed (seconds)
```

#### `PID.py` - Basic PID Controller
**What it does**: Traditional PID control implementation
- Calculates PID output based on error, integral, and derivative terms
- Includes anti-windup protection
- Used by both manual and adaptive control modes

**Key settings to adjust**:
```python
# In the PID controller initialization
self.output_limits = (min_output, max_output)  # Output clamping
```

### Auto-Tuning System

#### `ZieglerNicholsAutoTuner.py` - Automatic Parameter Finding
**What it does**: Finds optimal PID parameters automatically
- Gradually increases proportional gain until system oscillates
- Measures oscillation period and amplitude
- Calculates PID parameters using proven Ziegler-Nichols formulas

**Key settings to adjust**:
```python
self.kp_start = 0.001  # Starting gain (lower for sensitive systems)
self.kp_step = 0.001   # Gain increment step
self.oscillation_threshold = 1.0  # Minimum oscillation to detect (°C)
self.max_temp_overshoot = 50  # Safety limit (°C above setpoint)
```

### Adaptive Control System

#### `AdaptivePIDController.py` - Smart PID with Auto Re-tuning
**What it does**: Combines PID control with automatic parameter adjustment
- Monitors system performance continuously
- Triggers re-tuning when performance degrades
- Handles background re-tuning without stopping control
- Provides safety mechanisms and emergency stop

**Key settings to adjust**:
```python
self.max_consecutive_failures = 3  # Max failed re-tuning attempts
self.min_retune_interval = 300     # Minimum time between re-tunings (seconds)
self.max_retunes_per_hour = 3      # Safety limit for re-tuning frequency
```

#### `StabilityMonitor.py` - Performance Analysis
**What it does**: Continuously analyzes control performance
- Tracks settling time, overshoot, oscillations, and steady-state error
- Calculates stability score (0-100)
- Determines when re-tuning is needed

**Key settings to adjust**:
```python
self.max_steady_state_error = 2.0    # Max acceptable error (°C)
self.max_overshoot = 10.0            # Max acceptable overshoot (°C)
self.max_oscillation_amplitude = 3.0 # Max acceptable oscillation (°C)
self.min_stability_score = 70        # Trigger re-tuning below this score
```

### Device Interface Files

#### `Korad.py` - Power Supply Interface
**What it does**: Communicates with Korad PSU over serial
- Sets voltage and current limits
- Turns output on/off
- Reads current status

#### `Pyrometer.py` - Temperature Sensor Interface
**What it does**: Reads temperature from pyrometer over serial
- Handles serial communication protocol
- Converts readings to temperature values
- Includes error handling for failed readings

### Utility Files

#### `InputHandler.py` - Interactive Commands
**What it does**: Handles user input during control operation
- Allows manual re-tuning trigger ('r' + Enter)
- Non-blocking input so control continues
- Cross-platform compatibility

#### Test Files
- `test_autotuner.py` - Tests the auto-tuning system
- `test_adaptive_pid.py` - Tests the adaptive PID system
- `debug_oscillation.py` - Debugging tool for oscillation detection

## 🔧 How Everything Connects

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Pyrometer     │    │                  │    │   Power Supply  │
│  (Temperature)  │◄──►│  tunePID_korad.py│◄──►│   (Current)     │
└─────────────────┘    │   (Main Script)  │    └─────────────────┘
                       └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Control Mode   │
                    │    Selection     │
                    └──────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
           ▼                  ▼                  ▼
    ┌─────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │   Manual    │  │   Auto-Tuning   │  │   Adaptive PID  │
    │     PID     │  │  (Ziegler-Nichols) │  │ (Self-Tuning)  │
    └─────────────┘  └─────────────────┘  └─────────────────┘
                              │                  │
                              ▼                  ▼
                    ┌──────────────────┐  ┌─────────────────┐
                    │  PID Parameters  │  │ StabilityMonitor│
                    │   Calculated     │  │   + Auto-Retune │
                    └──────────────────┘  └─────────────────┘
```

## 🎛️ Control Modes Explained

### Mode 1: Default Parameters
- Uses pre-set PID values (Kp=1.0, Ki=0.1, Kd=0.01)
- Good for quick testing
- May not be optimal for your specific system

### Mode 2: Manual Parameters
- You enter Kp, Ki, Kd values manually
- Useful when you know good parameters
- Requires PID tuning knowledge

### Mode 3: Auto-Tuning (Ziegler-Nichols)
- Automatically finds optimal parameters once
- Takes 5-10 minutes to complete
- Parameters remain fixed during operation
- Good for systems that don't change over time

### Mode 4: Adaptive PID (Recommended)
- Starts with auto-tuned parameters
- Continuously monitors performance
- Automatically re-tunes when needed
- Provides real-time status and logging
- Best for long-term operation

## 📊 Understanding the Status Display (Mode 4)

```
🎯 Target: 200.0°C | Current: 199.8°C  ← Temperature info
⚡ Output: 2.35A                        ← Current power output
🔧 Mode: NORMAL                         ← Control mode (NORMAL/RETUNING/FAILED)
📊 Stability: 85/100 ✓                 ← Performance score (70+ is good)
🔄 Re-tunes: 2 success, 0 failed       ← Re-tuning history
📈 SS Error: 0.15°C                    ← Steady-state error
📈 Overshoot: 1.2°C                    ← Temperature overshoot
📈 Oscillations: 0.8°C                 ← Oscillation amplitude
```

## 🔧 Common Adjustments

### If Temperature Response is Too Slow:
```python
# In StabilityMonitor.py
self.max_settling_time = 60.0  # Reduce from 120s to 60s
```

### If System is Too Sensitive to Oscillations:
```python
# In StabilityMonitor.py
self.max_oscillation_amplitude = 5.0  # Increase from 3.0°C to 5.0°C
```

### If Re-tuning Happens Too Often:
```python
# In AdaptivePIDController.py
self.min_retune_interval = 600  # Increase from 300s to 600s (10 minutes)
```

### If Auto-tuning Fails to Find Parameters:
```python
# In ZieglerNicholsAutoTuner.py
self.kp_start = 0.0001      # Start with lower gain
self.kp_step = 0.0001       # Use smaller steps
self.max_iterations = 200   # Allow more iterations
```

## 🚀 Step-by-Step Operating Instructions

### Prerequisites
1. **Hardware Connected**:
   - Korad PSU connected via USB
   - Pyrometer connected via USB
   - Heating element connected to PSU output
   - Temperature sensor positioned at sample

2. **Software Setup**:
   - Python 3.x installed
   - Required packages: `numpy`, `matplotlib`, `pyserial`

### Step 1: Check Device Connections
```bash
# List available serial ports
ls /dev/cu.*

# You should see something like:
# /dev/cu.usbserial-B00378DF    (Pyrometer)
# /dev/cu.usbmodem00273B64024C1 (PSU)
```

### Step 2: Configure Serial Ports
1. Open `tunePID_korad.py`
2. Update the port settings:
```python
PYROMETER_PORT = "/dev/cu.usbserial-XXXXXXXX"  # Your pyrometer port
PSU_PORT = "/dev/cu.usbmodem-XXXXXXXX"         # Your PSU port
```

### Step 3: Set Safety Limits
```python
max_current = 10        # Maximum current (check your heating element rating)
min_current = 0         # Minimum current
temperature_tolerance = 0.5  # Temperature control tolerance (°C)
```

### Step 4: Start the Control System
```bash
cd "/Users/saadalam/CDBS Code/Controller"
python3 tunePID_korad.py
```

### Step 5: Choose Control Mode
You'll see:
```
PID Parameter Options:
1. Use default parameters (Kp=1.0, Ki=0.1, Kd=0.01)
2. Manually enter parameters
3. Auto-tune using Ziegler-Nichols method
4. Adaptive PID with automatic re-tuning

Select option (1/2/3/4): 4
```

**Recommended**: Choose option **4** for best results

### Step 6: Configure Initial Tuning
```
Adaptive PID with Automatic Re-tuning
Perform initial auto-tuning? (y/n): y
```

**Recommended**: Choose **y** for optimal starting parameters

### Step 7: Enter Target Temperature
```
Enter target temperature (°C): 200
```

### Step 8: Monitor Operation
- The system will start automatically
- Real-time plot shows temperature vs time
- Status updates every 5 seconds
- Log file created: `stability_monitor.log`

### Step 9: During Operation
- **Normal operation**: Just watch the status display
- **Manual re-tuning**: Type `r` + Enter
- **Emergency stop**: Press Ctrl+C

### Step 10: System Shutdown
- Press Ctrl+C to stop
- System automatically:
  - Turns off PSU output
  - Saves final plot
  - Logs shutdown statistics
  - Cleans up resources

## 🆘 Troubleshooting

### "Error initializing serial devices"
- Check USB connections
- Verify serial port names in code
- Ensure no other programs are using the ports

### "Failed to read temperature"
- Check pyrometer connection
- Verify pyrometer is powered on
- Check baud rate settings

### "Auto-tuning failed"
- Increase `max_iterations` in ZieglerNicholsAutoTuner.py
- Reduce `kp_start` for more sensitive systems
- Check heating element is working

### "System health check failed"
- Check `stability_monitor.log` for details
- Verify all connections are secure
- Restart the system

### High oscillations or instability
- Reduce `max_oscillation_amplitude` threshold
- Check for loose connections
- Ensure adequate thermal mass

## 📈 Performance Optimization

### For Faster Response:
- Reduce `control_interval` (but not below 0.1s)
- Increase maximum current limit (within safe limits)
- Reduce thermal mass in your system

### For Better Stability:
- Increase `control_interval` for slower systems
- Reduce `max_oscillation_amplitude` threshold
- Add thermal damping to your system

### For Long-term Operation:
- Use Mode 4 (Adaptive PID)
- Monitor `stability_monitor.log` regularly
- Set appropriate `min_retune_interval`

## 📝 Log Files

- `stability_monitor.log`: Detailed system performance log
- Real-time status in terminal
- Final plot saved automatically on exit

## 🔒 Safety Features

- Maximum current limiting
- Temperature overshoot protection
- Emergency stop capability
- Automatic PSU shutdown on errors
- Maximum re-tuning frequency limits
- System health monitoring

---

**Need Help?** Check the log files first, then examine the troubleshooting section above. Most issues are related to serial port configuration or device connections.
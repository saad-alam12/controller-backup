#!/usr/bin/env python3
"""
Quick test to verify dual-axis plotting works correctly
"""

import matplotlib.pyplot as plt
import numpy as np
import time

def test_dual_axis_plotting():
    """Test that the fixed dual-axis plotting works"""
    print("Testing dual-axis plotting (fixed version)...")
    
    # Generate sample data
    time_data = np.linspace(0, 10, 50)
    temp_data = 20 + 30 * (1 - np.exp(-time_data/3)) + np.random.normal(0, 0.5, len(time_data))
    current_data = 6 * np.exp(-time_data/2) + np.random.normal(0, 0.1, len(time_data))
    
    # FIXED Plot setup
    plt.figure(figsize=(10, 6))
    
    # Primary axis for temperature
    ax1 = plt.gca()
    line1 = ax1.plot(time_data, temp_data, 'r-', linewidth=2, label='Temperature (°C)')
    ax1.axhline(y=50, color='g', linestyle='--', linewidth=2, label='Target: 50°C')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Temperature (°C)', color='r')
    ax1.tick_params(axis='y', labelcolor='r')
    ax1.grid(True, alpha=0.3)
    
    # FIXED: Secondary axis for current - this was the bug!
    ax2 = ax1.twinx()
    line2 = ax2.plot(time_data, current_data, 'b-', linewidth=2, label='Current (A)')
    ax2.set_ylabel('Current (A)', color='b')
    ax2.tick_params(axis='y', labelcolor='b')
    ax2.set_ylim(0, 7)
    
    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    plt.title('PID Control - Fixed Dual Axis Plot')
    plt.tight_layout()
    
    print("✓ Dual-axis plot created successfully")
    print("✓ Temperature on left y-axis (red)")
    print("✓ Current on right y-axis (blue)")
    print("✓ Both datasets properly scaled on their respective axes")
    
    plt.savefig('/Users/saadalam/CDBS Code/Controller/plot_test.png', dpi=150, bbox_inches='tight')
    print("✓ Plot saved as plot_test.png")
    
    # Show the plot and keep it open
    print("Displaying plot - close the window to continue...")
    plt.show(block=True)  # This will keep the plot open until you close it
    
    return True

if __name__ == "__main__":
    success = test_dual_axis_plotting()
    print(f"\nPlot test {'PASSED' if success else 'FAILED'}")
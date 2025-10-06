

import sys
from obd_dashboard_gui import main

if __name__ == "__main__":
    # Check if user wants real OBD mode
    use_real_data = "--real" in sys.argv
    
    if use_real_data:
        print("=" * 60)
        print("STARTING OBD DASHBOARD IN REAL MODE")
        print("=" * 60)
        print("Connecting to OBD adapter...")
        print("Make sure:")
        print("  - OBD adapter is plugged into your car")
        print("  - Car ignition is ON")
        print("  - WiFi is connected to your OBD adapter")
        print("=" * 60)
        main(use_simulation=False)
    else:
        print("=" * 60)
        print("STARTING OBD DASHBOARD IN SIMULATION MODE")
        print("=" * 60)
        print("Using random simulated data for testing.")
        print("To use real OBD data, run:")
        print("  python run_dashboard.py --real")
        print("=" * 60)
        main(use_simulation=True)

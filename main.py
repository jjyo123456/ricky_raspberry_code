#!/usr/bin/env python3
"""
Ricky Smart Autometer System
Main entry point for the application
"""

import sys
import os
import signal

# Fix display issues BEFORE importing PyQt5
def setup_display():
    """Setup display environment for Raspberry Pi"""
    # Enable X11 forwarding if using SSH
    if 'SSH_CONNECTION' in os.environ and 'DISPLAY' not in os.environ:
        os.environ['DISPLAY'] = ':10.0'
    elif 'DISPLAY' not in os.environ:
        os.environ['DISPLAY'] = ':0'
    
    # Set Qt platform
    if 'QT_QPA_PLATFORM' not in os.environ:
        # Try xcb first, fallback to others if needed
        os.environ['QT_QPA_PLATFORM'] = 'xcb'

# Setup display before any Qt imports
setup_display()

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from frontend.ui_manager import RickyUI
from backend.gpio_manager import GPIOManager
from backend.gps_manager import GPSManager
from backend.fare_calculator import FareCalculator
from backend.mode_controller import ModeController
from backend.sos_system import SOSSystem

class RickyAutometer:
    def __init__(self):
        # Try to create QApplication with error handling
        try:
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("Ricky Autometer")
            print("✅ Qt Application created successfully")
        except Exception as e:
            print(f"⚠️ Qt display issue, trying alternative: {e}")
            # Try offscreen mode
            os.environ['QT_QPA_PLATFORM'] = 'offscreen'
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("Ricky Autometer")
            print("✅ Qt Application created in offscreen mode")
        
        # Initialize backend systems
        self.gpio_manager = GPIOManager()
        self.gps_manager = GPSManager()
        self.fare_calculator = FareCalculator(self.gps_manager)
        self.mode_controller = ModeController(self.gpio_manager)
        self.sos_system = SOSSystem(self.gpio_manager)
        
        # Initialize frontend
        self.ui = RickyUI(
            fare_calculator=self.fare_calculator,
            mode_controller=self.mode_controller,
            sos_system=self.sos_system
        )
        
        # Connect signals
        self.setup_connections()
        
        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        
        print("🚗 Ricky Autometer System Initialized")

    def setup_connections(self):
        """Connect backend signals to frontend updates"""
        # Mode changes
        self.mode_controller.mode_changed.connect(self.ui.update_mode)
        
        # Passenger updates (for sharing mode)
        self.gpio_manager.passenger_changed.connect(self.ui.update_passenger)
        self.gpio_manager.passenger_changed.connect(self.fare_calculator.handle_passenger_change)
        
        # SOS updates
        self.sos_system.sos_status_changed.connect(self.ui.update_sos_status)
        
        # Fare updates
        self.fare_calculator.fare_updated.connect(self.ui.update_fares)
        
        print("✅ Signal connections established")

    def run(self):
        """Start the application"""
        try:
            # Start all backend services
            self.gpio_manager.start()
            self.gps_manager.start()
            self.fare_calculator.start()
            self.mode_controller.start()
            self.sos_system.start()
            
            # Show UI in fullscreen
            self.ui.showFullScreen()
            
            print("🚀 Ricky Autometer started successfully!")
            return self.app.exec_()
            
        except Exception as e:
            print(f"❌ Error starting application: {e}")
            return 1

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n🛑 Shutdown signal received, cleaning up...")
        self.shutdown()
        sys.exit(0)

    def shutdown(self):
        """Clean shutdown of all systems"""
        try:
            self.fare_calculator.stop()
            self.gps_manager.stop()
            self.sos_system.stop()
            self.mode_controller.stop()
            self.gpio_manager.cleanup()
            print("🧹 Clean shutdown completed")
        except Exception as e:
            print(f"⚠️ Shutdown warning: {e}")

def main():
    print("=" * 50)
    print("🚗 RICKY SMART AUTOMETER SYSTEM")
    print("=" * 50)
    
    try:
        autometer = RickyAutometer()
        return autometer.run()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return 0
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
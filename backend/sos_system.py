"""
SOS System - Manages emergency alerts and responses
"""

import threading
import time
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal

class SOSSystem(QObject):
    # Signals
    sos_status_changed = pyqtSignal(str)  # status message
    sos_activated = pyqtSignal(dict)  # sos_data
    sos_deactivated = pyqtSignal()
    
    def __init__(self, gpio_manager):
        super().__init__()
        self.gpio_manager = gpio_manager
        self.sos_active = False
        self.countdown_active = False
        self.countdown_thread = None
        self.current_countdown = 0
        
        print("🚨 SOS System initialized")

    def start(self):
        """Start SOS monitoring"""
        # Connect to GPIO signals
        self.gpio_manager.sos_button_pressed.connect(self.handle_sos_button_press)
        self.gpio_manager.sos_button_released.connect(self.handle_sos_button_release)
        
        print("🚨 SOS System started")

    def handle_sos_button_press(self):
        """Handle SOS button press - start countdown"""
        if not self.countdown_active and not self.sos_active:
            self.countdown_active = True
            self.countdown_thread = threading.Thread(
                target=self._countdown_loop, daemon=True
            )
            self.countdown_thread.start()
            print("🚨 SOS button pressed - starting countdown")

    def handle_sos_button_release(self):
        """Handle SOS button release - cancel countdown if < 5 seconds"""
        if self.countdown_active:
            self.countdown_active = False
            self.sos_status_changed.emit("SOS Cancelled - Normal")
            print("✅ SOS cancelled - button released early")
        elif self.sos_active:
            self.deactivate_sos()

    def _countdown_loop(self):
        """5-second countdown loop"""
        for i in range(5, 0, -1):
            if not self.countdown_active:
                return  # Countdown cancelled
                
            self.current_countdown = i
            status_msg = f"SOS COUNTDOWN: {i} seconds"
            self.sos_status_changed.emit(status_msg)
            print(f"🚨 {status_msg}")
            time.sleep(1)
        
        # If we reach here, activate SOS
        if self.countdown_active:
            self.activate_sos()
            self.countdown_active = False

    def activate_sos(self):
        """Activate SOS emergency state"""
        self.sos_active = True
        activation_time = datetime.now()
        
        # Prepare SOS data
        sos_data = {
            'activation_time': activation_time,
            'timestamp': activation_time.isoformat(),
            'location': None,  # Will be filled by GPS if available
            'status': 'ACTIVE',
            'type': 'MANUAL_ACTIVATION'
        }
        
        # Try to get current location
        try:
            if hasattr(self, 'gps_manager'):
                location = self.gps_manager.get_location()
                sos_data['location'] = location
        except:
            pass
        
        self.sos_status_changed.emit("🚨 SOS ACTIVATED! 🚨")
        self.sos_activated.emit(sos_data)
        
        print("🚨" + "="*50)
        print("🚨 EMERGENCY SOS ACTIVATED!")
        print(f"🚨 Time: {activation_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if sos_data['location']:
            lat, lon = sos_data['location']
            print(f"🚨 Location: {lat:.6f}, {lon:.6f}")
        print("🚨" + "="*50)

    def deactivate_sos(self):
        """Deactivate SOS emergency state"""
        if self.sos_active:
            self.sos_active = False
            deactivation_time = datetime.now()
            
            self.sos_status_changed.emit("✅ SOS Deactivated - Normal")
            self.sos_deactivated.emit()
            
            print("✅ SOS DEACTIVATED")
            print(f"✅ Time: {deactivation_time.strftime('%Y-%m-%d %H:%M:%S')}")

    def get_sos_status(self):
        """Get current SOS status"""
        if self.sos_active:
            return "SOS_ACTIVE"
        elif self.countdown_active:
            return f"SOS_COUNTDOWN_{self.current_countdown}"
        else:
            return "NORMAL"

    def is_sos_active(self):
        """Check if SOS is currently active"""
        return self.sos_active

    def is_countdown_active(self):
        """Check if countdown is active"""
        return self.countdown_active

    def manual_sos_test(self):
        """Manually trigger SOS for testing"""
        print("🧪 Manual SOS test triggered")
        self.activate_sos()

    def stop(self):
        """Stop SOS system"""
        self.countdown_active = False
        self.deactivate_sos()
        print("🚨 SOS System stopped")
"""
UI Manager - Main coordinator for the entire interface
Updated to use real GPS data for all displays
"""

import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QStackedWidget, QLabel)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont

from .sharing_mode import SharingModeWidget
from .private_mode import PrivateModeWidget
from .ads_display import AdsDisplayWidget

class SOSStatusWidget(QWidget):
    """SOS status display widget"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.current_status = "Normal"
    
    def setup_ui(self):
        """Setup SOS status UI"""
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Status: Normal")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                background-color: #27AE60;
                padding: 12px 20px;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        
        layout.addWidget(self.status_label)
        self.setLayout(layout)
    
    def update_status(self, status):
        """Update SOS status"""
        self.current_status = status
        
        if "SOS" in status.upper() and "COUNTDOWN" in status.upper():
            # Countdown mode
            self.status_label.setText(status)
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: white;
                    background-color: #F39C12;
                    padding: 12px 20px;
                    border-radius: 8px;
                    margin: 5px;
                }
            """)
        elif "SOS" in status.upper() and "ACTIVATED" in status.upper():
            # Active SOS
            self.status_label.setText("🚨 EMERGENCY SOS ACTIVE! 🚨")
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 20px;
                    font-weight: bold;
                    color: white;
                    background-color: #E74C3C;
                    padding: 15px 25px;
                    border-radius: 8px;
                    margin: 5px;
                    border: 3px solid #C0392B;
                }
            """)
        else:
            # Normal status
            self.status_label.setText("Status: Normal")
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: white;
                    background-color: #27AE60;
                    padding: 12px 20px;
                    border-radius: 8px;
                    margin: 5px;
                }
            """)

class RickyUI(QMainWindow):
    """Main UI Manager - coordinates all interface components with real GPS data"""
    
    def __init__(self, fare_calculator, mode_controller, sos_system):
        super().__init__()
        
        # Store backend references
        self.fare_calculator = fare_calculator
        self.mode_controller = mode_controller
        self.sos_system = sos_system
        self.gps_manager = fare_calculator.gps_manager
        
        # Current mode tracking
        self.current_mode = "For Hire"
        
        # Real-time data tracking
        self.current_distance = 0.0
        self.current_duration = 0
        self.current_speed = 0.0
        
        # Setup main UI
        self.setup_ui()
        
        # Setup update timers
        self.setup_timers()
        
        # Connect to GPS signals
        self.setup_gps_connections()
        
        print("🖥️ UI Manager initialized with GPS integration")
    
    def setup_gps_connections(self):
        """Connect to GPS manager signals for real-time updates"""
        # Connect GPS signals
        self.gps_manager.location_updated.connect(self._on_gps_location_update)
        self.gps_manager.speed_updated.connect(self._on_gps_speed_update)
        self.gps_manager.distance_updated.connect(self._on_gps_distance_update)
        
        # Connect fare calculator signals for real-time data
        self.fare_calculator.distance_updated.connect(self._on_distance_update)
        self.fare_calculator.duration_updated.connect(self._on_duration_update)
        
        print("📡 GPS connections established for real-time UI updates")
    
    @pyqtSlot(float, float)
    def _on_gps_location_update(self, lat, lon):
        """Handle GPS location updates"""
        # You can use this to update location displays
        pass
    
    @pyqtSlot(float)
    def _on_gps_speed_update(self, speed):
        """Handle GPS speed updates"""
        self.current_speed = speed
    
    @pyqtSlot(float)
    def _on_gps_distance_update(self, distance):
        """Handle GPS distance updates"""
        self.current_distance = distance
    
    @pyqtSlot(float)
    def _on_distance_update(self, distance):
        """Handle fare calculator distance updates"""
        self.current_distance = distance
        if self.current_mode == "Private":
            self.private_widget.update_distance(distance)
    
    @pyqtSlot(int)
    def _on_duration_update(self, duration_minutes):
        """Handle duration updates"""
        self.current_duration = duration_minutes
        if self.current_mode == "Private":
            self.private_widget.update_duration(duration_minutes)

    def setup_ui(self):
        """Setup the main UI structure"""
        self.setWindowTitle("Ricky Smart Autometer")
        self.setGeometry(0, 0, 800, 480)  # Raspberry Pi 7" display resolution
        
        # Main central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Top section - Mode display area
        self.mode_stack = QStackedWidget()
        self.mode_stack.setMinimumHeight(280)
        
        # Create mode widgets
        self.sharing_widget = SharingModeWidget()
        self.private_widget = PrivateModeWidget()
        self.for_hire_widget = self.create_for_hire_widget()
        self.waiting_widget = self.create_waiting_widget()
        
        # Add widgets to stack
        self.mode_stack.addWidget(self.sharing_widget)      # Index 0
        self.mode_stack.addWidget(self.private_widget)      # Index 1  
        self.mode_stack.addWidget(self.for_hire_widget)     # Index 2
        self.mode_stack.addWidget(self.waiting_widget)      # Index 3
        
        # Middle section - SOS status
        self.sos_widget = SOSStatusWidget()
        
        # Bottom section - Ads display
        self.ads_widget = AdsDisplayWidget()
        
        # Add all sections to main layout
        main_layout.addWidget(self.mode_stack)
        main_layout.addWidget(self.sos_widget)
        main_layout.addWidget(self.ads_widget)
        
        # Set layout proportions
        main_layout.setStretchFactor(self.mode_stack, 3)   # 60% of space
        main_layout.setStretchFactor(self.sos_widget, 0)   # Minimal space
        main_layout.setStretchFactor(self.ads_widget, 1)   # 20% of space
        
        central_widget.setLayout(main_layout)
        
        # Set initial mode
        self.update_mode("For Hire")
        
        print("🖥️ UI structure setup completed")
    
    def create_for_hire_widget(self):
        """Create For Hire mode widget"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Main status
        status_label = QLabel("🚕 FOR HIRE")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                font-weight: bold;
                color: #2C3E50;
                background-color: #F8F9FA;
                border: 3px solid #27AE60;
                border-radius: 15px;
                padding: 40px;
                margin: 20px;
            }
        """)
        
        # Subtitle with GPS info
        self.for_hire_subtitle = QLabel("Ready to accept passengers")
        self.for_hire_subtitle.setAlignment(Qt.AlignCenter)
        self.for_hire_subtitle.setStyleSheet("""
            QLabel {
                font-size: 18px;
                color: #7F8C8D;
                margin-bottom: 20px;
            }
        """)
        
        layout.addWidget(status_label)
        layout.addWidget(self.for_hire_subtitle)
        widget.setLayout(layout)
        
        return widget
    
    def create_waiting_widget(self):
        """Create Waiting mode widget"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Main status
        status_label = QLabel("⏸️ WAITING")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                font-weight: bold;
                color: #2C3E50;
                background-color: #F8F9FA;
                border: 3px solid #F39C12;
                border-radius: 15px;
                padding: 40px;
                margin: 20px;
            }
        """)
        
        # Subtitle with GPS status
        self.waiting_subtitle = QLabel("Driver on break")
        self.waiting_subtitle.setAlignment(Qt.AlignCenter)
        self.waiting_subtitle.setStyleSheet("""
            QLabel {
                font-size: 18px;
                color: #7F8C8D;
                margin-bottom: 20px;
            }
        """)
        
        layout.addWidget(status_label)
        layout.addWidget(self.waiting_subtitle)
        widget.setLayout(layout)
        
        return widget
    
    def setup_timers(self):
        """Setup update timers for real-time GPS data"""
        # Real-time update timer - updates every 2 seconds
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.realtime_gps_update)
        self.update_timer.start(2000)  # 2 seconds
        
        # Fast update timer for dynamic content - every 1 second
        self.fast_update_timer = QTimer()
        self.fast_update_timer.timeout.connect(self.fast_update)
        self.fast_update_timer.start(1000)  # 1 second
        
        print("⏰ Real-time GPS update timers configured")
    
    @pyqtSlot(str)
    def update_mode(self, mode):
        """Update current mode and switch display"""
        self.current_mode = mode
        
        # Switch to appropriate widget
        mode_mapping = {
            "Sharing": 0,
            "Private": 1,
            "For Hire": 2,
            "Waiting": 3
        }
        
        if mode in mode_mapping:
            self.mode_stack.setCurrentIndex(mode_mapping[mode])
            
            # Handle mode-specific logic
            if mode == "Private":
                # Start private mode fare calculation
                self.fare_calculator.start_private_mode()
            elif self.current_mode == "Private" and mode != "Private":
                # Stop private mode if switching away
                self.fare_calculator.stop_private_mode()
        
        print(f"🔄 UI switched to {mode} mode")
    
    @pyqtSlot(int, bool)
    def update_passenger(self, passenger_id, onboard):
        """Update passenger status in sharing mode"""
        if self.current_mode == "Sharing":
            self.sharing_widget.update_passenger(passenger_id, onboard)
            print(f"🧑 Updated passenger {passenger_id + 1}: {'ONBOARD' if onboard else 'OFFBOARD'}")
    
    @pyqtSlot(int, float)
    def update_fares(self, passenger_id, fare):
        """Update fare displays"""
        if self.current_mode == "Sharing":
            self.sharing_widget.update_fare(passenger_id, fare)
        elif self.current_mode == "Private":
            # For private mode, passenger_id is ignored and fare is total
            self.private_widget.update_fare(fare)
    
    @pyqtSlot(str)
    def update_sos_status(self, status):
        """Update SOS status display"""
        self.sos_widget.update_status(status)
    
    def realtime_gps_update(self):
        """Update displays with real GPS data"""
        try:
            # Get real-time GPS statistics
            gps_stats = self.fare_calculator.get_real_time_stats()
            
            # Update private mode with real GPS data
            if self.current_mode == "Private":
                self.private_widget.update_distance(gps_stats['total_distance'])
                if gps_stats['trip_duration'] > 0:
                    self.private_widget.update_duration(int(gps_stats['trip_duration']))
            
            # Update sharing mode total info with real data
            elif self.current_mode == "Sharing":
                total_distance = gps_stats['total_distance']
                waiting_time = max(0, int(gps_stats['trip_duration'] - (total_distance / max(gps_stats['current_speed'], 1) * 60)))
                self.sharing_widget.update_total_info(total_distance, waiting_time)
            
            # Update subtitle info in for-hire and waiting modes
            elif self.current_mode == "For Hire":
                gps_info = f"GPS: {'Fixed' if gps_stats['gps_fix'] else 'Searching'} • Speed: {gps_stats['current_speed']:.1f} km/h"
                self.for_hire_subtitle.setText(f"Ready to accept passengers\n{gps_info}")
            
            elif self.current_mode == "Waiting":
                location = gps_stats['current_location']
                location_info = f"Location: {location[0]:.4f}, {location[1]:.4f}" if location else "Location: Unknown"
                self.waiting_subtitle.setText(f"Driver on break\n{location_info}")
        
        except Exception as e:
            print(f"⚠️ Real-time GPS update error: {e}")
    
    def fast_update(self):
        """Fast updates for dynamic content"""
        try:
            # Update passenger info cards with real-time data in sharing mode
            if self.current_mode == "Sharing":
                for pid in range(3):
                    passenger_data = self.fare_calculator.passengers[pid]
                    if passenger_data['onboard']:
                        # Update distance and time for each passenger
                        distance = passenger_data['total_distance']
                        duration = (datetime.now() - passenger_data['start_time']).total_seconds() / 60 if passenger_data['start_time'] else 0
                        time_str = f"{int(duration//60):02d}:{int(duration%60):02d}"
                        
                        # Update passenger card info
                        if hasattr(self.sharing_widget, 'passenger_cards'):
                            self.sharing_widget.passenger_cards[pid].update_info(
                                f"{distance:.1f}", time_str
                            )
        
        except Exception as e:
            print(f"⚠️ Fast update error: {e}")
    
    def get_current_mode(self):
        """Get current display mode"""
        return self.current_mode
    
    def emergency_override(self):
        """Emergency override for SOS situations"""
        print("🚨 Emergency override activated")
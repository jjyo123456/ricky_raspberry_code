"""
Private Mode UI - Single fare display
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QFrame)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont

class PrivateModeWidget(QWidget):
    """Private mode widget with single large fare display"""
    
    def __init__(self):
        super().__init__()
        self.total_fare = 0.0
        self.distance = 0.0
        self.duration = 0
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the private mode UI"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        
        # Header info
        header_layout = QHBoxLayout()
        
        # Distance info
        distance_frame = QFrame()
        distance_frame.setStyleSheet("""
            QFrame {
                background-color: #ECF0F1;
                border-radius: 15px;
                padding: 15px;
            }
        """)
        distance_layout = QVBoxLayout()
        
        self.distance_value = QLabel("12.8km")
        self.distance_value.setAlignment(Qt.AlignCenter)
        self.distance_value.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2C3E50;
                margin-bottom: 5px;
            }
        """)
        
        distance_label = QLabel("Total Distance")
        distance_label.setAlignment(Qt.AlignCenter)
        distance_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #7F8C8D;
            }
        """)
        
        distance_layout.addWidget(self.distance_value)
        distance_layout.addWidget(distance_label)
        distance_frame.setLayout(distance_layout)
        
        # Waiting time info
        time_frame = QFrame()
        time_frame.setStyleSheet("""
            QFrame {
                background-color: #ECF0F1;
                border-radius: 15px;
                padding: 15px;
            }
        """)
        time_layout = QVBoxLayout()
        
        self.time_value = QLabel("6min")
        self.time_value.setAlignment(Qt.AlignCenter)
        self.time_value.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2C3E50;
                margin-bottom: 5px;
            }
        """)
        
        time_label = QLabel("Waiting Time")
        time_label.setAlignment(Qt.AlignCenter)
        time_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #7F8C8D;
            }
        """)
        
        time_layout.addWidget(self.time_value)
        time_layout.addWidget(time_label)
        time_frame.setLayout(time_layout)
        
        header_layout.addWidget(distance_frame)
        header_layout.addWidget(time_frame)
        
        # Main fare display
        fare_frame = QFrame()
        fare_frame.setStyleSheet("""
            QFrame {
                background-color: #2C3E50;
                border-radius: 20px;
                padding: 30px;
            }
        """)
        
        fare_layout = QVBoxLayout()
        
        self.fare_amount = QLabel("₹110.90")
        self.fare_amount.setAlignment(Qt.AlignCenter)
        self.fare_amount.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 48px;
                font-weight: bold;
                margin-bottom: 10px;
            }
        """)
        
        fare_label = QLabel("Total Fare")
        fare_label.setAlignment(Qt.AlignCenter)
        fare_label.setStyleSheet("""
            QLabel {
                color: #BDC3C7;
                font-size: 18px;
            }
        """)
        
        fare_layout.addWidget(self.fare_amount)
        fare_layout.addWidget(fare_label)
        fare_frame.setLayout(fare_layout)
        
        # Add all to main layout
        main_layout.addLayout(header_layout)
        main_layout.addWidget(fare_frame)
        
        self.setLayout(main_layout)
    
    @pyqtSlot(float)
    def update_fare(self, fare):
        """Update total fare"""
        self.total_fare = fare
        self.fare_amount.setText(f"₹{fare:.2f}")
    
    def update_distance(self, distance_km):
        """Update distance"""
        self.distance = distance_km
        self.distance_value.setText(f"{distance_km:.1f}km")
    
    def update_duration(self, duration_minutes):
        """Update trip duration"""
        self.duration = duration_minutes
        if duration_minutes >= 60:
            hours = duration_minutes // 60
            minutes = duration_minutes % 60
            self.time_value.setText(f"{hours}h {minutes}min")
        else:
            self.time_value.setText(f"{duration_minutes}min")
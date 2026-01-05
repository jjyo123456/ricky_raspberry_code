"""
Sharing Mode UI - 3 individual passenger cards
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QFrame, QGridLayout)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont

class PassengerCard(QFrame):
    """Individual passenger card widget"""
    
    def __init__(self, passenger_id):
        super().__init__()
        self.passenger_id = passenger_id
        self.fare = 0.0
        self.onboard = False
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the passenger card UI"""
        self.setFixedSize(200, 180)
        self.setStyleSheet("""
            QFrame {
                background-color: #2C3E50;
                border-radius: 15px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Passenger number
        self.number_label = QLabel(f"{self.passenger_id}")
        self.number_label.setAlignment(Qt.AlignCenter)
        self.number_label.setStyleSheet("""
            QLabel {
                background-color: #34495E;
                border-radius: 20px;
                color: white;
                font-size: 24px;
                font-weight: bold;
                padding: 8px;
                max-width: 50px;
                max-height: 50px;
            }
        """)
        
        # Fare amount
        self.fare_label = QLabel("₹0")
        self.fare_label.setAlignment(Qt.AlignCenter)
        self.fare_label.setStyleSheet("""
            QLabel {
                color: #F1C40F;
                font-size: 26px;
                font-weight: bold;
                margin: 5px 0;
            }
        """)
        
        # Distance and time info
        self.info_label = QLabel("0km ⏱ 0:00")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("""
            QLabel {
                color: #BDC3C7;
                font-size: 12px;
                margin-bottom: 10px;
            }
        """)
        
        # Status indicator
        self.status_label = QLabel("OFFBOARD")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #E74C3C;
                color: white;
                border-radius: 8px;
                padding: 5px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        
        # Add to layout
        layout.addWidget(self.number_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.fare_label)
        layout.addWidget(self.info_label)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    @pyqtSlot(float)
    def update_fare(self, fare):
        """Update fare display"""
        self.fare = fare
        self.fare_label.setText(f"₹{fare:.0f}")
    
    @pyqtSlot(bool)
    def update_status(self, onboard):
        """Update passenger status"""
        self.onboard = onboard
        if onboard:
            self.status_label.setText("ONBOARD")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #27AE60;
                    color: white;
                    border-radius: 8px;
                    padding: 5px;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
        else:
            self.status_label.setText("OFFBOARD")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #E74C3C;
                    color: white;
                    border-radius: 8px;
                    padding: 5px;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
    
    def update_info(self, distance_km, time_str):
        """Update distance and time info"""
        self.info_label.setText(f"{distance_km}km ⏱ {time_str}")

class SharingModeWidget(QWidget):
    """Main sharing mode widget with 3 passenger cards"""
    
    def __init__(self):
        super().__init__()
        self.passenger_cards = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the sharing mode UI"""
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Sharing Mode")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                color: #2C3E50;
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(header)
        
        # Passenger cards container
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        # Create 3 passenger cards
        for i in range(3):
            card = PassengerCard(i + 1)
            self.passenger_cards.append(card)
            cards_layout.addWidget(card)
        
        layout.addLayout(cards_layout)
        
        # Additional info
        self.total_info = QLabel("Total Distance: 0km | Waiting Time: 0min")
        self.total_info.setAlignment(Qt.AlignCenter)
        self.total_info.setStyleSheet("""
            QLabel {
                color: #7F8C8D;
                font-size: 14px;
                margin-top: 10px;
            }
        """)
        layout.addWidget(self.total_info)
        
        self.setLayout(layout)
    
    def update_passenger(self, passenger_id, onboard, fare=None):
        """Update specific passenger"""
        if 0 <= passenger_id < len(self.passenger_cards):
            self.passenger_cards[passenger_id].update_status(onboard)
            if fare is not None:
                self.passenger_cards[passenger_id].update_fare(fare)
    
    def update_fare(self, passenger_id, fare):
        """Update passenger fare"""
        if 0 <= passenger_id < len(self.passenger_cards):
            self.passenger_cards[passenger_id].update_fare(fare)
    
    def update_total_info(self, total_distance, waiting_time):
        """Update total information"""
        self.total_info.setText(f"Total Distance: {total_distance:.1f}km | Waiting Time: {waiting_time}min")
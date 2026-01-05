"""
Ads Display Component - Updated timing: 15s ads, 30s maps
Alternates between ads and lightweight map with proper timing
"""

import os
import random
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QStackedWidget,
                           QHBoxLayout)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap, QFont, QPainter, QPen, QBrush, QColor

from .map_display import MapDisplayWidget

class AdsDisplayWidget(QWidget):
    """Enhanced ads display with configurable timing for map vs ads"""
    
    content_changed = pyqtSignal(str, str)  # content_type, content_name
    
    def __init__(self):
        super().__init__()
        self.current_index = 0
        
        # UPDATED TIMING: Longer map display as requested
        self.ad_duration = 15000      # 15 seconds for ads
        self.map_duration = 30000     # 30 seconds for maps
        self.current_duration = self.ad_duration
        
        # Create map widget
        self.map_widget = MapDisplayWidget()
        
        self.setup_ui()
        self.load_content()
        
        # Setup rotation timer with variable duration
        self.rotation_timer = QTimer()
        self.rotation_timer.timeout.connect(self.rotate_content)
        self.start_rotation()
    
    def setup_ui(self):
        """Setup UI"""
        self.setFixedHeight(220)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main display stack
        self.display_stack = QStackedWidget()
        
        # Ad frames with enhanced styling
        self.ad1_frame = self.create_ad_frame(
            "🍽️ DELICIOUSNESS\nat your DOORSTEP!\n\nOrder food online\nFast delivery • Hot & Fresh",
            "#DC2626"
        )
        
        self.ad2_frame = self.create_ad_frame(
            "📱 Fast Delivery Service\nZomato • Swiggy • Uber Eats\n\n🛵 Order Now & Save!\n⭐ Rated 4.5+ stars",
            "#2563EB"
        )
        
        # Add to stack
        self.display_stack.addWidget(self.ad1_frame)     # Index 0
        self.display_stack.addWidget(self.map_widget)    # Index 1  
        self.display_stack.addWidget(self.ad2_frame)     # Index 2
        
        # Enhanced indicators with timing info
        self.indicator_layout = self.create_indicators()
        
        layout.addWidget(self.display_stack)
        layout.addLayout(self.indicator_layout)
        
        self.setLayout(layout)
    
    def create_ad_frame(self, text, bg_color):
        """Create enhanced ad frame"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {bg_color}, stop:1 {self.darken_color(bg_color)});
                border-radius: 15px;
                border: 2px solid #E2E8F0;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 15px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
        """)
        
        layout.addWidget(label)
        frame.setLayout(layout)
        
        return frame
    
    def darken_color(self, hex_color):
        """Darken a hex color for gradient effect"""
        # Simple darkening by reducing RGB values
        color_map = {
            "#DC2626": "#B91C1C",  # Red to darker red
            "#2563EB": "#1D4ED8",  # Blue to darker blue
        }
        return color_map.get(hex_color, hex_color)
    
    def create_indicators(self):
        """Create enhanced page indicators with timing info"""
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        # Main indicators
        indicator_container = QHBoxLayout()
        indicator_container.setSpacing(8)
        
        self.indicators = []
        content_info = [
            ("Ad", "15s", "#FF6B6B"),
            ("Map", "30s", "#4ECDC4"), 
            ("Ad", "15s", "#45B7D1")
        ]
        
        for i, (label, duration, color) in enumerate(content_info):
            # Create indicator widget
            indicator_widget = QWidget()
            indicator_widget.setFixedSize(60, 20)
            
            indicator_label = QLabel(f"{label}\n{duration}")
            indicator_label.setAlignment(Qt.AlignCenter)
            indicator_label.setStyleSheet(f"""
                QLabel {{
                    color: #95A5A6;
                    font-size: 9px;
                    font-weight: bold;
                    border-radius: 10px;
                    padding: 2px;
                }}
            """)
            
            widget_layout = QVBoxLayout()
            widget_layout.setContentsMargins(0, 0, 0, 0)
            widget_layout.addWidget(indicator_label)
            indicator_widget.setLayout(widget_layout)
            
            self.indicators.append({
                'widget': indicator_widget,
                'label': indicator_label,
                'color': color
            })
            
            indicator_container.addWidget(indicator_widget)
        
        layout.addLayout(indicator_container)
        
        # Add timer display
        self.timer_label = QLabel("⏰ Next: --s")
        self.timer_label.setStyleSheet("""
            QLabel {
                color: #7F8C8D;
                font-size: 10px;
                margin-left: 10px;
            }
        """)
        layout.addWidget(self.timer_label)
        
        # Timer for countdown display
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        
        return layout
    
    def load_content(self):
        """Load content configuration with timing"""
        self.content_items = [
            {"type": "advertisement", "name": "Food Delivery Ad 1", "duration": self.ad_duration},
            {"type": "map", "name": "OpenStreetMap", "duration": self.map_duration},
            {"type": "advertisement", "name": "Food Delivery Ad 2", "duration": self.ad_duration}
        ]
        
        print(f"📱 Loaded {len(self.content_items)} items: Ads={self.ad_duration//1000}s, Map={self.map_duration//1000}s")
    
    def display_content(self, index):
        """Display content at index with proper timing"""
        if index < len(self.content_items):
            item = self.content_items[index]
            
            # Switch display
            self.display_stack.setCurrentIndex(index)
            
            # Update current duration for next rotation
            self.current_duration = item["duration"]
            
            # Update indicators
            self.update_indicators(index)
            
            # Start countdown timer
            self.countdown_remaining = self.current_duration // 1000  # Convert to seconds
            self.countdown_timer.start(1000)  # Update every second
            
            # Emit signal
            self.content_changed.emit(item["type"], item["name"])
            
            print(f"📱 Displaying: {item['name']} for {self.current_duration//1000}s")
            
            # Update rotation timer with new duration
            self.rotation_timer.setInterval(self.current_duration)
    
    def update_indicators(self, active_index):
        """Update indicators with enhanced styling"""
        for i, indicator in enumerate(self.indicators):
            label = indicator['label']
            color = indicator['color']
            
            if i == active_index:
                # Active indicator
                label.setStyleSheet(f"""
                    QLabel {{
                        color: white;
                        background-color: {color};
                        font-size: 9px;
                        font-weight: bold;
                        border-radius: 10px;
                        padding: 2px;
                    }}
                """)
            else:
                # Inactive indicator
                label.setStyleSheet("""
                    QLabel {
                        color: #BDC3C7;
                        background-color: transparent;
                        font-size: 9px;
                        font-weight: normal;
                        border-radius: 10px;
                        padding: 2px;
                    }
                """)
    
    def update_countdown(self):
        """Update countdown display"""
        if self.countdown_remaining > 0:
            self.timer_label.setText(f"⏰ Next: {self.countdown_remaining}s")
            self.countdown_remaining -= 1
        else:
            self.timer_label.setText("⏰ Switching...")
            self.countdown_timer.stop()
    
    def rotate_content(self):
        """Rotate to next content with variable timing"""
        self.current_index = (self.current_index + 1) % len(self.content_items)
        self.display_content(self.current_index)
    
    def start_rotation(self):
        """Start rotation with proper initial timing"""
        self.display_content(0)  # Start with first item
        self.rotation_timer.start(self.current_duration)
        print(f"📱 Started rotation: Ad={self.ad_duration//1000}s, Map={self.map_duration//1000}s")
    
    def stop_rotation(self):
        """Stop rotation"""
        self.rotation_timer.stop()
        self.countdown_timer.stop()
        print("📱 Stopped content rotation")
    
    def set_timing(self, ad_duration_seconds, map_duration_seconds):
        """Update display timing"""
        self.ad_duration = ad_duration_seconds * 1000
        self.map_duration = map_duration_seconds * 1000
        
        # Update content items
        for item in self.content_items:
            if item["type"] == "advertisement":
                item["duration"] = self.ad_duration
            elif item["type"] == "map":
                item["duration"] = self.map_duration
        
        print(f"⏰ Updated timing: Ads={ad_duration_seconds}s, Map={map_duration_seconds}s")
    
    @pyqtSlot(float, float)
    def update_map_location(self, lat, lon):
        """Update map location"""
        self.map_widget.update_gps_location(lat, lon)
    
    @pyqtSlot(dict)
    def update_gps_status(self, gps_status):
        """Update GPS status"""
        self.map_widget.update_gps_status(gps_status)
    
    def get_map_widget(self):
        """Get map widget"""
        return self.map_widget
    
    def force_show_map(self):
        """Force display map"""
        self.rotation_timer.stop()
        self.countdown_timer.stop()
        self.display_content(1)  # Map is at index 1
    
    def force_show_ad(self, ad_index=0):
        """Force display advertisement"""
        self.rotation_timer.stop()
        self.countdown_timer.stop()
        self.display_content(0 if ad_index == 0 else 2)
    
    def get_current_content_type(self):
        """Get current content type"""
        current_item = self.content_items[self.current_index]
        return current_item["type"]
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_rotation()
        self.map_widget.cleanup()
        print("🧹 Ads display cleaned up")
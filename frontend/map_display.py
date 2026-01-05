"""
Lightweight Map Display Widget for Raspberry Pi - FIXED VERSION
Uses static OpenStreetMap tiles with proper User-Agent and error handling
"""

import os
import json
import time
import math
import requests
import threading
from io import BytesIO
from datetime import datetime

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QFrame, QPushButton)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QThread, QMutex
from PyQt5.QtGui import QPixmap, QPainter, QPen, QBrush, QColor, QFont
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest

class TileDownloader(QThread):
    """Fixed background thread for downloading map tiles"""
    
    tile_downloaded = pyqtSignal(int, int, int, bytes)  # x, y, zoom, image_data
    download_progress = pyqtSignal(str)  # status message
    
    def __init__(self):
        super().__init__()
        self.download_queue = []
        self.running = True
        self.session = None
        self.mutex = QMutex()
        
        # Setup requests session with proper headers
        self.setup_session()
    
    def setup_session(self):
        """Setup requests session with proper User-Agent"""
        self.session = requests.Session()
        
        # CRITICAL: Proper User-Agent to avoid OSM blocking
        self.session.headers.update({
            'User-Agent': 'RickyAutometer/1.0 (Raspberry Pi GPS Autometer; contact: ricky@autometer.com)',
            'Accept': 'image/png,image/*,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=3600'
        })
        
        print("🌐 HTTP session configured with proper User-Agent for OSM")
    
    def add_download(self, x, y, zoom):
        """Add tile to download queue"""
        self.mutex.lock()
        # Avoid duplicates
        tile_tuple = (x, y, zoom)
        if tile_tuple not in self.download_queue:
            self.download_queue.append(tile_tuple)
        self.mutex.unlock()
    
    def run(self):
        """Download tiles in background"""
        while self.running:
            try:
                self.mutex.lock()
                if self.download_queue:
                    x, y, z = self.download_queue.pop(0)
                    self.mutex.unlock()
                    
                    self.download_progress.emit(f"Downloading tile {x},{y},{z}...")
                    success = self.download_tile(x, y, z)
                    
                    if success:
                        print(f"✅ Downloaded tile {x},{y},{z}")
                    else:
                        print(f"❌ Failed to download tile {x},{y},{z}")
                    
                    # Respectful delay between requests (OSM requirement)
                    time.sleep(0.5)  # 500ms between tile requests
                else:
                    self.mutex.unlock()
                    time.sleep(0.1)
                    
            except Exception as e:
                self.mutex.unlock()
                print(f"❌ Tile downloader error: {e}")
                time.sleep(1)
    
    def download_tile(self, x, y, z):
        """Download single tile with proper error handling"""
        try:
            # Use HTTPS and proper tile server URL
            url = f"https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            
            # Make request with timeout
            response = self.session.get(url, timeout=15, stream=True)
            
            if response.status_code == 200:
                # Read image data
                image_data = response.content
                if len(image_data) > 100:  # Valid image should be larger than 100 bytes
                    self.tile_downloaded.emit(x, y, z, image_data)
                    return True
                else:
                    print(f"⚠️ Invalid tile data size: {len(image_data)} bytes")
                    
            elif response.status_code == 429:
                print(f"⚠️ Rate limited by OSM server (429). Waiting 30 seconds...")
                time.sleep(30)  # Wait longer if rate limited
                
            elif response.status_code == 403:
                print(f"❌ Forbidden (403) - Check User-Agent string")
                
            else:
                print(f"⚠️ HTTP {response.status_code} for tile {x},{y},{z}")
                
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout downloading tile {x},{y},{z}")
            
        except requests.exceptions.ConnectionError:
            print(f"🌐 Connection error for tile {x},{y},{z}")
            
        except Exception as e:
            print(f"❌ Tile download error for {x},{y},{z}: {e}")
            
        return False
    
    def clear_queue(self):
        """Clear download queue"""
        self.mutex.lock()
        self.download_queue.clear()
        self.mutex.unlock()
    
    def stop(self):
        """Stop downloader"""
        self.running = False
        if self.session:
            self.session.close()

class LightweightMapWidget(QWidget):
    """Fixed lightweight map widget with proper tile loading"""
    
    def __init__(self):
        super().__init__()
        self.current_location = (19.0760, 72.8777)  # Mumbai default
        self.zoom_level = 15
        self.tile_size = 256
        self.map_width = 750
        self.map_height = 200
        
        # Tile management
        self.tile_cache = {}
        self.max_cache_size = 30  # Reduced for Raspberry Pi memory
        self.pending_tiles = set()
        
        # GPS tracking
        self.route_points = []
        self.gps_status = {'fix': False, 'satellites': 0}
        
        # Download status
        self.tiles_downloading = False
        self.last_download_time = 0
        
        # Setup downloader with better configuration
        self.tile_downloader = TileDownloader()
        self.tile_downloader.tile_downloaded.connect(self.on_tile_downloaded)
        self.tile_downloader.download_progress.connect(self.on_download_progress)
        self.tile_downloader.start()
        
        self.setup_ui()
        
        # Delayed initial update to avoid immediate download rush
        QTimer.singleShot(2000, self.update_map)  # Wait 2 seconds before first update
        
        print("🗺️ Fixed Lightweight Map Widget initialized")

    def setup_ui(self):
        """Setup map UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Map info header
        header_layout = QHBoxLayout()
        
        self.location_label = QLabel("📍 Initializing map...")
        self.location_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #2C3E50;
                padding: 5px;
            }
        """)
        
        self.status_label = QLabel("🔄 Starting...")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #3498DB;
                padding: 5px;
            }
        """)
        
        header_layout.addWidget(self.location_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
        
        # Map display area
        self.map_label = QLabel()
        self.map_label.setMinimumSize(self.map_width, self.map_height)
        self.map_label.setMaximumSize(self.map_width, self.map_height)
        self.map_label.setAlignment(Qt.AlignCenter)
        self.map_label.setStyleSheet("""
            QLabel {
                background-color: #F0F8FF;
                border: 2px solid #3498DB;
                border-radius: 10px;
            }
        """)
        
        # Create initial map
        self.create_loading_map()
        
        layout.addWidget(self.map_label)
        
        # Controls footer
        controls_layout = QHBoxLayout()
        
        # GPS status
        self.gps_status_label = QLabel("🛰️ GPS: Initializing...")
        self.gps_status_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #95A5A6;
                padding: 3px;
            }
        """)
        
        # Coordinates
        self.coords_label = QLabel("Coordinates: Loading...")
        self.coords_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #95A5A6;
                padding: 3px;
            }
        """)
        
        # Zoom controls
        zoom_out_btn = QPushButton("➖")
        zoom_out_btn.setFixedSize(25, 20)
        zoom_out_btn.clicked.connect(self.zoom_out)
        zoom_out_btn.setToolTip("Zoom Out")
        
        zoom_in_btn = QPushButton("➕")
        zoom_in_btn.setFixedSize(25, 20)
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_in_btn.setToolTip("Zoom In")
        
        controls_layout.addWidget(self.gps_status_label)
        controls_layout.addStretch()
        controls_layout.addWidget(self.coords_label)
        controls_layout.addWidget(zoom_out_btn)
        controls_layout.addWidget(zoom_in_btn)
        
        layout.addLayout(controls_layout)
        
        self.setLayout(layout)

    def create_loading_map(self):
        """Create loading map with better visual feedback"""
        pixmap = QPixmap(self.map_width, self.map_height)
        pixmap.fill(QColor("#EBF5FF"))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background pattern
        painter.setPen(QPen(QColor("#D1E7FF"), 1))
        for i in range(0, self.map_width, 20):
            painter.drawLine(i, 0, i, self.map_height)
        for i in range(0, self.map_height, 20):
            painter.drawLine(0, i, self.map_width, i)
        
        # Draw main message
        font_large = QFont("Arial", 18, QFont.Bold)
        painter.setFont(font_large)
        painter.setPen(QPen(QColor("#2C3E50")))
        
        main_text = "🗺️ Loading OpenStreetMap"
        text_rect = painter.fontMetrics().boundingRect(main_text)
        x = (self.map_width - text_rect.width()) // 2
        y = (self.map_height - text_rect.height()) // 2 - 20
        painter.drawText(x, y, main_text)
        
        # Draw status message
        font_small = QFont("Arial", 12)
        painter.setFont(font_small)
        painter.setPen(QPen(QColor("#7F8C8D")))
        
        status_text = "📡 Connecting to tile servers..."
        status_rect = painter.fontMetrics().boundingRect(status_text)
        x = (self.map_width - status_rect.width()) // 2
        y = (self.map_height - status_rect.height()) // 2 + 10
        painter.drawText(x, y, status_text)
        
        # Draw current coordinates
        lat, lon = self.current_location
        coords_text = f"📍 {lat:.6f}, {lon:.6f}"
        coords_rect = painter.fontMetrics().boundingRect(coords_text)
        x = (self.map_width - coords_rect.width()) // 2
        y = (self.map_height - coords_rect.height()) // 2 + 35
        painter.drawText(x, y, coords_text)
        
        painter.end()
        self.map_label.setPixmap(pixmap)

    def deg2num(self, lat_deg, lon_deg, zoom):
        """Convert lat/lon to tile numbers"""
        try:
            lat_rad = math.radians(lat_deg)
            n = 2.0 ** zoom
            x = int((lon_deg + 180.0) / 360.0 * n)
            y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
            return (x, y)
        except Exception as e:
            print(f"❌ Coordinate conversion error: {e}")
            return (0, 0)

    def update_map(self):
        """Update map with current location - FIXED VERSION"""
        try:
            current_time = time.time()
            
            # Avoid too frequent updates
            if current_time - self.last_download_time < 3.0:  # 3 second minimum interval
                return
            
            self.last_download_time = current_time
            
            lat, lon = self.current_location
            print(f"🗺️ Updating map for location: {lat:.6f}, {lon:.6f}")
            
            # Calculate center tile
            center_x, center_y = self.deg2num(lat, lon, self.zoom_level)
            
            # Calculate required tiles (smaller grid for better performance)
            tiles_needed = []
            
            # Only download 3x2 grid of tiles (6 tiles total)
            for dx in range(-1, 2):  # -1, 0, 1
                for dy in range(-1, 1):  # -1, 0
                    tile_x = center_x + dx
                    tile_y = center_y + dy
                    
                    # Ensure tile coordinates are valid
                    max_tile = 2 ** self.zoom_level
                    if 0 <= tile_x < max_tile and 0 <= tile_y < max_tile:
                        tiles_needed.append((tile_x, tile_y))
            
            # Check which tiles need downloading
            tiles_to_download = []
            for tile_x, tile_y in tiles_needed:
                tile_key = f"{self.zoom_level}_{tile_x}_{tile_y}"
                if tile_key not in self.tile_cache and (tile_x, tile_y, self.zoom_level) not in self.pending_tiles:
                    tiles_to_download.append((tile_x, tile_y))
                    self.pending_tiles.add((tile_x, tile_y, self.zoom_level))
            
            # Start downloads
            if tiles_to_download:
                print(f"📥 Starting download of {len(tiles_to_download)} tiles")
                self.tiles_downloading = True
                self.status_label.setText(f"📥 Loading {len(tiles_to_download)} tiles...")
                
                for tile_x, tile_y in tiles_to_download:
                    self.tile_downloader.add_download(tile_x, tile_y, self.zoom_level)
            else:
                print("✅ All required tiles are cached")
                self.tiles_downloading = False
                self.status_label.setText("✅ Map ready")
            
            # Always try to render with available tiles
            self.render_map()
            
            # Update location info
            self.update_location_info(lat, lon)
            
        except Exception as e:
            print(f"❌ Map update error: {e}")
            self.show_error_map(str(e))

    def render_map(self):
        """Render map from available cached tiles"""
        try:
            lat, lon = self.current_location
            center_x, center_y = self.deg2num(lat, lon, self.zoom_level)
            
            # Create map pixmap
            map_pixmap = QPixmap(self.map_width, self.map_height)
            map_pixmap.fill(QColor("#E8F4FD"))
            
            painter = QPainter(map_pixmap)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            tiles_drawn = 0
            
            # Draw tiles in 3x2 grid
            for dx in range(-1, 2):  # -1, 0, 1
                for dy in range(-1, 1):  # -1, 0
                    tile_x = center_x + dx
                    tile_y = center_y + dy
                    
                    tile_key = f"{self.zoom_level}_{tile_x}_{tile_y}"
                    
                    if tile_key in self.tile_cache:
                        tile_pixmap = self.tile_cache[tile_key]
                        
                        # Calculate exact position
                        pixel_x = self.map_width // 2 + dx * self.tile_size
                        pixel_y = self.map_height // 2 + dy * self.tile_size
                        
                        # Draw tile
                        painter.drawPixmap(
                            pixel_x - self.tile_size // 2, 
                            pixel_y - self.tile_size // 2, 
                            self.tile_size, 
                            self.tile_size,
                            tile_pixmap
                        )
                        tiles_drawn += 1
            
            # Draw current location marker
            self.draw_location_marker(painter)
            
            # Draw route if available
            if len(self.route_points) > 1:
                self.draw_route_trail(painter)
            
            # Show status if no tiles loaded
            if tiles_drawn == 0:
                font = QFont("Arial", 14, QFont.Bold)
                painter.setFont(font)
                painter.setPen(QPen(QColor("#E74C3C")))
                
                if self.tiles_downloading:
                    painter.drawText(map_pixmap.rect(), Qt.AlignCenter, 
                                   "🔄 Downloading tiles...\nPlease wait")
                else:
                    painter.drawText(map_pixmap.rect(), Qt.AlignCenter, 
                                   "❌ No map tiles available\nCheck internet connection")
            else:
                # Show tile count
                font = QFont("Arial", 10)
                painter.setFont(font)
                painter.setPen(QPen(QColor("#34495E")))
                painter.drawText(10, self.map_height - 10, f"Tiles: {tiles_drawn}/6")
            
            painter.end()
            
            self.map_label.setPixmap(map_pixmap)
            print(f"🎨 Rendered map with {tiles_drawn} tiles")
            
        except Exception as e:
            print(f"❌ Map render error: {e}")

    def draw_location_marker(self, painter):
        """Draw current location marker"""
        # Marker at center of map
        marker_x = self.map_width // 2
        marker_y = self.map_height // 2
        
        # Draw outer circle (red)
        painter.setPen(QPen(QColor("#E74C3C"), 3))
        painter.setBrush(QBrush(QColor("#E74C3C")))
        painter.drawEllipse(marker_x - 10, marker_y - 10, 20, 20)
        
        # Draw inner circle (white)
        painter.setPen(QPen(QColor("white"), 2))
        painter.setBrush(QBrush(QColor("white")))
        painter.drawEllipse(marker_x - 6, marker_y - 6, 12, 12)
        
        # Draw center dot
        painter.setPen(QPen(QColor("#E74C3C"), 2))
        painter.setBrush(QBrush(QColor("#E74C3C")))
        painter.drawEllipse(marker_x - 2, marker_y - 2, 4, 4)

    def draw_route_trail(self, painter):
        """Draw route trail"""
        if len(self.route_points) < 2:
            return
        
        try:
            painter.setPen(QPen(QColor("#3498DB"), 3))
            
            # Convert last 10 GPS points to screen coordinates
            screen_points = []
            center_lat, center_lon = self.current_location
            center_x, center_y = self.deg2num(center_lat, center_lon, self.zoom_level)
            
            for lat, lon in self.route_points[-10:]:  # Last 10 points only
                tile_x, tile_y = self.deg2num(lat, lon, self.zoom_level)
                
                # Convert to screen pixels
                screen_x = self.map_width // 2 + (tile_x - center_x) * self.tile_size
                screen_y = self.map_height // 2 + (tile_y - center_y) * self.tile_size
                
                # Only add points that are visible on screen
                if -50 <= screen_x <= self.map_width + 50 and -50 <= screen_y <= self.map_height + 50:
                    screen_points.append((screen_x, screen_y))
            
            # Draw route lines
            for i in range(1, len(screen_points)):
                x1, y1 = screen_points[i-1]
                x2, y2 = screen_points[i]
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
        except Exception as e:
            print(f"❌ Route drawing error: {e}")

    @pyqtSlot(int, int, int, bytes)
    def on_tile_downloaded(self, x, y, zoom, image_data):
        """Handle successfully downloaded tile"""
        try:
            if zoom == self.zoom_level:
                # Create pixmap from image data
                pixmap = QPixmap()
                success = pixmap.loadFromData(image_data)
                
                if success and not pixmap.isNull():
                    # Add to cache
                    tile_key = f"{zoom}_{x}_{y}"
                    self.tile_cache[tile_key] = pixmap
                    
                    # Remove from pending
                    self.pending_tiles.discard((x, y, zoom))
                    
                    # Manage cache size
                    if len(self.tile_cache) > self.max_cache_size:
                        # Remove 5 oldest entries
                        keys_to_remove = list(self.tile_cache.keys())[:5]
                        for key in keys_to_remove:
                            del self.tile_cache[key]
                    
                    print(f"✅ Cached tile {x},{y},{zoom} - Cache size: {len(self.tile_cache)}")
                    
                    # Re-render map
                    self.render_map()
                    
                    # Update status
                    if not self.pending_tiles:
                        self.tiles_downloading = False
                        self.status_label.setText("✅ Map loaded")
                    
                else:
                    print(f"❌ Invalid image data for tile {x},{y},{zoom}")
                    
        except Exception as e:
            print(f"❌ Tile processing error: {e}")

    @pyqtSlot(str)
    def on_download_progress(self, message):
        """Handle download progress updates"""
        self.status_label.setText(message)

    def show_error_map(self, error_msg):
        """Show error message on map"""
        pixmap = QPixmap(self.map_width, self.map_height)
        pixmap.fill(QColor("#FFE5E5"))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        font = QFont("Arial", 14, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#E74C3C")))
        
        text = f"❌ Map Error\n\n{error_msg}\n\nCheck internet connection"
        painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
        
        painter.end()
        self.map_label.setPixmap(pixmap)

    @pyqtSlot(float, float)
    def update_gps_location(self, lat, lon):
        """Update map with new GPS location"""
        print(f"📍 GPS Update: {lat:.6f}, {lon:.6f}")
        
        # Update location
        old_location = self.current_location
        self.current_location = (lat, lon)
        
        # Add to route trail
        self.route_points.append((lat, lon))
        
        # Limit route points to last 50
        if len(self.route_points) > 50:
            self.route_points = self.route_points[-50:]
        
        # Update map if location changed significantly
        if old_location:
            distance = math.sqrt((lat - old_location[0])**2 + (lon - old_location[1])**2)
            if distance > 0.001:  # ~100m threshold
                self.update_map()
            else:
                # Just re-render with new marker position
                self.render_map()

    def update_location_info(self, lat, lon):
        """Update location information display"""
        self.coords_label.setText(f"{lat:.6f}, {lon:.6f}")
        
        # Update location name in background
        threading.Thread(target=self.get_location_name, args=(lat, lon), daemon=True).start()

    def get_location_name(self, lat, lon):
        """Get location name from coordinates"""
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                'format': 'json',
                'lat': lat,
                'lon': lon,
                'zoom': 16,
                'addressdetails': 1
            }
            headers = {
                'User-Agent': 'RickyAutometer/1.0 (Raspberry Pi GPS Autometer; contact: ricky@autometer.com)'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=8)
            if response.status_code == 200:
                data = response.json()
                address = self.parse_address(data)
                # Update UI in main thread
                QTimer.singleShot(0, lambda: self.location_label.setText(f"📍 {address}"))
            else:
                print(f"⚠️ Geocoding failed: HTTP {response.status_code}")
            
        except Exception as e:
            print(f"⚠️ Location name lookup error: {e}")
            QTimer.singleShot(0, lambda: self.location_label.setText(f"📍 {lat:.4f}, {lon:.4f}"))

    def parse_address(self, data):
        """Parse address from geocoding response"""
        try:
            address = data.get('address', {})
            parts = []
            
            # Priority order for address components
            for key in ['road', 'suburb', 'neighbourhood', 'city', 'town', 'village']:
                if key in address and len(parts) < 2:
                    parts.append(address[key])
            
            if parts:
                return ', '.join(parts)
            else:
                display_name = data.get('display_name', '')
                return display_name[:40] + ('...' if len(display_name) > 40 else '')
                
        except Exception as e:
            print(f"❌ Address parsing error: {e}")
            return 'Unknown Location'

    def update_gps_status(self, gps_status):
        """Update GPS status display"""
        self.gps_status = gps_status
        
        if gps_status.get('fix', False):
            satellites = gps_status.get('satellites', 0)
            self.gps_status_label.setText(f"🛰️ GPS: {satellites} sats")
            self.gps_status_label.setStyleSheet("QLabel { color: #27AE60; font-size: 11px; }")
        else:
            self.gps_status_label.setText("🛰️ GPS: Searching...")
            self.gps_status_label.setStyleSheet("QLabel { color: #E74C3C; font-size: 11px; }")

    def zoom_in(self):
        """Zoom in"""
        if self.zoom_level < 18:
            self.zoom_level += 1
            print(f"🔍 Zoomed in to level {self.zoom_level}")
            self.tile_cache.clear()
            self.pending_tiles.clear()
            self.tile_downloader.clear_queue()
            self.update_map()

    def zoom_out(self):
        """Zoom out"""
        if self.zoom_level > 8:
            self.zoom_level -= 1
            print(f"🔍 Zoomed out to level {self.zoom_level}")
            self.tile_cache.clear()
            self.pending_tiles.clear()
            self.tile_downloader.clear_queue()
            self.update_map()

    def cleanup(self):
        """Cleanup resources"""
        print("🧹 Cleaning up map widget...")
        self.tile_downloader.stop()
        self.tile_downloader.wait(2000)  # Wait up to 2 seconds

# Wrapper class for compatibility
class MapDisplayWidget(QWidget):
    """Wrapper widget for the lightweight map"""
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.map_widget = LightweightMapWidget()
        layout.addWidget(self.map_widget)
        
        self.setLayout(layout)
        
        print("🗺️ Map Display Widget wrapper initialized")
    
    @pyqtSlot(float, float)
    def update_gps_location(self, lat, lon):
        """Update GPS location"""
        self.map_widget.update_gps_location(lat, lon)
    
    def update_gps_status(self, gps_status):
        """Update GPS status"""
        self.map_widget.update_gps_status(gps_status)
    
    def cleanup(self):
        """Cleanup resources"""
        self.map_widget.cleanup()
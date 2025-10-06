"""
OBD Data Dashboard GUI
A PyQt5-based dashboard for displaying vehicle OBD data with custom gauge widgets.
Multi-page dashboard with navigation between different OBD data categories.
Compatible with Python 3.9+
"""

import sys
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QProgressBar, QPushButton,
                             QStackedWidget, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics, QPainterPath, QConicalGradient
import math

# Global OBD connection and modules (initialized when needed)
obd_connection = None
read_json = None
OBD_AVAILABLE = False


def initialize_obd_connection():
    """
    Initialize OBD connection and load required modules.
    This is called only when running in real OBD mode.
    """
    global obd_connection, read_json, OBD_AVAILABLE
    
    try:
        import obd
        import read_json as rj
        read_json = rj
        
        print("Connecting to OBD-II adapter...")
        # Create OBD connection (using same config as get_data.py)
        obd_connection = obd.OBD("192.168.0.10", 35000)
        
        if obd_connection.is_connected():
            print("✓ OBD-II adapter connected successfully!")
            OBD_AVAILABLE = True
            return True
        else:
            print("✗ Failed to connect to OBD-II adapter")
            return False
            
    except Exception as e:
        print(f"✗ Error initializing OBD connection: {e}")
        return False


def read_obd_data(command):
    """
    Read data from OBD connection.
    This replaces get_data.read_obd_data() to avoid auto-connection on import.
    """
    global obd_connection
    
    if obd_connection is None:
        return None
    
    try:
        response = obd_connection.query(command)
        if response.is_null():
            return None
        return response.value
    except Exception as e:
        print(f"Error reading OBD data: {e}")
        return None


class GaugeWidget(QWidget):
    """
    Custom round gauge widget that displays a value with an arc and needle.
    Resembles a clean speedometer design.
    """
    
    def __init__(self, title="Gauge", min_value=0, max_value=100, unit="", parent=None):
        super().__init__(parent)
        self.title = title
        self.min_value = min_value
        self.max_value = max_value
        self.unit = unit
        self.current_value = 0
        
        # Visual settings
        self.arc_color = QColor(0, 200, 150)  # Teal/green
        self.needle_color = QColor(255, 80, 80)  # Red needle
        self.background_color = QColor(40, 40, 45)
        self.text_color = QColor(220, 220, 220)
        
        # Gauge geometry
        self.start_angle = 225  # Start from bottom-left
        self.span_angle = 270   # 270 degrees arc
        
        self.setMinimumSize(200, 200)
        
    def set_value(self, value):
        """Update the gauge value and trigger repaint."""
        self.current_value = max(self.min_value, min(self.max_value, value))
        self.update()
    
    def paintEvent(self, event):
        """Custom paint event to draw the gauge."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get dimensions
        width = self.width()
        height = self.height()
        side = min(width, height)
        
        # Center the gauge
        painter.translate(width / 2, height / 2)
        painter.scale(side / 240.0, side / 240.0)
        
        # Draw background circle
        painter.setPen(QPen(QColor(60, 60, 65), 2))
        painter.setBrush(self.background_color)
        painter.drawEllipse(QPointF(0, 0), 100, 100)
        
        # Draw outer ring
        painter.setPen(QPen(QColor(80, 80, 85), 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(0, 0), 105, 105)
        
        # Draw background arc (inactive part)
        painter.setPen(QPen(QColor(60, 60, 65), 12, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(QRectF(-90, -90, 180, 180), 
                       self.start_angle * 16, self.span_angle * 16)
        
        # Draw active arc (representing current value)
        value_ratio = (self.current_value - self.min_value) / (self.max_value - self.min_value)
        active_span = self.span_angle * value_ratio
        
        painter.setPen(QPen(self.arc_color, 12, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(QRectF(-90, -90, 180, 180), 
                       self.start_angle * 16, int(active_span * 16))
        
        # Draw scale marks
        self._draw_scale_marks(painter)
        
        # Draw needle
        self._draw_needle(painter, value_ratio)
        
        # Draw center cap
        painter.setPen(QPen(QColor(100, 100, 105), 2))
        painter.setBrush(QColor(70, 70, 75))
        painter.drawEllipse(QPointF(0, 0), 8, 8)
        
        # Draw value text
        painter.setPen(self.text_color)
        painter.setFont(QFont("Arial", 16, QFont.Bold))
        value_text = f"{int(self.current_value)}"
        painter.drawText(QRectF(-50, 20, 100, 30), Qt.AlignCenter, value_text)
        
        # Draw unit text
        painter.setFont(QFont("Arial", 8))
        painter.drawText(QRectF(-50, 45, 100, 20), Qt.AlignCenter, self.unit)
        
        # Draw title
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(QRectF(-50, -70, 100, 20), Qt.AlignCenter, self.title)
    
    def _draw_scale_marks(self, painter):
        """Draw tick marks around the gauge."""
        painter.save()
        
        num_ticks = 9  # Number of major ticks
        for i in range(num_ticks):
            angle = self.start_angle - (self.span_angle * i / (num_ticks - 1))
            angle_rad = math.radians(angle)
            
            # Major tick
            x1 = 85 * math.cos(angle_rad)
            y1 = -85 * math.sin(angle_rad)
            x2 = 75 * math.cos(angle_rad)
            y2 = -75 * math.sin(angle_rad)
            
            painter.setPen(QPen(QColor(150, 150, 155), 2))
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            
            # Draw value labels
            value = self.min_value + (self.max_value - self.min_value) * i / (num_ticks - 1)
            x_text = 65 * math.cos(angle_rad)
            y_text = -65 * math.sin(angle_rad)
            
            painter.setFont(QFont("Arial", 7))
            painter.setPen(QColor(180, 180, 185))
            painter.drawText(QRectF(x_text - 15, y_text - 8, 30, 16), 
                           Qt.AlignCenter, str(int(value)))
        
        painter.restore()
    
    def _draw_needle(self, painter, value_ratio):
        """Draw the gauge needle."""
        painter.save()
        
        # Calculate needle angle
        needle_angle = self.start_angle - (self.span_angle * value_ratio)
        painter.rotate(-needle_angle)
        
        # Draw needle shadow
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 80))
        needle_shadow = QPainterPath()
        needle_shadow.moveTo(2, 2)
        needle_shadow.lineTo(-6, -12)
        needle_shadow.lineTo(-72, -2)
        needle_shadow.lineTo(-72, 2)
        needle_shadow.lineTo(-6, 12)
        needle_shadow.closeSubpath()
        painter.drawPath(needle_shadow)
        
        # Draw needle
        painter.setBrush(self.needle_color)
        painter.setPen(QPen(QColor(200, 60, 60), 1))
        needle = QPainterPath()
        needle.moveTo(0, 0)
        needle.lineTo(-8, -10)
        needle.lineTo(-70, 0)
        needle.lineTo(-8, 10)
        needle.closeSubpath()
        painter.drawPath(needle)
        
        painter.restore()


class OBDDashboard(QMainWindow):
    """
    Main dashboard window for displaying OBD data across multiple pages.
    Can use either simulated data or real OBD data.
    Features 4 pages: Main, Temperatures, Fuel & Air, and Diagnostics.
    """
    
    def __init__(self, use_simulation=True):
        super().__init__()
        self.use_simulation = use_simulation
        self.commands = {}
        
        # Initialize OBD connection if using real mode
        if not use_simulation:
            success = initialize_obd_connection()
            if not success:
                print("⚠ Failed to connect to OBD adapter. Falling back to simulation mode.")
                self.use_simulation = True
            else:
                # Load OBD commands
                try:
                    self.commands = read_json.load_commands()
                    print(f"✓ Loaded {len(self.commands)} OBD commands")
                except Exception as e:
                    print(f"✗ Error loading OBD commands: {e}")
                    print("Falling back to simulation mode")
                    self.use_simulation = True
        
        self.init_ui()
        self.setup_timer()
        
    def init_ui(self):
        """Initialize the user interface."""
        mode_text = "Simulation" if self.use_simulation else "Live OBD"
        self.setWindowTitle(f"OBD Data Dashboard - {mode_text}")
        self.setGeometry(100, 100, 1024, 600)
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2a2a2e;
            }
            QLabel {
                color: #dcdcdc;
                font-size: 14px;
            }
            QProgressBar {
                border: 2px solid #505055;
                border-radius: 5px;
                background-color: #3a3a3e;
                text-align: center;
                color: #dcdcdc;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #00c896;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #3a3a3e;
                color: #dcdcdc;
                border: 2px solid #505055;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a4a4e;
                border-color: #00c896;
            }
            QPushButton:pressed {
                background-color: #00c896;
            }
            QPushButton#activeNavButton {
                background-color: #00c896;
                border-color: #00c896;
                color: #1a1a1e;
            }
        """)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Vehicle OBD Dashboard")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #00c896; margin-bottom: 5px;")
        main_layout.addWidget(title_label)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(10)
        
        self.nav_buttons = []
        nav_titles = ["Main", "Temperatures", "Fuel & Air", "Diagnostics"]
        
        for i, title in enumerate(nav_titles):
            btn = QPushButton(title)
            btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)
        
        main_layout.addLayout(nav_layout)
        
        # Create stacked widget for pages
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # Create all four pages
        self.create_page1_main()
        self.create_page2_temperatures()
        self.create_page3_fuel_air()
        self.create_page4_diagnostics()
        
        # Set initial page
        self.switch_page(0)
        
        # Initialize runtime counter and diagnostics data
        self.runtime_seconds = 0
        self.distance_since_clear = 0
        self.time_since_clear = 0
        
    def create_page1_main(self):
        """PAGE 1: Main dashboard with Speed, RPM, Throttle, Engine Load, Timing, Runtime"""
        page1 = QWidget()
        layout = QVBoxLayout(page1)
        layout.setSpacing(20)
        
        # Page title
        page_title = QLabel("Main Dashboard")
        page_title.setAlignment(Qt.AlignCenter)
        page_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00c896;")
        layout.addWidget(page_title)
        
        # Top row: Three gauges
        gauge_layout = QHBoxLayout()
        gauge_layout.setSpacing(20)
        
        # Speed gauge
        self.speed_gauge = GaugeWidget("SPEED", 0, 200, "km/h")
        gauge_layout.addWidget(self.speed_gauge)
        
        # RPM gauge
        self.rpm_gauge = GaugeWidget("RPM", 0, 8000, "rpm")
        gauge_layout.addWidget(self.rpm_gauge)
        
        # Throttle position gauge
        self.throttle_gauge = GaugeWidget("THROTTLE", 0, 100, "%")
        gauge_layout.addWidget(self.throttle_gauge)
        
        layout.addLayout(gauge_layout)
        
        # Bottom section: Text-based data
        data_layout = QVBoxLayout()
        data_layout.setSpacing(15)
        
        # Engine Load section
        load_container = QVBoxLayout()
        self.load_label = QLabel("ENGINE LOAD: 0%")
        self.load_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        load_container.addWidget(self.load_label)
        
        self.load_progress = QProgressBar()
        self.load_progress.setRange(0, 100)
        self.load_progress.setValue(0)
        self.load_progress.setMinimumHeight(30)
        load_container.addWidget(self.load_progress)
        
        data_layout.addLayout(load_container)
        
        # Additional data in horizontal layout
        additional_data_layout = QHBoxLayout()
        additional_data_layout.setSpacing(30)
        
        additional_data_layout.addStretch()
        
        # Timing Advance
        timing_container = QVBoxLayout()
        timing_title = QLabel("TIMING ADVANCE")
        timing_title.setAlignment(Qt.AlignCenter)
        timing_title.setStyleSheet("font-size: 12px; color: #aaaaaa;")
        self.timing_value = QLabel("0.0°")
        self.timing_value.setAlignment(Qt.AlignCenter)
        self.timing_value.setStyleSheet("font-size: 20px; font-weight: bold; color: #00c896;")
        timing_container.addWidget(timing_title)
        timing_container.addWidget(self.timing_value)
        additional_data_layout.addLayout(timing_container)
        
        # Run Time
        runtime_container = QVBoxLayout()
        runtime_title = QLabel("ENGINE RUN TIME")
        runtime_title.setAlignment(Qt.AlignCenter)
        runtime_title.setStyleSheet("font-size: 12px; color: #aaaaaa;")
        self.runtime_value = QLabel("00:00:00")
        self.runtime_value.setAlignment(Qt.AlignCenter)
        self.runtime_value.setStyleSheet("font-size: 20px; font-weight: bold; color: #00c896;")
        runtime_container.addWidget(runtime_title)
        runtime_container.addWidget(self.runtime_value)
        additional_data_layout.addLayout(runtime_container)
        
        additional_data_layout.addStretch()
        data_layout.addLayout(additional_data_layout)
        
        layout.addLayout(data_layout)
        layout.addStretch()
        
        self.stacked_widget.addWidget(page1)
    
    def create_page2_temperatures(self):
        """PAGE 2: Temperature gauges - Coolant, Intake, Oil"""
        page2 = QWidget()
        layout = QVBoxLayout(page2)
        layout.setSpacing(20)
        
        # Page title
        page_title = QLabel("Temperature Monitoring")
        page_title.setAlignment(Qt.AlignCenter)
        page_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00c896;")
        layout.addWidget(page_title)
        
        # Three temperature gauges
        gauge_layout = QHBoxLayout()
        gauge_layout.setSpacing(20)
        
        # Coolant Temperature gauge
        self.coolant_gauge = GaugeWidget("COOLANT", -40, 120, "°C")
        gauge_layout.addWidget(self.coolant_gauge)
        
        # Intake Air Temperature gauge
        self.intake_temp_gauge = GaugeWidget("INTAKE AIR", -40, 80, "°C")
        gauge_layout.addWidget(self.intake_temp_gauge)
        
        # Oil Temperature gauge
        self.oil_temp_gauge = GaugeWidget("OIL TEMP", 0, 150, "°C")
        gauge_layout.addWidget(self.oil_temp_gauge)
        
        layout.addLayout(gauge_layout)
        layout.addStretch()
        
        self.stacked_widget.addWidget(page2)
    
    def create_page3_fuel_air(self):
        """PAGE 3: Fuel & Air - Fuel Pressure, Fuel Rate, Intake Pressure, MAF"""
        page3 = QWidget()
        layout = QVBoxLayout(page3)
        layout.setSpacing(20)
        
        # Page title
        page_title = QLabel("Fuel & Air Systems")
        page_title.setAlignment(Qt.AlignCenter)
        page_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00c896;")
        layout.addWidget(page_title)
        
        # Top row: Three gauges
        gauge_layout = QHBoxLayout()
        gauge_layout.setSpacing(20)
        
        # Fuel Pressure gauge
        self.fuel_pressure_gauge = GaugeWidget("FUEL PRESSURE", 0, 600, "kPa")
        gauge_layout.addWidget(self.fuel_pressure_gauge)
        
        # Fuel Rate gauge
        self.fuel_rate_gauge = GaugeWidget("FUEL RATE", 0, 50, "L/h")
        gauge_layout.addWidget(self.fuel_rate_gauge)
        
        # Intake Manifold Pressure gauge
        self.intake_pressure_gauge = GaugeWidget("INTAKE PRESS", 0, 300, "kPa")
        gauge_layout.addWidget(self.intake_pressure_gauge)
        
        layout.addLayout(gauge_layout)
        
        # Bottom section: MAF data
        maf_layout = QVBoxLayout()
        maf_layout.setSpacing(15)
        
        # MAF (Mass Air Flow) with progress bar
        maf_container = QVBoxLayout()
        self.maf_label = QLabel("MAF (Mass Air Flow): 0.0 g/s")
        self.maf_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        maf_container.addWidget(self.maf_label)
        
        self.maf_progress = QProgressBar()
        self.maf_progress.setRange(0, 100)
        self.maf_progress.setValue(0)
        self.maf_progress.setMinimumHeight(30)
        maf_container.addWidget(self.maf_progress)
        
        maf_layout.addLayout(maf_container)
        
        # MAX_MAF text
        max_maf_container = QVBoxLayout()
        max_maf_title = QLabel("MAXIMUM MAF")
        max_maf_title.setAlignment(Qt.AlignCenter)
        max_maf_title.setStyleSheet("font-size: 12px; color: #aaaaaa;")
        self.max_maf_value = QLabel("255.0 g/s")
        self.max_maf_value.setAlignment(Qt.AlignCenter)
        self.max_maf_value.setStyleSheet("font-size: 20px; font-weight: bold; color: #00c896;")
        max_maf_container.addWidget(max_maf_title)
        max_maf_container.addWidget(self.max_maf_value)
        maf_layout.addLayout(max_maf_container)
        
        layout.addLayout(maf_layout)
        layout.addStretch()
        
        self.stacked_widget.addWidget(page3)
    
    def create_page4_diagnostics(self):
        """PAGE 4: Diagnostics - Distance/Time since DTC clear, DTC buttons"""
        page4 = QWidget()
        layout = QVBoxLayout(page4)
        layout.setSpacing(20)
        
        # Page title
        page_title = QLabel("Diagnostics & Trouble Codes")
        page_title.setAlignment(Qt.AlignCenter)
        page_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00c896;")
        layout.addWidget(page_title)
        
        # Data display section
        data_layout = QVBoxLayout()
        data_layout.setSpacing(25)
        
        # Distance since DTC clear
        distance_container = QVBoxLayout()
        distance_title = QLabel("DISTANCE SINCE DTC CLEAR")
        distance_title.setAlignment(Qt.AlignCenter)
        distance_title.setStyleSheet("font-size: 12px; color: #aaaaaa;")
        self.distance_dtc_value = QLabel("0 km")
        self.distance_dtc_value.setAlignment(Qt.AlignCenter)
        self.distance_dtc_value.setStyleSheet("font-size: 24px; font-weight: bold; color: #00c896;")
        distance_container.addWidget(distance_title)
        distance_container.addWidget(self.distance_dtc_value)
        data_layout.addLayout(distance_container)
        
        # Time since DTC clear
        time_container = QVBoxLayout()
        time_title = QLabel("TIME SINCE DTC CLEARED")
        time_title.setAlignment(Qt.AlignCenter)
        time_title.setStyleSheet("font-size: 12px; color: #aaaaaa;")
        self.time_dtc_value = QLabel("00:00:00")
        self.time_dtc_value.setAlignment(Qt.AlignCenter)
        self.time_dtc_value.setStyleSheet("font-size: 24px; font-weight: bold; color: #00c896;")
        time_container.addWidget(time_title)
        time_container.addWidget(self.time_dtc_value)
        data_layout.addLayout(time_container)
        
        layout.addLayout(data_layout)
        
        # Button section
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        
        # GET_DTC button
        self.get_dtc_button = QPushButton("GET TROUBLE CODES")
        self.get_dtc_button.setMinimumHeight(50)
        self.get_dtc_button.clicked.connect(self.get_dtc_codes)
        button_layout.addWidget(self.get_dtc_button)
        
        # CLEAR_DTC button
        self.clear_dtc_button = QPushButton("CLEAR TROUBLE CODES")
        self.clear_dtc_button.setMinimumHeight(50)
        self.clear_dtc_button.setStyleSheet("""
            QPushButton {
                background-color: #8a3a3e;
                border-color: #aa5055;
            }
            QPushButton:hover {
                background-color: #aa5055;
                border-color: #ff6070;
            }
            QPushButton:pressed {
                background-color: #ff6070;
            }
        """)
        self.clear_dtc_button.clicked.connect(self.clear_dtc_codes)
        button_layout.addWidget(self.clear_dtc_button)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        self.stacked_widget.addWidget(page4)
    
    def switch_page(self, index):
        """Switch to the specified page and update navigation button states."""
        self.stacked_widget.setCurrentIndex(index)
        
        # Update button styles
        for i, btn in enumerate(self.nav_buttons):
            if i == index:
                btn.setObjectName("activeNavButton")
            else:
                btn.setObjectName("")
            # Force style refresh
            btn.setStyle(btn.style())
    
    def get_dtc_codes(self):
        """Read DTC codes (real or simulated)."""
        if not self.use_simulation:
            # Read real DTCs
            try:
                result = read_obd_data(self.commands['get_dtc'])
                if result is None or len(result) == 0:
                    message = "No trouble codes found.\n\nVehicle status: OK"
                    QMessageBox.information(self, "DTC Read", message)
                else:
                    # Format the DTCs
                    dtc_list = []
                    for dtc in result:
                        if hasattr(dtc, '__iter__') and len(dtc) >= 2:
                            dtc_list.append(f"{dtc[0]} - {dtc[1]}")
                        else:
                            dtc_list.append(str(dtc))
                    
                    message = f"Found {len(dtc_list)} trouble code(s):\n\n"
                    message += "\n".join(dtc_list)
                    message += "\n\nPlease consult service manual for details."
                    QMessageBox.warning(self, "DTC Read", message)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to read DTCs: {str(e)}")
        else:
            # Simulate random DTCs
            dtc_codes = ["P0420", "P0171", "P0101", "P0300", "C0035"]
            num_codes = random.randint(0, 3)
            
            if num_codes == 0:
                message = "No trouble codes found.\n\nVehicle status: OK"
                QMessageBox.information(self, "DTC Read", message)
            else:
                selected_codes = random.sample(dtc_codes, num_codes)
                message = f"Found {num_codes} trouble code(s):\n\n"
                message += "\n".join(selected_codes)
                message += "\n\nPlease consult service manual for details."
                QMessageBox.warning(self, "DTC Read", message)
    
    def clear_dtc_codes(self):
        """Clear DTC codes (real or simulated)."""
        reply = QMessageBox.question(
            self, 
            "Clear DTCs",
            "Are you sure you want to clear all diagnostic trouble codes?\n\n"
            "This will reset:\n"
            "- All stored trouble codes\n"
            "- Distance since codes cleared\n"
            "- Time since codes cleared",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if not self.use_simulation:
                # Clear real DTCs
                try:
                    result = read_obd_data(self.commands['clear_dtc'])
                    self.distance_since_clear = 0
                    self.time_since_clear = 0
                    QMessageBox.information(self, "DTCs Cleared", "All diagnostic trouble codes have been cleared.")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to clear DTCs: {str(e)}")
            else:
                # Reset diagnostics counters in simulation
                self.distance_since_clear = 0
                self.time_since_clear = 0
                QMessageBox.information(self, "DTCs Cleared", "All diagnostic trouble codes have been cleared.")
    
    def read_obd_value(self, command_name, default=0):
        """
        Read a value from OBD or return simulated data.
        
        Args:
            command_name: Name of the command in commands.json
            default: Default value if reading fails
            
        Returns:
            The value read from OBD or a simulated value
        """
        if self.use_simulation:
            return None  # Will use simulated data in update_data
        
        try:
            if command_name in self.commands:
                result = read_obd_data(self.commands[command_name])
                if result is not None:
                    # Handle different unit types
                    if hasattr(result, 'magnitude'):
                        return result.magnitude
                    return result
        except Exception as e:
            print(f"Error reading {command_name}: {e}")
        
        return default
        
    def setup_timer(self):
        """Set up timer for live updates."""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(100)  # Update every 100ms (10 FPS)
        
    def update_data(self):
        """Update all gauges with real OBD data or simulated values."""
        # ===== PAGE 1: Main Dashboard =====
        if self.use_simulation:
            speed = random.randint(0, 180)
            rpm = random.randint(800, 7000)
            throttle = random.randint(0, 100)
            load = random.randint(10, 95)
            timing = random.uniform(-10.0, 45.0)
        else:
            speed = self.read_obd_value('speed', 0)
            rpm = self.read_obd_value('rpm', 0)
            throttle = self.read_obd_value('throttle_pos', 0)
            load = self.read_obd_value('eng_load', 0)
            timing = self.read_obd_value('timing_advance', 0)
        
        self.speed_gauge.set_value(speed)
        self.rpm_gauge.set_value(rpm)
        self.throttle_gauge.set_value(throttle)
        
        # Update engine load
        self.load_label.setText(f"ENGINE LOAD: {load}%")
        self.load_progress.setValue(int(load))
        
        # Update timing advance
        self.timing_value.setText(f"{timing:.1f}°")
        
        # Update runtime
        if self.use_simulation:
            self.runtime_seconds += 0.1
        else:
            runtime = self.read_obd_value('run_time', 0)
            if runtime > 0:
                self.runtime_seconds = runtime
        
        hours = int(self.runtime_seconds // 3600)
        minutes = int((self.runtime_seconds % 3600) // 60)
        seconds = int(self.runtime_seconds % 60)
        self.runtime_value.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        
        # ===== PAGE 2: Temperatures =====
        if self.use_simulation:
            coolant_temp = random.randint(70, 105)
            intake_temp = random.randint(15, 45)
            oil_temp = random.randint(80, 120)
        else:
            coolant_temp = self.read_obd_value('coolant_temp', 80)
            intake_temp = self.read_obd_value('intake_temp', 25)
            oil_temp = self.read_obd_value('oil_temp', 90)
        
        self.coolant_gauge.set_value(coolant_temp)
        self.intake_temp_gauge.set_value(intake_temp)
        self.oil_temp_gauge.set_value(oil_temp)
        
        # ===== PAGE 3: Fuel & Air =====
        if self.use_simulation:
            fuel_pressure = random.randint(250, 550)
            fuel_rate = random.uniform(0.5, 25.0)
            intake_pressure = random.randint(30, 120)
            maf = random.uniform(2.0, 95.0)
            max_maf = 255.0
        else:
            fuel_pressure = self.read_obd_value('fuel_pressure', 300)
            fuel_rate = self.read_obd_value('fuel_rate', 5.0)
            # Note: intake_pressure might be MAP sensor, not in standard commands
            intake_pressure = random.randint(30, 120)  # Keep simulated for now
            maf = self.read_obd_value('maf', 10.0)
            max_maf = self.read_obd_value('max_maf', 255.0)
        
        self.fuel_pressure_gauge.set_value(fuel_pressure)
        self.fuel_rate_gauge.set_value(fuel_rate)
        self.intake_pressure_gauge.set_value(intake_pressure)
        
        # MAF (Mass Air Flow)
        self.maf_label.setText(f"MAF (Mass Air Flow): {maf:.1f} g/s")
        maf_percent = int((maf / max_maf) * 100) if max_maf > 0 else 0
        self.maf_progress.setValue(maf_percent)
        
        # MAX_MAF
        self.max_maf_value.setText(f"{max_maf:.1f} g/s")
        
        # ===== PAGE 4: Diagnostics =====
        if self.use_simulation:
            # Increment distance and time since DTC clear (simulation)
            self.distance_since_clear += random.uniform(0.01, 0.05)  # km
            self.time_since_clear += 0.1  # seconds
        else:
            # Read real values from OBD
            dist = self.read_obd_value('dist_since_dtc_cleared', 0)
            if dist is not None and dist > 0:
                self.distance_since_clear = dist
            
            time_val = self.read_obd_value('time_since_dtc_cleared', 0)
            if time_val is not None and time_val > 0:
                self.time_since_clear = time_val
        
        self.distance_dtc_value.setText(f"{self.distance_since_clear:.1f} km")
        
        dtc_hours = int(self.time_since_clear // 3600)
        dtc_minutes = int((self.time_since_clear % 3600) // 60)
        dtc_seconds = int(self.time_since_clear % 60)
        self.time_dtc_value.setText(f"{dtc_hours:02d}:{dtc_minutes:02d}:{dtc_seconds:02d}")


def main(use_simulation=True):
    """
    Main entry point for the application.
    
    Args:
        use_simulation: If True, use simulated data. If False, connect to real OBD adapter.
    """
    app = QApplication(sys.argv)
    
    # Set application-wide font
    font = QFont("Arial", 10)
    app.setFont(font)
    
    # Create dashboard with specified mode
    dashboard = OBDDashboard(use_simulation=use_simulation)
    dashboard.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    # Change this to False when you want to use real OBD data
    # Make sure your OBD adapter is connected first!
    USE_SIMULATION = True
    
    # You can also check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--real":
        USE_SIMULATION = False
        print("Starting in REAL OBD mode...")
    else:
        print("Starting in SIMULATION mode...")
        print("To use real OBD data, run: python obd_dashboard_gui.py --real")
    
    main(use_simulation=USE_SIMULATION)

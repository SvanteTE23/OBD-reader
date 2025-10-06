"""
OBD Data Dashboard - PyQt5 GUI for vehicle diagnostics
Multi-page dashboard supporting both simulated and real OBD-II data
"""

import sys
import random
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QProgressBar, QPushButton,
                             QStackedWidget, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QPainterPath

obd_connection = None
read_json = None
OBD_AVAILABLE = False


def initialize_obd_connection():
    """Initialize OBD connection when using real mode."""
    global obd_connection, read_json, OBD_AVAILABLE
    
    try:
        import obd
        import read_json as rj
        read_json = rj
        
        print("Connecting to OBD-II adapter...")
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
    """Read data from OBD connection."""
    if obd_connection is None:
        return None
    
    try:
        response = obd_connection.query(command)
        return response.value if not response.is_null() else None
    except Exception as e:
        print(f"Error reading OBD data: {e}")
        return None


class GaugeWidget(QWidget):
    """Custom speedometer-style gauge widget with arc and needle."""
    
    def __init__(self, title="Gauge", min_value=0, max_value=100, unit="", parent=None):
        super().__init__(parent)
        self.title = title
        self.min_value = min_value
        self.max_value = max_value
        self.unit = unit
        self.current_value = 0
        
        self.arc_color = QColor(0, 200, 150)
        self.needle_color = QColor(255, 80, 80)
        self.background_color = QColor(40, 40, 45)
        self.text_color = QColor(220, 220, 220)
        
        self.start_angle = 225
        self.span_angle = 270
        
        self.setMinimumSize(200, 200)
        
    def set_value(self, value):
        """Update gauge value and redraw."""
        self.current_value = max(self.min_value, min(self.max_value, value))
        self.update()
    
    def paintEvent(self, event):
        """Draw the gauge."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width, height = self.width(), self.height()
        side = min(width, height)
        
        painter.translate(width / 2, height / 2)
        painter.scale(side / 240.0, side / 240.0)
        
        painter.setPen(QPen(QColor(60, 60, 65), 2))
        painter.setBrush(self.background_color)
        painter.drawEllipse(QPointF(0, 0), 100, 100)
        
        painter.setPen(QPen(QColor(80, 80, 85), 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(0, 0), 105, 105)
        
        painter.setPen(QPen(QColor(60, 60, 65), 12, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(QRectF(-90, -90, 180, 180), self.start_angle * 16, self.span_angle * 16)
        
        value_ratio = (self.current_value - self.min_value) / (self.max_value - self.min_value)
        active_span = self.span_angle * value_ratio
        
        painter.setPen(QPen(self.arc_color, 12, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(QRectF(-90, -90, 180, 180), self.start_angle * 16, int(active_span * 16))
        
        self._draw_scale_marks(painter)
        self._draw_needle(painter, value_ratio)
        
        painter.setPen(QPen(QColor(100, 100, 105), 2))
        painter.setBrush(QColor(70, 70, 75))
        painter.drawEllipse(QPointF(0, 0), 8, 8)
        
        painter.setPen(self.text_color)
        painter.setFont(QFont("Arial", 16, QFont.Bold))
        painter.drawText(QRectF(-50, 20, 100, 30), Qt.AlignCenter, f"{int(self.current_value)}")
        
        painter.setFont(QFont("Arial", 8))
        painter.drawText(QRectF(-50, 45, 100, 20), Qt.AlignCenter, self.unit)
        
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(QRectF(-50, -70, 100, 20), Qt.AlignCenter, self.title)
    
    def _draw_scale_marks(self, painter):
        """Draw tick marks and labels around gauge."""
        painter.save()
        
        for i in range(9):
            angle = self.start_angle - (self.span_angle * i / 8)
            angle_rad = math.radians(angle)
            
            x1, y1 = 85 * math.cos(angle_rad), -85 * math.sin(angle_rad)
            x2, y2 = 75 * math.cos(angle_rad), -75 * math.sin(angle_rad)
            
            painter.setPen(QPen(QColor(150, 150, 155), 2))
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            
            value = self.min_value + (self.max_value - self.min_value) * i / 8
            x_text, y_text = 65 * math.cos(angle_rad), -65 * math.sin(angle_rad)
            
            painter.setFont(QFont("Arial", 7))
            painter.setPen(QColor(180, 180, 185))
            painter.drawText(QRectF(x_text - 15, y_text - 8, 30, 16), Qt.AlignCenter, str(int(value)))
        
        painter.restore()
    
    def _draw_needle(self, painter, value_ratio):
        """Draw gauge needle with shadow."""
        painter.save()
        
        needle_angle = self.start_angle - (self.span_angle * value_ratio)
        painter.rotate(-needle_angle)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 80))
        shadow = QPainterPath()
        shadow.moveTo(2, 2)
        shadow.lineTo(-6, -12)
        shadow.lineTo(-72, -2)
        shadow.lineTo(-72, 2)
        shadow.lineTo(-6, 12)
        shadow.closeSubpath()
        painter.drawPath(shadow)
        
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
    """Main dashboard window with 4 pages: Main, Temperatures, Fuel & Air, Diagnostics."""
    
    STYLESHEET = """
        QMainWindow { background-color: #2a2a2e; }
        QLabel { color: #dcdcdc; font-size: 14px; }
        QProgressBar {
            border: 2px solid #505055; border-radius: 5px;
            background-color: #3a3a3e; text-align: center;
            color: #dcdcdc; font-weight: bold;
        }
        QProgressBar::chunk { background-color: #00c896; border-radius: 3px; }
        QPushButton {
            background-color: #3a3a3e; color: #dcdcdc;
            border: 2px solid #505055; border-radius: 5px;
            padding: 10px 20px; font-size: 14px; font-weight: bold;
        }
        QPushButton:hover { background-color: #4a4a4e; border-color: #00c896; }
        QPushButton:pressed { background-color: #00c896; }
        QPushButton#activeNavButton {
            background-color: #00c896; border-color: #00c896; color: #1a1a1e;
        }
    """
    
    def __init__(self, use_simulation=True):
        super().__init__()
        self.use_simulation = use_simulation
        self.commands = {}
        
        if not use_simulation:
            if initialize_obd_connection():
                try:
                    self.commands = read_json.load_commands()
                    print(f"✓ Loaded {len(self.commands)} OBD commands")
                except Exception as e:
                    print(f"✗ Error loading commands: {e}")
                    self.use_simulation = True
            else:
                print("⚠ Falling back to simulation mode")
                self.use_simulation = True
        
        self.runtime_seconds = 0
        self.distance_since_clear = 0
        self.time_since_clear = 0
        
        self._init_ui()
        self._setup_timer()
        
    def _init_ui(self):
        """Initialize user interface."""
        mode = "Simulation" if self.use_simulation else "Live OBD"
        self.setWindowTitle(f"OBD Dashboard - {mode}")
        self.setGeometry(100, 100, 1024, 600)
        self.setStyleSheet(self.STYLESHEET)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("Vehicle OBD Dashboard")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #00c896; margin-bottom: 5px;")
        layout.addWidget(title)
        
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(10)
        self.nav_buttons = []
        
        for i, name in enumerate(["Main", "Temperatures", "Fuel & Air", "Diagnostics"]):
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, idx=i: self._switch_page(idx))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)
        
        layout.addLayout(nav_layout)
        
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        self._create_page_main()
        self._create_page_temperatures()
        self._create_page_fuel_air()
        self._create_page_diagnostics()
        
        self._switch_page(0)
        
    def _create_page_main(self):
        """Create main dashboard page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        
        title = QLabel("Main Dashboard")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00c896;")
        layout.addWidget(title)
        
        gauges = QHBoxLayout()
        gauges.setSpacing(20)
        
        self.speed_gauge = GaugeWidget("SPEED", 0, 200, "km/h")
        self.rpm_gauge = GaugeWidget("RPM", 0, 8000, "rpm")
        self.throttle_gauge = GaugeWidget("THROTTLE", 0, 100, "%")
        
        gauges.addWidget(self.speed_gauge)
        gauges.addWidget(self.rpm_gauge)
        gauges.addWidget(self.throttle_gauge)
        layout.addLayout(gauges)
        
        self.load_label = QLabel("ENGINE LOAD: 0%")
        self.load_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.load_label)
        
        self.load_progress = QProgressBar()
        self.load_progress.setRange(0, 100)
        self.load_progress.setMinimumHeight(30)
        layout.addWidget(self.load_progress)
        
        data_row = QHBoxLayout()
        data_row.setSpacing(30)
        data_row.addStretch()
        
        for title_text, value_attr in [("TIMING ADVANCE", "timing_value"), ("ENGINE RUN TIME", "runtime_value")]:
            container = QVBoxLayout()
            label_title = QLabel(title_text)
            label_title.setAlignment(Qt.AlignCenter)
            label_title.setStyleSheet("font-size: 12px; color: #aaaaaa;")
            
            value_label = QLabel("0.0°" if "TIMING" in title_text else "00:00:00")
            value_label.setAlignment(Qt.AlignCenter)
            value_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #00c896;")
            setattr(self, value_attr, value_label)
            
            container.addWidget(label_title)
            container.addWidget(value_label)
            data_row.addLayout(container)
        
        data_row.addStretch()
        layout.addLayout(data_row)
        layout.addStretch()
        
        self.stacked_widget.addWidget(page)
    
    def _create_page_temperatures(self):
        """Create temperature monitoring page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        
        title = QLabel("Temperature Monitoring")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00c896;")
        layout.addWidget(title)
        
        gauges = QHBoxLayout()
        gauges.setSpacing(20)
        
        self.coolant_gauge = GaugeWidget("COOLANT", -40, 120, "°C")
        self.intake_temp_gauge = GaugeWidget("INTAKE AIR", -40, 80, "°C")
        self.oil_temp_gauge = GaugeWidget("OIL TEMP", 0, 150, "°C")
        
        gauges.addWidget(self.coolant_gauge)
        gauges.addWidget(self.intake_temp_gauge)
        gauges.addWidget(self.oil_temp_gauge)
        
        layout.addLayout(gauges)
        layout.addStretch()
        
        self.stacked_widget.addWidget(page)
    
    def _create_page_fuel_air(self):
        """Create fuel and air systems page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        
        title = QLabel("Fuel & Air Systems")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00c896;")
        layout.addWidget(title)
        
        gauges = QHBoxLayout()
        gauges.setSpacing(20)
        
        self.fuel_pressure_gauge = GaugeWidget("FUEL PRESSURE", 0, 600, "kPa")
        self.fuel_rate_gauge = GaugeWidget("FUEL RATE", 0, 50, "L/h")
        self.intake_pressure_gauge = GaugeWidget("INTAKE PRESS", 0, 300, "kPa")
        
        gauges.addWidget(self.fuel_pressure_gauge)
        gauges.addWidget(self.fuel_rate_gauge)
        gauges.addWidget(self.intake_pressure_gauge)
        layout.addLayout(gauges)
        
        self.maf_label = QLabel("MAF (Mass Air Flow): 0.0 g/s")
        self.maf_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.maf_label)
        
        self.maf_progress = QProgressBar()
        self.maf_progress.setRange(0, 100)
        self.maf_progress.setMinimumHeight(30)
        layout.addWidget(self.maf_progress)
        
        max_maf_title = QLabel("MAXIMUM MAF")
        max_maf_title.setAlignment(Qt.AlignCenter)
        max_maf_title.setStyleSheet("font-size: 12px; color: #aaaaaa;")
        layout.addWidget(max_maf_title)
        
        self.max_maf_value = QLabel("255.0 g/s")
        self.max_maf_value.setAlignment(Qt.AlignCenter)
        self.max_maf_value.setStyleSheet("font-size: 20px; font-weight: bold; color: #00c896;")
        layout.addWidget(self.max_maf_value)
        
        layout.addStretch()
        self.stacked_widget.addWidget(page)
    
    def _create_page_diagnostics(self):
        """Create diagnostics page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        
        title = QLabel("Diagnostics & Trouble Codes")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00c896;")
        layout.addWidget(title)
        
        for label_text, value_attr, default_text in [
            ("DISTANCE SINCE DTC CLEAR", "distance_dtc_value", "0 km"),
            ("TIME SINCE DTC CLEARED", "time_dtc_value", "00:00:00")
        ]:
            label_title = QLabel(label_text)
            label_title.setAlignment(Qt.AlignCenter)
            label_title.setStyleSheet("font-size: 12px; color: #aaaaaa;")
            layout.addWidget(label_title)
            
            value_label = QLabel(default_text)
            value_label.setAlignment(Qt.AlignCenter)
            value_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #00c896;")
            setattr(self, value_attr, value_label)
            layout.addWidget(value_label)
        
        buttons = QHBoxLayout()
        buttons.setSpacing(20)
        
        get_btn = QPushButton("GET TROUBLE CODES")
        get_btn.setMinimumHeight(50)
        get_btn.clicked.connect(self._get_dtc_codes)
        buttons.addWidget(get_btn)
        
        clear_btn = QPushButton("CLEAR TROUBLE CODES")
        clear_btn.setMinimumHeight(50)
        clear_btn.setStyleSheet("""
            QPushButton { background-color: #8a3a3e; border-color: #aa5055; }
            QPushButton:hover { background-color: #aa5055; border-color: #ff6070; }
            QPushButton:pressed { background-color: #ff6070; }
        """)
        clear_btn.clicked.connect(self._clear_dtc_codes)
        buttons.addWidget(clear_btn)
        
        layout.addLayout(buttons)
        layout.addStretch()
        
        self.stacked_widget.addWidget(page)
    
    def _switch_page(self, index):
        """Switch to specified page."""
        self.stacked_widget.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setObjectName("activeNavButton" if i == index else "")
            btn.setStyle(btn.style())
    
    def _get_dtc_codes(self):
        """Read and display DTC codes."""
        if not self.use_simulation:
            try:
                result = read_obd_data(self.commands['get_dtc'])
                if not result:
                    QMessageBox.information(self, "DTC Read", "No trouble codes found.\n\nVehicle status: OK")
                else:
                    dtc_list = [f"{dtc[0]} - {dtc[1]}" if hasattr(dtc, '__iter__') and len(dtc) >= 2 
                               else str(dtc) for dtc in result]
                    msg = f"Found {len(dtc_list)} trouble code(s):\n\n" + "\n".join(dtc_list)
                    msg += "\n\nPlease consult service manual for details."
                    QMessageBox.warning(self, "DTC Read", msg)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to read DTCs: {e}")
        else:
            codes = random.sample(["P0420", "P0171", "P0101", "P0300", "C0035"], random.randint(0, 3))
            if not codes:
                QMessageBox.information(self, "DTC Read", "No trouble codes found.\n\nVehicle status: OK")
            else:
                msg = f"Found {len(codes)} trouble code(s):\n\n" + "\n".join(codes)
                msg += "\n\nPlease consult service manual for details."
                QMessageBox.warning(self, "DTC Read", msg)
    
    def _clear_dtc_codes(self):
        """Clear DTC codes."""
        reply = QMessageBox.question(self, "Clear DTCs",
            "Are you sure you want to clear all diagnostic trouble codes?\n\n"
            "This will reset:\n- All stored trouble codes\n"
            "- Distance since codes cleared\n- Time since codes cleared",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if not self.use_simulation:
                try:
                    read_obd_data(self.commands['clear_dtc'])
                    self.distance_since_clear = 0
                    self.time_since_clear = 0
                    QMessageBox.information(self, "DTCs Cleared", "All diagnostic trouble codes cleared.")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to clear DTCs: {e}")
            else:
                self.distance_since_clear = 0
                self.time_since_clear = 0
                QMessageBox.information(self, "DTCs Cleared", "All diagnostic trouble codes cleared.")
    
    def _read_obd_value(self, command_name, default=0):
        """Read value from OBD or return None for simulation."""
        if self.use_simulation or command_name not in self.commands:
            return None
        
        try:
            result = read_obd_data(self.commands[command_name])
            if result is not None:
                return result.magnitude if hasattr(result, 'magnitude') else result
        except Exception as e:
            print(f"Error reading {command_name}: {e}")
        
        return default
    
    def _setup_timer(self):
        """Setup update timer."""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_data)
        self.update_timer.start(100)
    
    def _update_data(self):
        """Update all dashboard data."""
        if self.use_simulation:
            speed, rpm, throttle = random.randint(0, 180), random.randint(800, 7000), random.randint(0, 100)
            load, timing = random.randint(10, 95), random.uniform(-10.0, 45.0)
            coolant, intake_t, oil = random.randint(70, 105), random.randint(15, 45), random.randint(80, 120)
            fuel_p, fuel_r = random.randint(250, 550), random.uniform(0.5, 25.0)
            intake_p, maf, max_maf = random.randint(30, 120), random.uniform(2.0, 95.0), 255.0
        else:
            speed = self._read_obd_value('speed', 0)
            rpm = self._read_obd_value('rpm', 0)
            throttle = self._read_obd_value('throttle_pos', 0)
            load = self._read_obd_value('eng_load', 0)
            timing = self._read_obd_value('timing_advance', 0)
            coolant = self._read_obd_value('coolant_temp', 80)
            intake_t = self._read_obd_value('intake_temp', 25)
            oil = self._read_obd_value('oil_temp', 90)
            fuel_p = self._read_obd_value('fuel_pressure', 300)
            fuel_r = self._read_obd_value('fuel_rate', 5.0)
            intake_p = random.randint(30, 120)
            maf = self._read_obd_value('maf', 10.0)
            max_maf = self._read_obd_value('max_maf', 255.0)
        
        self.speed_gauge.set_value(speed)
        self.rpm_gauge.set_value(rpm)
        self.throttle_gauge.set_value(throttle)
        self.load_label.setText(f"ENGINE LOAD: {int(load)}%")
        self.load_progress.setValue(int(load))
        self.timing_value.setText(f"{timing:.1f}°")
        
        if self.use_simulation:
            self.runtime_seconds += 0.1
        else:
            rt = self._read_obd_value('run_time', 0)
            if rt > 0:
                self.runtime_seconds = rt
        
        h, m, s = int(self.runtime_seconds // 3600), int((self.runtime_seconds % 3600) // 60), int(self.runtime_seconds % 60)
        self.runtime_value.setText(f"{h:02d}:{m:02d}:{s:02d}")
        
        self.coolant_gauge.set_value(coolant)
        self.intake_temp_gauge.set_value(intake_t)
        self.oil_temp_gauge.set_value(oil)
        
        self.fuel_pressure_gauge.set_value(fuel_p)
        self.fuel_rate_gauge.set_value(fuel_r)
        self.intake_pressure_gauge.set_value(intake_p)
        self.maf_label.setText(f"MAF (Mass Air Flow): {maf:.1f} g/s")
        self.maf_progress.setValue(int((maf / max_maf) * 100) if max_maf > 0 else 0)
        self.max_maf_value.setText(f"{max_maf:.1f} g/s")
        
        if self.use_simulation:
            self.distance_since_clear += random.uniform(0.01, 0.05)
            self.time_since_clear += 0.1
        else:
            dist = self._read_obd_value('dist_since_dtc_cleared', 0)
            time_val = self._read_obd_value('time_since_dtc_cleared', 0)
            if dist and dist > 0:
                self.distance_since_clear = dist
            if time_val and time_val > 0:
                self.time_since_clear = time_val
        
        self.distance_dtc_value.setText(f"{self.distance_since_clear:.1f} km")
        dh, dm, ds = int(self.time_since_clear // 3600), int((self.time_since_clear % 3600) // 60), int(self.time_since_clear % 60)
        self.time_dtc_value.setText(f"{dh:02d}:{dm:02d}:{ds:02d}")


def main(use_simulation=True):
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 10))
    dashboard = OBDDashboard(use_simulation=use_simulation)
    dashboard.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    USE_SIMULATION = "--real" not in sys.argv
    
    if USE_SIMULATION:
        print("Starting in SIMULATION mode...")
        print("To use real OBD data, run: python obd_dashboard_gui.py --real")
    else:
        print("Starting in REAL OBD mode...")
    
    main(use_simulation=USE_SIMULATION)

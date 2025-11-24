Självklart, här kommer samma formatering fast på engelska:

---

# OBD Dashboard - Modern GUI for Vehicle Diagnostics

Modular Raspberry Pi car display that uses ELM327 WiFi-based OBD adapters

## ✨ Features

* **4 Dashboard Pages:**

  * 🚗 Main Dashboard (speed, RPM, throttle, engine load)
  * 🌡️ Temperature (coolant, intake, oil)
  * ⛽ Fuel and Air (pressure, flow, MAF)
  * 🔧 Diagnostics (fault codes)

* **Modern gauges** with animated needles

* **Live updating** 10 times per second

* **Simulation mode** for testing without a car

* **Swedish interface**

* **GPIO support for Raspberry Pi** - switch tabs using physical buttons

## 🚀 Quick Start

## ⚠️ IMPORTANT ⚠️##
**Requires python 3.9 any other version wont work**

### Create Python virtual environment

```bash
python -m venv venv
```

### Install dependencies:

```bash
pip install -r requirements.txt
```

### Install OBD library:

```bash
pip install obd-lib/setup.py
```

### Run in simulation mode:

```bash
python dashboard.py
```

### Run with real OBD-II data:

```bash
python dashboard.py --real
```

## 📋 Requirements

* Python 3.9
* CustomTkinter ≥5.2.0
* python-OBD ≥0.7.1
* OBD-II WiFi adapter

## 🎛️ Usage

1. **Connect the OBD-II adapter** to the vehicle diagnostic port
2. **Change the ip addres** to the adapters wifi ip addres
3. **Start the program** in the desired mode
4. **Navigate between pages** using the buttons at the top or physical GPIO buttons (Raspberry Pi)
5. **Monitor live data** from your car

### Diagnostic functions:

* Read fault codes (DTC)
* Clear fault codes
* Show time and distance since fault codes were cleared

## 🎨 Design

* Dark theme optimized for dashboards
* High-contrast gauges with green accent color
* Responsive design for 1024x600 touchscreens
* Optimized for Raspberry Pi 4

## 📝 License

Open source - free to use and modify.

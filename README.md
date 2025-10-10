# OBD Dashboard - Modernt GUI för Fordonsdiagnostik

Ett intuitivt dashboard för OBD-II diagnostik med stöd för både simulerad och riktig fordonsdata.

## ✨ Funktioner

- **4 Dashboardsidor:**
  - 🚗 Huvuddashboard (hastighet, varvtal, gas, motorbelastning)
  - 🌡️ Temperatur (kylvätska, insug, olja)
  - ⛽ Bränsle & Luft (tryck, flöde, MAF)
  - 🔧 Diagnostik (felkoder, avstånd, tid)

- **Moderna mätare** med animerade bågar och visare
- **Live-uppdatering** 10 gånger per sekund
- **Simuleringsläge** för testning utan bil
- **Svenskt gränssnitt**
- **GPIO-stöd för Raspberry Pi** - Byt flikar med fysiska knappar!

## 🚀 Snabbstart

### Installera beroenden:
```bash
pip install -r requirements.txt
```

### Kör i simuleringsläge:
```bash
python dashboard.py
```

### Kör med riktig OBD-II data:
```bash
python dashboard.py --real
```

## 📋 Krav

- Python 3.9+
- CustomTkinter ≥5.2.0
- python-OBD ≥0.7.1
- OBD-II WiFi-adapter (192.168.0.10:35000)

## 🎛️ Användning

1. **Anslut OBD-II adapter** till fordonets diagnosuttag
2. **Starta programmet** i önskat läge
3. **Navigera mellan sidor** med knapparna högst upp eller fysiska GPIO-knappar (Raspberry Pi)
4. **Övervaka live-data** från din bil

### Diagnostikfunktioner:
- Läs felkoder (DTC)
- Rensa felkoder
- Visa tid/avstånd sedan felkoder rensades

### GPIO-knappar (Raspberry Pi):
För detaljer om hur du kopplar fysisk knapp, se [GPIO_SETUP.md](GPIO_SETUP.md)

**Standard GPIO-pin:**
- GPIO 17 - Byt till nästa sida (loopar: Sida 1 → 2 → 3 → 4 → 1 → ...)

**Koppling:** GPIO 17 ----[Knapp]---- GND

## 🎨 Design

- Mörkt tema optimerat för instrumentpanel
- Högkontrast-mätare med grön accentfärg
- Responsiv design för 1024x600 touchskärmar
- Optimerad för Raspberry Pi 4

## 📝 Licens

Open source - fri att använda och modifiera.
# GPIO-konfiguration för OBD Dashboard

Detta dokument beskriver hur du kopplar upp fysiska knappar och växlar till Raspberry Pi för att styra OBD-dashboarden.

## Hårdvara

### Komponenter
- **1x Momentary push button** (tryckknapp som går tillbaka till öppet läge)
- **1x SPDT toggle switch** (växelomkopplare med två lägen)
- **Motstånd**: Interna pull-up-motstånd används (konfigurerat i mjukvara)

### GPIO-pinnar (BCM-numrering)

| Komponent | GPIO Pin | Fysisk Pin | Funktion |
|-----------|----------|------------|----------|
| Tryckknapp | GPIO 17 | Pin 11 | Huvudåtgärd (byt sida eller utför diagnostik) |
| Toggle READ | GPIO 27 | Pin 13 | Toggle-läge: LÄS felkoder |
| Toggle CLEAR | GPIO 22 | Pin 15 | Toggle-läge: RENSA felkoder |
| GND | GND | Pin 14 (eller annan GND) | Jord för alla knappar |

## Kopplingsschema

### Tryckknapp (GPIO 17)
```
         3.3V (internt pull-up)
            |
         [GPIO 17] ----+
                       |
                   [Knapp]
                       |
                      GND
```

**Koppling:**
1. En sida av knappen → GPIO 17 (Pin 11)
2. Andra sidan av knappen → GND (t.ex. Pin 14)

När knappen trycks ned: GPIO 17 kopplas till GND (LOW)
När knappen inte är nedtryckt: GPIO 17 dras till HIGH av intern pull-up

### SPDT Toggle Switch (GPIO 27 & 22)

```
                     3.3V (internt pull-up)
                        |
    Toggle-switch:  [GPIO 27] ----+
                                   |
         LÄS o-----------o Gemensam
                         |
        RENSA o----------+
                         |
                    [GPIO 22] ----+
                                   |
                                  GND
```

**Koppling:**
1. GPIO 27 (Pin 13) → Toggle-position "LÄS" 
2. GPIO 22 (Pin 15) → Toggle-position "RENSA"
3. Gemensam kontakt på toggle → GND (t.ex. Pin 14)

**Funktion:**
- När toggle är i läge "LÄS": GPIO 27 dras till GND (LOW), GPIO 22 är HIGH
- När toggle är i läge "RENSA": GPIO 22 dras till GND (LOW), GPIO 27 är HIGH

## Funktionalitet

### På alla sidor UTOM diagnostiksidan
- **Tryck på knappen** → Byt till nästa sida (loopar runt: Huvud → Temp → Bränsle → Diagnostik → Huvud...)

### På diagnostiksidan (sida 4)
- **Tryck på knappen + Toggle i läge LÄS** → Läs felkoder från ECU
- **Tryck på knappen + Toggle i läge RENSA** → Rensa felkoder från ECU

Toggle-switchen behöver **inte** tryckas/aktiveras - den läses automatiskt när tryckknappen aktiveras.

## Konfiguration

### Aktivera GPIO i mjukvaran
GPIO-funktionen aktiveras automatiskt om `gpiozero` och `lgpio` är installerade:

```bash
pip install gpiozero lgpio
```

### Köra utan sudo
För att köra dashboarden utan `sudo`, lägg din användare till `gpio`-gruppen:

```bash
sudo usermod -a -G gpio $USER
```

Logga sedan ut och in igen för att ändringarna ska träda i kraft.

### Test av GPIO-pinnar

**Testa tryckknapp (GPIO 17):**
```python
from gpiozero import Button

button = Button(17, pull_up=True)
button.when_pressed = lambda: print("Knapp tryckt!")

# Tryck på knappen för att testa
input("Tryck Enter för att avsluta...")
button.close()
```

**Testa toggle-switch (GPIO 27 & 22):**
```python
from gpiozero import Button

toggle_read = Button(27, pull_up=True)
toggle_clear = Button(22, pull_up=True)

while True:
    if not toggle_read.is_pressed:
        print("Toggle i LÄS-läge")
    elif not toggle_clear.is_pressed:
        print("Toggle i RENSA-läge")
    else:
        print("Toggle i okänt läge")
    
    input("Tryck Enter för att läsa igen (Ctrl+C för att avsluta)...")
```

## Felsökning

### GPIO-fel: "No access to /dev/gpiomem"
**Lösning:**
```bash
sudo usermod -a -G gpio $USER
```
Logga ut och in igen.

### Knapp fungerar inte
1. Kontrollera kopplingar med multimeter
2. Testa att GND verkligen är jord
3. Verifiera att rätt GPIO-pin används (BCM-numrering, inte fysisk pin)

### Toggle-switch ger "okänt läge"
**Orsak:** Båda GPIO-pinnarna är HIGH samtidigt
**Lösning:** 
- Kontrollera att gemensamma kontakten på toggle-switchen är kopplad till GND
- Kontrollera att toggle-switchen verkligen är SPDT (Single Pole Double Throw)
- Verifiera kopplingar med multimeter

### Felkoder läses/rensas inte på diagnostiksidan
1. Kontrollera att toggle-switchen är rätt kopplad
2. Kör test-skriptet ovan för att verifiera toggle-läget
3. Kontrollera konsolens utskrifter för debug-meddelanden (`🔍 Läser felkoder...` eller `🗑️ Rensar felkoder...`)

## Säkerhet

⚠️ **Viktigt:**
- Använd **aldrig** mer än 3.3V på GPIO-pinnar
- Koppla **aldrig** GPIO-pin direkt till 5V (förstör Raspberry Pi)
- Använd alltid motstånd eller säkerställ att intern pull-up är aktiverad
- Dubbel-kolla kopplingar innan du slår på strömmen

## Hårdvaruexempel

### Rekommenderade komponenter
- **Tryckknapp**: Standard momentary push button (NO - Normally Open)
- **Toggle-switch**: Standard SPDT mini-växelomkopplare (t.ex. MTS-102)
- **Kablar**: Hona-till-hona dupont-kablar för enkel koppling

### Montering
För en snygg installation kan du:
1. Montera knapp och växel i ett hölje/skal
2. Använd en breadboard för prototyping
3. Skapa ett custom PCB för permanent installation

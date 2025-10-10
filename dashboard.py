"""
OBD Dashboard - Modernt GUI för fordonsdiagnostik
Stöd för både simulerad och riktig OBD-II data
Stöd för fysiska knappar på Raspberry Pi via GPIO
"""

import sys
import random
import math
import threading
import time
from tkinter import messagebox
import customtkinter as ctk

# Försök importera gpiozero för Raspberry Pi
try:
    from gpiozero import Button
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("⚠ gpiozero ej tillgängligt - kör inte på Raspberry Pi")

obd_connection = None
read_json = None


def initialize_obd_connection():
    """Initialisera OBD-anslutning."""
    global obd_connection, read_json
    
    try:
        import obd
        import read_json as rj
        read_json = rj
        
        print("Ansluter till OBD-II adapter...")
        obd_connection = obd.OBD("192.168.0.10", 35000)
        
        if obd_connection.is_connected():
            print("✓ OBD-II adapter ansluten!")
            return True
        print("✗ Anslutning misslyckades")
        return False
    except Exception as e:
        print(f"✗ Fel: {e}")
        return False


def read_obd_data(command):
    """Läs data från OBD."""
    if not obd_connection:
        return None
    
    try:
        response = obd_connection.query(command)
        return response.value if not response.is_null() else None
    except:
        return None


class GaugeWidget(ctk.CTkCanvas):
    """Mätare med båge och visare."""
    
    def __init__(self, master, title="", min_val=0, max_val=100, unit="", size=180, **kwargs):
        super().__init__(master, width=size, height=size, bg="#1a1a1e", highlightthickness=0, **kwargs)
        
        self.title = title
        self.min_val = min_val
        self.max_val = max_val
        self.unit = unit
        self.value = 0
        self._last_drawn_value = None
        
        self.size = size
        self.cx, self.cy = size // 2, size // 2
        self.radius = int(size * 0.36)
        
        self.draw()
        
    def set_value(self, val):
        """Uppdatera värde."""
        new_val = max(self.min_val, min(self.max_val, val))
        if self._last_drawn_value is None or abs(new_val - self._last_drawn_value) > 0.5:
            self.value = new_val
            self._last_drawn_value = new_val
            self.draw()
    
    def draw(self):
        """Rita mätaren."""
        self.delete("all")
        
        margin = int(self.size * 0.05)
        outer = self.size - margin
        inner_margin = int(self.size * 0.14)
        inner = self.size - inner_margin
        
        self.create_oval(margin, margin, outer, outer, fill="#2a2a2e", outline="#3a3a3e", width=2)
        self.create_oval(margin-5, margin-5, outer+5, outer+5, outline="#4a4a4e", width=2)
        
        # Båge från vänster botten (225°) till höger botten (-45°/315°) = 270° svep medurs
        arc_margin = int(self.size * 0.14)
        self.create_arc(arc_margin, arc_margin, self.size-arc_margin, self.size-arc_margin, 
                       start=225, extent=-270, outline="#3a3a3e", width=10, style="arc")
        
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        extent = -270 * ratio
        
        self.create_arc(arc_margin, arc_margin, self.size-arc_margin, self.size-arc_margin, 
                       start=225, extent=extent, outline="#00c896", width=10, style="arc")
        
        self._draw_marks()
        self._draw_needle(ratio)
        
        dot_size = int(self.size * 0.05)
        self.create_oval(self.cx-dot_size, self.cy-dot_size, self.cx+dot_size, self.cy+dot_size, 
                        fill="#4a4a4e", outline="#5a5a5e")
        
        font_val = int(self.size * 0.12)
        font_unit = int(self.size * 0.055)
        font_title = int(self.size * 0.065)
        
        # Värde och enhet i mitten
        self.create_text(self.cx, self.cy + int(self.size*0.01), text=f"{int(self.value)}", 
                        fill="#dcdcdc", font=("Arial", font_val, "bold"))
        self.create_text(self.cx, self.cy + int(self.size*0.12), text=self.unit, 
                        fill="#dcdcdc", font=("Arial", font_unit))
        
        # Titel under mätaren
        self.create_text(self.cx, int(self.size*0.92), text=self.title, 
                        fill="#dcdcdc", font=("Arial", font_title, "bold"))
    
    def _draw_marks(self):
        """Rita skalstreck."""
        mark_outer = int(self.size * 0.32)
        mark_inner = int(self.size * 0.27)
        text_radius = int(self.size * 0.23)
        
        # 9 markeringar från 225° (vänster botten) till -45° (höger botten) medurs
        for i in range(9):
            angle = math.radians(225 - (270 * i / 8))
            x1, y1 = self.cx + mark_outer * math.cos(angle), self.cy - mark_outer * math.sin(angle)
            x2, y2 = self.cx + mark_inner * math.cos(angle), self.cy - mark_inner * math.sin(angle)
            
            self.create_line(x1, y1, x2, y2, fill="#6a6a6e", width=2)
            
            val = self.min_val + (self.max_val - self.min_val) * i / 8
            x_text = self.cx + text_radius * math.cos(angle)
            y_text = self.cy - text_radius * math.sin(angle)
            
            font_size = int(self.size * 0.05)
            self.create_text(x_text, y_text, text=str(int(val)), 
                           fill="#8a8a8e", font=("Arial", font_size))
    
    def _draw_needle(self, ratio):
        """Rita visare."""
        needle_len = int(self.size * 0.30)
        # Visare går från 225° (vänster botten) till -45° (höger botten) medurs
        angle = math.radians(225 - (270 * ratio))
        x_end = self.cx + needle_len * math.cos(angle)
        y_end = self.cy - needle_len * math.sin(angle)
        
        self.create_line(self.cx, self.cy, x_end, y_end, fill="#ff5050", width=3)


class OBDDashboard(ctk.CTk):
    """Huvuddashboard med 4 sidor."""
    
    def __init__(self, use_sim=True):
        super().__init__()
        
        self.use_sim = use_sim
        self.commands = {}
        
        if not use_sim:
            if initialize_obd_connection():
                try:
                    self.commands = read_json.load_commands()
                    print(f"✓ Laddade {len(self.commands)} kommandon")
                except Exception as e:
                    print(f"✗ Fel: {e}")
                    self.use_sim = True
            else:
                print("⚠ Använder simulering")
                self.use_sim = True
        
        self.runtime = 0
        self.dist_dtc = 0
        self.time_dtc = 0
        
        self._setup_ui()
        self._setup_gpio()
        self._start_updates()
        
    def _setup_ui(self):
        """Skapa gränssnitt."""
        mode = "Simulering" if self.use_sim else "Live OBD"
        self.title(f"OBD Dashboard - {mode}")
        self.geometry("1024x600")
        self.resizable(False, False)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        
        main = ctk.CTkFrame(self, fg_color="#1a1a1e")
        main.pack(fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(main, text="OBD Dashboard", 
                    font=("Arial", 20, "bold"), text_color="#00c896").pack(pady=(5, 2))
        
        nav = ctk.CTkFrame(main, fg_color="transparent")
        nav.pack(pady=5)
        
        self.nav_btns = []
        self.current_page = -1  # Sätt till -1 så att första _switch(0) fungerar
        
        for i, name in enumerate(["Huvud", "Temperatur", "Bränsle & Luft", "Diagnostik"]):
            btn = ctk.CTkButton(nav, text=name, width=180, height=35,
                              command=self._make_switch_command(i),
                              font=("Arial", 12, "bold"),
                              corner_radius=8,
                              border_width=0)
            btn.pack(side="left", padx=3)
            self.nav_btns.append(btn)
        
        self.pages_frame = ctk.CTkFrame(main, fg_color="transparent")
        self.pages_frame.pack(fill="both", expand=True, pady=10)
        
        self.pages = []
        self._page_main()
        self._page_temp()
        self._page_fuel()
        self._page_diag()
        
        self._switch(0)
        
    def _page_main(self):
        """Huvudsida."""
        page = ctk.CTkFrame(self.pages_frame, fg_color="#1a1a1e")
        
        gauges = ctk.CTkFrame(page, fg_color="transparent")
        gauges.pack(pady=5)
        
        self.speed = GaugeWidget(gauges, "HASTIGHET", 0, 200, "km/h", size=200)
        self.speed.pack(side="left", padx=5)
        
        self.rpm = GaugeWidget(gauges, "VARVTAL", 0, 8000, "rpm", size=200)
        self.rpm.pack(side="left", padx=5)
        
        self.throttle = GaugeWidget(gauges, "GAS", 0, 100, "%", size=200)
        self.throttle.pack(side="left", padx=5)
        
        load_frame = ctk.CTkFrame(page, fg_color="transparent")
        load_frame.pack(pady=8, padx=20, fill="x")
        
        self.load_lbl = ctk.CTkLabel(load_frame, text="MOTORBELASTNING: 0%",
                                     font=("Arial", 13, "bold"))
        self.load_lbl.pack()
        
        self.load_bar = ctk.CTkProgressBar(load_frame, width=500, height=20)
        self.load_bar.set(0)
        self.load_bar.pack(pady=5)
        
        info_panel = ctk.CTkFrame(page, fg_color="#2a2a2e", corner_radius=8)
        info_panel.pack(pady=8, padx=20, fill="x")
        
        data = ctk.CTkFrame(info_panel, fg_color="transparent")
        data.pack(pady=8, padx=20)
        
        timing = ctk.CTkFrame(data, fg_color="transparent")
        timing.pack(side="left", padx=30)
        
        ctk.CTkLabel(timing, text="TÄNDNING", font=("Arial", 11, "bold"), 
                    text_color="#888").pack()
        self.timing = ctk.CTkLabel(timing, text="0.0°",
                                   font=("Arial", 24, "bold"), text_color="#00c896")
        self.timing.pack(pady=2)
        
        rt = ctk.CTkFrame(data, fg_color="transparent")
        rt.pack(side="left", padx=30)
        
        ctk.CTkLabel(rt, text="KÖRTID", font=("Arial", 11, "bold"), 
                    text_color="#888").pack()
        self.runtime_lbl = ctk.CTkLabel(rt, text="00:00:00",
                                        font=("Arial", 24, "bold"), text_color="#00c896")
        self.runtime_lbl.pack(pady=2)
        
        self.pages.append(page)
    
    def _page_temp(self):
        """Temperatursida."""
        page = ctk.CTkFrame(self.pages_frame, fg_color="#1a1a1e")
        
        ctk.CTkLabel(page, text="Temperaturövervakning",
                    font=("Arial", 16, "bold"), text_color="#00c896").pack(pady=8)
        
        gauges = ctk.CTkFrame(page, fg_color="transparent")
        gauges.pack(pady=15)
        
        self.coolant = GaugeWidget(gauges, "KYLVÄTSKA", -40, 120, "°C", size=200)
        self.coolant.pack(side="left", padx=15)
        
        self.intake_t = GaugeWidget(gauges, "INSUG", -40, 80, "°C", size=200)
        self.intake_t.pack(side="left", padx=15)
        
        self.oil = GaugeWidget(gauges, "OLJA", 0, 150, "°C", size=200)
        self.oil.pack(side="left", padx=15)
        
        self.pages.append(page)
    
    def _page_fuel(self):
        """Bränsle & luftsida."""
        page = ctk.CTkFrame(self.pages_frame, fg_color="#1a1a1e")
        
        ctk.CTkLabel(page, text="Bränsle & Luft",
                    font=("Arial", 16, "bold"), text_color="#00c896").pack(pady=5)
        
        gauges = ctk.CTkFrame(page, fg_color="transparent")
        gauges.pack(pady=8)
        
        self.fuel_p = GaugeWidget(gauges, "TRYCK", 0, 600, "kPa", size=200)
        self.fuel_p.pack(side="left", padx=8)
        
        self.fuel_r = GaugeWidget(gauges, "FLÖDE", 0, 50, "L/h", size=200)
        self.fuel_r.pack(side="left", padx=8)
        
        self.intake_p = GaugeWidget(gauges, "INSUG", 0, 300, "kPa", size=200)
        self.intake_p.pack(side="left", padx=8)
        
        maf = ctk.CTkFrame(page, fg_color="transparent")
        maf.pack(pady=10, padx=30, fill="x")
        
        self.maf_lbl = ctk.CTkLabel(maf, text="MAF (Luftflöde): 0.0 g/s",
                                    font=("Arial", 13, "bold"))
        self.maf_lbl.pack()
        
        self.maf_bar = ctk.CTkProgressBar(maf, width=500, height=20)
        self.maf_bar.set(0)
        self.maf_bar.pack(pady=5)
        
        ctk.CTkLabel(maf, text="MAX MAF", font=("Arial", 10), 
                    text_color="#aaa").pack(pady=(5, 0))
        self.max_maf = ctk.CTkLabel(maf, text="255.0 g/s",
                                    font=("Arial", 16, "bold"), text_color="#00c896")
        self.max_maf.pack()
        
        self.pages.append(page)
    
    def _page_diag(self):
        """Diagnostiksida."""
        page = ctk.CTkFrame(self.pages_frame, fg_color="#1a1a1e")
        
        ctk.CTkLabel(page, text="Diagnostik & Felkoder",
                    font=("Arial", 16, "bold"), text_color="#00c896").pack(pady=8)
        
        data = ctk.CTkFrame(page, fg_color="transparent")
        data.pack(pady=15)
        
        dist = ctk.CTkFrame(data, fg_color="transparent")
        dist.pack(pady=10)
        
        ctk.CTkLabel(dist, text="AVSTÅND SEDAN FELKODER RENSADES",
                    font=("Arial", 11, "bold"), text_color="#aaa").pack()
        self.dist_lbl = ctk.CTkLabel(dist, text="0 km",
                                     font=("Arial", 24, "bold"), text_color="#00c896")
        self.dist_lbl.pack()
        
        tm = ctk.CTkFrame(data, fg_color="transparent")
        tm.pack(pady=10)
        
        ctk.CTkLabel(tm, text="TID SEDAN FELKODER RENSADES",
                    font=("Arial", 11, "bold"), text_color="#aaa").pack()
        self.time_lbl = ctk.CTkLabel(tm, text="00:00:00",
                                     font=("Arial", 24, "bold"), text_color="#00c896")
        self.time_lbl.pack()
        
        btns = ctk.CTkFrame(page, fg_color="transparent")
        btns.pack(pady=20)
        
        ctk.CTkButton(btns, text="LÄS FELKODER", width=250, height=45,
                     font=("Arial", 14, "bold"), 
                     corner_radius=8,
                     command=self._get_dtc).pack(side="left", padx=8)
        
        ctk.CTkButton(btns, text="RENSA FELKODER", width=250, height=45,
                     font=("Arial", 14, "bold"), 
                     fg_color="#8a3a3e", 
                     hover_color="#aa5055",
                     corner_radius=8,
                     command=self._clear_dtc).pack(side="left", padx=8)
        
        self.pages.append(page)
    
    def _make_switch_command(self, page_idx):
        """Skapa kommando för att byta sida."""
        def switch_cmd():
            self._switch(page_idx)
        return switch_cmd
    
    def _switch(self, idx):
        """Byt sida."""
        if idx == self.current_page:
            return
        
        self.current_page = idx
        
        for i, page in enumerate(self.pages):
            if i == idx:
                page.pack(fill="both", expand=True)
            else:
                page.pack_forget()
        
        for i, btn in enumerate(self.nav_btns):
            if i == idx:
                btn.configure(fg_color="#00c896", hover_color="#00b080", text_color="#1a1a1e")
            else:
                btn.configure(fg_color="#3B8ED0", hover_color="#1F6AA5", text_color="white")
    
    def _setup_gpio(self):
        """Konfigurera GPIO-knapp för Raspberry Pi."""
        if not GPIO_AVAILABLE:
            return
        
        try:
            # GPIO-pinnnummer (BCM-numrering)
            gpio_pin = 17  # GPIO 17 (Pin 11) för att byta sida
            
            # Skapa knapp med gpiozero (automatiskt pull-up och debounce)
            self.gpio_button = Button(gpio_pin, pull_up=True, bounce_time=0.2)
            
            # Koppla knapp-händelse till sidbytesfunktion
            self.gpio_button.when_pressed = self._gpio_next_page
            
            print(f"✓ GPIO-knapp konfigurerad på GPIO {gpio_pin} (Pin 11)")
            print("  Tryck på knappen för att byta sida")
            
        except Exception as e:
            print(f"✗ GPIO-konfiguration misslyckades: {e}")
    
    def _gpio_next_page(self):
        """Byt till nästa sida via GPIO-knapp (loopar runt)."""
        next_page = (self.current_page + 1) % len(self.pages)
        self.after(0, lambda: self._switch(next_page))
    
    def _get_dtc(self):
        """Läs felkoder."""
        if not self.use_sim:
            try:
                result = read_obd_data(self.commands.get('get_dtc'))
                if not result:
                    messagebox.showinfo("Felkoder", "Inga felkoder.\n\nStatus: OK")
                else:
                    codes = [f"{c[0]} - {c[1]}" if hasattr(c, '__iter__') and len(c) >= 2 
                            else str(c) for c in result]
                    msg = f"Hittade {len(codes)} felkod(er):\n\n" + "\n".join(codes)
                    messagebox.showwarning("Felkoder", msg + "\n\nKonsultera manual.")
            except Exception as e:
                messagebox.showerror("Fel", f"Kunde inte läsa felkoder: {e}")
        else:
            codes = random.sample(["P0420", "P0171", "P0101", "P0300", "C0035"], 
                                random.randint(0, 3))
            if not codes:
                messagebox.showinfo("Felkoder", "Inga felkoder.\n\nStatus: OK")
            else:
                msg = f"Hittade {len(codes)} felkod(er):\n\n" + "\n".join(codes)
                messagebox.showwarning("Felkoder", msg + "\n\nKonsultera manual.")
    
    def _clear_dtc(self):
        """Rensa felkoder."""
        if messagebox.askyesno("Rensa",
            "Rensa alla felkoder?\n\nDetta återställer:\n"
            "- Alla felkoder\n- Avstånd\n- Tid"):
            
            if not self.use_sim:
                try:
                    read_obd_data(self.commands.get('clear_dtc'))
                    self.dist_dtc = 0
                    self.time_dtc = 0
                    messagebox.showinfo("Klart", "Felkoder rensade.")
                except Exception as e:
                    messagebox.showerror("Fel", f"Kunde inte rensa: {e}")
            else:
                self.dist_dtc = 0
                self.time_dtc = 0
                messagebox.showinfo("Klart", "Felkoder rensade.")
    
    def _read(self, cmd, default=0):
        """Läs OBD-värde."""
        if self.use_sim or cmd not in self.commands:
            return None
        
        try:
            result = read_obd_data(self.commands[cmd])
            if result is not None:
                return result.magnitude if hasattr(result, 'magnitude') else result
        except:
            pass
        
        return default
    
    def _start_updates(self):
        """Starta uppdateringar."""
        self._running = True
        
        def update():
            while self._running:
                try:
                    self.after(0, self._update)
                except:
                    break
                time.sleep(0.3)
        
        threading.Thread(target=update, daemon=True).start()
    
    def _update(self):
        """Uppdatera data."""
        if self.use_sim:
            spd, r, thr = random.randint(0, 180), random.randint(800, 7000), random.randint(0, 100)
            ld, tim = random.randint(10, 95), random.uniform(-10, 45)
            cool, int_t, oil = random.randint(70, 105), random.randint(15, 45), random.randint(80, 120)
            fp, fr = random.randint(250, 550), random.uniform(0.5, 25)
            ip, maf, mmaf = random.randint(30, 120), random.uniform(2, 95), 255.0
        else:
            spd = self._read('speed', 0)
            r = self._read('rpm', 0)
            thr = self._read('throttle_pos', 0)
            ld = self._read('eng_load', 0)
            tim = self._read('timing_advance', 0)
            cool = self._read('coolant_temp', 80)
            int_t = self._read('intake_temp', 25)
            oil = self._read('oil_temp', 90)
            fp = self._read('fuel_pressure', 300)
            fr = self._read('fuel_rate', 5)
            ip = random.randint(30, 120)
            maf = self._read('maf', 10)
            mmaf = self._read('max_maf', 255)
        
        self.speed.set_value(spd)
        self.rpm.set_value(r)
        self.throttle.set_value(thr)
        self.load_lbl.configure(text=f"MOTORBELASTNING: {int(ld)}%")
        self.load_bar.set(ld / 100)
        self.timing.configure(text=f"{tim:.1f}°")
        
        if self.use_sim:
            self.runtime += 0.1
        else:
            rt = self._read('run_time', 0)
            if rt > 0:
                self.runtime = rt
        
        h, m, s = int(self.runtime // 3600), int((self.runtime % 3600) // 60), int(self.runtime % 60)
        self.runtime_lbl.configure(text=f"{h:02d}:{m:02d}:{s:02d}")
        
        self.coolant.set_value(cool)
        self.intake_t.set_value(int_t)
        self.oil.set_value(oil)
        
        self.fuel_p.set_value(fp)
        self.fuel_r.set_value(fr)
        self.intake_p.set_value(ip)
        self.maf_lbl.configure(text=f"MAF (Luftflöde): {maf:.1f} g/s")
        self.maf_bar.set((maf / mmaf) if mmaf > 0 else 0)
        self.max_maf.configure(text=f"{mmaf:.1f} g/s")
        
        if self.use_sim:
            self.dist_dtc += random.uniform(0.01, 0.05)
            self.time_dtc += 0.1
        else:
            d = self._read('dist_since_dtc_cleared', 0)
            t = self._read('time_since_dtc_cleared', 0)
            if d and d > 0:
                self.dist_dtc = d
            if t and t > 0:
                self.time_dtc = t
        
        self.dist_lbl.configure(text=f"{self.dist_dtc:.1f} km")
        dh, dm, ds = int(self.time_dtc // 3600), int((self.time_dtc % 3600) // 60), int(self.time_dtc % 60)
        self.time_lbl.configure(text=f"{dh:02d}:{dm:02d}:{ds:02d}")
    
    def destroy(self):
        """Cleanup när programmet stängs."""
        self._running = False
        
        # Städa GPIO
        if GPIO_AVAILABLE and hasattr(self, 'gpio_button'):
            try:
                self.gpio_button.close()
                print("✓ GPIO städat")
            except:
                pass
        
        super().destroy()


if __name__ == "__main__":
    use_sim = "--real" not in sys.argv
    
    print("Startar i", "SIMULERING" if use_sim else "LIVE OBD", "läge...")
    if use_sim:
        print("För riktig data: python dashboard.py --real")
    
    app = OBDDashboard(use_sim=use_sim)
    app.mainloop()

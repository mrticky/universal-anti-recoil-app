import os
import json
import re
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter import StringVar, DoubleVar, IntVar

from pynput import mouse, keyboard
import ctypes
from ctypes import wintypes
from PIL import Image, ImageTk

# ===================== Win32 SendInput =====================
ULONG_PTR = ctypes.POINTER(ctypes.c_ulong)

class MOUSEINPUT(ctypes.Structure):
    _fields_ = (
        ("dx",          wintypes.LONG),
        ("dy",          wintypes.LONG),
        ("mouseData",   wintypes.DWORD),
        ("dwFlags",     wintypes.DWORD),
        ("time",        wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    )

class INPUT(ctypes.Structure):
    class _I(ctypes.Union):
        _fields_ = (("mi", MOUSEINPUT),)
    _anonymous_ = ("i",)
    _fields_ = (("type", wintypes.DWORD), ("i", _I))

SendInput = ctypes.windll.user32.SendInput
SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
SendInput.restype  = wintypes.UINT

INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001

def send_mouse_move_rel(dx, dy):
    inp = INPUT()
    inp.type = INPUT_MOUSE
    inp.mi = MOUSEINPUT(dx=int(dx), dy=int(dy),
                        mouseData=0, dwFlags=MOUSEEVENTF_MOVE,
                        time=0, dwExtraInfo=None)
    SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

# ===================== Smooth movement core =====================
MICROSTEP_RATE_HZ = 240  # micro-steps for butter-smooth motion

left_down = False
right_down = False
listener_mouse = None
listener_kb = None
stop_event = threading.Event()

def on_mouse_click(x, y, button, pressed):
    global left_down, right_down
    try:
        if button == mouse.Button.left:
            left_down = pressed
        elif button == mouse.Button.right:
            right_down = pressed
    except Exception:
        pass

def on_key_press(_key):  # no emergency stop hotkey in this build
    pass

def start_listeners():
    global listener_mouse, listener_kb
    if listener_mouse is None:
        listener_mouse = mouse.Listener(on_click=on_mouse_click)
        listener_mouse.daemon = True
        listener_mouse.start()
    if listener_kb is None:
        listener_kb = keyboard.Listener(on_press=on_key_press)
        listener_kb.daemon = True
        listener_kb.start()

def stop_listeners():
    global listener_mouse, listener_kb
    if listener_mouse:
        listener_mouse.stop()
        listener_mouse = None
    if listener_kb:
        listener_kb.stop()
        listener_kb = None

def smooth_interval_move(dx_total, dy_total, interval_s):
    """
    Render total (dx, dy) over interval_s at a fixed microstep rate
    using DDA accumulators to avoid rounding jitter.
    """
    steps = max(1, int(interval_s * MICROSTEP_RATE_HZ))
    if steps == 1:
        send_mouse_move_rel(dx_total, dy_total)
        return

    step_dx_f = dx_total / steps
    step_dy_f = dy_total / steps
    acc_x = 0.0
    acc_y = 0.0

    step_period = interval_s / steps
    t0 = time.perf_counter()

    for i in range(steps):
        if stop_event.is_set():
            return

        acc_x += step_dx_f
        acc_y += step_dy_f
        move_x = int(round(acc_x)); acc_x -= move_x
        move_y = int(round(acc_y)); acc_y -= move_y

        if move_x or move_y:
            send_mouse_move_rel(move_x, move_y)

        target = t0 + (i + 1) * step_period
        while True:
            now = time.perf_counter()
            remaining = target - now
            if remaining <= 0:
                break
            time.sleep(0.0015 if remaining > 0.002 else 0)

def movement_loop(get_params):
    """
    RIGHT = arm; while RIGHT is held, holding LEFT applies the movement each interval.
    UI shows only 'toggled on/off'.
    """
    global left_down, right_down
    try:
        while not stop_event.is_set():
            while not right_down and not stop_event.is_set():
                time.sleep(0.004)
            if stop_event.is_set():
                break

            while right_down and not left_down and not stop_event.is_set():
                time.sleep(0.002)
            if stop_event.is_set():
                break

            while right_down and left_down and not stop_event.is_set():
                p = get_params()
                dx_total = float(p["x"])
                dy_total = float(p["y"])
                interval_ms = max(1.0, float(p["interval_ms"]))
                interval_s  = interval_ms / 1000.0

                t_start = time.perf_counter()
                smooth_interval_move(dx_total, dy_total, interval_s)

                # keep cadence
                while (interval_s - (time.perf_counter() - t_start) > 0 and
                       right_down and left_down and not stop_event.is_set()):
                    time.sleep(0.0015)
    finally:
        pass

# ===================== Config files =====================
CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs")
os.makedirs(CONFIG_DIR, exist_ok=True)

def sanitize_name(name: str) -> str:
    name = (name or "").strip()
    name = re.sub(r"\s+", " ", name)
    safe = re.sub(r"[^A-Za-z0-9 _-]", "", name)
    return safe[:60] if safe else "config"

def config_path(name: str) -> str:
    return os.path.join(CONFIG_DIR, f"{name}.json")

def list_configs() -> list:
    return sorted(
        [os.path.splitext(f)[0] for f in os.listdir(CONFIG_DIR) if f.lower().endswith(".json")],
        key=str.lower
    )

def save_config(name: str, data: dict) -> None:
    with open(config_path(name), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_config(name: str) -> dict:
    with open(config_path(name), "r", encoding="utf-8") as f:
        return json.load(f)

def delete_config(name: str) -> None:
    p = config_path(name)
    if os.path.exists(p):
        os.remove(p)

# ===================== Dark theme =====================
BG_APP   = "#0b0d10"
BG_CARD  = "#111318"
BG_SIDE  = "#0e1014"
FG_TEXT  = "#e6e8eb"
BORDER   = "#22252b"
SEL_BG   = "#2a2f37"
SEL_FG   = "#ffffff"

FONT_BASE   = ("Segoe UI", 10)
FONT_HEADER = ("Segoe UI", 16, "bold")

def apply_dark_theme(root: tk.Tk):
    style = ttk.Style(root)
    style.theme_use("clam")
    root.configure(bg=BG_APP)

    style.configure("TFrame", background=BG_APP)
    style.configure("Card.TFrame", background=BG_CARD, borderwidth=1, relief="solid")
    style.configure("TLabelframe", background=BG_CARD, bordercolor=BORDER, borderwidth=1, relief="solid")
    style.configure("TLabelframe.Label", background=BG_CARD, foreground=FG_TEXT, font=FONT_BASE)

    style.configure("TLabel", background=BG_APP, foreground=FG_TEXT, font=FONT_BASE)
    style.configure("Header.TLabel", background=BG_APP, foreground="#ffffff", font=FONT_HEADER)

    style.configure("TButton", background=BG_CARD, foreground=FG_TEXT,
                    bordercolor=BORDER, focusthickness=2, focuscolor=BORDER,
                    padding=(12,7))
    style.map("TButton", background=[("active", "#171a20")])

    style.configure("TSpinbox", fieldbackground="#0d0f13", background="#0d0f13",
                    foreground=FG_TEXT, bordercolor=BORDER, arrowsize=12)
    style.configure("TScale", background=BG_CARD, troughcolor="#0d0f13")

# ===================== Image background (draws immediately) =====================
class ImageBackground(tk.Label):
    """
    Loads 'background.png' / '.jpg' / '.jpeg' and paints it as a cover-fit background.
    Draws immediately on startup and on every resize. Falls back to solid dark if missing.
    """
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self["bg"] = BG_APP
        self._img = None            # PIL Image
        self._imgtk = None          # PhotoImage
        self._target_w = 1
        self._target_h = 1
        self._load_image()

        # draw once the window exists
        self.bind("<Configure>", self._on_resize)
        self.after(50, self._initial_draw)

    def _load_image(self):
        base = os.path.dirname(os.path.abspath(__file__))
        for name in ("background.png", "background.jpg", "background.jpeg"):
            path = os.path.join(base, name)
            if os.path.exists(path):
                try:
                    self._img = Image.open(path).convert("RGB")
                    print(f"[image] loaded {name}")
                except Exception as e:
                    print(f"[image] failed to open {name}: {e}")
                    self._img = None
                break
        if self._img is None:
            print("[image] no background.png/.jpg found — using solid bg")

    def _initial_draw(self):
        try:
            self._target_w = max(1, self.winfo_width())
            self._target_h = max(1, self.winfo_height())
        except Exception:
            pass
        self._redraw()

    def _on_resize(self, _e=None):
        self._target_w = max(1, self.winfo_width())
        self._target_h = max(1, self.winfo_height())
        self._redraw()

    def _redraw(self):
        if self._img is None:
            return
        img = self._cover_fit(self._img, self._target_w, self._target_h)
        self._imgtk = ImageTk.PhotoImage(img)
        self.configure(image=self._imgtk)

    @staticmethod
    def _cover_fit(img: Image.Image, tw: int, th: int) -> Image.Image:
        if tw <= 0 or th <= 0:
            return img
        w, h = img.size
        in_aspect = w / h
        out_aspect = tw / th
        if in_aspect > out_aspect:
            new_w = int(w * (th / h))
            img = img.resize((new_w, th), Image.BILINEAR)
            x0 = (new_w - tw) // 2
            img = img.crop((x0, 0, x0 + tw, th))
        else:
            new_h = int(h * (tw / w))
            img = img.resize((tw, new_h), Image.BILINEAR)
            y0 = (new_h - th) // 2
            img = img.crop((0, y0, tw, y0 + th))
        return img

# ===================== UI App =====================
class RecoilApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("tickys recoil app")
        self.geometry("980x520")
        self.minsize(920, 480)
        self.configure(bg=BG_APP)

        apply_dark_theme(self)

        # Background image (draw right away and keep behind everything)
        self.bg_image = ImageBackground(self)
        self.bg_image.place(x=0, y=0, relwidth=1, relheight=1)
        self.bg_image.lower()
        self.bg_image._initial_draw()

        # Vars
        self.y_var = DoubleVar(value=-50.0)
        self.x_var = DoubleVar(value=0.0)
        self.interval_var = IntVar(value=120)
        self.status_var = StringVar(value="toggled off")

        # State
        self.listener_running = False
        self.worker_thread = None
        self.current_config_name = None

        self._build_ui()
        self._refresh_config_list()

    def _build_ui(self):
        # Foreground container (above background)
        root = ttk.Frame(self, style="TFrame")
        root.place(x=0, y=0, relwidth=1, relheight=1)

        content = ttk.Frame(root, style="TFrame")
        content.pack(fill="both", expand=True, padx=16, pady=16)

        # LEFT — Config sidebar
        left = ttk.Frame(content, style="Card.TFrame")
        left.pack(side="left", fill="y")
        left.configure(width=280)

        ttk.Label(left, text="configs", style="Header.TLabel").pack(anchor="w", padx=14, pady=(14,6))

        self.config_list = tk.Listbox(
            left, height=18, exportselection=False,
            bg=BG_SIDE, fg=FG_TEXT,
            selectbackground=SEL_BG, selectforeground=SEL_FG,
            highlightthickness=0, bd=0, relief="flat", font=FONT_BASE
        )
        self.config_list.pack(fill="both", expand=True, padx=12, pady=(4,8))

        b1 = ttk.Frame(left, style="TFrame"); b1.pack(fill="x", padx=12, pady=(0,8))
        ttk.Button(b1, text="new", width=10, command=self._new_config).pack(side="left", padx=4)
        ttk.Button(b1, text="save", width=10, command=self._save_config).pack(side="left", padx=4)
        ttk.Button(b1, text="save as", width=10, command=self._save_config_as).pack(side="left", padx=4)

        b2 = ttk.Frame(left, style="TFrame"); b2.pack(fill="x", padx=12, pady=(0,12))
        ttk.Button(b2, text="load", width=10, command=self._load_selected).pack(side="left", padx=4)
        ttk.Button(b2, text="delete", width=10, command=self._delete_selected).pack(side="left", padx=4)
        ttk.Button(b2, text="refresh", width=10, command=self._refresh_config_list).pack(side="left", padx=4)

        # RIGHT — Controls
        right = ttk.Frame(content, style="TFrame")
        right.pack(side="left", fill="both", expand=True, padx=(16,0))

        ttk.Label(right, text="tickys recoil app", style="Header.TLabel").pack(anchor="w", pady=(0,10))

        controls = ttk.LabelFrame(right, text="movement controls", style="TLabelframe")
        controls.pack(fill="x", pady=(0,12))

        self._add_slider_with_spin(controls, "Y (vertical)", -200, 200, self.y_var, step=1, digits=0)
        self._add_slider_with_spin(controls, "X (horizontal)", -200, 200, self.x_var, step=1, digits=0)
        self._add_slider_with_spin(controls, "Interval (ms)", 1, 2000, self.interval_var, step=1, digits=0, is_int=True)

        row = ttk.Frame(right, style="TFrame"); row.pack(pady=(2,10))
        ttk.Button(row, text="toggle on", command=self.toggle_on).pack(side="left", padx=6)
        ttk.Button(row, text="toggle off", command=self.toggle_off).pack(side="left", padx=6)

        srow = ttk.Frame(right, style="TFrame"); srow.pack(fill="x")
        ttk.Label(srow, text="status:", style="TLabel").pack(side="left")
        ttk.Label(srow, textvariable=self.status_var).pack(side="left", padx=(8,0))

        ttk.Frame(right, style="TFrame").pack(fill="both", expand=True)

    def _add_slider_with_spin(self, parent, label, minv, maxv, var, step=1, digits=0, is_int=False):
        row = ttk.Frame(parent, style="TFrame"); row.pack(fill="x", padx=12, pady=8)
        ttk.Label(row, text=label).pack(side="left", padx=(0,10))
        scale = ttk.Scale(row, from_=minv, to=maxv, variable=var)
        scale.pack(side="left", fill="x", expand=True, padx=(0,12))
        sb = ttk.Spinbox(row, from_=minv, to=maxv, increment=step,
                         textvariable=var, width=10, style="TSpinbox")
        sb.pack(side="left")
        def clamp_var(*_):
            try:
                v = int(float(var.get())) if is_int else float(var.get())
            except Exception:
                v = minv
            v = max(minv, min(maxv, v))
            var.set(int(v) if is_int or digits == 0 else round(v, digits))
        sb.bind("<FocusOut>", lambda e: clamp_var())
        sb.bind("<Return>",   lambda e: clamp_var())

    # -------- Config actions --------
    def _refresh_config_list(self):
        self.config_list.delete(0, tk.END)
        for name in list_configs():
            self.config_list.insert(tk.END, name)

    def _new_config(self):
        self.y_var.set(-50.0)
        self.x_var.set(0.0)
        self.interval_var.set(120)
        self.current_config_name = None
        self.config_list.selection_clear(0, tk.END)

    def _save_config(self):
        if not self.current_config_name:
            return self._save_config_as()
        try:
            save_config(self.current_config_name, self._current_data())
            self._refresh_config_list()
        except Exception as e:
            messagebox.showerror("save error", str(e))

    def _save_config_as(self):
        name = simpledialog.askstring("save config as", "name:")
        if not name:
            return

        name = sanitize_name(name)
        path = config_path(name)

        if os.path.exists(path):
            overwrite = messagebox.askyesno("overwrite?", f'"{name}" exists. overwrite?')
            if not overwrite:
                return

        try:
            save_config(name, self._current_data())
            self.current_config_name = name
            self._refresh_config_list()
            # highlight in list
            for i in range(self.config_list.size()):
                if self.config_list.get(i) == name:
                    self.config_list.selection_clear(0, tk.END)
                    self.config_list.selection_set(i)
                    self.config_list.see(i)
                    break
        except Exception as e:
            messagebox.showerror("save error", str(e))

    def _load_selected(self):
        sel = self._selected_name()
        if not sel:
            messagebox.showinfo("load config", "select a config from the list.")
            return
        try:
            data = load_config(sel)
            self._apply_data(data)
            self.current_config_name = sel
        except Exception as e:
            messagebox.showerror("load error", str(e))

    def _delete_selected(self):
        sel = self._selected_name()
        if not sel:
            messagebox.showinfo("delete config", "select a config from the list.")
            return
        if not messagebox.askyesno("delete config", f'delete "{sel}"?'):
            return
        try:
            delete_config(sel)
            if self.current_config_name == sel:
                self.current_config_name = None
            self._refresh_config_list()
        except Exception as e:
            messagebox.showerror("delete error", str(e))

    def _selected_name(self):
        try:
            sel = self.config_list.curselection()
            if not sel:
                return None
            return self.config_list.get(sel[0])
        except Exception:
            return None

    def _current_data(self):
        return {
            "x": float(self.x_var.get()),
            "y": float(self.y_var.get()),
            "interval_ms": int(self.interval_var.get()),
        }

    def _apply_data(self, data: dict):
        self.x_var.set(float(data.get("x", 0.0)))
        self.y_var.set(float(data.get("y", -50.0)))
        self.interval_var.set(int(data.get("interval_ms", 120)))

    # -------- Toggle controls --------
    def toggle_on(self):
        if not self.listener_running:
            start_listeners()
            self.listener_running = True
        if not (self.worker_thread and self.worker_thread.is_alive()):
            stop_event.clear()
            self.worker_thread = threading.Thread(
                target=movement_loop, args=(self._get_params,), daemon=True
            )
            self.worker_thread.start()
        self.status_var.set("toggled on")

    def toggle_off(self):
        stop_event.set()
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=0.3)
        stop_listeners()
        self.listener_running = False
        global left_down, right_down
        left_down = False
        right_down = False
        stop_event.clear()
        self.status_var.set("toggled off")

    def _get_params(self):
        return {
            "x": self.x_var.get(),
            "y": self.y_var.get(),
            "interval_ms": self.interval_var.get(),
        }

    def on_close(self):
        try:
            self.toggle_off()
        finally:
            self.destroy()

# ===================== Main =====================
def main():
    app = RecoilApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()

if __name__ == "__main__":
    main()

<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/6677ee36-e073-4087-8a28-c587eab7a98d" />



<h1 align="center">🎯 tickys recoil app</h1>
<p align="center">
  <i>Ultra-smooth, universal anti-recoil controller for Windows — built with Python.</i><br>
  <b>Beautiful UI • Config System • Microstep Precision</b>
</p>

---

## 🧠 Overview

**tickys recoil app** is a standalone Windows tool that simulates ultra-precise, microstepped mouse movement.  
It’s designed for testing, development, and accessibility — featuring a dark modern UI, background image support,  
and full config management for saving and loading recoil profiles.

<p align="center">
  <img width="983" height="557" alt="{9FEA11F2-F408-4A23-A487-C8138DB8055A}" src="https://github.com/user-attachments/assets/60886057-215c-4d79-b877-1ba17c76a3ea" />
</p>


Uploading showcase.mp4…


---



## ⚙️ Features

✅ **Ultra-smooth motion engine**  
240Hz microstep mouse movement using Win32 `SendInput` for pixel-perfect motion.

🎮 **Dual-button trigger system**  
- Hold **Right Mouse Button** → arms the app.  
- While holding right, press **Left Mouse Button** → applies movement pattern.

🎚️ **Adjustable Controls**
- **Y (vertical)** – recoil pull-down or up adjustment  
- **X (horizontal)** – left/right correction  
- **Interval (ms)** – delay between movements  
- Precision **spinboxes** + **sliders** for smooth tuning.

💾 **Config Manager**
- Save, load, and delete `.json` configs from the built-in sidebar.  
- Configs stored in `/configs/` folder.  
- “New”, “Save As”, “Refresh” buttons for quick workflow.

🖼️ **Aesthetic UI**
- Deep dark theme with monochrome highlights.  
- Live background image support (`background.png` / `.jpg`).  
- Auto-resizes to window dimensions.

🪶 **Lightweight & Portable**
- Single `main.py` file  
- Requires only `pillow` + `pynput`  
- Works on Windows 10/11 — no installer or admin required.

---

## 🚀 Setup

```bash
# 1. Install dependencies
pip install pillow pynput

# 2. (Optional) Add your background image
# Place a file named background.png or background.jpg next to main.py

# 3. Run the app
python main.py

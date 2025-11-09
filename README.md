<img width="772" height="406" alt="{3D0989C3-C8D4-4993-B374-9CA925412B57}" src="https://github.com/user-attachments/assets/d2f98f77-d149-4fdd-b517-8f1d726ed31b" />


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
  <img src="preview.png" width="80%" alt="App UI Preview">
</p>

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

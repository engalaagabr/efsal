<p align="center">
  <img src="assets/penguin-stretch.svg" alt="Penguin stretching" width="220" />
</p>

# Efsal

A calm, lightweight GNOME desktop application that tracks active computer usage and gently reminds you to move, stretch, and hydrate.

![GNOME](https://img.shields.io/badge/GNOME-4a86cf?style=flat&logo=gnome&logoColor=white)
![GTK4](https://img.shields.io/badge/GTK4-4a86cf?style=flat)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

---

## How to Build and Install

### Prerequisites (Fedora)

```bash
# Install system dependencies
sudo dnf install python3 python3-pip python3-gobject gtk4 libadwaita
```

### Installation

```bash
# Clone the repository
git clone https://github.com/gentlebreak/efsal.git
cd efsal

# (Optional) Create a virtual environment
python3 -m venv .venv --system-site-packages
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install the desktop app and icon to your system
chmod +x install.sh
./install.sh
```

> **Note:** The `--system-site-packages` flag is important because PyGObject, GTK4, and Libadwaita are system libraries that can't be installed via pip alone.

Once installed, you can launch **Efsal** directly from your GNOME application menu!

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

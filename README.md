# Luxafor Sync – Zoho Cliq Integration

**Made by Nikita P.**

Dieses Tool synchronisiert den Benutzerstatus aus **Zoho Cliq** mit einem **Luxafor USB-Gerät**. Die App wurde für den internen Einsatz bei einer Firma entwickelt, ist aber frei nutzbar für ähnliche Anwendungen.

## 🔧 Features

- Dark Mode GUI mit `customtkinter`
- Automatische OAuth2 Token-Erneuerung für Zoho
- CLIQ-Statusabfrage alle 4 Sekunden
- Webhook-gesteuerte Luxafor-Farbänderung
- Setup-GUI beim ersten Start (cfg-Erzeugung)
- Minimierung in den System-Tray mit Menü:
  - 🖥 Öffnen
  - 🛠 Config (öffnet Notepad)
  - ❌ Beenden

## 🚀 Setup

### Abhängigkeiten (Install via pip):

```bash
pip install customtkinter pystray pillow requests
```

### Start:

```bash
python luxafor_sync.py
```

Beim ersten Start wird eine Konfigurations-GUI geöffnet.

---

## 🧾 Lizenz

Dieses Projekt ist frei verwendbar. Keine Garantie, keine Haftung.

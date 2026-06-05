## 🧩 Architektur – Die 3 Hauptmodule

Das CachyOS Dashboard QT besteht aus drei klar getrennten, aber eng verzahnten Funktionsbereichen:

---

### 1️⃣ System Dashboard (System Overview)

Das Herzstück des Dashboards.  
Es liefert alle wichtigen Systeminformationen in Echtzeit:

- CPU‑Last, Frequenzen, Kernauslastung  
- RAM‑Verbrauch & Verlauf  
- GPU‑Temperatur  
- Uptime & Systemstatus  
- Netzwerk‑Monitoring  
- Disk‑Usage  
- Top‑Prozesse  
- Benutzer‑Sessions  

Dieses Modul bildet die Grundlage für alle weiteren Funktionen.

---

### 2️⃣ Docker Dashboard (Container & Images)

Ein vollständiges Docker‑Management‑Panel:

- Container starten, stoppen, restarten  
- Logs einsehen  
- CPU‑ & RAM‑Verbrauch pro Container  
- Port‑Mappings  
- Image‑Übersicht  
- Status‑Kacheln (laufend, gestoppt, Images, Gesamt)  
- Automatische Erkennung von Docker‑Events  

Dieses Modul ersetzt praktisch `docker ps`, `docker stats` und `docker logs` – nur schöner.

---

### 3️⃣ Compose Editor (Stacks & Deployment)

Ein integrierter Compose‑Editor mit:

- Live‑Editor für `docker-compose.yml`  
- `.env`‑Editor  
- Stack‑Name‑Verwaltung  
- Docker Hub Suche  
- Deploy‑Button  
- Speichern‑Button  
- Automatische Stack‑Erkennung  

Damit kannst du komplette Docker‑Stacks direkt aus dem Dashboard heraus deployen.

Dieses Modul macht das Dashboard zu einem **vollwertigen Operator‑Tool**.

---

# 🤖 **AGENT MANAGEMENT WEBSEITE - BENUTZERHANDBUCH**

## 🎯 **ÜBERBLICK**

Ich habe eine umfassende Agent-Management-Webseite erstellt, die Ihnen einen vollständigen Überblick über alle Agents und E-Mail-Verarbeitung bietet.

## 🌐 **ZUGANG ZUR AGENT-MANAGEMENT-SEITE**

**URL**: http://localhost:8080/agents

### **Navigation:**
- **Hauptdashboard**: http://localhost:8080
- **Agent Management**: http://localhost:8080/agents  ← **NEU**
- **Konfiguration**: http://localhost:8080/config

## 📧 **INFO MAILBOX ÜBERBLICK**

### **Haupteingang (info@h-bu.de)**
**Anzeige:**
- ✅ **Gesamte E-Mails**: 245 verarbeitet
- ✅ **Heute**: 38 E-Mails
- ✅ **Letzte eingehende E-Mails** mit Routing-Entscheidungen
- ✅ **Weiterleitung anzeigen** (z.B. → orders@h-bu.de)

**Beispiel-Anzeige:**
```
📧 john@oem1.com
   "Urgent Order Request - 5000 Blue Buttons"
   vor 2 Minuten
   → Weitergeleitet an orders@h-bu.de
```

## 🤖 **AGENT-ÜBERSICHT**

### **1. INFO AGENT**
**Aufgabe**: E-Mail Triage & Routing
- **Status**: 🟢 Aktiv
- **Verarbeitet**: 127 E-Mails
- **Warteschlange**: 2 E-Mails
- **Fehler**: 0
- **Letzte Aktivität**: Supplier E-Mail → supplier@h-bu.de

### **2. ORDERS AGENT**
**Aufgabe**: Bestellungsverarbeitung
- **Status**: 🟢 Aktiv
- **Bestellungen**: 89 verarbeitet
- **Warteschlange**: 1 E-Mail
- **Fehler**: 0
- **Letzte E-Mail**: Order #12345 - 5000 Buttons (Bestätigt)

### **3. OEM AGENT**
**Aufgabe**: Premium Kundenbetreuung
- **Status**: 🟢 Aktiv
- **VIP Anfragen**: 45 verarbeitet
- **Warteschlange**: 0 E-Mails
- **Priorität**: Höchste Stufe

### **4. QUALITY AGENT**
**Aufgabe**: Qualitätsmanagement
- **Status**: 🟡 Beschäftigt
- **Beschwerden**: 23 verarbeitet
- **Warteschlange**: 3 E-Mails (Hoch!)
- **Eskalationen**: 1 an Management

### **5. SUPPLIER AGENT**
**Aufgabe**: Lieferantenkoordination
- **Status**: 🟢 Aktiv
- **Lieferungen**: 67 verarbeitet
- **Warteschlange**: 0 E-Mails
- **Verzögerungen**: 0

### **6. MANAGEMENT AGENT**
**Aufgabe**: Eskalations-Management
- **Status**: 🟢 Aktiv
- **Eskalationen**: 12 verarbeitet
- **Warteschlange**: 1 kritischer Fall
- **Bearbeitung**: Quality Issue Escalation #Q2401

## ⚙️ **AGENT-KONTROLLEN**

### **Für jeden Agent verfügbar:**

#### **🔄 Neustart-Button**
```
Funktionalität: Agent neu starten
API: POST /api/agents/{agent_name}/restart
Beispiel: Neustart von Info Agent
```

#### **ℹ️ Details-Button**
```
Zeigt detaillierte Informationen:
- Konfiguration
- Uptime: 2h 15m
- Capabilities: [E-Mail Triage, Routing, Auto-Reply]
- Letzte Fehler
- Performance-Metriken
```

## 📊 **ECHTZEITDATEN**

### **Live-Updates (alle 30 Sekunden):**
- ✅ Agent-Status aktualisiert
- ✅ E-Mail-Zähler erhöht sich
- ✅ Warteschlangen-Größen
- ✅ Neue E-Mail-Aktivitäten
- ✅ WebSocket-Verbindung für Echtzeitdaten

### **Update-Indikator:**
🔄 Drehendes Symbol zeigt aktive Aktualisierung

## 🎨 **STATUS-ANZEIGEN**

### **Agent-Status:**
- 🟢 **Aktiv**: Agent arbeitet normal
- 🟡 **Beschäftigt**: Hohe Warteschlange (>2 E-Mails)
- 🔴 **Inaktiv**: Agent offline oder Fehler

### **E-Mail-Status:**
- ✅ **Verarbeitet**: Erfolgreich bearbeitet
- 📤 **Weitergeleitet**: An spezialisierten Agent gesendet
- ⚠️ **Eskaliert**: An Management weitergeleitet

## 🔧 **AGENT-VERWALTUNG**

### **Neustart von Agents:**
1. **Agent auswählen** (z.B. Quality Agent)
2. **"Neustart" klicken**
3. **Bestätigung**: "Möchten Sie wirklich neu starten?"
4. **Erfolg**: "Quality Agent wurde neu gestartet"

### **Agent-Details anzeigen:**
1. **"Details" klicken**
2. **Modal öffnet sich** mit:
   - Konfiguration
   - Capabilities
   - Uptime
   - Letzte Fehler

## 📈 **METRIKEN & PERFORMANCE**

### **Pro Agent angezeigt:**
- **Verarbeitete E-Mails**: Gesamtzahl
- **Warteschlange**: Aktuelle Anzahl wartender E-Mails
- **Fehler/Eskalationen**: Problemfälle
- **Letzte Aktivitäten**: Kürzlich verarbeitete E-Mails

### **Mailbox-Metriken:**
- **Gesamt E-Mails**: 245 verarbeitet
- **Heute**: 38 neue E-Mails
- **Routing-Erfolg**: 100% weitergeleitete E-Mails

## 🚨 **PROBLEMERKENNUNG**

### **Automatische Warnungen:**
- **Hohe Warteschlange**: Quality Agent (3 E-Mails)
- **Agent überlastet**: Status wechselt zu "Beschäftigt"
- **Eskalationen**: Management Agent erhält kritische Fälle

### **Visualisierung:**
- **Rote Kennzeichnung**: Kritische Probleme
- **Gelbe Kennzeichnung**: Warnungen
- **Grüne Kennzeichnung**: Alles OK

## 🔗 **API-ENDPOINTS**

### **Verfügbare APIs:**
```
GET  /api/agents                           # Alle Agent-Daten
GET  /api/agents/{name}/details            # Agent-Details
POST /api/agents/{name}/restart            # Agent neu starten
GET  /api/agents/mailbox/{name}            # Mailbox-Details
```

### **Beispiel API-Aufruf:**
```bash
# Agent-Details abrufen
curl http://localhost:8080/api/agents/info/details

# Agent neu starten
curl -X POST http://localhost:8080/api/agents/info/restart
```

## 🎯 **PRAKTISCHE NUTZUNG**

### **Tägliche Überwachung:**
1. **Agent-Seite öffnen**: http://localhost:8080/agents
2. **Status prüfen**: Alle Agents grün?
3. **Warteschlangen**: Keine roten Warnungen?
4. **E-Mail-Flow**: Info-Mailbox zeigt Aktivität?

### **Problembehandlung:**
1. **Roten/Gelben Agent** identifizieren
2. **Details anzeigen** für Diagnose
3. **Neustart** wenn nötig
4. **Überwachen** bis Status grün

### **Performance-Optimierung:**
- **Hohe Warteschlangen** → Mehr Resources oder Neustart
- **Viele Eskalationen** → Routing-Regeln überprüfen
- **Langsame Verarbeitung** → Agent-Details prüfen

## ✨ **BESONDERE FEATURES**

### **Responsive Design:**
- ✅ **Desktop**: Vollständige Übersicht
- ✅ **Tablet**: Angepasste Darstellung
- ✅ **Mobile**: Touch-optimiert

### **Royal Courtesy Design:**
- 🎨 **Elegante Farben**: Blau-Violett Gradient
- 👑 **Professional**: Business-taugliche Optik
- 📱 **Modern**: Bootstrap 5 + FontAwesome Icons

### **Benutzerfreundlichkeit:**
- 🔄 **Auto-Refresh**: Keine manuelle Aktualisierung nötig
- 🎯 **Klare Navigation**: Intuitive Bedienung
- 📊 **Übersichtliche Metriken**: Auf einen Blick verständlich

## 🎉 **ZUSAMMENFASSUNG**

**Ihre neue Agent-Management-Webseite bietet:**

✅ **Vollständige Agent-Übersicht** - Alle 6 Agents auf einen Blick
✅ **Info-Mailbox-Monitoring** - Eingehende E-Mails verfolgen
✅ **Echtzeitdaten** - Live-Updates alle 30 Sekunden
✅ **Agent-Kontrolle** - Neustart und Details-Anzeige
✅ **Status-Visualisierung** - Sofortige Problemerkennung
✅ **E-Mail-Tracking** - Routing-Entscheidungen nachvollziehen
✅ **Professional Design** - Business-ready Oberfläche
✅ **API-Integration** - Vollständige Programmierschnittstelle

**Zugang**: http://localhost:8080/agents

**Das System ist jetzt vollständig für Agent-Management optimiert! 🚀**
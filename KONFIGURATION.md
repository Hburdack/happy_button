# 🔧 **HAPPY BUTTONS SYSTEM - KONFIGURATIONSANLEITUNG**

## **📋 SCHNELLSTART**

Das System läuft bereits! Zugang über:
- **Web-Dashboard**: http://localhost:8080
- **Konfiguration**: http://localhost:8080/config

## **🔧 HAUPTKONFIGURATIONSDATEIEN**

### **1. Globale Firmeneinstellungen**
**Datei**: `config/company.yaml`

```yaml
# KPI-Ziele anpassen
kpis:
  auto_handled_share_target: 70  # % automatisch bearbeitete E-Mails
  average_response_time_target: 1  # Stunden durchschnittliche Antwortzeit
  on_time_ship_target: 90  # % pünktliche Lieferungen

# SLA-Zeiten konfigurieren
sla:
  default_response_hours: 12    # Standard-Antwortzeit
  oem_priority_hours: 24        # OEM-Kunden Bearbeitungszeit
  escalation_hours: 4           # Eskalation nach X Stunden
```

### **2. E-Mail-Routing konfigurieren**
**Datei**: `config/units/info_agent.yaml`

#### **Routing-Regeln bearbeiten:**
```yaml
routing_rules:
  # PDF-Bestellungen automatisch weiterleiten
  - condition: "has_pdf_attachment and contains('order')"
    destination: "orders@h-bu.de"
    priority: "high"

  # OEM-Kunden priorisieren
  - condition: "sender_domain in ['oem1.com', 'oem2.com']"
    destination: "oem1@h-bu.de"
    priority: "critical"

  # Beschwerden eskalieren
  - condition: "contains('complaint', 'defect', 'quality')"
    destination: "quality@h-bu.de"
    priority: "high"
    escalate_to: "management@h-bu.de"
```

### **3. Bestellungsverarbeitung**
**Datei**: `config/units/orders_agent.yaml`

```yaml
order_processing:
  auto_confirm: true                    # Automatische Bestätigung
  require_approval_above: 50000         # Genehmigung ab 50.000 EUR
  default_lead_time_days: 14           # Standard-Lieferzeit
  expedite_available: true             # Express-Lieferung möglich

validation:
  min_order_quantity: 100              # Mindestbestellmenge
  max_order_quantity: 1000000          # Höchstbestellmenge
```

## **🌐 WEB-KONFIGURATION**

### **Dashboard-Zugang**
1. **Hauptdashboard**: http://localhost:8080
   - Systemübersicht und Echtzeitmetriken
   - Service-Status und Performance-Charts

2. **Konfigurationsseite**: http://localhost:8080/config
   - Template-Verwaltung
   - Agent-Einstellungen
   - Business-Rules

### **E-Mail-Tester**
Testen Sie das Routing direkt im Dashboard:
1. Öffnen Sie http://localhost:8080
2. Scrollen Sie zum "Email Tester"
3. Wählen Sie verschiedene Szenarien:
   - OEM-Kunde
   - Standard-Bestellung
   - Beschwerde
   - Lieferantenanfrage

## **📧 E-MAIL-ROUTING ANPASSEN**

### **Neue Routing-Regel hinzufügen:**

1. **Datei bearbeiten**: `config/units/info_agent.yaml`
2. **Neue Regel hinzufügen**:
```yaml
routing_rules:
  # Neue Regel für VIP-Kunden
  - condition: "sender_domain in ['vip-customer.com']"
    destination: "vip@h-bu.de"
    priority: "critical"
    auto_reply: "vip_welcome"
```

3. **System neu starten**:
```bash
python happy_buttons.py restart --service email_processor
```

### **Verfügbare Bedingungen:**
- `contains('text')` - E-Mail enthält Text
- `sender_domain in ['domain.com']` - Absender-Domain
- `has_pdf_attachment` - PDF-Anhang vorhanden
- `subject_contains('text')` - Betreff enthält Text
- `priority_keywords` - Prioritäts-Schlüsselwörter

## **🎨 TEMPLATES ANPASSEN**

### **Royal Courtesy Templates**
**Verzeichnis**: `templates/replies/`

#### **Neue Template erstellen:**
```yaml
# Datei: templates/replies/vip_welcome.txt
Sehr geehrte Damen und Herren,

als geschätzter VIP-Kunde bedanken wir uns für Ihr Vertrauen.
Ihre Anfrage wird mit höchster Priorität bearbeitet.

Mit freundlichen Grüßen
Happy Buttons Team
```

### **Template-Variablen:**
- `{customer_name}` - Kundenname
- `{order_number}` - Bestellnummer
- `{delivery_date}` - Liefertermin
- `{current_date}` - Aktuelles Datum

## **⚙️ SYSTEM-BEFEHLE**

### **Service-Verwaltung:**
```bash
# System starten
python happy_buttons.py start

# System stoppen
python happy_buttons.py stop

# Status prüfen
python happy_buttons.py status

# Einzelnen Service neu starten
python happy_buttons.py restart --service dashboard
python happy_buttons.py restart --service email_processor

# System überwachen
python happy_buttons.py monitor
```

### **Konfiguration neu laden:**
```bash
# E-Mail-Service neu starten (lädt Konfiguration)
python happy_buttons.py restart --service email_processor

# Dashboard neu starten
python happy_buttons.py restart --service dashboard
```

## **📊 MONITORING UND LOGS**

### **Log-Dateien:**
- `logs/happy_buttons.log` - Hauptsystem
- `logs/dashboard_stderr.log` - Dashboard-Fehler
- `logs/email_processor_stderr.log` - E-Mail-Verarbeitung

### **Echtzeitüberwachung:**
```bash
# System-Logs verfolgen
tail -f logs/happy_buttons.log

# Dashboard-Aktivität
tail -f logs/dashboard_stderr.log

# E-Mail-Verarbeitung
tail -f logs/email_processor_stderr.log
```

### **Performance-Metriken:**
- **Dashboard**: http://localhost:8080/api/metrics
- **E-Mail-Service**: http://localhost:8081/stats
- **Health-Checks**: http://localhost:8080/health

## **🚨 FEHLERBEHEBUNG**

### **Häufige Probleme:**

1. **Service startet nicht:**
```bash
# Logs prüfen
cat logs/dashboard_stderr.log
cat logs/email_processor_stderr.log

# Port-Konflikte prüfen
lsof -i :8080
lsof -i :8081
```

2. **E-Mail-Routing funktioniert nicht:**
```bash
# Konfiguration validieren
python -c "import yaml; yaml.safe_load(open('config/units/info_agent.yaml'))"

# Service neu starten
python happy_buttons.py restart --service email_processor
```

3. **Dashboard nicht erreichbar:**
```bash
# Service-Status prüfen
python happy_buttons.py status

# Dashboard neu starten
python happy_buttons.py restart --service dashboard
```

## **🔄 KONFIGURATION AKTIVIEREN**

Nach Änderungen an der Konfiguration:

1. **Relevante Services neu starten:**
```bash
# Bei E-Mail-Routing-Änderungen
python happy_buttons.py restart --service email_processor

# Bei Dashboard-Änderungen
python happy_buttons.py restart --service dashboard

# Komplettes System neu starten
python happy_buttons.py restart
```

2. **Änderungen testen:**
- Web-Dashboard: http://localhost:8080
- E-Mail-Tester verwenden
- API-Endpoints testen

## **📞 UNTERSTÜTZUNG**

Bei Problemen:
1. Logs prüfen: `logs/` Verzeichnis
2. System-Status: `python happy_buttons.py status`
3. Health-Checks: http://localhost:8080/health

**Das System ist jetzt bereit für Ihre Konfiguration! 🎉**
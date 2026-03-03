import requests
import os
import re
from pathlib import Path
from datetime import datetime

# --- Configurazione ---
URL_SITO = "https://www.unimi.it/it/corsi/laurea-triennale/scienze-psicologiche-la-prevenzione-e-la-cura"
MARCATORE = "Bando di ammissione"
FILE_DI_STATO = Path("last_status.txt")

def invia_telegram(chat_id, testo, silenzioso=False):
    token = os.environ['TELEGRAM_TOKEN']
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": testo, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": True,
        "disable_notification": silenzioso
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Errore Telegram: {e}")

def main():
    evento = os.environ.get('GITHUB_EVENT_NAME', 'unknown')
    controllo_manuale = (evento == 'workflow_dispatch')
    controllo_automatico = (evento == 'schedule')
    
    chat_lei = os.environ['CHAT_ID_LEI']
    chat_lui = os.environ['CHAT_ID_LUI']
    
    if not FILE_DI_STATO.exists():
        FILE_DI_STATO.write_text("NOT_FOUND")
    old_status = FILE_DI_STATO.read_text()

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(URL_SITO, headers=headers, timeout=15)
        html = res.text
        
        # --- RACCOLTA DATI PER LA TUA TRANQUILLITÀ ---
        status_http = res.status_code
        byte_letti = len(html)
        ora_attuale = datetime.now().strftime("%H:%M:%S")
        
        start_pos = html.lower().find(MARCATORE.lower())
        
        if start_pos == -1:
            # SEZIONE NON TROVATA: Ti avvisa sempre, anche se è l'orologio automatico!
            invia_telegram(chat_lui, f"⚠️ *ALLARME STRUTTURA SITO*\nIl sito ha risposto ({status_http}) ma non trovo più la sezione '{MARCATORE}'. Hanno rifatto la pagina?")
            return

        snippet = html[start_pos : start_pos + 3000]
        data_2026 = re.search(r'\d{1,2}/\d{1,2}/2026', snippet)
        anno_2026 = "2026/2027" in snippet
        
        if data_2026 or anno_2026:
            if old_status != "FOUND":
                msg = f"🚨 *BANDO 2026 RILEVATO!* 🚨\n\n👉 {URL_SITO}"
                invia_telegram(chat_lei, msg)
                invia_telegram(chat_lui, f"✅ Notifica bando inviata a Evelyn.\n(Byte letti: {byte_letti})")
                FILE_DI_STATO.write_text("FOUND")
        else:
            if old_status == "FOUND":
                FILE_DI_STATO.write_text("NOT_FOUND")
            
            # --- REPORT PER TE (Con Metriche Reali) ---
            dettagli = f"\n\n📊 *Dettagli Tecnici (per Tia):*\n- HTTP: {status_http} (OK)\n- HTML Letti: {byte_letti} byte\n- Target: Sezione trovata\n- Ora UTC: {ora_attuale}"
            
            if controllo_manuale:
                # A lei arriva semplice, a te con i dati
                invia_telegram(chat_lei, "🤷‍♂️ *Nessuna novità*\nIl bando 2026 non c'è ancora.")
                invia_telegram(chat_lui, f"🤷‍♂️ *Nessuna novità*{dettagli}")
            
            elif controllo_automatico:
                # Heartbeat per te ogni 2 ore, rigorosamente silenzioso
                invia_telegram(chat_lui, f"📡 *Heartbeat OK*{dettagli}", silenzioso=True)

    except Exception as e:
        # Se la connessione fallisce per qualsiasi motivo, tu lo saprai!
        invia_telegram(chat_lui, f"❌ *Errore Esecuzione Python:*\n{e}")

if __name__ == "__main__":
    main()

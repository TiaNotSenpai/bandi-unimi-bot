import requests
import os
import re
from pathlib import Path

# --- Configurazione ---
URL_SITO = "https://www.unimi.it/it/corsi/laurea-triennale/scienze-psicologiche-la-prevenzione-e-la-cura"
MARCATORE = "Bando di ammissione"
FILE_DI_STATO = Path("last_status.txt")

def invia_telegram(chat_id, testo, silenzioso=False):
    token = os.environ['TELEGRAM_TOKEN']
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # disable_notification=True fa arrivare il messaggio senza suono/vibrazione
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
    # Detect dell'evento (schedule = orologio, workflow_dispatch = bottone)
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
        
        start_pos = html.lower().find(MARCATORE.lower())
        if start_pos == -1:
            if controllo_manuale:
                invia_telegram(chat_lui, "⚠️ *Errore:* Sezione non trovata sul sito.")
            return

        snippet = html[start_pos : start_pos + 3000]
        data_2026 = re.search(r'\d{1,2}/\d{1,2}/2026', snippet)
        anno_2026 = "2026/2027" in snippet
        
        if data_2026 or anno_2026:
            if old_status != "FOUND":
                msg = f"🚨 *BANDO 2026 RILEVATO!* 🚨\n\n👉 {URL_SITO}"
                invia_telegram(chat_lei, msg)
                invia_telegram(chat_lui, "✅ Notifica inviata a Evelyn.")
                FILE_DI_STATO.write_text("FOUND")
        else:
            if old_status == "FOUND":
                FILE_DI_STATO.write_text("NOT_FOUND")
            
            # --- LOGICA DELLE CONFERME DI FUNZIONAMENTO ---
            if controllo_manuale:
                # Risposta a te e a lei per il comando manuale (con suono)
                msg_negativo = "🤷‍♂️ *Nessuna novità*\nIl bando 2026 non c'è ancora."
                invia_telegram(chat_lui, msg_negativo)
                invia_telegram(chat_lei, msg_negativo)
            
            elif controllo_automatico:
                # Conferma di vita SOLO A TE e SILENZIOSA ogni 2 ore
                msg_heartbeat = "📡 *Heartbeat:* Controllo automatico OK. Nulla di nuovo."
                invia_telegram(chat_lui, msg_heartbeat, silenzioso=True)

    except Exception as e:
        if controllo_manuale:
            invia_telegram(chat_lui, f"❌ Errore: {e}")

if __name__ == "__main__":
    main()

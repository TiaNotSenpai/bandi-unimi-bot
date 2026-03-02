import requests
import os
import re
from pathlib import Path

# --- Configurazione ---
URL_SITO = "https://www.unimi.it/it/corsi/laurea-triennale/scienze-psicologiche-la-prevenzione-e-la-cura"
MARCATORE = "Bando di ammissione"
FILE_DI_STATO = Path("last_status.txt")

def invia_telegram(chat_id, testo):
    token = os.environ['TELEGRAM_TOKEN']
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # disable_web_page_preview=True evita che il bot carichi l'enorme immagine di copertina dell'UniMi in chat
    payload = {"chat_id": chat_id, "text": testo, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Errore Telegram: {e}")

def main():
    evento = os.environ.get('GITHUB_EVENT_NAME', 'unknown')
    controllo_manuale = (evento == 'workflow_dispatch')
    
    chat_lei = os.environ['CHAT_ID_LEI']
    chat_lui = os.environ['CHAT_ID_LUI']
    
    if not FILE_DI_STATO.exists():
        FILE_DI_STATO.write_text("NOT_FOUND")
    
    old_status = FILE_DI_STATO.read_text()


    try:
        # 1. Scarichiamo il sito (mascherati da browser normale per non farsi bloccare)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(URL_SITO, headers=headers, timeout=15)
        html = res.text
        
        # 2. Troviamo la sezione esatta (ignorando maiuscole/minuscole per sicurezza)
        start_pos = html.lower().find(MARCATORE.lower())
        
        if start_pos == -1:
            print(f"Sezione '{MARCATORE}' non trovata. Hanno cambiato il template del sito?")
            if controllo_manuale:
                invia_telegram(chat_lui, "⚠️ *Attenzione:* Non trovo più la scritta 'Bando di ammissione' sul sito UniMi. Controllare la pagina.")
            return

        # Tagliamo un pezzo di 3000 caratteri da quel punto in poi
        snippet = html[start_pos : start_pos + 3000]
        
        # 3. RICERCA CHIRURGICA CON REGEX
        # \d{1,2} significa "1 o 2 numeri". Quindi trova 13/03/2026 ma NON 2025/2026
        data_2026 = re.search(r'\d{1,2}/\d{1,2}/2026', snippet)
        
        # In alternativa, se cambiano solo l'intestazione dell'anno accademico
        anno_2026 = "2026/2027" in snippet
        
        if data_2026 or anno_2026:
            # BANDO TROVATO!
            if old_status != "FOUND":
                msg = f"🚨 *BANDO 2026 RILEVATO!* 🚨\n\nLe date sono state aggiornate!\n👉 {URL_SITO}"
                invia_telegram(chat_lei, msg)
                invia_telegram(chat_lui, "✅ *System Alert:* Notifica di bando inviata a Evelyn.")
                FILE_DI_STATO.write_text("FOUND")
            else:
                if controllo_manuale:
                    invia_telegram(chat_lui, "ℹ️ *Controllo Manuale:* Il bando 2026 è GIA' online, notifica già inviata in passato.")
                    invia_telegram(chat_lei, "ℹ️ *Controllo Manuale:* Il bando 2026 è GIA' online, notifica già inviata in passato.")
        else:
            # BANDO NON TROVATO
            if old_status == "FOUND":
                FILE_DI_STATO.write_text("NOT_FOUND")
            
            if controllo_manuale:
                # Questo è il tuo vecchio /check
                msg_negativo = "🤷‍♂️ *Nessuna novità*\n\nHo appena ispezionato il sito UniMi: del bando 2026 per ora non c'è traccia. Rilassatevi!"
                invia_telegram(chat_lui, msg_negativo)
                invia_telegram(chat_lei, msg_negativo)
            else:
                print("Controllo orario automatico: Nessun bando rilevato. Il bot resta in silenzio.")
            elif controllo_automatico:
                # Conferma di vita SOLO A TE e SILENZIOSA ogni 2 ore
                msg_heartbeat = "📡 *Heartbeat:* Controllo automatico OK. Nulla di nuovo."
                invia_telegram(chat_lui, msg_heartbeat, silenzioso=True)

    except Exception as e:
        print(f"Errore script: {e}")
        if controllo_manuale:
            invia_telegram(chat_lui, f"❌ *Errore Tecnico (Server GitHub):* {e}")

if __name__ == "__main__":
    main()

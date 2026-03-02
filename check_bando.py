import requests
import os
from pathlib import Path

# --- Configurazione ---
URL_SITO = "https://www.unimi.it/it/corsi/laurea-triennale/scienze-psicologiche-la-prevenzione-e-la-cura"
PAROLE_CHIAVE =["/2026", "2026/2027"] 
MARCATORE_SEZIONE = "Bando di ammissione"
FILE_DI_STATO = Path("last_status.txt")

def invia_telegram(chat_id, testo):
    token = os.environ['TELEGRAM_TOKEN']
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": testo, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Errore invio a {chat_id}: {e}")

def main():
    # Scopriamo se lo script è partito in automatico o se hai premuto il bottone
    evento = os.environ.get('GITHUB_EVENT_NAME', 'unknown')
    controllo_manuale = (evento == 'workflow_dispatch')
    
    chat_lei = os.environ['CHAT_ID_LEI']
    chat_lui = os.environ['CHAT_ID_LUI']
    
    old_status = FILE_DI_STATO.read_text() if FILE_DI_STATO.exists() else "NOT_FOUND"

    try:
        res = requests.get(URL_SITO, timeout=15)
        html = res.text
        
        start_pos = html.find(MARCATORE_SEZIONE)
        if start_pos == -1:
            print("Sezione 'Bando di ammissione' non trovata.")
            if controllo_manuale:
                invia_telegram(chat_lui, "⚠️ *Errore Controllo:* Sezione bando non trovata nel sito dell'UniMi.")
            return

        snippet = html[start_pos : start_pos + 2500]
        
        # Controlliamo se c'è il bando
        if any(parola in snippet for parola in PAROLE_CHIAVE):
            if old_status != "FOUND":
                msg = f"🚨 *BANDO 2026 RILEVATO!* 🚨\n\nLe date sono state aggiornate!\n👉 {URL_SITO}"
                invia_telegram(chat_lei, msg)
                invia_telegram(chat_lui, "✅ *System Alert:* Notifica di bando inviata a Evelyn.")
                FILE_DI_STATO.write_text("FOUND")
            else:
                if controllo_manuale:
                    invia_telegram(chat_lui, "ℹ️ *Controllo Manuale:* Il bando 2026 è GIA' online.")
                    invia_telegram(chat_lei, "ℹ️ *Controllo Manuale:* Il bando 2026 è GIA' online.")
        else:
            # NON c'è il bando
            if old_status == "FOUND":
                FILE_DI_STATO.write_text("NOT_FOUND")
            
            # SE HAI PREMUTO IL BOTTONE: Invia il report negativo a entrambi!
            if controllo_manuale:
                msg_negativo = "🤷‍♂️ *Nessuna novità (Controllo Manuale)*\n\nHo appena ispezionato il sito: del bando 2026 per ora non c'è traccia. Rilassatevi!"
                invia_telegram(chat_lui, msg_negativo)
                invia_telegram(chat_lei, msg_negativo)
            else:
                # Se è l'orologio delle 2 ore a girare, stampa solo nel log silenzioso di GitHub
                print("Controllo orario silenzioso: Nessun bando rilevato.")

    except Exception as e:
        print(f"Errore durante il controllo del sito: {e}")
        if controllo_manuale:
            invia_telegram(chat_lui, f"❌ *Errore Tecnico:* {e}")

if __name__ == "__main__":
    main()

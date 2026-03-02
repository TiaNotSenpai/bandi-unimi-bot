import requests
import os

# --- Configurazione ---
URL_SITO = "https://www.unimi.it/it/corsi/laurea-triennale/scienze-psicologiche-la-prevenzione-e-la-cura"
PAROLE_CHIAVE = ["/2026", "2026/2027"] # Cerca una data o l'anno accademico
MARCATORE_SEZIONE = "Bando di ammissione"

def invia_telegram(chat_id, testo):
    token = os.environ['TELEGRAM_TOKEN']
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": testo, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def main():
    try:
        res = requests.get(URL_SITO, timeout=15)
        html = res.text
        
        # Leggiamo lo stato precedente
        try:
            with open("last_status.txt", "r") as f:
                old_status = f.read()
        except FileNotFoundError:
            old_status = "NOT_FOUND"

        # Cerchiamo solo nella sezione giusta
        start_pos = html.find(MARCATORE_SEZIONE)
        if start_pos != -1:
            snippet = html[start_pos : start_pos + 2000]
            
            if any(parola in snippet for parola in PAROLE_CHIAVE):
                # Trovato!
                if old_status != "FOUND":
                    msg = f"🚨 *BANDO 2026 RILEVATO!* 🚨\n\nControlla subito: {URL_SITO}"
                    invia_telegram(os.environ['CHAT_ID_LEI'], msg)
                    invia_telegram(os.environ['CHAT_ID_LUI'], "✅ Notifica bando inviata.")
                    
                    # Salviamo il nuovo stato
                    with open("last_status.txt", "w") as f:
                        f.write("FOUND")
            else:
                # Non trovato
                print("Nessun bando 2026 rilevato.")
                # Se prima c'era e ora non più, resetta lo stato
                if old_status == "FOUND":
                     with open("last_status.txt", "w") as f:
                        f.write("NOT_FOUND")
        else:
            print("Sezione 'Bando di ammissione' non trovata.")

    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    main()

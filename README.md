# Esame Introduzione alle Applicazioni Web di giugno 2025

**Importante:** non prendere questo file come linee guida assolute per l'esame, non posso sapere se i contenuti del corso o le direttive per la creazione dei progetti sono cambiate da quando ho sostenuto io l'esame, nel dubbio chiedi chiarimenti al professore (che si è sempre dimostrato disponibile per domande o chiarimenti sul gruppo Telegram ufficiale del corso).

Elaborato per l'esame di Introduzione alle Applicazioni Web di [giugno 2025](https://docs.google.com/document/d/1P5qTU0oU2jlxHHxbXlDaB2t9CdrUOKS0w3HIMpGg9QY/edit?tab=t.0).

Il progetto nella repo è uguale a quello portato all'esame (come elaborato andava caricato il progetto con dei dati già inseriti, nella repo non sono presenti ma nelle release ho caricato una versione con qualche dato già aggiunto), tranne per un piccolo bugfix in un if-else e in un form nella pagina gestione (comunque senza stravolgimenti o funzionalità aggiunte dopo l'esame).

Il corso non prevede lezioni su JavaScript, ma era possibile utilizzare (oltre al JS che Bootstrap usa "implicitamente" per far funzionare alcuni elementi) piccoli script, a patto di sapere cosa faccesse il codice e che non venisse utilizzato per svolgere compiti di cui si sarebbe dovuto occupare il backend; nel mio progetto ho usato solo una riga di JS per far funzionare il pulsante chiudi nei messaggi a comparsa.

Era inoltre possibile utilizzare moduli Python esterni per arricchire le funzionalità, nel mio caso ho utilizzato [PyOTP](https://pypi.org/project/pyotp/) (gli altri tre moduli sono trattati nel corso); inoltre era consigliato anche l'utilizzo di [Pillow](https://pypi.org/project/pillow/) per ridimensionare le immagini al momento del caricamento, ma non l'ho implementato per mancanza di tempo.

Per comodità personale, ho inserito i miei moduli in una sottocartella, e ho implementato l'accesso ai dati nel database tramite classi, cose che però non erano richieste o trattate nel corso (tantomeno vengono trattati ORM).

Era anche possibile aggiungere funzionalità extra a piacimento, ma è stato anche sottolineato come sarebbe stato valutato solo quanto richiesto dalla traccia (e, detto sinceramente, dato il tempo necessario per sviluppare il progetto con tutti i requisiti della traccia, che si è rilevata essere più complessa di quanto sembrasse a prima vista, consiglio vivamente di implementare i requisiti prima di arricchire).

Nella release, le immagini utilizzate sono state create o scattate da me.

### Note sulla tranccia
"Ogni partecipante può acquistare un solo tipo di biglietto per edizione" poteva essere interpretato sia come un limite di un biglietto in assoluto per partecipante, sia come limite di una tipologia di biglietto ma con possibilità di acquistarne di più tipi (evitando però sovrapposizioni); io l'ho interpretata come limite di un biglietto in assoluto.

Per gli artisti, era possibile imporre un limite assoluto di una voce nel database per artista, indipendentemente dallo status di pubblicazione, o anche prevedere l'inserimento di bozze multiple per un singolo artista ma consentendo la pubblicazione solamente di una; io l'ho interpretata come limite assoluto di una voce per artista.

### Note sulle funzionalità
È possibile modificare il valore `MAX_TICKETS_PER_DAY` in *modules/values.py* per vedere cosa succede in caso di biglietti esauriti in una giornata (il comportamento in caso di impostazione di un valore superiore al numero di biglietti già venduti o "errato" (0, numeri non interi positivi, tipi non interi, etc.) in una giornata non è stato testato).

La funzione OTP è stata testata con [Aegis](https://getaegis.app/) (ma qualsiasi applicazione per l'autenticazione a due fattori dovrebbe funzionare), la chiave segreta si trova come `OTP_KEY` in *modules/values.py*.

Come richiesto dalla traccia, i controlli avvengono sia sul frontend (quando possibile puramente con HTML) che sul backend; vi invito quindi a verificare cosa succede nei casi limite (rimozione di parametri *required* o altri vincoli dall'HTML, inserimento forzato di valori non validi nei form, tentativo di modifica/eliminazione di una performance dopo averla pubblicata da un'altra scheda, tentativo di modificare o visualizzare una performance in stato di bozza appartenente a un altro organizzatore, tentativo di acquisto di un biglietto dopo averne comprato già uno da un'altra scheda, etc.).

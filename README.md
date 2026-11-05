# IT Helpdesk MAS

Sistem multi-agent (MAS) construit cu **Google ADK** care automatizeaza
triajul si rezolvarea de nivel 1 a tichetelor IT dintr-o organizatie.

## Problema

Departamentul IT dintr-o companie primeste zilnic cereri repetitive
(resetare parola, probleme wifi, instalare software etc.) pe care un om
trebuie sa le citeasca, sa le clasifice si sa le rezolve sau sa le rutheze
manual catre tehnicianul potrivit. Sistemul de fata automatizeaza acest flux.

## Arhitectura

```
Utilizator
    |
    v
Coordinator (root_agent)  --- transfera automat, mereu, orice cerere noua
    |
    v
Triage Agent               --- clasifica (categorie + prioritate)
    |                           tool: log_ticket
    | transfera automat cu contextul (ticket_id, categorie)
    v
Resolution Agent           --- cauta solutie sau escaladeaza
    |                           tools: search_knowledge_base, escalate_to_human
    | transfera automat (raspunsul e salvat in state: resolution_response)
    v
Insights Agent              --- verifica daca aceasta categorie a devenit
                                 recurenta la nivel de organizatie
                                 tool: analyze_recurring_issues
```

- **Coordinator**: singurul rol e sa initieze fluxul, transferand mereu catre
  `triage_agent`. Nu raspunde niciodata direct la o problema tehnica.
- **Triage Agent**: clasifica cererea in `hardware` / `software` / `acces` /
  `retea`, stabileste prioritatea, o inregistreaza (`log_ticket`), apoi
  transfera catre `resolution_agent`.
- **Resolution Agent**: cauta o solutie cunoscuta (`search_knowledge_base`).
  Daca gaseste una cu incredere ridicata o ofera direct; altfel escaladeaza
  (`escalate_to_human`) catre un tehnician uman. Apoi transfera catre
  `insights_agent`.
- **Insights Agent**: nu se ocupa de tichetul individual, ci verifica daca
  ACEASTA categorie de probleme a aparut de mai multe ori in organizatie
  (`analyze_recurring_issues`). Daca da, adauga o notă separata pentru
  echipa IT cu o recomandare sistemica (ex: upgrade infrastructura wifi).
  Asta transforma sistemul dintr-un simplu "rezolvator de tichete" intr-unul
  care detecteaza tipare la nivel de organizatie.

Criteriul de selectie a agentilor e descris explicit in `instruction`-ul
fiecarui agent (vezi `agent.py`) — fiecare agent transfera mai departe catre
urmatorul din lant dupa ce isi termina partea lui.

## Cum rulezi local (pe laptopul tau)

1. Ai nevoie de o cheie API gratuita Google AI Studio:
   https://aistudio.google.com/apikey

2. Instaleaza dependinta:
   ```bash
   pip install -r requirements.txt
   ```

3. Copiaza `it_helpdesk_agent/.env.example` in `it_helpdesk_agent/.env` si
   pune cheia ta:
   ```bash
   cp it_helpdesk_agent/.env.example it_helpdesk_agent/.env
   # editeaza .env si pune GOOGLE_API_KEY=cheia_ta
   ```

4. Din directorul `it_helpdesk_mas` (parintele folderului agentului), ruleaza:
   ```bash
   adk web
   ```

5. Se deschide automat interfata grafica (implicit pe
   `http://localhost:8000`). Selecteaza `it_helpdesk_agent` din dropdown si
   incepe conversatia.

## Exemple de utilizare

- "Nu imi merge wifi-ul de doua ore, nu pot lucra deloc" → triaj: `retea`,
  prioritate `ridicata` → resolution gaseste solutie in KB → raspuns direct.
- "As vrea sa instalez Photoshop" → triaj: `software` → solutie din KB.
- "Mi s-a stricat monitorul extern" → triaj: `hardware` → nu exista solutie
  in KB → escaladare automata catre tehnician.
- "Mi-am uitat parola de la cont" → triaj: `acces` → solutie din KB.

**Pentru a demonstra si detectarea problemelor recurente** (insights_agent):
trimite DOUA mesaje diferite din aceeasi categorie in aceeasi sesiune de
`adk web` (fara sa apesi "New Session" intre ele), de exemplu:
1. "Nu imi merge wifi-ul"
2. "Wifi-ul cade foarte des azi"

La al doilea mesaj, `insights_agent` ar trebui sa adauge o "Nota interna
pentru echipa IT" semnaland ca s-au inregistrat 2 tichete de categoria
`retea` si sugerand un upgrade de infrastructura. Asta e cel mai puternic
moment de demo — arata ca sistemul nu doar rezolva cazuri individuale, ci
identifica tendinte la nivel de organizatie.

## Posibile extinderi

- Adauga un al treilea agent `feedback_agent` care cere un scurt feedback
  dupa rezolvare si il salveaza.
- Conecteaza `log_ticket` la un fisier JSON real in loc de lista in memorie,
  ca sa arati persistenta intre rulari.
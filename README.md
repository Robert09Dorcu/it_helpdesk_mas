# IT Helpdesk MAS — Provocarea ITSS Summer School 2026

Sistem multi-agent (MAS) construit cu **Google ADK** care automatizeaza
triajul si rezolvarea de nivel 1 a tichetelor IT dintr-o organizatie.

## Problema recurenta aleasa

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
  care detecteaza tipare — exact tema provocarii ("problema recurenta").

Criteriul de selectie a agentilor e descris explicit in `instruction`-ul
fiecarui agent (vezi `agent.py`) — fiecare agent transfera mai departe catre
urmatorul din lant dupa ce isi termina partea lui.

## Cum rulezi local (pe laptopul tau)

1. Ai nevoie de o cheie API gratuita Google AI Studio:
   https://aistudio.google.com/apikey

2. Instaleaza dependinta (ai deja Python pe Ubuntu):
   ```bash
   pip install google-adk --break-system-packages
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

## Exemple de mesaje pentru demo

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

## Ce sa arati/spui la prezentare (mapat pe cerintele slide-ului)

- **Cum sunt apelati agentii**: coordinator → triage_agent → resolution_agent
  → insights_agent, prin transfer automat (`transfer_to_agent`), vizibil live
  in tab-ul "Events" din `adk web`.
- **Criteriile de selectie pentru fiecare agent**: regulile sunt scrise
  explicit in instructiunile fiecarui agent — fiecare agent transfera mai
  departe catre urmatorul din lant dupa ce isi termina partea lui.
- **Tool-urile activate in fiecare etapa**: `log_ticket` (triage),
  `search_knowledge_base` + `escalate_to_human` (resolution),
  `analyze_recurring_issues` (insights) — vizibile ca function calls in
  "Events".
- **Componentele arhitecturale**: 4 agenti (1 coordonator + 3 specializati),
  o baza de cunostinte simulata, un jurnal de tichete simulat, un mecanism
  de detectare a tiparelor recurente.
- **Fluxul de comunicare**: utilizator → coordinator → triage (clasificare +
  logare) → resolution (cautare solutie / escaladare) → insights (detectare
  recurenta) → raspuns final catre utilizator, plus nota interna pentru IT
  daca e cazul.
- **De ce e relevant pentru "problema recurenta" din cerinta**: sistemul nu
  se opreste la rezolvarea unui singur tichet — `insights_agent` inchide
  bucla, transformand date individuale in informatie utila pentru
  organizatie (exact "invatarea" din agentic AI, spre deosebire de un tool
  traditional care doar raspunde comenzilor).

## Extindere rapida (daca vrei sa impresionezi si mai mult)

- Adauga un al treilea agent `feedback_agent` care cere un scurt feedback
  dupa rezolvare si il salveaza.
- Conecteaza `log_ticket` la un fisier JSON real in loc de lista in memorie,
  ca sa arati persistenta intre rulari.
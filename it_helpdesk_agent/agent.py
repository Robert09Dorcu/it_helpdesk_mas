"""
IT Helpdesk Multi-Agent System
--------------------------------
Provocare tehnica: implementeaza o solutie bazata pe Agentic AI (Google ADK)
care rezolva o problema recurenta dintr-o organizatie.

Problema aleasa: departamentul IT dintr-o companie primeste zilnic zeci de
tichete repetitive (resetare parola, probleme wifi, instalare software etc.)
pe care un om trebuie sa le citeasca, sa le clasifice si sa le rezolve sau
sa le trimita catre tehnicianul potrivit. Acest sistem automatizeaza triajul
si rezolvarea de nivel 1 a acestor cereri.

Arhitectura (3 agenti + un coordonator):
    Coordinator (root_agent)
        -> Triage Agent    : clasifica cererea si o logheaza
        -> Resolution Agent: cauta o solutie in baza de cunostinte sau escaladeaza
        -> Insights Agent  : verifica daca aceasta categorie de problema a
                              devenit recurenta in organizatie si, daca da,
                              semnaleaza acest lucru echipei IT (nu doar
                              rezolva cazul individual, ci detecteaza tiparul)

Ruleaza local cu:
    adk web
din directorul parinte (it_helpdesk_mas), apoi deschide interfata grafica
in browser. Acolo poti observa live: transferul intre agenti, tool call-urile
facute de fiecare agent si raspunsurile lor (tab-ul "Events").
"""

from google.adk.agents import Agent

MODEL = "gemini-3.5-flash-lite"

# --------------------------------------------------------------------------
# "Baze de date" simulate (in memorie) - simuleaza sistemele interne
# ale organizatiei (ticketing system + knowledge base)
# --------------------------------------------------------------------------

TICKET_LOG: list[dict] = []

KNOWLEDGE_BASE = {
    "acces": {
        "keywords": ["parola", "cont", "login", "blocat", "acces"],
        "solution": (
            "Mergi pe portalul intern 'reset.compania.ro', introdu adresa de "
            "email si urmeaza link-ul primit pentru resetarea parolei. "
            "Contul se deblocheaza automat dupa resetare."
        ),
    },
    "retea": {
        "keywords": ["wifi", "internet", "retea", "conexiune", "vpn"],
        "solution": (
            "Conecteaza-te la reteaua 'CORP-SECURE' folosind acelasi user si "
            "parola de la calculator. Daca problema persista, reporneste "
            "routerul de birou din camera de comunicatii de la etajul tau."
        ),
    },
    "software": {
        "keywords": ["instalare", "aplicatie", "program", "licenta", "update"],
        "solution": (
            "Aplicatiile aprobate de companie pot fi instalate direct din "
            "Software Center (icon-ul din system tray). Cauta numele "
            "aplicatiei si apasa 'Install'."
        ),
    },
    "hardware": {
        "keywords": ["laptop", "monitor", "tastatura", "mouse", "imprimanta"],
        "solution": None,  # nu exista o solutie standard -> se escaladeaza mereu
    },
}

# Praguri si recomandari pentru detectarea problemelor recurente la nivel
# de organizatie (nu doar per angajat individual)
RECURRING_THRESHOLD = 2

SYSTEMIC_RECOMMENDATIONS = {
    "retea": "upgrade-ul infrastructurii de retea/wifi la nivelul biroului",
    "software": "crearea unei imagini standard cu aplicatiile cele mai cerute",
    "acces": "implementarea unui sistem de auto-reset al parolei (SSO)",
    "hardware": "inventarierea si inlocuirea preventiva a echipamentelor vechi",
}


# --------------------------------------------------------------------------
# Tool-uri (functii Python simple; ADK le transforma automat in FunctionTool)
# --------------------------------------------------------------------------

def log_ticket(description: str, category: str, priority: str) -> dict:
    """Inregistreaza un tichet nou in sistemul de ticketing al organizatiei.

    Args:
        description: descrierea problemei asa cum a fost raportata de angajat.
        category: una dintre 'hardware', 'software', 'acces', 'retea'.
        priority: una dintre 'scazuta', 'medie', 'ridicata', 'critica'.

    Returns:
        Un dict cu id-ul generat pentru tichet si statusul operatiei.
    """
    ticket_id = f"TCK-{len(TICKET_LOG) + 1:04d}"
    TICKET_LOG.append(
        {
            "ticket_id": ticket_id,
            "description": description,
            "category": category,
            "priority": priority,
            "status": "inregistrat",
        }
    )
    return {"ticket_id": ticket_id, "status": "inregistrat"}


def search_knowledge_base(category: str, keywords: str) -> dict:
    """Cauta in baza de cunostinte interna o solutie cunoscuta pentru o cerere.

    Args:
        category: categoria tichetului (hardware, software, acces, retea).
        keywords: cuvinte cheie extrase din cererea utilizatorului.

    Returns:
        Un dict cu found (bool), solution (str sau None) si confidence
        (nivelul de incredere in solutia gasita).
    """
    entry = KNOWLEDGE_BASE.get(category.lower().strip())
    if not entry or not entry["solution"]:
        return {"found": False, "solution": None, "confidence": "scazuta"}

    keyword_hit = any(k in keywords.lower() for k in entry["keywords"])
    if keyword_hit:
        return {"found": True, "solution": entry["solution"], "confidence": "ridicata"}
    return {"found": False, "solution": None, "confidence": "scazuta"}


def escalate_to_human(ticket_id: str, reason: str) -> dict:
    """Escaladeaza tichetul catre un tehnician IT uman.

    Se foloseste atunci cand agentul de rezolvare nu gaseste o solutie
    automata cu incredere suficienta.

    Args:
        ticket_id: id-ul tichetului generat anterior de log_ticket.
        reason: motivul pentru care tichetul necesita interventie umana.

    Returns:
        Un dict cu statusul escaladarii.
    """
    for ticket in TICKET_LOG:
        if ticket["ticket_id"] == ticket_id:
            ticket["status"] = "escaladat"
    return {
        "ticket_id": ticket_id,
        "status": "escaladat",
        "reason": reason,
        "message": "Un tehnician uman va contacta angajatul in cel mai scurt timp.",
    }


def analyze_recurring_issues(category: str) -> dict:
    """Verifica daca o categorie de probleme a devenit recurenta in organizatie.

    Numara cate tichete din TOATE conversatiile de pana acum (nu doar cea
    curenta) apartin aceleiasi categorii. Daca numarul depaseste un prag,
    problema nu mai e un caz izolat, ci un semnal ca ceva la nivel de
    infrastructura/proces trebuie schimbat.

    Args:
        category: categoria tichetului curent (hardware, software, acces, retea).

    Returns:
        Un dict cu category, count (numarul de tichete din aceasta categorie),
        is_recurring (bool) si recommendation (str sau None).
    """
    category = category.lower().strip()
    count = sum(1 for t in TICKET_LOG if t["category"].lower() == category)
    is_recurring = count >= RECURRING_THRESHOLD
    recommendation = SYSTEMIC_RECOMMENDATIONS.get(category) if is_recurring else None
    return {
        "category": category,
        "count": count,
        "is_recurring": is_recurring,
        "recommendation": recommendation,
    }


# --------------------------------------------------------------------------
# Agentul de triaj
# --------------------------------------------------------------------------

triage_agent = Agent(
    name="triage_agent",
    model=MODEL,
    description=(
        "Clasifica cererile IT primite de la angajati pe categorie si "
        "prioritate, apoi le inregistreaza in sistemul de ticketing."
    ),
    instruction="""
Esti agentul de TRIAJ al departamentului IT dintr-o companie.

Cand primesti o cerere de la un angajat:
1. Clasific-o intr-una din categoriile: hardware, software, acces, retea.
2. Stabileste prioritatea: scazuta, medie, ridicata sau critica
   (ex: "nu pot lucra deloc" = ridicata/critica; intrebare generala = scazuta).
3. Apeleaza tool-ul log_ticket cu descrierea, categoria si prioritatea stabilite.
4. Dupa ce ai id-ul tichetului, transfera automat conversatia catre
   `resolution_agent`, mentionand id-ul tichetului si categoria stabilita,
   pentru ca acesta sa continue rezolvarea.

Nu incerca sa rezolvi tu problema tehnica - rolul tau este strict clasificarea
si inregistrarea.
""",
    tools=[log_ticket],
)


# --------------------------------------------------------------------------
# Agentul de rezolvare
# --------------------------------------------------------------------------

resolution_agent = Agent(
    name="resolution_agent",
    model=MODEL,
    description=(
        "Cauta o solutie cunoscuta pentru un tichet deja clasificat; daca nu "
        "gaseste una sigura, escaladeaza cererea catre un tehnician uman."
    ),
    instruction="""
Esti agentul de REZOLVARE al departamentului IT.

Primesti de la triage_agent un tichet deja clasificat (id, categorie,
descriere/cuvinte cheie).

1. Apeleaza tool-ul search_knowledge_base cu categoria si cuvintele cheie
   relevante din cererea originala a angajatului.
2. Daca found=True si confidence='ridicata', formuleaza un raspuns prietenos
   catre angajat cu solutia gasita, mentionand id-ul tichetului.
3. Daca found=False (nu exista solutie cunoscuta sau incredere insuficienta),
   apeleaza tool-ul escalate_to_human cu id-ul tichetului si un motiv scurt,
   apoi formuleaza un raspuns catre angajat anuntand escaladarea.
4. Dupa ce ai formulat raspunsul (fie solutie, fie escaladare), transfera
   automat conversatia catre `insights_agent`, mentionand categoria
   tichetului curent, pentru o ultima verificare la nivel de organizatie.

Nu inventa niciodata o solutie tehnica care nu vine din knowledge base -
daca nu exista, escaladeaza. Nu incheia tu conversatia - transfera mereu
catre insights_agent la final.
""",
    tools=[search_knowledge_base, escalate_to_human],
)


# --------------------------------------------------------------------------
# Agentul de insights - detecteaza probleme recurente la nivel de organizatie
# --------------------------------------------------------------------------

insights_agent = Agent(
    name="insights_agent",
    model=MODEL,
    description=(
        "Verifica daca o categorie de tichete a devenit recurenta in "
        "organizatie si semnaleaza acest lucru echipei IT, pe langa "
        "rezolvarea cazului individual."
    ),
    instruction="""
Esti agentul de INSIGHTS al departamentului IT.

resolution_agent a formulat deja, mai sus in aceasta conversatie, raspunsul
final catre angajat (solutie sau escaladare).

Pasii tai:
1. Apeleaza tool-ul analyze_recurring_issues cu categoria tichetului curent
   (cea stabilita anterior de triage_agent in aceasta conversatie).
2. Repeta EXACT raspunsul pe care resolution_agent l-a formulat deja mai sus
   pentru angajat, fara sa il modifici sau sa il rescrii.
3. Daca is_recurring este True, adauga DUPA acel raspuns o sectiune separata,
   clar marcata, de tipul "Nota interna pentru echipa IT:", in care mentionezi
   cate tichete de aceasta categorie au fost inregistrate pana acum si
   recomandarea primita de la tool.
4. Daca is_recurring este False, nu adauga nimic in plus.

Nu inventa recomandari proprii - foloseste doar informatia primita de la
tool. Rolul tau e sa detectezi tipare, nu sa rezolvi tichete individuale.
""",
    tools=[analyze_recurring_issues],
)


# --------------------------------------------------------------------------
# Coordonatorul (root agent) - orchestreaza cei doi agenti
# --------------------------------------------------------------------------

root_agent = Agent(
    name="helpdesk_coordinator",
    model=MODEL,
    description=(
        "Punctul de intrare al sistemului de IT Helpdesk automatizat. "
        "Primeste cererea angajatului si o directioneaza catre agentii "
        "specializati."
    ),
    instruction="""
Esti coordonatorul sistemului de IT Helpdesk automatizat al unei companii.

Regula de delegare (criteriul de selectie a agentilor):
- Orice cerere noua, nerezolvata inca, trebuie transferata IMEDIAT catre
  `triage_agent`, pentru clasificare si inregistrare in sistem.
- `triage_agent` va transfera mai departe automat catre `resolution_agent`
  dupa ce a clasificat si inregistrat tichetul.
- `resolution_agent` va transfera mai departe automat catre `insights_agent`
  dupa ce a formulat raspunsul, pentru verificarea problemelor recurente.
- Tu nu incerci niciodata sa clasifici, sa rezolvi sau sa raspunzi direct
  la o problema tehnica - rolul tau este doar sa initiezi fluxul.

Salut-te scurt cu angajatul daca e nevoie, apoi transfera conversatia catre
triage_agent.
""",
    sub_agents=[triage_agent, resolution_agent, insights_agent],
)
import re
from datetime import datetime


def extract_subscription(email_subject, email_body, sender="unknown"):
    text = f"{email_subject}\n{email_body}"
    lowered = text.lower()

    subscription_keywords = [
        "subscription", "renewal", "renew", "invoice", "billing",
        "payment", "receipt", "plan", "membership", "auto-renew", "autorenew",
        "abonnement", "renouvellement", "renouveler", "facture", "paiement",
        "renouvelle", "renouvelé"
    ]

    if not any(keyword in lowered for keyword in subscription_keywords):
        return None

    known_services = [
        "Microsoft 365", "Adobe Creative Cloud", "Canva Enterprise",
        "AWS", "Amazon Web Services", "Slack Business+", "Zoom",
        "Google Workspace", "Dropbox", "Notion", "Djezzy Business", "Djezzy",
        "Algérie Télécom Fibre Pro", "Algérie Télécom"
    ]

    service = None
    for name in known_services:
        if name.lower() in lowered:
            service = name
            break

    if service is None:
        subject_match = re.search(
            r"(?:your|renewal|subscription|invoice|billing|abonnement|renouvellement|facture)\s+([A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9 .&+\-]{2,50})",
            email_subject,
            re.IGNORECASE,
        )
        if subject_match:
            service = subject_match.group(1).strip()

    service = service or "Unknown Service"

    cost = None
    currency = None
    cost_patterns = [
        r"(\d[\d,\.\s]*)\s*(DZD|DA|USD|EUR|\$|€)",
        r"(DZD|DA|USD|EUR|\$|€)\s*(\d[\d,\.\s]*)",
    ]

    for pattern in cost_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        groups = match.groups()
        if groups[0].replace(",", "").replace(".", "").replace(" ", "").isdigit():
            raw_cost, raw_currency = groups[0], groups[1]
        else:
            raw_currency, raw_cost = groups[0], groups[1]

        raw_cost = raw_cost.replace(" ", "")
        if "," in raw_cost and "." not in raw_cost:
            raw_cost = raw_cost.replace(",", "")
        try:
            cost = float(raw_cost)
            currency = {"DA": "DZD", "$": "USD", "€": "EUR"}.get(raw_currency.upper(), raw_currency.upper())
        except ValueError:
            pass
        if cost is not None:
            break

    renewal_date = None
    date_patterns = [
        r"(\d{4}-\d{2}-\d{2})",
        r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})",
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})",
    ]

    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        try:
            if len(match.groups()) == 1:
                renewal_date = datetime.strptime(match.group(1), "%Y-%m-%d").strftime("%Y-%m-%d")
            elif match.group(1).isalpha():
                renewal_date = datetime.strptime(
                    f"{match.group(1)} {match.group(2)} {match.group(3)}", "%B %d %Y"
                ).strftime("%Y-%m-%d")
            else:
                renewal_date = datetime.strptime(
                    f"{match.group(1)}/{match.group(2)}/{match.group(3)}", "%d/%m/%Y"
                ).strftime("%Y-%m-%d")
            break
        except ValueError:
            continue

    auto_renew = None
    negative_auto_patterns = [
        "auto-renewal is disabled", "auto-renew is disabled", "auto renewal is disabled",
        "will not automatically renew", "does not automatically renew",
        "ne sera pas renouvelé automatiquement", "renouvellement automatique désactivé",
    ]
    positive_auto_patterns = [
        "auto-renewal", "auto-renew", "automatically renew", "automatically renews",
        "renews automatically", "renew automatically", "autorenew", "renouvelé automatiquement",
        "renouvellement automatique", "sera renouvelé automatiquement",
    ]
    if any(pattern in lowered for pattern in negative_auto_patterns):
        auto_renew = False
    elif any(pattern in lowered for pattern in positive_auto_patterns):
        auto_renew = True

    seats = None
    seat_patterns = [
        r"(\d+)\s+(?:seats|users|licenses|licences|lignes)",
        r"(?:seats|users|licenses|licences|lignes)\s*[:\-]?\s*(\d+)",
    ]
    for pattern in seat_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            seats = int(match.group(1))
            break

    return {
        "Service": service,
        "Monthly Cost": cost,
        "Currency": currency,
        "Renewal Date": renewal_date,
        "Auto-Renew": auto_renew,
        "Seats": seats,
        "Source": "Email + Rule Parser",
        "Sender": sender,
        "Subject": email_subject,
        "AI Confidence": 0.70,
    }

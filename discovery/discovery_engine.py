def normalize_service_name(name):
    if not name:
        return ""

    value = " ".join(str(name).lower().strip().split())

    aliases = {
        "aws": "aws",
        "amazon web services": "aws",
        "aws cloud infrastructure": "aws",
        "microsoft 365": "microsoft 365",
        "office 365": "microsoft 365",
        "adobe creative cloud": "adobe creative cloud",
        "canva enterprise": "canva enterprise",
        "slack business+": "slack",
        "slack": "slack",
        "zoom": "zoom",
        "zoom pro": "zoom",
        "notion": "notion",
        "notion business": "notion",
        "algerie telecom": "algérie télécom",
        "algérie télécom": "algérie télécom",
        "algérie télécom fibre pro": "algérie télécom",
        "djezzy": "djezzy",
        "djezzy business": "djezzy",
    }

    return aliases.get(value, value)


def discover_subscription(email_subscription, registry):
    service = email_subscription.get("Service", "Unknown Service")
    normalized_service = normalize_service_name(service)
    matched_subscription = None

    for subscription in registry:
        if normalized_service == normalize_service_name(subscription.get("Service", "")):
            matched_subscription = subscription
            break

    monthly_cost = email_subscription.get("Monthly Cost")
    annual_cost = monthly_cost * 12 if monthly_cost is not None else 0
    currency = email_subscription.get("Currency")

    if matched_subscription is None:
        return {
            "Service": service,
            "Status": "Forgotten Subscription",
            "Risk": "High" if email_subscription.get("Auto-Renew") is not False else "Medium",
            "Monthly Cost": monthly_cost,
            "Annual Cost": annual_cost,
            "Currency": currency or "UNKNOWN",
            "Renewal Date": email_subscription.get("Renewal Date"),
            "Auto-Renew": email_subscription.get("Auto-Renew"),
            "Seats": email_subscription.get("Seats"),
            "Source": email_subscription.get("Source", "Email"),
            "Sender": email_subscription.get("Sender"),
            "Subject": email_subscription.get("Subject"),
            "Recommendation": (
                f"Review the {service} subscription before renewal. It was discovered in email "
                "but is not present in the enterprise registry."
            ),
            "Confidence": email_subscription.get("AI Confidence", 0.95),
        }

    registry_cost = matched_subscription.get("Monthly Cost", 0)
    registry_currency = matched_subscription.get("Currency")
    registry_utilization = matched_subscription.get("Utilization", 0)
    registry_auto_renew = matched_subscription.get("Auto-Renew", False)
    findings = []

    if currency and registry_currency and currency != registry_currency:
        findings.append(f"Currency mismatch ({currency} vs {registry_currency})")
    elif monthly_cost is not None and registry_cost:
        if abs(monthly_cost - registry_cost) > 0.01:
            findings.append("Cost mismatch")

    if email_subscription.get("Auto-Renew") is True and not registry_auto_renew:
        findings.append("Auto-renewal detected")

    if registry_utilization <= 20:
        findings.append("Underutilized")

    if findings:
        return {
            "Service": service,
            "Status": "Known - Requires Review",
            "Risk": "Medium",
            "Monthly Cost": monthly_cost,
            "Annual Cost": annual_cost,
            "Currency": currency or registry_currency or "UNKNOWN",
            "Renewal Date": email_subscription.get("Renewal Date"),
            "Auto-Renew": email_subscription.get("Auto-Renew"),
            "Seats": email_subscription.get("Seats"),
            "Source": email_subscription.get("Source", "Email"),
            "Sender": email_subscription.get("Sender"),
            "Subject": email_subscription.get("Subject"),
            "Recommendation": (
                f"{service} exists in the registry but the email reveals additional information: "
                f"{', '.join(findings)}."
            ),
            "Confidence": email_subscription.get("AI Confidence", 0.90),
        }

    return {
        "Service": service,
        "Status": "Known Subscription",
        "Risk": "Low",
        "Monthly Cost": monthly_cost,
        "Annual Cost": annual_cost,
        "Currency": currency or registry_currency or "UNKNOWN",
        "Renewal Date": email_subscription.get("Renewal Date"),
        "Auto-Renew": email_subscription.get("Auto-Renew"),
        "Seats": email_subscription.get("Seats"),
        "Source": email_subscription.get("Source", "Email"),
        "Sender": email_subscription.get("Sender"),
        "Subject": email_subscription.get("Subject"),
        "Recommendation": f"{service} matches the existing subscription registry.",
        "Confidence": email_subscription.get("AI Confidence", 0.90),
    }


def run_discovery(email_subscriptions, registry):
    return [discover_subscription(subscription, registry) for subscription in email_subscriptions]

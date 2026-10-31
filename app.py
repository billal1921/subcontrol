import json
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from discovery.email_parser import extract_subscription
from discovery.discovery_engine import run_discovery

# Current Google GenAI SDK (recommended by Google). The app still works without it.
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

GEMINI_MODEL = "gemini-3.8-flash"

st.set_page_config(
    page_title="SubControl | Enterprise Subscription Agent",
    layout="wide",
    page_icon="⚡",
)


def get_secret(name: str) -> str:
    try:
        value = st.secrets.get(name, "")
        return str(value).strip() if value else ""
    except Exception:
        return ""


def format_money(value, currency):
    if value is None or pd.isna(value):
        return "—"
    symbol = "DZD" if currency == "DZD" else "$"
    return f"{value:,.0f} {symbol}" if currency == "DZD" else f"${value:,.2f}"


def run_gemini_extraction(subject, body, sender, api_key):
    """Use Gemini structured output to extract subscription facts from an email."""
    if not (GEMINI_AVAILABLE and api_key):
        return None

    schema = {
        "type": "object",
        "properties": {
            "service": {"type": "string"},
            "monthly_cost": {"type": "number", "nullable": True},
            "currency": {"type": "string", "enum": ["DZD", "USD", "EUR", "UNKNOWN"]},
            "renewal_date": {"type": "string", "nullable": True},
            "auto_renew": {"type": "boolean", "nullable": True},
            "seats": {"type": "integer", "nullable": True},
            "is_subscription": {"type": "boolean"},
            "confidence": {"type": "number"},
        },
        "required": [
            "service",
            "monthly_cost",
            "currency",
            "renewal_date",
            "auto_renew",
            "seats",
            "is_subscription",
            "confidence",
        ],
    }

    prompt = f"""
You are the perception layer of SubControl, an enterprise subscription discovery agent.
Read the email below and extract only facts supported by the email.
Do not invent missing values. If a field is unknown, use null or UNKNOWN.
Normalize currency to DZD, USD, EUR, or UNKNOWN.
If the amount is explicitly monthly, return it as monthly_cost.
If the email gives an annual amount, divide by 12 only if the text clearly says it is annual.
Return a subscription only when the message is actually about a subscription, billing, invoice, renewal, plan, or recurring service.

Sender: {sender}
Subject: {subject}
Body:
{body}
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
        data = json.loads(response.text)
        if not data.get("is_subscription"):
            return None

        return {
            "Service": data.get("service") or "Unknown Service",
            "Monthly Cost": data.get("monthly_cost"),
            "Currency": data.get("currency") if data.get("currency") != "UNKNOWN" else None,
            "Renewal Date": data.get("renewal_date"),
            "Auto-Renew": data.get("auto_renew"),
            "Seats": data.get("seats"),
            "Source": "Email + Gemini",
            "Sender": sender,
            "Subject": subject,
            "AI Confidence": float(data.get("confidence", 0.0)),
        }
    except Exception:
        return None


# ---------------------------------------------------------
# INITIALIZE STATE — MIXED DZD / USD ENTERPRISE REGISTRY
# ---------------------------------------------------------
if "subscriptions" not in st.session_state:
    st.session_state.subscriptions = [
        {
            "Service": "Microsoft 365 Business",
            "Category": "Productivity",
            "Monthly Cost": 65000,
            "Currency": "DZD",
            "Seats": 25,
            "Active Seats": 22,
            "Utilization (%)": 88,
            "Renewal Date": (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d"),
            "Auto-Renew": True,
        },
        {
            "Service": "Adobe Creative Cloud",
            "Category": "Design",
            "Monthly Cost": 42,
            "Currency": "USD",
            "Seats": 10,
            "Active Seats": 1,
            "Utilization (%)": 10,
            "Renewal Date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "Auto-Renew": True,
        },
        {
            "Service": "AWS Cloud Infrastructure",
            "Category": "Cloud",
            "Monthly Cost": 195,
            "Currency": "USD",
            "Seats": 1,
            "Active Seats": 1,
            "Utilization (%)": 94,
            "Renewal Date": (datetime.now() + timedelta(days=21)).strftime("%Y-%m-%d"),
            "Auto-Renew": True,
        },
        {
            "Service": "Algérie Télécom Fibre Pro",
            "Category": "Telecom",
            "Monthly Cost": 32000,
            "Currency": "DZD",
            "Seats": 1,
            "Active Seats": 1,
            "Utilization (%)": 100,
            "Renewal Date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
            "Auto-Renew": False,
        },
        {
            "Service": "Djezzy Business",
            "Category": "Telecom",
            "Monthly Cost": 8000,
            "Currency": "DZD",
            "Seats": 10,
            "Active Seats": 9,
            "Utilization (%)": 90,
            "Renewal Date": (datetime.now() + timedelta(days=18)).strftime("%Y-%m-%d"),
            "Auto-Renew": True,
        },
        {
            "Service": "Slack Business+",
            "Category": "Communication",
            "Monthly Cost": 28,
            "Currency": "USD",
            "Seats": 25,
            "Active Seats": 4,
            "Utilization (%)": 16,
            "Renewal Date": (datetime.now() + timedelta(days=12)).strftime("%Y-%m-%d"),
            "Auto-Renew": True,
        },
    ]

if "email_discovery_findings" not in st.session_state:
    st.session_state.email_discovery_findings = []

if "agent_activity" not in st.session_state:
    st.session_state.agent_activity = []

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
st.sidebar.header("🤖 AI Engine")
secret_key = get_secret("GEMINI_API_KEY")
manual_key = st.sidebar.text_input(
    "Gemini API Key (optional)",
    type="password",
    help="For the live AI extraction demo. In Streamlit Cloud, prefer GEMINI_API_KEY in Secrets.",
)
gemini_api_key = manual_key.strip() or secret_key

if gemini_api_key and GEMINI_AVAILABLE:
    st.sidebar.success("Gemini perception: ACTIVE")
elif gemini_api_key and not GEMINI_AVAILABLE:
    st.sidebar.warning("API key found, but google-genai is not installed.")
else:
    st.sidebar.info("Gemini unavailable → deterministic email parser will be used.")

st.sidebar.markdown("---")
st.sidebar.header("🛠️ Enterprise Registry")

with st.sidebar.form("add_sub_form"):
    new_name = st.text_input("Service Name", placeholder="e.g. Djezzy Business / Zoom")
    new_cat = st.selectbox(
        "Category", ["SaaS", "Cloud", "Telecom", "Design", "Security", "Productivity", "Communication"]
    )
    new_currency = st.selectbox("Currency", ["DZD", "USD"])
    new_cost = st.number_input("Monthly Cost", min_value=0.01, value=25000.0, step=1000.0)
    new_seats = st.number_input("Total Seats", min_value=1, value=10)
    new_util = st.slider("Active Utilization (%)", 0, 100, 5)
    new_days = st.slider("Days Until Expiration", 1, 60, 3)
    new_auto = st.checkbox("Auto-Renewal Enabled", value=True)

    submitted = st.form_submit_button("➕ Add to Registry")
    if submitted and new_name:
        active_seats = max(0, int((new_util / 100.0) * new_seats))
        st.session_state.subscriptions.append(
            {
                "Service": new_name,
                "Category": new_cat,
                "Monthly Cost": new_cost,
                "Currency": new_currency,
                "Seats": int(new_seats),
                "Active Seats": active_seats,
                "Utilization (%)": new_util,
                "Renewal Date": (datetime.now() + timedelta(days=new_days)).strftime("%Y-%m-%d"),
                "Auto-Renew": new_auto,
            }
        )
        st.sidebar.success(f"Added {new_name}.")

st.sidebar.markdown("---")
st.sidebar.header("📧 Email Discovery")
st.sidebar.caption("Perception → extraction → registry matching → risk → savings")

if st.sidebar.button("🔎 Run Email Discovery", type="primary"):
    try:
        with open("data/sample_emails.json", "r", encoding="utf-8-sig") as f:
            sample_emails = json.load(f)

        activity = [
            "✓ Scanning billing and renewal emails",
        ]
        parsed_emails = []
        ai_used = 0

        for email in sample_emails:
            extracted = None
            if gemini_api_key and GEMINI_AVAILABLE:
                extracted = run_gemini_extraction(
                    email["subject"], email["body"], email.get("sender", "unknown"), gemini_api_key
                )
                if extracted:
                    ai_used += 1

            if extracted is None:
                extracted = extract_subscription(
                    email["subject"], email["body"], email.get("sender", "unknown")
                )
                if extracted:
                    extracted["Source"] = "Email + Rule Parser"

            if extracted:
                parsed_emails.append(extracted)

        activity.append(f"✓ Extracted {len(parsed_emails)} subscription signals")
        if ai_used:
            activity.append(f"✓ Gemini understood {ai_used}/{len(sample_emails)} emails")
        else:
            activity.append("✓ Deterministic parser completed extraction")
        activity.append("✓ Matching discovered services against enterprise registry")

        discovery_registry = [
            {
                "Service": sub["Service"],
                "Monthly Cost": sub["Monthly Cost"],
                "Currency": sub["Currency"],
                "Utilization": sub["Utilization (%)"],
                "Auto-Renew": sub["Auto-Renew"],
            }
            for sub in st.session_state.subscriptions
        ]

        findings = run_discovery(parsed_emails, discovery_registry)
        st.session_state.email_discovery_findings = findings

        forgotten_count = sum(1 for item in findings if item["Status"] == "Forgotten Subscription")
        activity.append(f"✓ Detected {forgotten_count} subscriptions missing from the registry")
        activity.append("✓ Assessed risk and calculated annual financial exposure")
        activity.append("✓ Generated human-review recommendations")
        st.session_state.agent_activity = activity

        st.sidebar.success(f"Discovery complete: {len(parsed_emails)} subscriptions analyzed.")
    except Exception as exc:
        st.sidebar.error(f"Email discovery error: {exc}")

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Agent Thresholds")
days_threshold = st.sidebar.slider("Alert Window (Days before renewal)", 1, 30, 7)
util_threshold = st.sidebar.slider("Low Utilization Threshold (%)", 5, 50, 25)

if st.sidebar.button("🔄 Reset Demo Data"):
    for key in ["subscriptions", "email_discovery_findings", "agent_activity"]:
        st.session_state.pop(key, None)
    st.rerun()

# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
st.title("⚡ SubControl: Autonomous Enterprise Subscription Agent")
st.markdown(
    "**Discover hidden subscriptions, assess renewal and utilization risk, and identify potential savings — "
    "using a Perception → Decision → Action workflow.**"
)

with st.expander("🔍 How the agent works"):
    st.markdown(
        """
        **1. Perception** — reads enterprise billing/renewal emails and extracts service, cost, currency, renewal, auto-renewal and seat information.

        **2. Decision** — compares discovered subscriptions with the enterprise registry and applies deterministic risk rules.

        **3. Action** — prioritizes forgotten subscriptions, zombie licenses, renewal risks and right-sizing opportunities, then estimates financial impact.

        **AI boundary:** Gemini is used for understanding unstructured email content. Critical financial decisions remain deterministic and auditable in Python.
        """
    )

# ---------------------------------------------------------
# TOP METRICS — KEEP CURRENCIES SEPARATE
# ---------------------------------------------------------
df = pd.DataFrame(st.session_state.subscriptions)
dzd_monthly = df.loc[df["Currency"] == "DZD", "Monthly Cost"].sum()
usd_monthly = df.loc[df["Currency"] == "USD", "Monthly Cost"].sum()
dzd_annual = dzd_monthly * 12
usd_annual = usd_monthly * 12
low_util_count = len(df[df["Utilization (%)"] <= util_threshold])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Contracts Monitored", f"{len(df)}")
c2.metric("🇩🇿 Monthly Spend", f"{dzd_monthly:,.0f} DZD")
c3.metric("🇺🇸 Monthly Spend", f"${usd_monthly:,.2f}")
c4.metric("Underutilized", f"{low_util_count} flagged")

# ---------------------------------------------------------
# AGENT ACTIVITY — MAKE AUTONOMY VISIBLE
# ---------------------------------------------------------
if st.session_state.agent_activity:
    st.markdown("---")
    st.subheader("🤖 Agent Activity")
    for step in st.session_state.agent_activity:
        st.write(step)

# ---------------------------------------------------------
# EMAIL DISCOVERY FINDINGS
# ---------------------------------------------------------
if st.session_state.email_discovery_findings:
    st.markdown("---")
    st.subheader("📧 Discovery Results")
    st.caption("Email signals have been extracted, matched against the registry, and classified by the agent.")

    findings_df = pd.DataFrame(st.session_state.email_discovery_findings)
    forgotten = findings_df[findings_df["Status"] == "Forgotten Subscription"]
    known_review = findings_df[findings_df["Status"] == "Known - Requires Review"]

    fd1, fd2, fd3, fd4 = st.columns(4)
    fd1.metric("🔎 Discovered", len(findings_df))
    fd2.metric("🔴 Forgotten", len(forgotten))

    forgotten_dzd = forgotten.loc[forgotten["Currency"] == "DZD", "Annual Cost"].sum()
    forgotten_usd = forgotten.loc[forgotten["Currency"] == "USD", "Annual Cost"].sum()
    fd3.metric("🇩🇿 Forgotten / yr", f"{forgotten_dzd:,.0f} DZD")
    fd4.metric("🇺🇸 Forgotten / yr", f"${forgotten_usd:,.2f}")

    display_columns = [
        "Service", "Status", "Risk", "Monthly Cost", "Currency",
        "Annual Cost", "Renewal Date", "Auto-Renew", "Seats", "Confidence"
    ]
    st.dataframe(findings_df[display_columns], width="stretch", hide_index=True)

    if not forgotten.empty:
        st.markdown("### 🔴 Potential Forgotten Subscriptions")
        for _, finding in forgotten.iterrows():
            st.error(
                f"**{finding['Service']}** — **{finding['Risk']} Risk**\n\n"
                f"💰 **Annual exposure:** {format_money(finding['Annual Cost'], finding['Currency'])}\n\n"
                f"📅 **Renewal:** {finding['Renewal Date'] or 'Not detected'}\n\n"
                f"🔁 **Auto-renew:** {finding['Auto-Renew'] if finding['Auto-Renew'] is not None else 'Unknown'}\n\n"
                f"🤖 **Agent recommendation:** {finding['Recommendation']}"
            )

    if not known_review.empty:
        st.markdown("### 🟠 Known Subscriptions Requiring Review")
        for _, finding in known_review.iterrows():
            st.warning(f"**{finding['Service']}** — {finding['Recommendation']}")

# ---------------------------------------------------------
# REGISTRY + CURRENCY-AWARE ANALYTICS
# ---------------------------------------------------------
col_table, col_charts = st.columns([2, 1])

with col_table:
    st.subheader("📋 Enterprise Subscription Registry")
    st.dataframe(df, width="stretch", hide_index=True)

with col_charts:
    st.subheader("📊 Spend by Category")
    dzd_category = df[df["Currency"] == "DZD"].groupby("Category")["Monthly Cost"].sum()
    usd_category = df[df["Currency"] == "USD"].groupby("Category")["Monthly Cost"].sum()
    st.caption("DZD")
    if not dzd_category.empty:
        st.bar_chart(dzd_category)
    st.caption("USD")
    if not usd_category.empty:
        st.bar_chart(usd_category)

st.markdown("---")

# ---------------------------------------------------------
# DETERMINISTIC AGENT EXECUTION ENGINE
# ---------------------------------------------------------
st.subheader("🧠 Decision & Action Engine")
st.write("Run auditable rules against utilization, renewal timing, auto-renewal and service criticality.")

if st.button("🚀 Run SubControl Agent Audit", type="primary", width="stretch"):
    critical_directives = []
    continuity_risks = []
    optimization_advisories = []
    savings_by_currency = {"DZD": 0, "USD": 0}

    for sub in st.session_state.subscriptions:
        renewal_dt = datetime.strptime(sub["Renewal Date"], "%Y-%m-%d")
        days_left = (renewal_dt - datetime.now()).days + 1
        cost = sub["Monthly Cost"]
        currency = sub["Currency"]
        util = sub["Utilization (%)"]
        auto = sub["Auto-Renew"]
        name = sub["Service"]

        if util == 0 and auto:
            annual_save = cost * 12
            savings_by_currency[currency] += annual_save
            critical_directives.append(
                {
                    "Service": name,
                    "Type": "ZOMBIE LICENSE (0% USAGE)",
                    "Urgency": f"Auto-renews in {days_left} days",
                    "Directive": f"Disable auto-renewal immediately. 0 of {sub['Seats']} seats are active.",
                    "Annual_Saving": annual_save,
                    "Currency": currency,
                }
            )

        elif util <= util_threshold and days_left <= days_threshold and auto:
            unused_ratio = (100 - util) / 100.0
            estimated_save = int(cost * unused_ratio * 0.8 * 12)
            savings_by_currency[currency] += estimated_save
            critical_directives.append(
                {
                    "Service": name,
                    "Type": f"UNDERUTILIZED ({util}% USAGE)",
                    "Urgency": f"Auto-renews in {days_left} days",
                    "Directive": f"Downscale from {sub['Seats']} to {max(1, sub['Active Seats'])} seats before billing locks.",
                    "Annual_Saving": estimated_save,
                    "Currency": currency,
                }
            )

        elif not auto and days_left <= days_threshold and util >= 50:
            continuity_risks.append(
                {
                    "Service": name,
                    "Type": "OUTAGE RISK (MANUAL RENEWAL)",
                    "Urgency": f"Expires in {days_left} days (Auto-Renew OFF)",
                    "Directive": f"High utilization ({util}%). Process manual renewal immediately to prevent service interruption.",
                    "Annual_Saving": 0,
                    "Currency": currency,
                }
            )

        elif util <= util_threshold:
            estimated_save = int(cost * 0.5 * 12)
            savings_by_currency[currency] += estimated_save
            optimization_advisories.append(
                {
                    "Service": name,
                    "Type": f"LOW ADOPTION ({util}%)",
                    "Urgency": f"Renews in {days_left} days",
                    "Directive": f"Only {sub['Active Seats']}/{sub['Seats']} active seats. Audit adoption or downgrade tier.",
                    "Annual_Saving": estimated_save,
                    "Currency": currency,
                }
            )

    cat_counts = df["Category"].value_counts()
    redundant_cats = cat_counts[cat_counts > 1].index.tolist()

    st.success(f"✅ Audit complete — evaluated {len(df)} enterprise contracts.")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🇩🇿 Savings", f"{savings_by_currency['DZD']:,.0f} DZD / yr")
    m2.metric("🇺🇸 Savings", f"${savings_by_currency['USD']:,.2f} / yr")
    m3.metric("🔴 Cost Interventions", f"{len(critical_directives)}")
    m4.metric("⚠️ Continuity Risks", f"{len(continuity_risks)}")

    # ---------------------------------------------------------
    # GEMINI EXECUTIVE SYNTHESIS — REAL AI USE
    # ---------------------------------------------------------
    st.markdown("### 🧠 AI Executive Brief")
    if gemini_api_key and GEMINI_AVAILABLE:
        try:
            with st.spinner("Gemini is synthesizing the audit for management..."):
                client = genai.Client(api_key=gemini_api_key)
                prompt = f"""
You are SubControl, an enterprise subscription optimization agent.
Create a concise management brief in 3 bullet points.
Mention DZD and USD separately; never add them together.
Explain the most important cost risk, continuity risk, and optimization opportunity.
This is an advisory system: recommend human review before consequential actions.

Registry: {df.to_dict(orient='records')}
Critical directives: {critical_directives}
Continuity risks: {continuity_risks}
Optimization advisories: {optimization_advisories}
"""
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                )
                st.info(response.text)
        except Exception as exc:
            st.warning(f"Gemini unavailable for this run; deterministic synthesis used instead. ({exc})")
            st.info(
                f"**Deterministic synthesis:** {len(critical_directives)} cost interventions, "
                f"{len(continuity_risks)} continuity risks, and separate potential savings of "
                f"{savings_by_currency['DZD']:,.0f} DZD/year and ${savings_by_currency['USD']:,.2f}/year."
            )
    else:
        st.info(
            f"**Deterministic synthesis:** {len(critical_directives)} cost interventions, "
            f"{len(continuity_risks)} continuity risks, and separate potential savings of "
            f"{savings_by_currency['DZD']:,.0f} DZD/year and ${savings_by_currency['USD']:,.2f}/year. "
            "Add a Gemini API key to enable live AI synthesis."
        )

    if critical_directives:
        st.markdown("### 🔴 Immediate Financial Interventions")
        for item in critical_directives:
            st.error(
                f"**{item['Service']} — {item['Type']}** | ⏳ *{item['Urgency']}*\n\n"
                f"👉 **Agent Directive:** {item['Directive']}\n\n"
                f"💵 **Projected annual impact:** {format_money(item['Annual_Saving'], item['Currency'])}"
            )

    if continuity_risks:
        st.markdown("### 🟠 Continuity & Outage Protection")
        for risk in continuity_risks:
            st.warning(
                f"**{risk['Service']}** | ⏳ *{risk['Urgency']}*\n\n"
                f"👉 **Agent Directive:** {risk['Directive']}"
            )

    if optimization_advisories or redundant_cats:
        st.markdown("### 🔵 Right-Sizing & Tool Consolidation")
        for adv in optimization_advisories:
            st.info(
                f"**{adv['Service']}** ({adv['Urgency']}) — {adv['Directive']} "
                f"(Est. saving: **{format_money(adv['Annual_Saving'], adv['Currency'])}/yr**)"
            )
        for r_cat in redundant_cats:
            tools_in_cat = df[df["Category"] == r_cat]["Service"].tolist()
            st.info(
                f"💡 **Redundancy in `{r_cat}`:** {', '.join(tools_in_cat)}. "
                "Consider consolidation after human review."
            )

    # ---------------------------------------------------------
    # EXPORT + ACTION SIMULATION
    # ---------------------------------------------------------
    st.markdown("---")
    col_exp1, col_exp2 = st.columns(2)
    report_data = critical_directives + continuity_risks + optimization_advisories
    if report_data:
        report_df = pd.DataFrame(report_data)
        csv_data = report_df.to_csv(index=False).encode("utf-8")
        with col_exp1:
            st.download_button(
                label="📥 Export Agent Directives Report (CSV)",
                data=csv_data,
                file_name="subcontrol_agent_directives.csv",
                mime="text/csv",
                width="stretch",
            )
    with col_exp2:
        if st.button("📨 Dispatch Alerts to IT & Finance", width="stretch"):
            st.toast("✅ Action queue prepared for IT & Finance — human approval required.")

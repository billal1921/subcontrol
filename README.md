\# SubControl



> An autonomous enterprise subscription optimization agent that discovers hidden subscriptions, assesses risk, and recommends cost-saving actions.



\## 1. Overview



SubControl is an AI-assisted enterprise subscription optimization agent designed to help organizations discover and manage software, cloud, and telecom subscriptions.



Instead of relying only on a manually maintained subscription registry, SubControl analyzes billing and renewal emails, extracts subscription signals, compares them with the enterprise registry, detects forgotten or risky subscriptions, estimates financial exposure, and generates human-review recommendations.



The current MVP uses realistic local sample billing emails to demonstrate the perception workflow. Live Gmail integration is a planned next step.



\## 2. Problem



Organizations often lose money through:



\- Forgotten subscriptions

\- Automatically renewed services

\- Unused or underutilized licenses

\- Duplicate tools serving similar purposes

\- Renewal risks for critical services

\- Subscriptions missing from the central registry



These issues are difficult to detect when subscription information is distributed across emails, invoices, and manually maintained records.



\## 3. What SubControl Does



SubControl follows an agent-style workflow:



```text

Email Signals

&#x20;    ↓

Perception

&#x20;    ↓

Subscription Extraction

&#x20;    ↓

Registry Matching

&#x20;    ↓

Risk Assessment

&#x20;    ↓

Financial Exposure

&#x20;    ↓

Human-Review Recommendation

```



\### Perception



Gemini analyzes unstructured billing and renewal emails and extracts structured information such as:



\- Service name

\- Monthly cost

\- Currency

\- Renewal date

\- Auto-renewal status

\- Number of seats

\- Confidence



If Gemini is unavailable, the system falls back to a deterministic rule-based parser.



\### Decision



The deterministic Python engine performs auditable business logic:



\- Registry matching

\- Forgotten subscription detection

\- Risk assessment

\- Underutilization detection

\- Renewal risk detection

\- Annual financial exposure calculation

\- Optimization recommendations



\### Action



SubControl currently produces recommendations for human review.



Consequential actions such as cancellation or renewal are intentionally not executed automatically in this MVP.



\## 4. AI Architecture



SubControl uses a hybrid architecture.



\### Gemini



Gemini is responsible for the perception layer:



```text

Unstructured Email

&#x20;      ↓

Gemini

&#x20;      ↓

Structured JSON

```



This allows the system to understand natural-language billing and renewal emails.



\### Python Decision Engine



The decision layer remains deterministic:



```text

Structured Subscription Data

&#x20;      ↓

Enterprise Registry

&#x20;      ↓

Rules

&#x20;      ↓

Risk + Savings + Recommendations

```



This separation makes financial decisions more predictable and auditable.



\## 5. Currency Handling



SubControl keeps financial metrics separated by currency.



Algerian services are represented in \*\*DZD\*\*.



International services are represented in \*\*USD\*\*.



The MVP does not combine DZD and USD without an explicit exchange-rate conversion.



\## 6. Current Demo Scenario



The demo includes subscriptions such as:



\- Microsoft 365 Business

\- Adobe Creative Cloud

\- AWS Cloud Infrastructure

\- Algérie Télécom Fibre Pro

\- Djezzy Business

\- Slack Business+

\- Canva Enterprise

\- Zoom Pro

\- Notion Business



The system demonstrates both known subscriptions and subscriptions discovered outside the enterprise registry.



\## 7. Example Agent Activity



During discovery, the interface exposes the agent workflow:



```text

✓ Scanning billing and renewal emails

✓ Extracting subscription signals

✓ Gemini understanding email content

✓ Matching discovered services against enterprise registry

✓ Detecting forgotten subscriptions

✓ Assessing risk

✓ Calculating financial exposure

✓ Generating human-review recommendations

```



\## 8. Tech Stack



\- Python

\- Streamlit

\- Google Gemini API

\- Google GenAI SDK

\- Pandas

\- JSON

\- Git / GitHub



\## 9. Project Structure



```text

SubControl/

│

├── app.py

├── requirements.txt

├── README.md

│

├── data/

│   └── sample\_emails.json

│

├── discovery/

│   ├── email\_parser.py

│   └── discovery\_engine.py

│

└── .streamlit/

&#x20;   └── secrets.toml

```



`secrets.toml` is local-only and is excluded from Git using `.gitignore`.



\## 10. Installation



Clone the repository:



```bash

git clone https://github.com/billal1921/subcontrol.git

cd subcontrol

```



Create a virtual environment:



\### Windows



```powershell

python -m venv .venv

.\\.venv\\Scripts\\Activate.ps1

```



\### Linux / macOS



```bash

python3 -m venv .venv

source .venv/bin/activate

```



Install dependencies:



```bash

pip install -r requirements.txt

```



\## 11. Gemini API Configuration



Create:



```text

.streamlit/secrets.toml

```



Add:



```toml

GEMINI\_API\_KEY = "YOUR\_API\_KEY"

```



Never commit this file or expose the API key publicly.



If Gemini is unavailable, SubControl can fall back to its deterministic email parser.



\## 12. Run Locally



```bash

streamlit run app.py

```



Then open the local Streamlit URL shown in the terminal.



\## 13. Team



\### SubControl



\- \*\*Belmihoub Yahia\*\* — Founder \& Developer



\## 14. Current MVP Limitations



The current version is intentionally focused on demonstrating the core agent workflow.



Current limitations:



\- Email discovery uses local sample emails rather than live Gmail.

\- Recommendations require human review before consequential actions.

\- No automatic subscription cancellation is performed.

\- Exchange-rate conversion between DZD and USD is not performed.

\- Enterprise authentication and multi-tenant management are outside the current MVP scope.



\## 15. Roadmap



Future versions can extend SubControl with:



1\. Gmail API integration

2\. Automatic ingestion of real billing emails

3\. Enterprise authentication

4\. Persistent subscription storage

5\. Approval workflows

6\. Integration with procurement and finance systems

7\. Real-time exchange-rate conversion

8\. Human-approved automated actions

9\. Multi-tenant enterprise deployment



\## 16. Why SubControl Is an Agent



SubControl is designed around a perception → decision → action architecture rather than being only a reporting dashboard.



It perceives information from unstructured email signals, reasons over the discovered information using enterprise rules, identifies risks and optimization opportunities, and proposes the next action for human approval.



The MVP makes this reasoning workflow visible through the Agent Activity interface.



\---



\*\*Built by Team SubControl\*\*


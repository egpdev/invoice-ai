# 🏛️ InvoiceAI — KI-gestützte Rechnungsverarbeitung

<p align="center">
  <strong>Automated financial data extraction for German accounting standards (DATEV).</strong><br>
  Upload PDF invoices or photo receipts → get structured CSV, Excel, or XML in seconds.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python" />
  <img src="https://img.shields.io/badge/Streamlit-Cloud-ff4b4b?logo=streamlit" />
  <img src="https://img.shields.io/badge/AI-Llama%204%20Scout-orange?logo=meta" />
  <img src="https://img.shields.io/badge/License-Proprietary-red" />
</p>

---

## 🚀 What is InvoiceAI?

InvoiceAI is a SaaS tool that uses **Large Language Models (LLM)** to extract structured financial data from German invoices and receipts — automatically.

Instead of manually typing invoice numbers, amounts, and tax rates into spreadsheets, accountants simply upload their documents and download a ready-to-use DATEV-compatible file.

### Key Features

| Feature | Description |
|---|---|
| 📄 **Multimodal Input** | Supports PDF documents **and** photo receipts (JPG/PNG) via AI Vision |
| 🧮 **MwSt Validation** | Automatic Netto + MwSt vs. Brutto check with red highlighting on errors |
| 📊 **DATEV Export** | One-click export to CSV (semicolon), Excel (.xlsx), or XML |
| 🔐 **DSGVO Compliant** | Zero data retention — no files or data are stored on our servers |
| 👤 **User Accounts** | Registration, login, and credit-based billing system |
| 🔧 **Admin Panel** | Full user management and credit top-up dashboard |
| 🌍 **Multilingual** | Full DE/EN interface localization |

---

## 🏗️ Tech Stack

- **Frontend:** Streamlit (Python)
- **AI Models:** Meta Llama 4 Scout (Vision) + Llama 3.3 70B (Text) via Groq API
- **PDF Parsing:** pdfplumber
- **Database:** SQLite (user auth & credits)
- **Deployment:** Streamlit Cloud

---

## 📸 Screenshots

### Landing Page
> Professional German-language landing page with pricing and feature cards.

### Dashboard
> Clean dark-mode interface with file upload, metrics cards, and data grid.

### Admin Panel
> Full user management with credit top-up functionality.

---

## 💰 Business Model

- New users receive **10 free credits** upon registration
- **1 credit = 1 processed invoice**
- Credits can be purchased by contacting the administrator
- Admin panel enables manual credit top-up after payment

---

## 🛠️ Local Development

```bash
# Clone the repository
git clone https://github.com/egpdev/invoice-ai.git
cd invoice-ai

# Install dependencies
pip install -r requirements.txt

# Set your Groq API key
echo "GROQ_API_KEY=gsk_your_key_here" > .env

# Run the app
streamlit run app.py
```

---

## 📋 Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Your Groq API key for LLM inference |

---

## 📄 License

This is a proprietary SaaS product. All rights reserved.

---

<p align="center">
  Built with ❤️ in Germany<br>
  <a href="https://groq.com">Powered by Groq</a>
</p>

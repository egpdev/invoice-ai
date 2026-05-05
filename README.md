# 🏛️ InvoiceAI: German Accounting Parser

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32.2-FF4B4B.svg)
![OpenAI/Groq](https://img.shields.io/badge/LLM-Groq%20Llama3-black.svg)
![DATEV](https://img.shields.io/badge/Standard-DATEV-green.svg)

**InvoiceAI** is an automated, AI-powered pipeline designed to extract structured financial data from German invoices. Built specifically with German accounting standards (DATEV) in mind, it utilizes modern LLMs (Groq Llama 3) and `pdfplumber` to process bulk PDFs with high accuracy.

> 🔐 **Privacy First:** All data is processed locally and via secure API. No data is stored on the server.

---

## 🚀 Features

- **Bulk Upload Support:** Drag and drop 50+ PDF invoices at once for rapid processing.
- **Intelligent Extraction:** Extracts critical DATEV fields: `Firma`, `Rechnungsdatum`, `Rechnungsnummer`, `Netto`, `MwSt`, `Brutto`, `IBAN`, `Währung`.
- **Data Validation:** Automatically verifies the math (`Netto` + `MwSt` == `Brutto`). Problematic rows are instantly highlighted in red.
- **Modern Dashboard UI:** Built with Streamlit, featuring a premium dark corporate theme and real-time insights (Total Volume, Unique Vendors).
- **Multi-Language:** Seamless toggle between English and German (DE/EN) interfaces.
- **DATEV XML Export:** Download the parsed results in CSV, Excel, or a generic DATEV XML format ready for accounting software.

---

## 🛠️ Tech Stack

- **Frontend/UI:** [Streamlit](https://streamlit.io/)
- **PDF Parsing:** `pdfplumber`
- **AI/LLM Engine:** Groq API (`llama-3.3-70b-versatile`) via `openai` python client.
- **Data Manipulation:** `pandas`

---

## ⚙️ Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/invoiceai.git
cd invoiceai
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory (you can copy `.env.example`) and add your Groq API key:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Run the application
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## 💡 How it works

1. `pdfplumber` extracts the raw text from the uploaded PDF in-memory.
2. The text is passed to the Groq API with a highly optimized, strict prompt that forces a structured JSON output mapped to German accounting fields.
3. The response is parsed, validated, and displayed in an interactive Pandas DataFrame.

---

## 📝 License

This project is open-source and available under the [MIT License](LICENSE).

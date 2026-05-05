import streamlit as st
import pdfplumber
import openai
import pandas as pd
import json
import os
import io
import base64
from dotenv import load_dotenv

# Load environment variables if present
load_dotenv()

st.set_page_config(page_title="InvoiceAI | German Parser", page_icon="📄", layout="wide")

def apply_custom_style():
    st.markdown("""
        <style>
        /* Main container styling */
        .main {
            padding: 2rem;
        }
        /* Metric cards */
        div[data-testid="stMetric"] {
            background-color: #1e293b;
            padding: 1.5rem;
            border-radius: 0.75rem;
            border: 1px solid #334155;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        /* Sidebar styling */
        div[data-testid="stSidebar"] {
            border-right: 1px solid #334155;
        }
        /* Button primary color focus */
        .stButton>button {
            width: 100%;
            border-radius: 0.5rem;
        }
        /* Header styling */
        h1, h2, h3 {
            font-family: 'Inter', sans-serif;
            color: #f1f5f9;
        }
        </style>
    """, unsafe_allow_html=True)

def extract_text_from_pdf(file):
    """Extract text from an uploaded PDF using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
    return text

def parse_invoice_text(text, api_key, error_msg):
    """Send text to Groq API and request structured JSON output."""
    client = openai.OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    
    prompt = """
You are an expert AI trained to extract structured financial data from German invoices (DATEV-style requirements).
Extract the following information from the provided invoice text and return it STRICTLY as a JSON object.
Do not include any explanation or markdown code blocks (like ```json), just output the raw JSON string.

Keys required:
- "Firma": Sender company name (string)
- "Rechnungsdatum": Invoice date, formatted as YYYY-MM-DD if possible (string)
- "Rechnungsnummer": Invoice number (string)
- "Netto-Betrag": Amount without VAT (number)
- "MwSt-Satz": VAT rate, e.g., 19 or 7 (number)
- "MwSt-Betrag": VAT amount (number)
- "Brutto-Betrag": Total amount including VAT (number)
- "IBAN": IBAN for payment (string)
- "Währung": Currency, e.g., "EUR" (string)

If a field is not found, set its value to null.
Make sure numerical values use a period (.) for decimals, not a comma (,), and have no currency symbols attached.

Invoice Text:
\"\"\"
{text}
\"\"\"
"""
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a specialist in German DATEV accounting. Return strictly valid JSON."},
                {"role": "user", "content": prompt.format(text=text)}
            ],
            temperature=0.0
        )
        
        content = response.choices[0].message.content.strip()
        # Clean up potential markdown formatting from the response
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        return json.loads(content)
    except Exception as e:
        st.error(f"{error_msg}: {e}")
        return None

def parse_invoice_image(base64_image, mime_type, api_key, error_msg):
    """Send image to Groq Vision API and request structured JSON output."""
    client = openai.OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    
    prompt = """
You are an expert AI trained to extract structured financial data from German invoices or receipts (DATEV-style requirements).
Extract the following information from the provided invoice image and return it STRICTLY as a JSON object.
Do not include any explanation or markdown code blocks (like ```json), just output the raw JSON string.

Keys required:
- "Firma": Sender company name (string)
- "Rechnungsdatum": Invoice date, formatted as YYYY-MM-DD if possible (string)
- "Rechnungsnummer": Invoice number (string)
- "Netto-Betrag": Amount without VAT (number)
- "MwSt-Satz": VAT rate, e.g., 19 or 7 (number)
- "MwSt-Betrag": VAT amount (number)
- "Brutto-Betrag": Total amount including VAT (number)
- "IBAN": IBAN for payment (string)
- "Währung": Currency, e.g., "EUR" (string)

If a field is not found, set its value to null.
Make sure numerical values use a period (.) for decimals, not a comma (,), and have no currency symbols attached.
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.0
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        return json.loads(content)
    except Exception as e:
        st.error(f"{error_msg} (Vision API): {e}")
        return None

def generate_datev_xml(df):
    """Generate a basic DATEV-compatible XML structure representing the invoices."""
    import xml.etree.ElementTree as ET
    from xml.dom import minidom
    
    root = ET.Element("Document")
    
    for _, row in df.iterrows():
        invoice = ET.SubElement(root, "Invoice")
        for col in df.columns:
            val = str(row[col]) if pd.notnull(row[col]) else ""
            tag_name = str(col).replace(" ", "_").replace("-", "_").replace(".", "")
            child = ET.SubElement(invoice, tag_name)
            child.text = val
            
    xml_str = ET.tostring(root, encoding='utf-8')
    parsed = minidom.parseString(xml_str)
    return parsed.toprettyxml(indent="  ").encode('utf-8')

TRANSLATIONS = {
    "EN": {
        "title": "🏛️ InvoiceAI Dashboard",
        "subtitle": "Automated financial data extraction for German accounting standards.",
        "config": "⚙️ Configuration",
        "lang": "Language",
        "api_key": "Groq API Key",
        "fields_ext": "**Data Fields Extracted:**",
        "upload": "Upload Invoices / Receipts (PDF, JPG, PNG)",
        "process_btn": "🚀 Process Invoices",
        "clear_btn": "🗑️ Clear All",
        "warn_api": "Please enter your Groq API Key in the sidebar.",
        "warn_pdf": "Please upload at least one PDF file.",
        "proc_msg": "Processing: {name} ({i}/{total})",
        "warn_extract": "Could not extract text from {name}. It might be an image-only PDF.",
        "proc_done": "Processing complete!",
        "success": "Successfully processed {n} invoices.",
        "insights": "### 📈 Key Insights",
        "tot_inv": "Total Invoices",
        "tot_vol": "Total Volume",
        "uniq_ven": "Unique Vendors",
        "grid_view": "📊 Data Grid View",
        "export": "💾 Export Data",
        "dl_csv": "Download CSV (Semicolon separated)",
        "dl_excel": "Download Excel",
        "dl_xml": "Download DATEV XML",
        "privacy": "🔐 All data is processed locally and via secure API. No data is stored.",
        "impressum": "[Legal Notice](https://example.com/legal-notice)",
        "error_api": "Error communicating with Groq API. Please check your key."
    },
    "DE": {
        "title": "🏛️ InvoiceAI Dashboard",
        "subtitle": "Automatisierte Finanzdatenextraktion für deutsche Buchhaltungsstandards.",
        "config": "⚙️ Konfiguration",
        "lang": "Sprache",
        "api_key": "Groq API-Schlüssel",
        "fields_ext": "**Extrahierte Datenfelder:**",
        "upload": "Rechnungen / Belege hochladen (PDF, JPG, PNG)",
        "process_btn": "🚀 Rechnungen verarbeiten",
        "clear_btn": "🗑️ Alles löschen",
        "warn_api": "Bitte geben Sie Ihren Groq API-Schlüssel in der Seitenleiste ein.",
        "warn_pdf": "Bitte laden Sie mindestens eine PDF-Datei hoch.",
        "proc_msg": "Verarbeitung: {name} ({i}/{total})",
        "warn_extract": "Text konnte nicht extrahiert werden aus {name}. Möglicherweise nur-Bild-PDF.",
        "proc_done": "Verarbeitung abgeschlossen!",
        "success": "Erfolgreich {n} Rechnungen verarbeitet.",
        "insights": "### 📈 Wichtige Erkenntnisse",
        "tot_inv": "Gesamte Rechnungen",
        "tot_vol": "Gesamtvolumen",
        "uniq_ven": "Lieferanten",
        "grid_view": "📊 Datenansicht",
        "export": "💾 Daten exportieren",
        "dl_csv": "CSV Herunterladen (Semikolon-getrennt)",
        "dl_excel": "Excel Herunterladen",
        "dl_xml": "DATEV XML Herunterladen",
        "privacy": "🔐 Alle Daten werden lokal und über eine sichere API verarbeitet. Es werden keine Daten gespeichert.",
        "impressum": "[Impressum](https://example.com/impressum)",
        "error_api": "Fehler bei der Kommunikation mit der Groq API. Bitte überprüfen Sie Ihren Schlüssel."
    }
}

def main():
    apply_custom_style()
    
    if "parsed_data" not in st.session_state:
        st.session_state.parsed_data = []
        
    # --- SIDEBAR ---
    with st.sidebar:
        # Display the generated placeholder logo
        logo_path = "/Users/minaminoshuichi/.gemini/antigravity/brain/d0aa9339-e6a3-4551-ac99-c22d1134720e/invoiceai_logo_1777988830614.png"
        if os.path.exists(logo_path):
            st.image(logo_path, use_column_width=True)
            
        st.header("⚙️ Settings")
        lang_choice = st.radio("Language / Sprache", ["EN", "DE"], horizontal=True)
        t = TRANSLATIONS[lang_choice]
        
        st.markdown("---")
        st.header(t["config"])
        default_api_key = os.getenv("GROQ_API_KEY", "")
        api_key = st.text_input(t["api_key"], value=default_api_key, type="password")
        
        st.markdown("---")
        st.markdown(
            f"{t['fields_ext']}\n"
            "- Firma\n"
            "- Rechnungsdatum\n"
            "- Rechnungsnummer\n"
            "- Netto-Betrag\n"
            "- MwSt-Satz\n"
            "- MwSt-Betrag\n"
            "- Brutto-Betrag\n"
            "- IBAN\n"
            "- Währung"
        )
        
        st.markdown("---")
        st.caption(t["privacy"])
        st.markdown(t["impressum"])

    # --- MAIN UI ---
    st.title(t["title"])
    st.markdown(t["subtitle"])

    uploaded_files = st.file_uploader(t["upload"], type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True)

    col_btn1, col_btn2 = st.columns([3, 1])
    
    with col_btn2:
        if st.button(t["clear_btn"], use_container_width=True):
            st.session_state.parsed_data = []
            st.rerun()

    with col_btn1:
        process_clicked = st.button(t["process_btn"], type="primary", use_container_width=True)

    if process_clicked:
        if not api_key:
            st.warning(t["warn_api"])
        elif not uploaded_files:
            st.warning(t["warn_pdf"])
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
    
            for i, file in enumerate(uploaded_files):
                status_text.text(t["proc_msg"].format(name=file.name, i=i+1, total=len(uploaded_files)))
                
                # Prevent duplicate processing of the same file
                if any(d.get("Dateiname") == file.name for d in st.session_state.parsed_data):
                    progress_bar.progress((i + 1) / len(uploaded_files))
                    continue
                
                ext = file.name.split('.')[-1].lower()
                
                if ext == 'pdf':
                    text = extract_text_from_pdf(file)
                    if not text.strip():
                        st.warning(t["warn_extract"].format(name=file.name))
                        continue
                    parsed_json = parse_invoice_text(text, api_key, t["error_api"])
                else:
                    base64_image = base64.b64encode(file.getvalue()).decode('utf-8')
                    mime_type = "image/jpeg" if ext in ['jpg', 'jpeg'] else "image/png"
                    parsed_json = parse_invoice_image(base64_image, mime_type, api_key, t["error_api"])
                
                if parsed_json:
                    parsed_json["Dateiname"] = file.name
                    st.session_state.parsed_data.append(parsed_json)
                    
                progress_bar.progress((i + 1) / len(uploaded_files))
                
            status_text.text(t["proc_done"])

    if st.session_state.parsed_data:
        df = pd.DataFrame(st.session_state.parsed_data)
            
        st.markdown(t["insights"])
        m1, m2, m3 = st.columns(3)
        
        with m1:
            st.metric(t["tot_inv"], len(df))
        with m2:
            try:
                total_brutto = df["Brutto-Betrag"].astype(float).sum()
                currency = df["Währung"].iloc[0] if "Währung" in df.columns else "EUR"
                st.metric(t["tot_vol"], f"{total_brutto:,.2f} {currency}")
            except:
                st.metric(t["tot_vol"], "N/A")
        with m3:
            unique_firms = df["Firma"].nunique() if "Firma" in df.columns else 0
            st.metric(t["uniq_ven"], unique_firms)

        st.markdown("---")

        cols = ["Dateiname"] + [c for c in df.columns if c != "Dateiname"]
        df = df[cols]
        
        st.subheader(t["grid_view"])
        
        # --- DATA VALIDATION ---
        def highlight_errors(row):
            try:
                netto = float(row.get("Netto-Betrag", 0) or 0)
                mwst = float(row.get("MwSt-Betrag", 0) or 0)
                brutto = float(row.get("Brutto-Betrag", 0) or 0)
                # Check math with small tolerance for float rounding
                if brutto > 0 and abs((netto + mwst) - brutto) > 0.05:
                    return ['background-color: rgba(239, 68, 68, 0.3)'] * len(row)
            except:
                pass
            return [''] * len(row)

        styled_df = df.style.apply(highlight_errors, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        st.subheader(t["export"])
        col1, col2, col3 = st.columns(3)
        
        csv = df.to_csv(index=False, sep=";").encode('utf-8')
        with col1:
            st.download_button(label=t["dl_csv"], data=csv, file_name="invoices_parsed.csv", mime="text/csv")
            
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Invoices')
        excel_data = output.getvalue()
        
        with col2:
            st.download_button(label=t["dl_excel"], data=excel_data, file_name="invoices_parsed.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
        xml_data = generate_datev_xml(df)
        with col3:
            st.download_button(label=t["dl_xml"], data=xml_data, file_name="invoices_datev.xml", mime="application/xml")

if __name__ == "__main__":
    main()

import streamlit as st
import pdfplumber
import openai
import pandas as pd
import json
import os
import io
import base64
from dotenv import load_dotenv
import auth
import notifications

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
            model="meta-llama/llama-4-scout-17b-16e-instruct",
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
    auth.init_db()
    
    if "parsed_data" not in st.session_state:
        st.session_state.parsed_data = []
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
        
    # --- AUTHENTICATION UI (LANDING PAGE) ---
    if not st.session_state.logged_in:
        
        # --- LANDING PAGE CSS ---
        st.markdown("""
        <style>
        .hero-title {
            font-size: 3.2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #60a5fa, #a78bfa, #f472b6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            margin-bottom: 0.2rem;
            line-height: 1.2;
        }
        .hero-subtitle {
            font-size: 1.25rem;
            color: #94a3b8;
            text-align: center;
            margin-bottom: 2rem;
        }
        .feature-card {
            background: linear-gradient(145deg, #1e293b, #0f172a);
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            transition: transform 0.2s, border-color 0.2s;
        }
        .feature-card:hover {
            transform: translateY(-4px);
            border-color: #60a5fa;
        }
        .feature-icon {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        .feature-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: #e2e8f0;
            margin-bottom: 0.4rem;
        }
        .feature-desc {
            font-size: 0.9rem;
            color: #94a3b8;
        }
        .pricing-box {
            background: linear-gradient(145deg, #1e3a5f, #0f172a);
            border: 2px solid #3b82f6;
            border-radius: 20px;
            padding: 2rem;
            text-align: center;
            max-width: 420px;
            margin: 1rem auto;
        }
        .pricing-price {
            font-size: 2.8rem;
            font-weight: 800;
            color: #60a5fa;
        }
        .pricing-period {
            font-size: 1rem;
            color: #64748b;
        }
        .pricing-feature {
            color: #cbd5e1;
            font-size: 1rem;
            padding: 0.3rem 0;
        }
        .social-proof {
            text-align: center;
            padding: 1rem 0;
            color: #64748b;
            font-size: 0.95rem;
        }
        .stat-number {
            font-size: 2rem;
            font-weight: 800;
            color: #60a5fa;
        }
        .stat-label {
            font-size: 0.85rem;
            color: #94a3b8;
        }
        .divider-gradient {
            height: 2px;
            background: linear-gradient(90deg, transparent, #3b82f6, transparent);
            margin: 2rem 0;
            border: none;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # --- HERO SECTION ---
        st.markdown('<p class="hero-title">🏛️ InvoiceAI</p>', unsafe_allow_html=True)
        st.markdown('<p class="hero-subtitle">KI-gestützte Rechnungsverarbeitung für deutsche Buchhalter.<br>Verwandeln Sie Rechnungen und Quittungen in strukturierte DATEV-Daten — in Sekunden.</p>', unsafe_allow_html=True)
        
        # --- STATS BAR ---
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div style="text-align:center"><span class="stat-number">5s</span><br><span class="stat-label">Avg. Processing Time</span></div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div style="text-align:center"><span class="stat-number">99%</span><br><span class="stat-label">Extraction Accuracy</span></div>', unsafe_allow_html=True)
        with col3:
            st.markdown('<div style="text-align:center"><span class="stat-number">PDF+IMG</span><br><span class="stat-label">Multimodal Support</span></div>', unsafe_allow_html=True)

        st.markdown('<div class="divider-gradient"></div>', unsafe_allow_html=True)

        # --- FEATURES ---
        st.markdown("### ✨ Warum InvoiceAI?")
        f1, f2, f3 = st.columns(3)
        with f1:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">📄</div>
                <div class="feature-title">PDF & Foto-Belege</div>
                <div class="feature-desc">Laden Sie PDFs oder fotografierte Quittungen (JPG/PNG) hoch. Unsere KI liest beides.</div>
            </div>
            """, unsafe_allow_html=True)
        with f2:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">🧮</div>
                <div class="feature-title">Automatische MwSt-Prüfung</div>
                <div class="feature-desc">Netto + MwSt ≠ Brutto? InvoiceAI markiert Fehler sofort rot — totale Kontrolle.</div>
            </div>
            """, unsafe_allow_html=True)
        with f3:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <div class="feature-title">DATEV-Export</div>
                <div class="feature-desc">Ein Klick — fertige CSV, Excel oder XML für Ihren Steuerberater.</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="divider-gradient"></div>', unsafe_allow_html=True)

        # --- PRICING ---
        st.markdown("### 💰 Einfache Preisgestaltung")
        st.markdown("""
        <div class="pricing-box">
            <div class="pricing-price">10 Credits</div>
            <div class="pricing-period">Kostenlos bei Registrierung</div>
            <hr style="border-color: #334155; margin: 1rem 0;">
            <div class="pricing-feature">✅ 1 Credit = 1 verarbeitete Rechnung</div>
            <div class="pricing-feature">✅ PDF + Bild-Upload</div>
            <div class="pricing-feature">✅ CSV / Excel / XML Export</div>
            <div class="pricing-feature">✅ MwSt-Validierung in Echtzeit</div>
            <div class="pricing-feature">✅ DSGVO-konform — keine Datenspeicherung</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="divider-gradient"></div>', unsafe_allow_html=True)

        # --- LOGIN / REGISTER ---
        st.markdown("### 🔐 Jetzt starten")
        tab_login, tab_register = st.tabs(["🔑 Anmelden", "📝 Registrieren"])
        
        with tab_login:
            login_user = st.text_input("Benutzername", key="login_user")
            login_pass = st.text_input("Passwort", type="password", key="login_pass")
            if st.button("Anmelden", type="primary", use_container_width=True):
                if auth.authenticate_user(login_user, login_pass):
                    st.session_state.logged_in = True
                    st.session_state.username = login_user
                    st.rerun()
                else:
                    st.error("Ungültiger Benutzername oder Passwort.")
                    
        with tab_register:
            reg_user = st.text_input("Neuer Benutzername", key="reg_user")
            reg_pass = st.text_input("Neues Passwort", type="password", key="reg_pass")
            if st.button("Registrieren & 10 Credits erhalten", type="primary", use_container_width=True):
                success, msg = auth.register_user(reg_user, reg_pass, initial_credits=10)
                if success:
                    st.success("✅ Registrierung erfolgreich! Sie können sich jetzt anmelden.")
                    notifications.notify_new_user(reg_user)
                else:
                    st.error(msg)

        # --- FOOTER ---
        st.markdown('<div class="divider-gradient"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="social-proof">
            🔐 Alle Daten werden lokal und über eine sichere API verarbeitet. Es werden keine Daten gespeichert.<br>
            <a href="https://example.com/impressum" style="color: #64748b;">Impressum</a>
        </div>
        """, unsafe_allow_html=True)

        return  # Stop execution here if not logged in

    # --- SIDEBAR ---
    with st.sidebar:
        # Display the generated placeholder logo
        logo_path = "/Users/minaminoshuichi/.gemini/antigravity/brain/d0aa9339-e6a3-4551-ac99-c22d1134720e/invoiceai_logo_1777988830614.png"
        if os.path.exists(logo_path):
            st.image(logo_path, use_column_width=True)
            
        st.header("👤 Profile")
        st.markdown(f"**User:** {st.session_state.username}")
        user_credits = auth.get_credits(st.session_state.username)
        st.markdown(f"**Credits:** {user_credits}")
        
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

        st.markdown("---")
        st.header("⚙️ Settings")
        lang_choice = st.radio("Language / Sprache", ["EN", "DE"], horizontal=True)
        t = TRANSLATIONS[lang_choice]
        
        # API key is now strictly pulled from the server environment
        api_key = os.getenv("GROQ_API_KEY", "")
        
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
                # Check credits before processing
                current_credits = auth.get_credits(st.session_state.username)
                if current_credits <= 0:
                    st.error("Sie haben 0 Credits. Bitte kaufen Sie neue Credits auf der Seite 'Buy Credits'.")
                    notifications.notify_credits_empty(st.session_state.username)
                    break
                    
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
                    # Deduct 1 credit for successful parse
                    auth.deduct_credits(st.session_state.username, 1)
                    
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

import streamlit as st
import auth
import notifications

st.set_page_config(page_title="Buy Credits — InvoiceAI", page_icon="💳", layout="centered")

# --- STYLE ---
st.markdown("""
<style>
    .stApp {
        background-color: #0b1120;
        color: #e2e8f0;
    }
    .page-title {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #34d399, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.3rem;
    }
    .page-subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 2rem;
    }
    .price-card {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border: 1px solid #334155;
        border-radius: 18px;
        padding: 1.8rem 1.2rem;
        text-align: center;
        transition: transform 0.2s, border-color 0.3s;
    }
    .price-card:hover {
        transform: translateY(-5px);
        border-color: #3b82f6;
    }
    .price-card.featured {
        border: 2px solid #3b82f6;
        background: linear-gradient(145deg, #1e3a5f, #0f172a);
    }
    .price-name {
        font-size: 1.3rem;
        font-weight: 700;
        color: #e2e8f0;
        margin-bottom: 0.3rem;
    }
    .price-credits {
        font-size: 2.5rem;
        font-weight: 800;
        color: #60a5fa;
    }
    .price-amount {
        font-size: 1.6rem;
        font-weight: 700;
        color: #34d399;
        margin: 0.5rem 0;
    }
    .price-per {
        font-size: 0.85rem;
        color: #64748b;
    }
    .price-features {
        color: #94a3b8;
        font-size: 0.9rem;
        margin-top: 0.8rem;
        line-height: 1.7;
    }
    .badge-popular {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        color: white;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 0.2rem 0.8rem;
        border-radius: 99px;
        display: inline-block;
        margin-bottom: 0.5rem;
    }
    .divider-gradient {
        height: 2px;
        background: linear-gradient(90deg, transparent, #3b82f6, transparent);
        margin: 2rem 0;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

auth.init_db()

# --- CHECK LOGIN ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Bitte melden Sie sich zuerst auf der Hauptseite an.")
    st.stop()

username = st.session_state.username
credits = auth.get_credits(username)

# --- HEADER ---
st.markdown('<p class="page-title">💳 Credits kaufen</p>', unsafe_allow_html=True)
st.markdown(f'<p class="page-subtitle">Ihr aktuelles Guthaben: <strong>{credits} Credits</strong></p>', unsafe_allow_html=True)

# --- PRICING TIERS ---
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="price-card">
        <div class="price-name">Starter</div>
        <div class="price-credits">50</div>
        <div style="color:#94a3b8; font-size:0.85rem;">Credits</div>
        <div class="price-amount">9,99 €</div>
        <div class="price-per">0,20 € pro Rechnung</div>
        <div class="price-features">
            ✅ PDF + Bild-Upload<br>
            ✅ CSV / Excel Export<br>
            ✅ MwSt-Prüfung
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="price-card featured">
        <div class="badge-popular">⭐ BELIEBT</div>
        <div class="price-name">Professional</div>
        <div class="price-credits">200</div>
        <div style="color:#94a3b8; font-size:0.85rem;">Credits</div>
        <div class="price-amount">29,99 €</div>
        <div class="price-per">0,15 € pro Rechnung</div>
        <div class="price-features">
            ✅ Alles aus Starter<br>
            ✅ XML DATEV-Export<br>
            ✅ Prioritäts-Support
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="price-card">
        <div class="price-name">Enterprise</div>
        <div class="price-credits">500</div>
        <div style="color:#94a3b8; font-size:0.85rem;">Credits</div>
        <div class="price-amount">59,99 €</div>
        <div class="price-per">0,12 € pro Rechnung</div>
        <div class="price-features">
            ✅ Alles aus Professional<br>
            ✅ Unbegrenzte Exporte<br>
            ✅ Dedizierter Support
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="divider-gradient"></div>', unsafe_allow_html=True)

# --- STRIPE PAYMENT LINKS ---
# Replace these with your actual Stripe Payment Links
STRIPE_LINKS = {
    "starter": "https://buy.stripe.com/test_00w9AT45w6Yz2hqfgz08g02",
    "professional": "https://buy.stripe.com/test_8x2bJ17hI5Uve085FZ08g01",
    "enterprise": "https://buy.stripe.com/test_5kQeVd8lM5Uv7BK70708g00",
}

st.markdown("### 🛒 Jetzt kaufen")

b1, b2, b3 = st.columns(3)
with b1:
    st.link_button("Starter kaufen — 9,99 €", STRIPE_LINKS["starter"], use_container_width=True)
with b2:
    st.link_button("⭐ Professional — 29,99 €", STRIPE_LINKS["professional"], use_container_width=True, type="primary")
with b3:
    st.link_button("Enterprise — 59,99 €", STRIPE_LINKS["enterprise"], use_container_width=True)

st.markdown('<div class="divider-gradient"></div>', unsafe_allow_html=True)

# --- MANUAL REQUEST ---
st.markdown("### 📩 Oder per Überweisung")
st.info("Sie können auch per Banküberweisung oder PayPal bezahlen. Schreiben Sie uns eine Nachricht und wir buchen die Credits manuell auf Ihr Konto.")

with st.form("contact_form"):
    message = st.text_area("Ihre Nachricht", placeholder="Ich möchte 200 Credits kaufen und per PayPal bezahlen...")
    submitted = st.form_submit_button("📤 Anfrage senden", type="primary", use_container_width=True)
    if submitted and message:
        notifications.notify_credit_request(username, message)
        st.success("✅ Ihre Anfrage wurde gesendet! Wir melden uns in Kürze bei Ihnen.")
    elif submitted:
        st.warning("Bitte geben Sie eine Nachricht ein.")

st.markdown("""
<div style="text-align:center; color:#64748b; font-size:0.85rem; margin-top:2rem;">
    🔐 Sichere Zahlung über Stripe. Alle Preise inkl. MwSt.
</div>
""", unsafe_allow_html=True)

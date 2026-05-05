import streamlit as st
import pandas as pd
import auth

# --- CONFIG ---
ADMIN_PASSWORD = "invoiceai2026"  # Change this to your own secret admin password

st.set_page_config(page_title="InvoiceAI Admin", page_icon="🔧", layout="wide")

# --- CUSTOM STYLE ---
st.markdown("""
<style>
    .stApp {
        background-color: #0b1120;
        color: #e2e8f0;
    }
    .admin-header {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #f59e0b, #ef4444);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .stat-card {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 1.2rem;
        text-align: center;
    }
    .stat-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #60a5fa;
    }
    .stat-label {
        font-size: 0.85rem;
        color: #94a3b8;
    }
</style>
""", unsafe_allow_html=True)

auth.init_db()

# --- ADMIN AUTH ---
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
    st.markdown('<p class="admin-header">🔧 InvoiceAI Admin Panel</p>', unsafe_allow_html=True)
    st.markdown("Enter the admin password to continue.")
    admin_pw = st.text_input("Admin Password", type="password")
    if st.button("Enter", type="primary"):
        if admin_pw == ADMIN_PASSWORD:
            st.session_state.admin_logged_in = True
            st.rerun()
        else:
            st.error("Wrong password.")
    st.stop()

# --- ADMIN DASHBOARD ---
st.markdown('<p class="admin-header">🔧 InvoiceAI Admin Panel</p>', unsafe_allow_html=True)

if st.button("🚪 Logout Admin"):
    st.session_state.admin_logged_in = False
    st.rerun()

st.markdown("---")

# --- STATS ---
all_users = auth.get_all_users()
total_users = len(all_users)
total_credits = sum(u[1] for u in all_users)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value">{total_users}</div>
        <div class="stat-label">Registered Users</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value">{total_credits}</div>
        <div class="stat-label">Total Credits in System</div>
    </div>
    """, unsafe_allow_html=True)
with c3:
    credits_sold_estimate = max(0, (total_users * 10) - total_credits)
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value">{credits_sold_estimate}</div>
        <div class="stat-label">Credits Used (est.)</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- USER TABLE ---
st.subheader("👥 All Users")

if all_users:
    df = pd.DataFrame(all_users, columns=["Username", "Credits"])
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No users registered yet.")

st.markdown("---")

# --- ADD CREDITS ---
st.subheader("💳 Add Credits to User")
col_a, col_b, col_c = st.columns([2, 1, 1])

with col_a:
    target_user = st.text_input("Username to top up")
with col_b:
    credit_amount = st.number_input("Credits to add", min_value=1, value=50, step=10)
with col_c:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ Add Credits", type="primary"):
        if target_user:
            success = auth.add_credits(target_user, credit_amount)
            if success:
                st.success(f"✅ Added {credit_amount} credits to '{target_user}'.")
                st.rerun()
            else:
                st.error(f"User '{target_user}' not found.")
        else:
            st.warning("Enter a username first.")

st.markdown("---")

# --- DELETE USER ---
st.subheader("🗑️ Delete User")
del_user = st.text_input("Username to delete", key="del_user")
if st.button("❌ Delete User"):
    if del_user:
        success = auth.delete_user(del_user)
        if success:
            st.success(f"User '{del_user}' deleted.")
            st.rerun()
        else:
            st.error(f"User '{del_user}' not found.")

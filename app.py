import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
import json

# -------------------------------
# ✅ Uygulama Temel Ayarları
# -------------------------------
st.set_page_config(
    page_title="AR-NE Tarım Yönetim Sistemi",
    page_icon="🌿",
    layout="centered"
)

PRIMARY = "#064e3b"
ACCENT = "#d4a017"

st.markdown(f"""
<style>
:root {{
  --primary: {PRIMARY};
  --accent: {ACCENT};
}}
h1, h2, h3, h4 {{
  color: var(--primary);
}}
div.stButton>button {{
  background: var(--primary);
  color: white;
  border-radius: 8px;
  border: none;
  font-weight: bold;
}}
div.stButton>button:hover {{
  background: var(--accent);
  color: black;
}}
.stTextInput>div>div>input {{
  border-radius: 6px;
}}
</style>
""", unsafe_allow_html=True)


# -------------------------------
# ✅ Google Sheets Bağlantısı
# -------------------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=SCOPES
)
client = gspread.authorize(creds)

SPREADSHEET_ID = st.secrets["app"]["SPREADSHEET_ID"]
sheet = client.open_by_key(SPREADSHEET_ID)


def get_ws(name="kayitlar"):
    try:
        return sheet.worksheet(name)
    except:
        ws = sheet.add_worksheet(name, 1000, 20)
        ws.append_row(["timestamp", "tarih", "istasyon", "ilac_adi", "dozaj_ml_da", "parsel_no", "uygulayici", "not", "giren_kullanici"])
        return ws


def add_record(row, ws="kayitlar"):
    ws = get_ws(ws)
    ws.append_row(row)


def fetch_all(ws="kayitlar"):
    ws = get_ws(ws)
    return pd.DataFrame(ws.get_all_records())


# -------------------------------
# ✅ Kullanıcı Yönetimi
# -------------------------------
USERS = json.loads(st.secrets["app"]["USERS"])
ISTASYONLAR = st.secrets["app"]["ISTASYONLAR"].split(",")


def login():
    st.markdown("### 🔐 Giriş Yap")
    u = st.text_input("Kullanıcı Adı")
    p = st.text_input("Şifre", type="password")
    if st.button("Giriş"):
        if u in USERS and USERS[u]["password"] == p:
            st.session_state["auth"] = True
            st.session_state["user"] = u
            st.session_state["role"] = USERS[u]["role"]
            st.rerun()
        else:
            st.error("❌ Giriş bilgileri hatalı!")


def logout():
    if st.sidebar.button("🚪 Çıkış Yap"):
        for k in ["auth", "user", "role"]:
            st.session_state.pop(k, None)
        st.rerun()


# -------------------------------
# ✅ Kullanıcı Ekranı – Kayıt Formu
# -------------------------------
def user_page():
    st.sidebar.info(f"Kullanıcı: {st.session_state['user']}")
    logout()

    st.markdown("## 🧪 İlaçlama Kaydı Ekle")

    istasyon = st.selectbox("İstasyon", ISTASYONLAR)
    tarih = st.date_input("Tarih", date.today())
    ilac = st.text_input("İlaç Adı")
    dozaj = st.text_input("Dozaj (ml/da)")
    parsel = st.text_input("Parsel No")
    uygulayici = st.text_input("Uygulayıcı")
    notu = st.text_area("Not")

    if st.button("Kaydı Gönder ✅"):
        if not ilac or not dozaj:
            st.warning("❗ İlaç adı ve dozaj alanı zorunludur.")
            return
        add_record([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            tarih.strftime("%d/%m/%Y"),
            istasyon,
            ilac,
            dozaj,
            parsel,
            uygulayici,
            notu,
            st.session_state["user"]
        ])
        st.success("✅ Kayıt başarıyla eklendi!")


# -------------------------------
# ✅ Patron Paneli – Raporlama
# -------------------------------
def patron_page():
    st.sidebar.success("👑 Patron Paneli")
    logout()
    st.markdown("## 📊 Kayıt Raporları")

    df = fetch_all()
    if df.empty:
        st.info("Henüz kayıt yok.")
        return

    istasyon_filtre = st.multiselect("İstasyon", ISTASYONLAR, default=ISTASYONLAR)
    ilac_filtre = st.text_input("İlaç adı filtrele")

    fdf = df.copy()
    if istasyon_filtre:
        fdf = fdf[fdf["istasyon"].isin(istasyon_filtre)]
    if ilac_filtre:
        fdf = fdf[fdf["ilac_adi"].str.contains(ilac_filtre, case=False, na=False)]

    st.dataframe(fdf, use_container_width=True)

    st.download_button(
        "⬇️ Excel olarak indir",
        fdf.to_csv(index=False).encode("utf-8"),
        file_name="ilac_kayitlari.csv",
        mime="text/csv"
    )


# -------------------------------
# ✅ Uygulama Akışı
# -------------------------------
if not st.session_state.get("auth"):
    login()
else:
    if st.session_state["role"] == "patron":
        patron_page()
    else:
        user_page()

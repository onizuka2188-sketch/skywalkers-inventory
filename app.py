import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from io import BytesIO
from PIL import Image
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---------------------------------------------------------
# [설정] 다크모드 강제 고정 (config.toml 생성)
# ---------------------------------------------------------
def create_config():
    if not os.path.exists(".streamlit"):
        os.makedirs(".streamlit")
    config_path = ".streamlit/config.toml"
    config_content = """
[theme]
base="dark"
primaryColor="#003399"
backgroundColor="#111111"
secondaryBackgroundColor="#000000"
textColor="#FFFFFF"
font="sans serif"
"""
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config_content.strip())
    except: pass

create_config()

# ---------------------------------------------------------
# 메인 코드 시작
# ---------------------------------------------------------

# --- 설정 ---
CLOTHES_SIZES = ["S", "M", "L", "XL", "2XL", "3XL", "4XL", "Free"]
SHOE_SIZES = [str(s) for s in range(250, 325, 5)]
STAFF_ROLES = ["감독", "수석코치", "코치", "트레이너", "전력분석", "통역", "매니저", "닥터"]
CATEGORIES = ["전체보기", "하계용품", "동계용품", "연습복", "유니폼", "양말", "신발"]
MEMO_CATS = ["팀 연혁", "드래프트", "트레이드", "입/퇴사", "부상/재활", "기타 비고"]

# --- ★★★ [구글 시트 연결 - 파일 전용 모드] ★★★ ---
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

@st.cache_resource
def init_connection():
    try:
        # 1. 파일이 있는지 확인
        if not os.path.exists('service_account.json'):
            st.error("🚨 'service_account.json' 파일을 찾을 수 없습니다!")
            st.warning("👉 해결법: 구글 클라우드에서 다운받은 키 파일을 app.py가 있는 폴더에 넣어주세요.")
            return None
        
        # 2. 파일로 연결 시도
        creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', SCOPE)
        client = gspread.authorize(creds)
        return client.open("skywalkers_db")

    except Exception as e:
        st.error(f"❌ 연결 에러 발생: {e}")
        st.info("💡 팁: service_account.json 파일이 손상되었을 수 있습니다. 구글 클라우드에서 키를 새로 발급받아 교체해보세요.")
        return None

sh = init_connection()

# --- 데이터베이스 함수 ---
def get_data(sheet_name):
    if sh:
        try:
            worksheet = sh.worksheet(sheet_name)
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            if df.empty and 'id' not in df.columns: return pd.DataFrame(columns=['id'])
            return df
        except: return pd.DataFrame()
    return pd.DataFrame()

def add_data(sheet_name, row_data):
    if sh:
        worksheet = sh.worksheet(sheet_name)
        try:
            col_vals = worksheet.col_values(1)
            last_id = int(col_vals[-1]) if len(col_vals) > 1 and col_vals[-1].isdigit() else 0
        except: last_id = 0
        row_data.insert(0, last_id + 1)
        worksheet.append_row(row_data)

def update_data(sheet_name, row_id, col_name, new_value):
    if sh:
        worksheet = sh.worksheet(sheet_name)
        try:
            cell = worksheet.find(str(row_id), in_column=1)
            col_idx = worksheet.row_values(1).index(col_name) + 1
            worksheet.update_cell(cell.row, col_idx, new_value)
        except: pass

def delete_data(sheet_name, row_id):
    if sh:
        worksheet = sh.worksheet(sheet_name)
        try:
            cell = worksheet.find(str(row_id), in_column=1)
            worksheet.delete_rows(cell.row)
        except: pass

# --- 이미지 처리 ---
def image_to_base64(image_file):
    if image_file:
        try:
            img = Image.open(image_file).convert('RGB')
            img.thumbnail((300, 300))
            buf = BytesIO()
            img.save(buf, format="JPEG")
            return base64.b64encode(buf.getvalue()).decode()
        except: return ""
    return ""

def get_local_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as f: return base64.b64encode(f.read()).decode()
    return ""

# --- 페이지 설정 ---
st.set_page_config(page_title="SKYWALKERS V-EQ Manager", page_icon="🏐", layout="wide", initial_sidebar_state="expanded")

# --- [디자인] 스파이더 블랙 테마 ---
st.markdown("""
    <style>
    .stApp, [data-testid="stAppViewContainer"] { background-color: #111111 !important; }
    h1, h2, h3, h4, h5, h6, p, span, div, label, li, input, textarea, button { color: #FFFFFF !important; }
    [data-testid="stSidebar"] { background-color: #000000 !important; border-right: 1px solid #333333; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    [data-testid="stSidebar"] .stCaption { color: #999999 !important; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stNumberInput input, .stDateInput input, .stTextArea textarea {
        background-color: #262730 !important; color: #FFFFFF !important; border: 1px solid #444444 !important;
    }
    div[data-baseweb="popover"], ul[data-baseweb="menu"] { background-color: #262730 !important; border: 1px solid #444444 !important; }
    ul[data-baseweb="menu"] li { background-color: #262730 !important; color: #FFFFFF !important; }
    ul[data-baseweb="menu"] li:hover, ul[data-baseweb="menu"] li[aria-selected="true"] { background-color: #003399 !important; color: #FFFFFF !important; }
    div[data-baseweb="select"] span { color: #FFFFFF !important; }
    .stButton > button { background-color: #003399 !important; color: #FFFFFF !important; border: none !important; font-weight: bold; }
    .stButton > button:hover { background-color: #FFFFFF !important; color: #003399 !important; }
    [data-testid="stDataFrame"] { background-color: #111111 !important; }
    [data-testid="stDataFrame"] th { background-color: #003399 !important; color: #FFFFFF !important; }
    [data-testid="stDataFrame"] td { background-color: #111111 !important; color: #FFFFFF !important; border-bottom: 1px solid #333 !important; }
    .main-header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #FFFFFF !important; padding: 15px 20px; border-radius: 12px; margin-bottom: 20px; border-bottom: 4px solid #003399;
    }
    .main-header-container h1 { color: #003399 !important; }
    .main-header-container p { color: #000000 !important; }
    .main-header-container span { color: #000000 !important; }
    div[data-baseweb="calendar"] { background-color: #262730 !important; color: #FFFFFF !important; }
    div[data-baseweb="calendar"] button { color: #FFFFFF !important; }
    div[data-baseweb="calendar"] div { color: #FFFFFF !important; }
    div[data-baseweb="modal"] div { background-color: #222222 !important; color: white !important; }
    [data-testid="stFileUploader"] section { background-color: #262730 !important; }
    </style>
    """, unsafe_allow_html=True)

@st.dialog("🗑️ 삭제 확인")
def confirm_delete_dialog(ids, table_name, rerun_callback):
    st.warning(f"선택한 {len(ids)}개 항목을 영구 삭제합니다.")
    col1, col2 = st.columns(2)
    if col1.button("확인", type="primary", use_container_width=True):
        for i in ids: delete_data(table_name, i)
        st.success("삭제됨"); rerun_callback()
    if col2.button("취소", use_container_width=True): st.rerun()

def main():
    if 'current_menu' not in st.session_state: st.session_state.current_menu = '물품 입고'
    with st.sidebar:
        st.markdown("## 🏐 HYUNDAI CAPITAL\n## SKYWALKERS")
        st.caption(f"제작자 : 네바아빠 | {datetime.now().strftime('%Y-%m-%d')}")
        st.markdown("---")
        st.markdown("### 📦 물품 및 지급")
        if st.button("📥 물품 입고", use_container_width=True): st.session_state.current_menu = "물품 입고"
        if st.button("🎁 지급 하기", use_container_width=True): st.session_state.current_menu = "지급 하기"
        if st.button("📦 재고 현황", use_container_width=True): st.session_state.current_menu = "재고 현황"
        if st.button("📋 전체 내역", use_container_width=True): st.session_state.current_menu = "전체 내역"
        st.markdown("### 👥 인원 및 기록")
        if st.button("🏐 선수 명단", use_container_width=True): st.session_state.current_menu = "선수 명단"
        if st.button("👔 스텝 명단", use_container_width=True): st.session_state.current_menu = "스텝 명단"
        if st.button("📝 비고/연혁", use_container_width=True): st.session_state.current_menu = "비고/연혁"
        st.markdown("---")

    header_html = f"""
    <div class="main-header-container">
        <img src="data:image/png;base64,{get_local_image_base64('logo_skywalkers.png')}" style="height:60px;">
        <div style="text-align:center; flex-grow:1;">
            <h1 style="font-size:2rem; font-weight:900;">HYUNDAI CAPITAL SKYWALKERS</h1>
            <p style="margin:0; font-weight:bold;">EQUIPMENT MANAGEMENT SYSTEM <span>x SPYDER</span></p>
        </div>
        <img src="data:image/png;base64,{get_local_image_base64('logo_spyder.png')}" style="height:60px;">
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    menu = st.session_state.current_menu
    if menu == "물품 입고": page_inbound()
    elif menu == "지급 하기": page_distribute()
    elif menu == "재고 현황": page_inventory()
    elif menu == "선수 명단": page_players()
    elif menu == "스텝 명단": page_staff()
    elif menu == "전체 내역": page_history()
    elif menu == "비고/연혁": page_memo()

def page_inbound():
    st.markdown("### 📥 물품 입고 (ADD ITEMS)")
    if not sh: return
    col1, col2 = st.columns(2)
    i_date = col1.date_input("날짜"); i_cat = col1.selectbox("분류", CATEGORIES[1:]); i_name = col1.text_input("품명")
    i_size = col2.selectbox("사이즈", SHOE_SIZES if i_cat=="신발" else CLOTHES_SIZES)
    i_qty = col2.number_input("수량", 10); i_img = col2.file_uploader("사진", type=['png','jpg'])
    if st.button("입고 확정", use_container_width=True):
        if i_name:
            path = image_to_base64(i_img); df = get_data("inventory")
            exists = False
            if not df.empty and 'item_name' in df.columns:
                match = df[(df['item_name']==i_name)&(df['size']==i_size)&(df['category']==i_cat)]
                if not match.empty:
                    exists=True; rid=match.iloc[0]['id']; q=match.iloc[0]['quantity']
                    update_data("inventory", rid, "quantity", int(q)+int(i_qty))
                    if path: update_data("inventory", rid, "image_path", path)
            if not exists: add_data("inventory", [i_date.strftime("%Y-%m-%d"), i_cat, i_name, i_size, i_qty, path])
            add_data("inbound_logs", [i_date.strftime("%Y-%m-%d"), i_cat, i_name, i_size, i_qty])
            st.success("입고 완료!"); st.rerun()
        else: st.error("품명 입력 필요")

def page_distribute():
    st.markdown("### 🎁 물품 지급 (DISTRIBUTE)")
    if not sh: return
    c1, c2 = st.columns([1,2])
    t_type = c1.radio("구분", ["선수", "스텝"], horizontal=True)
    df = get_data("players" if t_type=="선수" else "staff")
    t_name = c1.selectbox("이름", df['name'].tolist() if not df.empty else [])
    if t_name:
        p = df[df['name']==t_name].iloc[0]
        img = f'<img src="data:image/jpeg;base64,{p["image_path"]}" style="width:100px; height:100px; border-radius:50%; object-fit:cover;">' if str(p['image_path']) else '🏐'
        rn = p['back_number'] if t_type=="선수" else p['role']
        c1.markdown(f"""<div style="background:#003399; padding:15px; border-radius:10px; text-align:center; color:white;">{img}<h3>{rn} {t_name}</h3><p>👕{p['top_size']} 👖{p['bottom_size']} 👟{p['shoe_size']}</p></div>""", unsafe_allow_html=True)
    
    c_filter = c2.selectbox("분류", CATEGORIES)
    inv = get_data("inventory")
    if not inv.empty:
        inv = inv[inv['quantity']>0]
        if c_filter!="전체보기": inv = inv[inv['category']==c_filter]
        item = c2.selectbox("품목", inv['item_name'].unique().tolist() if not inv.empty else [])
        if item:
            stock = inv[inv['item_name']==item]
            s_opt = c2.selectbox("사이즈", [f"{r['size']} (재고:{r['quantity']})" for i,r in stock.iterrows()])
            qty = c2.number_input("수량", 1)
            if c2.button("지급 확정", use_container_width=True):
                row = stock[stock['size']==s_opt.split(" ")[0]].iloc[0]
                if row['quantity'] >= qty:
                    update_data("inventory", row['id'], "quantity", int(row['quantity'])-qty)
                    add_data("logs", [datetime.now().strftime("%Y-%m-%d"), t_type, t_name, item, row['size'], qty])
                    st.success("지급 완료!"); st.rerun()
                else: st.error("재고 부족")

def page_inventory():
    st.markdown("### 📦 재고 현황")
    if not sh: return
    c1, c2 = st.columns(2)
    cat = c1.selectbox("분류", CATEGORIES); search = c2.text_input("검색")
    df = get_data("inventory")
    if not df.empty:
        view = df[df['quantity']>0]
        if cat!="전체보기": view = view[view['category']==cat]
        if search: view = view[view['item_name'].str.contains(search)]
        view = view[['id','category','item_name','size','quantity']]
        view.columns = ['ID','구분','품명','사이즈','수량']
        evt = st.dataframe(view, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")
        if len(evt.selection.rows)>0:
            ids = view.iloc[evt.selection.rows]['ID'].tolist()
            if st.button(f"🗑️ {len(ids)}개 삭제"): confirm_delete_dialog(ids, "inventory", st.rerun)
    
    with st.expander("🛠️ 재고 수정"):
        if not df.empty:
            sel = st.selectbox("품목", [f"{r['id']}:{r['item_name']}-{r['size']}" for i,r in df.iterrows()])
            if sel:
                rid = int(sel.split(":")[0]); row = df[df['id']==rid].iloc[0]
                nn = st.text_input("품명", row['item_name']); nq = st.number_input("수량", value=int(row['quantity']))
                if st.button("수정"):
                    update_data("inventory", rid, "item_name", nn); update_data("inventory", rid, "quantity", nq)
                    st.success("완료"); st.rerun()

def page_players():
    st.markdown("### 🏐 선수 명단")
    if not sh: return
    with st.expander("➕ 선수 등록"):
        c1, c2, c3 = st.columns(3)
        pn = c1.text_input("배번"); nm = c2.text_input("이름"); ps = c3.selectbox("신발", SHOE_SIZES)
        pt = c4 = st.columns(2)[0].selectbox("상의", CLOTHES_SIZES); pb = st.columns(2)[1].selectbox("하의", CLOTHES_SIZES)
        pi = st.file_uploader("사진", type=['png','jpg'])
        if st.button("저장"):
            add_data("players", [nm, pn, pt, pb, ps, image_to_base64(pi)]); st.rerun()
    
    df = get_data("players")
    if not df.empty:
        disp = df[['id','back_number','name','top_size','bottom_size','shoe_size']].copy()
        disp.columns = ['ID','배번','이름','상의','하의','신발']
        evt = st.dataframe(disp, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")
        if len(evt.selection.rows)>0:
            ids = disp.iloc[evt.selection.rows]['ID'].tolist()
            if st.button(f"🗑️ {len(ids)}명 삭제"): confirm_delete_dialog(ids, "players", st.rerun)
        
        with st.expander("🛠️ 수정"):
            tgt = st.selectbox("대상", df['name'].tolist())
            if tgt:
                p = df[df['name']==tgt].iloc[0]
                try: st.image(BytesIO(base64.b64decode(p['image_path'])), width=100)
                except: pass
                c1, c2, c3 = st.columns(3)
                en = c1.text_input("배번", p['back_number'], key="en"); enm = c2.text_input("이름", p['name'], key="enm"); es = c3.selectbox("신발", SHOE_SIZES, index=SHOE_SIZES.index(str(p['shoe_size'])) if str(p['shoe_size']) in SHOE_SIZES else 0, key="es")
                et = st.columns(2)[0].selectbox("상의", CLOTHES_SIZES, index=CLOTHES_SIZES.index(str(p['top_size'])) if str(p['top_size']) in CLOTHES_SIZES else 0, key="et")
                eb = st.columns(2)[1].selectbox("하의", CLOTHES_SIZES, index=CLOTHES_SIZES.index(str(p['bottom_size'])) if str(p['bottom_size']) in CLOTHES_SIZES else 0, key="eb")
                ei = st.file_uploader("사진변경", type=['png','jpg'], key="ei")
                if st.button("수정"):
                    update_data("players", p['id'], "back_number", en); update_data("players", p['id'], "name", enm); update_data("players", p['id'], "shoe_size", es)
                    update_data("players", p['id'], "top_size", et); update_data("players", p['id'], "bottom_size", eb)
                    if ei: update_data("players", p['id'], "image_path", image_to_base64(ei))
                    st.success("완료"); st.rerun()

def page_staff():
    st.markdown("### 👔 스텝 명단")
    if not sh: return
    with st.expander("➕ 스텝 등록"):
        c1, c2 = st.columns(2)
        sr = c1.selectbox("직책", STAFF_ROLES); sn = c2.text_input("이름")
        st_t = st.columns(3)[0].selectbox("상의", CLOTHES_SIZES, key="stt"); st_b = st.columns(3)[1].selectbox("하의", CLOTHES_SIZES, key="stb"); st_s = st.columns(3)[2].selectbox("신발", SHOE_SIZES, key="sts")
        si = st.file_uploader("사진", type=['png','jpg'])
        if st.button("저장"):
            add_data("staff", [sn, sr, st_t, st_b, st_s, image_to_base64(si)]); st.rerun()
    
    df = get_data("staff")
    if not df.empty:
        disp = df[['id','role','name','top_size','bottom_size','shoe_size']].copy()
        disp.columns = ['ID','직책','이름','상의','하의','신발']
        evt = st.dataframe(disp, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")
        if len(evt.selection.rows)>0:
            ids = disp.iloc[evt.selection.rows]['ID'].tolist()
            if st.button(f"🗑️ {len(ids)}명 삭제"): confirm_delete_dialog(ids, "staff", st.rerun)
        
        with st.expander("🛠️ 수정"):
            tgt = st.selectbox("대상", df['name'].tolist())
            if tgt:
                s = df[df['name']==tgt].iloc[0]
                try: st.image(BytesIO(base64.b64decode(s['image_path'])), width=100)
                except: pass
                c1, c2 = st.columns(2)
                er = c1.selectbox("직책", STAFF_ROLES, index=STAFF_ROLES.index(s['role']) if s['role'] in STAFF_ROLES else 0, key="er")
                enm = c2.text_input("이름", s['name'], key="senm")
                et = st.columns(3)[0].selectbox("상의", CLOTHES_SIZES, index=CLOTHES_SIZES.index(str(s['top_size'])) if str(s['top_size']) in CLOTHES_SIZES else 0, key="set")
                eb = st.columns(3)[1].selectbox("하의", CLOTHES_SIZES, index=CLOTHES_SIZES.index(str(s['bottom_size'])) if str(s['bottom_size']) in CLOTHES_SIZES else 0, key="seb")
                es = st.columns(3)[2].selectbox("신발", SHOE_SIZES, index=SHOE_SIZES.index(str(s['shoe_size'])) if str(s['shoe_size']) in SHOE_SIZES else 0, key="ses")
                ei = st.file_uploader("사진변경", type=['png','jpg'], key="sei")
                if st.button("수정"):
                    update_data("staff", s['id'], "role", er); update_data("staff", s['id'], "name", enm); update_data("staff", s['id'], "top_size", et)
                    update_data("staff", s['id'], "bottom_size", eb); update_data("staff", s['id'], "shoe_size", es)
                    if ei: update_data("staff", s['id'], "image_path", image_to_base64(ei))
                    st.success("완료"); st.rerun()

def page_history():
    st.markdown("### 📋 전체 내역")
    if not sh: return
    t1, t2 = st.tabs(["📤 지급", "📥 입고"])
    with t1:
        search = st.text_input("검색")
        df = get_data("logs")
        if not df.empty:
            if search: df = df[df['target_name'].str.contains(search)]
            df = df.sort_values('id', ascending=False)
            disp = df[['id','date','target_name','item_name','size','quantity']].copy()
            disp.columns = ['ID','날짜','이름','품명','사이즈','수량']
            evt = st.dataframe(disp, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")
            if len(evt.selection.rows)>0:
                ids = disp.iloc[evt.selection.rows]['ID'].tolist()
                if st.button(f"🗑️ {len(ids)}개 삭제"): confirm_delete_dialog(ids, "logs", st.rerun)
    with t2:
        df = get_data("inbound_logs")
        if not df.empty:
            df = df.sort_values('id', ascending=False)
            disp = df[['id','date','item_name','size','quantity']].copy()
            disp.columns = ['ID','날짜','품명','사이즈','수량']
            evt = st.dataframe(disp, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")
            if len(evt.selection.rows)>0:
                ids = disp.iloc[evt.selection.rows]['ID'].tolist()
                if st.button(f"🗑️ {len(ids)}개 삭제"): confirm_delete_dialog(ids, "inbound_logs", st.rerun)

def page_memo():
    st.markdown("### 📝 비고")
    if not sh: return
    with st.form("m"):
        c1, c2 = st.columns([1,2])
        d = c1.date_input("날짜"); c = c2.selectbox("구분", MEMO_CATS); t = st.text_area("내용")
        if st.form_submit_button("저장"): add_data("memos", [d.strftime("%Y-%m-%d"), c, t]); st.rerun()
    df = get_data("memos")
    if not df.empty: st.dataframe(df.sort_values('id', ascending=False), use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from io import BytesIO
from PIL import Image
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 설정 ---
CLOTHES_SIZES = ["S", "M", "L", "XL", "2XL", "3XL", "4XL", "Free"]
SHOE_SIZES = [str(s) for s in range(250, 325, 5)]
STAFF_ROLES = ["감독", "수석코치", "코치", "트레이너", "전력분석", "통역", "매니저", "닥터"]
CATEGORIES = ["전체보기", "하계용품", "동계용품", "연습복", "유니폼", "양말", "신발"]
MEMO_CATS = ["팀 연혁", "드래프트", "트레이드", "입/퇴사", "부상/재활", "기타 비고"]

# --- [긴급 처방] 다크모드 강제 고정 설정 ---
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

# --- 구글 스프레드시트 연결 설정 (로컬/웹 자동 감지) ---
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

@st.cache_resource
def init_connection():
    try:
        # 1. 내 컴퓨터(로컬) 파일 확인
        if os.path.exists('service_account.json'):
            creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', SCOPE)
            client = gspread.authorize(creds)
            return client.open("skywalkers_db")
        
        # 2. 웹(Streamlit Cloud) Secrets 확인
        elif "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
            client = gspread.authorize(creds)
            return client.open("skywalkers_db")
            
        else:
            st.error("🚨 인증 파일을 찾을 수 없습니다! (service_account.json 또는 Secrets)")
            return None

    except Exception as e:
        st.error(f"❌ 구글 시트 연결 실패: {e}")
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
            last_id = int(col_vals[-1]) if len(col_vals) > 1 and str(col_vals[-1]).isdigit() else 0
        except: last_id = 0
        row_data.insert(0, last_id + 1)
        worksheet.append_row(row_data)

def update_data(sheet_name, row_id, col_name, new_value):
    if sh:
        worksheet = sh.worksheet(sheet_name)
        try:
            cell = worksheet.find(str(row_id), in_column=1)
            header = worksheet.row_values(1)
            col_idx = header.index(col_name) + 1
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

# --- [디자인] 스파이더 블랙 테마 (완벽 수리) ---
st.markdown("""
    <style>
    /* 1. 전체 배경 */
    .stApp, [data-testid="stAppViewContainer"] { background-color: #111111 !important; }
    
    /* 2. 기본 글씨 */
    h1, h2, h3, h4, h5, h6, p, span, div, label, li, input, textarea, button { color: #FFFFFF !important; }

    /* 3. 사이드바 */
    [data-testid="stSidebar"] { background-color: #000000 !important; border-right: 1px solid #333333; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    [data-testid="stSidebar"] .stCaption { color: #999999 !important; font-size: 14px !important; }

    /* 4. 입력창 */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stNumberInput input, .stDateInput input, .stTextArea textarea {
        background-color: #262730 !important; color: #FFFFFF !important; border: 1px solid #444444 !important;
    }
    
    /* 5. 드롭다운 메뉴 (검은 배경 + 흰 글씨) */
    div[data-baseweb="popover"], ul[data-baseweb="menu"] { 
        background-color: #262730 !important; 
        border: 1px solid #444444 !important; 
    }
    ul[data-baseweb="menu"] li { 
        background-color: #262730 !important; 
        color: #FFFFFF !important; 
    }
    ul[data-baseweb="menu"] li:hover, ul[data-baseweb="menu"] li[aria-selected="true"] { 
        background-color: #003399 !important; 
        color: #FFFFFF !important; 
    }
    div[data-baseweb="select"] span { 
        color: #FFFFFF !important; 
    }

    /* 6. 버튼 */
    .stButton > button { background-color: #003399 !important; color: #FFFFFF !important; border: none !important; font-weight: bold; }
    .stButton > button:hover { background-color: #FFFFFF !important; color: #003399 !important; }

    /* 7. 표 */
    [data-testid="stDataFrame"] { background-color: #111111 !important; }
    [data-testid="stDataFrame"] th { background-color: #003399 !important; color: #FFFFFF !important; }
    [data-testid="stDataFrame"] td { background-color: #111111 !important; color: #FFFFFF !important; border-bottom: 1px solid #333 !important; }

    /* 8. 확장 패널 */
    .streamlit-expanderHeader { background-color: #222222 !important; color: #FFFFFF !important; border: 1px solid #444; }
    .streamlit-expanderContent { background-color: #111111 !important; color: #FFFFFF !important; border-top: 1px solid #444; }

    /* 9. 헤더 로고 박스 */
    .main-header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #FFFFFF !important; padding: 15px 20px; border-radius: 12px; margin-bottom: 20px; border-bottom: 4px solid #003399;
    }
    .main-header-container h1 { color: #003399 !important; }
    .main-header-container p { color: #000000 !important; }
    .main-header-container span { color: #000000 !important; }

    /* 10. 달력 */
    div[data-baseweb="calendar"] { background-color: #262730 !important; color: #FFFFFF !important; }
    div[data-baseweb="calendar"] button { color: #FFFFFF !important; }
    div[data-baseweb="calendar"] div { color: #FFFFFF !important; }
    div[data-baseweb="modal"] div { background-color: #222222 !important; color: white !important; }
    [data-testid="stFileUploader"] section { background-color: #262730 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- [NEW] 삭제 확인 팝업창 함수 ---
@st.dialog("🗑️ 삭제 확인")
def confirm_delete_dialog(ids, table_name, rerun_callback):
    st.warning(f"선택한 {len(ids)}개 항목을 정말 삭제하시겠습니까?")
    st.markdown("삭제 후에는 복구할 수 없습니다. (구글 시트에서 삭제됨)")
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("확인 (삭제)", type="primary", use_container_width=True):
            for row_id in ids:
                delete_data(table_name, row_id)
            st.success("삭제되었습니다.")
            rerun_callback()
    with col_b:
        if st.button("취소", use_container_width=True):
            st.rerun()

# --- 메인 앱 로직 ---
def main():
    if 'current_menu' not in st.session_state:
        st.session_state.current_menu = '물품 입고'

    with st.sidebar:
        st.markdown("## 🏐 HYUNDAI CAPITAL")
        st.markdown("## SKYWALKERS")
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
        <img src="data:image/png;base64,{get_local_image_base64('logo_skywalkers.png')}" style="height:60px;" alt="Skywalkers">
        <div style="text-align:center; flex-grow:1;">
            <h1 style="font-size:2rem; font-weight:900;">HYUNDAI CAPITAL SKYWALKERS</h1>
            <p style="margin:0; font-weight:bold;">EQUIPMENT MANAGEMENT SYSTEM <span>x SPYDER</span></p>
        </div>
        <img src="data:image/png;base64,{get_local_image_base64('logo_spyder.png')}" style="height:60px;" alt="Spyder">
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

# 1. 물품 입고 (구글 시트)
def page_inbound():
    st.markdown("### 📥 물품 입고 (ADD ITEMS)")
    if not sh: 
        st.warning("⚠️ service_account.json 파일이 없거나 Secrets 설정이 필요합니다.")
        return
    
    st.info("구글 스프레드시트에 자동 저장됩니다.")
    
    col1, col2 = st.columns(2)
    with col1:
        i_date = st.date_input("입고 날짜", datetime.now())
        i_cat = st.selectbox("카테고리", CATEGORIES[1:])
        i_name = st.text_input("품명 (예: 반팔티)")
    with col2:
        if i_cat == "신발": i_size = st.selectbox("사이즈", SHOE_SIZES)
        else: i_size = st.selectbox("사이즈", CLOTHES_SIZES)
        i_qty = st.number_input("입고 수량", min_value=1, value=10)
        i_img = st.file_uploader("사진", type=['png', 'jpg', 'jpeg'])

    if st.button("📥 입고 확정", use_container_width=True):
        if i_name:
            img_path = image_to_base64(i_img)
            inv_df = get_data("inventory")
            exists = False
            if not inv_df.empty and 'item_name' in inv_df.columns:
                match = inv_df[(inv_df['item_name'] == i_name) & (inv_df['size'] == i_size) & (inv_df['category'] == i_cat)]
                if not match.empty:
                    exists = True
                    row_id = match.iloc[0]['id']
                    curr_qty = match.iloc[0]['quantity']
                    update_data("inventory", row_id, "quantity", int(curr_qty) + int(i_qty))
                    if img_path: update_data("inventory", row_id, "image_path", img_path)

            if not exists:
                add_data("inventory", [i_date.strftime("%Y-%m-%d"), i_cat, i_name, i_size, i_qty, img_path])
            
            add_data("inbound_logs", [i_date.strftime("%Y-%m-%d"), i_cat, i_name, i_size, i_qty])
            st.success(f"✅ {i_name} ({i_size}) {i_qty}개 입고 및 저장 완료!")
        else: st.error("품명을 입력해주세요.")

# 2. 지급 페이지 (구글 시트)
def page_distribute():
    st.markdown("### 🎁 물품 지급 (DISTRIBUTE)")
    if not sh: return
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.markdown("#### 1. 대상 선택")
        t_type = st.radio("구분", ["선수", "스텝"], horizontal=True)
        df_people = get_data("players" if t_type == "선수" else "staff")
        names = df_people['name'].tolist() if not df_people.empty and 'name' in df_people.columns else []
        t_name = st.selectbox("이름", names if names else ["없음"])
        
        if t_name != "없음" and not df_people.empty:
            person = df_people[df_people['name'] == t_name].iloc[0]
            img_html = ""
            try:
                img_data = str(person['image_path'])
                if len(img_data) > 50:
                    img_html = f'<img src="data:image/jpeg;base64,{img_data}" style="width:120px; height:120px; object-fit:cover; border-radius:50%; border:3px solid white; margin-bottom:10px;">'
                else:
                    img_html = '<div style="width:120px; height:120px; background-color:#ddd; border-radius:50%; border:3px solid white; display:flex; align-items:center; justify-content:center; margin:0 auto 10px auto; color:black; font-weight:bold; font-size:40px;">🏐</div>'
            except:
                img_html = '<div style="width:120px; height:120px; background-color:#ddd; border-radius:50%; border:3px solid white; display:flex; align-items:center; justify-content:center; margin:0 auto 10px auto; color:black; font-weight:bold; font-size:40px;">🏐</div>'

            role_or_num = person['back_number'] if t_type == "선수" else person['role']
            st.markdown(f"""
            <div style="background-color:#003399; padding:20px; border-radius:15px; box-shadow: 0 4px 8px rgba(0,0,0,0.5); border: 1px solid #333; text-align:center;">
                {img_html}
                <h2 style="color:white !important; margin:0; padding-bottom:10px; border-bottom:2px solid white;">{role_or_num} {t_name}</h2>
                <div style="margin-top:15px; text-align:left; padding-left:10px;">
                    <p style="color:white !important; font-size:1.2rem; margin:5px 0;">👕 상의: <b style="color:#FFD700;">{person['top_size']}</b></p>
                    <p style="color:white !important; font-size:1.2rem; margin:5px 0;">👖 하의: <b style="color:#FFD700;">{person['bottom_size']}</b></p>
                    <p style="color:white !important; font-size:1.2rem; margin:5px 0;">👟 신발: <b style="color:#FFD700;">{person['shoe_size']}</b></p>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with c2:
        st.markdown("#### 2. 물품 선택")
        c_filter = st.selectbox("카테고리 선택", CATEGORIES)
        inv_df = get_data("inventory")
        if not inv_df.empty and 'quantity' in inv_df.columns:
            inv_df = inv_df[inv_df['quantity'] > 0]
            if c_filter != "전체보기": inv_df = inv_df[inv_df['category'] == c_filter]
            items = inv_df['item_name'].unique().tolist()
            s_item = st.selectbox("품목 선택", items if items else ["재고 없음"])
            
            if s_item != "재고 없음":
                stock_data = inv_df[inv_df['item_name'] == s_item]
                size_opts = {f"{row['size']} (재고: {row['quantity']})": row for idx, row in stock_data.iterrows()}
                s_size_opt = st.selectbox("사이즈 선택", list(size_opts.keys()))
                qty = st.number_input("수량", 1, value=1)
                
                if st.button("🚀 지급 확정", use_container_width=True):
                    sel_row = size_opts[s_size_opt]
                    current_qty = int(sel_row['quantity'])
                    if current_qty >= qty:
                        update_data("inventory", sel_row['id'], "quantity", current_qty - qty)
                        add_data("logs", [datetime.now().strftime("%Y-%m-%d"), t_type, t_name, s_item, sel_row['size'], qty])
                        st.success("지급 완료 및 저장됨!")
                        st.rerun()
                    else: st.error("재고 부족")
        else:
            st.warning("재고 데이터가 없습니다.")

# 3. 재고 현황 (구글 시트)
def page_inventory():
    st.markdown("### 📦 재고 현황")
    if not sh: return
    c1, c2 = st.columns(2)
    v_cat = c1.selectbox("카테고리", CATEGORIES)
    search = c2.text_input("검색")
    df = get_data("inventory")
    if not df.empty and 'quantity' in df.columns:
        df_view = df[df['quantity'] > 0]
        if v_cat != "전체보기":
            df_view = df_view[df_view['category'] == v_cat]
        if search:
            df_view = df_view[df_view['item_name'].str.contains(search)]
        
        view_cols = ['id', 'category', 'item_name', 'size', 'quantity']
        event = st.dataframe(df_view[view_cols], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row", key="inv_event")
        
        if len(event.selection.rows) > 0:
            selected_indices = event.selection.rows
            ids_to_delete = df_view.iloc[selected_indices]['id'].tolist()
            if st.button(f"🗑️ 선택한 {len(ids_to_delete)}개 항목 삭제", type="primary"):
                confirm_delete_dialog(ids_to_delete, "inventory", st.rerun)

    with st.expander("🛠️ 재고 정보 수정"):
        if not df.empty:
            item_list = [f"{row['id']}: {row['item_name']} - {row['size']}" for idx, row in df.iterrows()]
            edit_item = st.selectbox("수정할 품목", item_list)
            if edit_item:
                sel_id = int(edit_item.split(":")[0])
                curr_row = df[df['id'] == sel_id].iloc[0]
                new_name = st.text_input("품명", value=curr_row['item_name'])
                new_qty = st.number_input("수량", value=int(curr_row['quantity']))
                if st.button("수정 저장"):
                    update_data("inventory", sel_id, "item_name", new_name)
                    update_data("inventory", sel_id, "quantity", new_qty)
                    st.success("수정 완료")
                    st.rerun()

# 4. 선수 명단 (구글 시트)
def page_players():
    st.markdown("### 🏐 선수 명단")
    if not sh: return
    with st.expander("➕ 선수 등록"):
        c1, c2, c3 = st.columns(3)
        p_num = c1.text_input("배번")
        p_name = c2.text_input("이름")
        p_shoe = c3.selectbox("신발", SHOE_SIZES)
        c4, c5 = st.columns(2)
        p_top = c4.selectbox("상의", CLOTHES_SIZES)
        p_bot = c5.selectbox("하의", CLOTHES_SIZES)
        p_img = st.file_uploader("프로필 사진", type=['png', 'jpg'])
        if st.button("저장"):
            img_b64 = image_to_base64(p_img)
            add_data("players", [p_name, p_num, p_top, p_bot, p_shoe, img_b64])
            st.rerun()
            
    df = get_data("players")
    if not df.empty:
        # [한글 컬럼명 표시]
        df_display = df[['id','back_number','name','top_size','bottom_size','shoe_size']].copy()
        df_display.columns = ['ID', '배번', '이름', '상의', '하의', '신발']
        
        event = st.dataframe(df_display, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")
        if len(event.selection.rows) > 0:
            selected_rows = df_display.iloc[event.selection.rows]
            ids_to_delete = selected_rows['ID'].tolist()
            if st.button(f"🗑️ 선택한 {len(ids_to_delete)}명 삭제", type="primary"):
                confirm_delete_dialog(ids_to_delete, "players", st.rerun)

        # [수정] 선수 정보 수정
        with st.expander("🛠️ 정보 수정"):
            edit_target = st.selectbox("수정 대상", df['name'].tolist())
            if edit_target:
                p_curr = df[df['name'] == edit_target].iloc[0]
                try:
                    if str(p_curr['image_path']) and len(str(p_curr['image_path'])) > 50:
                        st.image(BytesIO(base64.b64decode(p_curr['image_path'])), width=100)
                except: pass
                
                ec1, ec2, ec3 = st.columns(3)
                e_num = ec1.text_input("배번", value=str(p_curr['back_number']), key="epn")
                e_name = ec2.text_input("이름", value=p_curr['name'], key="epnn")
                e_shoe = ec3.selectbox("신발", SHOE_SIZES, index=SHOE_SIZES.index(str(p_curr['shoe_size'])) if str(p_curr['shoe_size']) in SHOE_SIZES else 0, key="eps")
                
                ec4, ec5 = st.columns(2)
                e_top = ec4.selectbox("상의", CLOTHES_SIZES, index=CLOTHES_SIZES.index(str(p_curr['top_size'])) if str(p_curr['top_size']) in CLOTHES_SIZES else 0, key="ept")
                e_bot = ec5.selectbox("하의", CLOTHES_SIZES, index=CLOTHES_SIZES.index(str(p_curr['bottom_size'])) if str(p_curr['bottom_size']) in CLOTHES_SIZES else 0, key="epb")
                
                e_img = st.file_uploader("사진 변경 (선택)", type=['png', 'jpg'], key="p_edit_img")

                if st.button("수정 완료", key="bpe"):
                    update_data("players", p_curr['id'], "back_number", e_num)
                    update_data("players", p_curr['id'], "name", e_name)
                    update_data("players", p_curr['id'], "shoe_size", e_shoe)
                    update_data("players", p_curr['id'], "top_size", e_top)
                    update_data("players", p_curr['id'], "bottom_size", e_bot)
                    if e_img:
                        new_img = image_to_base64(e_img)
                        update_data("players", p_curr['id'], "image_path", new_img)
                    st.success("수정 완료")
                    st.rerun()

# 5. 스텝 명단 (구글 시트)
def page_staff():
    st.markdown("### 👔 스텝 명단")
    if not sh: return
    with st.expander("➕ 스텝 등록"):
        c1, c2 = st.columns(2)
        s_role = c1.selectbox("직책", STAFF_ROLES)
        s_name = c2.text_input("이름")
        c3, c4, c5 = st.columns(3)
        s_top = c3.selectbox("상의", CLOTHES_SIZES, key="st")
        s_bot = c4.selectbox("하의", CLOTHES_SIZES, key="sb")
        s_shoe = c5.selectbox("신발", SHOE_SIZES, key="ss")
        s_img = st.file_uploader("프로필 사진", type=['png', 'jpg'])
        if st.button("저장"):
            img_b64 = image_to_base64(s_img)
            add_data("staff", [s_name, s_role, s_top, s_bot, s_shoe, img_b64])
            st.rerun()

    df = get_data("staff")
    if not df.empty:
        # [한글 컬럼명 표시]
        df_display = df[['id','role','name','top_size','bottom_size','shoe_size']].copy()
        df_display.columns = ['ID', '직책', '이름', '상의', '하의', '신발']

        event = st.dataframe(df_display, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")
        if len(event.selection.rows) > 0:
            selected_rows = df_display.iloc[event.selection.rows]
            ids_to_delete = selected_rows['ID'].tolist()
            if st.button(f"🗑️ 선택한 {len(ids_to_delete)}명 삭제", type="primary"):
                confirm_delete_dialog(ids_to_delete, "staff", st.rerun)
        
        # [추가됨] 스텝 정보 수정 기능
        with st.expander("🛠️ 정보 수정"):
            edit_target = st.selectbox("수정 대상", df['name'].tolist())
            if edit_target:
                s_curr = df[df['name'] == edit_target].iloc[0]
                try:
                    if str(s_curr['image_path']) and len(str(s_curr['image_path'])) > 50:
                        st.image(BytesIO(base64.b64decode(s_curr['image_path'])), width=100)
                except: pass
                
                ec1, ec2 = st.columns(2)
                e_role = ec1.selectbox("직책", STAFF_ROLES, index=STAFF_ROLES.index(s_curr['role']) if s_curr['role'] in STAFF_ROLES else 0, key="esr")
                e_name = ec2.text_input("이름", value=s_curr['name'], key="esn")
                
                ec3, ec4, ec5 = st.columns(3)
                e_top = ec3.selectbox("상의", CLOTHES_SIZES, index=CLOTHES_SIZES.index(str(s_curr['top_size'])) if str(s_curr['top_size']) in CLOTHES_SIZES else 0, key="est")
                e_bot = ec4.selectbox("하의", CLOTHES_SIZES, index=CLOTHES_SIZES.index(str(s_curr['bottom_size'])) if str(s_curr['bottom_size']) in CLOTHES_SIZES else 0, key="esb")
                e_shoe = ec5.selectbox("신발", SHOE_SIZES, index=SHOE_SIZES.index(str(s_curr['shoe_size'])) if str(s_curr['shoe_size']) in SHOE_SIZES else 0, key="ess")
                
                e_img = st.file_uploader("사진 변경 (선택)", type=['png', 'jpg'], key="s_img_edit")

                if st.button("수정 완료", key="bse"):
                    update_data("staff", s_curr['id'], "role", e_role)
                    update_data("staff", s_curr['id'], "name", e_name)
                    update_data("staff", s_curr['id'], "top_size", e_top)
                    update_data("staff", s_curr['id'], "bottom_size", e_bot)
                    update_data("staff", s_curr['id'], "shoe_size", e_shoe)
                    if e_img:
                        new_img = image_to_base64(e_img)
                        update_data("staff", s_curr['id'], "image_path", new_img)
                    st.success("수정 완료")
                    st.rerun()

# 6. 전체 내역 (구글 시트)
def page_history():
    st.markdown("### 📋 전체 내역")
    if not sh: return
    t1, t2 = st.tabs(["📤 지급 내역", "📥 입고 내역"])
    with t1:
        search = st.text_input("이름 검색")
        df_out = get_data("logs")
        if not df_out.empty:
            if search: df_out = df_out[df_out['target_name'].str.contains(search)]
            df_out = df_out.sort_values(by='id', ascending=False)
            
            # [한글 컬럼명]
            df_disp = df_out[['id','date','target_name','item_name','size','quantity']].copy()
            df_disp.columns = ['ID','날짜','이름','품명','사이즈','수량']

            event_out = st.dataframe(df_disp, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")
            if len(event_out.selection.rows) > 0:
                ids = df_disp.iloc[event_out.selection.rows]['ID'].tolist()
                if st.button(f"🗑️ 선택한 {len(ids)}개 지급 내역 삭제", type="primary"):
                    confirm_delete_dialog(ids, "logs", st.rerun)

    with t2:
        df_in = get_data("inbound_logs")
        if not df_in.empty:
            df_in = df_in.sort_values(by='id', ascending=False)
            # [한글 컬럼명]
            df_disp_in = df_in[['id','date','item_name','size','quantity']].copy()
            df_disp_in.columns = ['ID','날짜','품명','사이즈','수량']

            event_in = st.dataframe(df_disp_in, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")
            if len(event_in.selection.rows) > 0:
                ids = df_disp_in.iloc[event_in.selection.rows]['ID'].tolist()
                if st.button(f"🗑️ 선택한 {len(ids)}개 입고 내역 삭제", type="primary"):
                    confirm_delete_dialog(ids, "inbound_logs", st.rerun)

# 7. 비고
def page_memo():
    st.markdown("### 📝 비고")
    if not sh: return
    with st.form("memo"):
        c1, c2 = st.columns([1,2])
        d = c1.date_input("날짜"); c = c2.selectbox("구분", MEMO_CATS)
        t = st.text_area("내용")
        if st.form_submit_button("저장"):
            add_data("memos", [d.strftime("%Y-%m-%d"), c, t])
            st.rerun()
    df = get_data("memos")
    if not df.empty:
        st.dataframe(df.sort_values(by='id', ascending=False), use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()

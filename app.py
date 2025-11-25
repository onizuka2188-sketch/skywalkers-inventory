import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
import base64
from io import BytesIO
from PIL import Image

# --- 설정 ---
CLOTHES_SIZES = ["S", "M", "L", "XL", "2XL", "3XL", "4XL", "Free"]
SHOE_SIZES = [str(s) for s in range(250, 325, 5)]
STAFF_ROLES = ["감독", "수석코치", "코치", "트레이너", "전력분석", "통역", "매니저", "닥터"]
CATEGORIES = ["전체보기", "하계용품", "동계용품", "연습복", "유니폼", "양말", "신발"]
MEMO_CATS = ["팀 연혁", "드래프트", "트레이드", "입/퇴사", "부상/재활", "기타 비고"]
DB_FILENAME = "skywalkers_data.db"

# 폴더 생성 확인
if not os.path.exists("item_images"): os.makedirs("item_images")
if not os.path.exists("profile_images"): os.makedirs("profile_images")

# --- 페이지 설정 ---
st.set_page_config(
    page_title="SKYWALKERS V-EQ Manager",
    page_icon="🏐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- [CSS 정의] 스파이더 블랙 테마 (강제 고정) ---
st.markdown("""
    <style>
    /* 1. 전체 배경 */
    .stApp, [data-testid="stAppViewContainer"] { background-color: #111111 !important; }
    
    /* 2. 기본 글씨 */
    h1, h2, h3, h4, h5, h6, p, span, div, label, li, input, textarea { color: #FFFFFF !important; }

    /* 3. 사이드바 */
    [data-testid="stSidebar"] { background-color: #000000 !important; border-right: 1px solid #333333; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    [data-testid="stSidebar"] .stCaption { color: #999999 !important; font-size: 14px !important; }

    /* 4. 입력창 */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stNumberInput input, .stDateInput input, .stTextArea textarea {
        background-color: #262730 !important; color: #FFFFFF !important; border: 1px solid #444444 !important;
    }
    
    /* 5. 드롭다운 메뉴 */
    div[data-baseweb="popover"], ul[data-baseweb="menu"] { background-color: #262730 !important; border: 1px solid #444444 !important; }
    ul[data-baseweb="menu"] li { background-color: #262730 !important; color: #FFFFFF !important; }
    ul[data-baseweb="menu"] li:hover { background-color: #003399 !important; color: #FFFFFF !important; }
    div[data-baseweb="select"] span { color: #FFFFFF !important; }

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
    
    /* 11. 팝업창(모달) 스타일 */
    div[data-baseweb="modal"] div { background-color: #222222 !important; color: white !important; }
    
    /* 12. 파일 업로더 */
    [data-testid="stFileUploader"] { background-color: #262730; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- DB 함수 ---
def init_db():
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS players (id INTEGER PRIMARY KEY, name TEXT, back_number TEXT, top_size TEXT, bottom_size TEXT, shoe_size TEXT, image_path TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS staff (id INTEGER PRIMARY KEY, name TEXT, role TEXT, top_size TEXT, bottom_size TEXT, shoe_size TEXT, image_path TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY, date TEXT, category TEXT, item_name TEXT, size TEXT, quantity INTEGER DEFAULT 0, image_path TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY, date TEXT, target_type TEXT, target_name TEXT, item_name TEXT, size TEXT, quantity INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS inbound_logs (id INTEGER PRIMARY KEY, date TEXT, category TEXT, item_name TEXT, size TEXT, quantity INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS memos (id INTEGER PRIMARY KEY, date TEXT, category TEXT, content TEXT)')
    conn.commit()
    conn.close()

def run_query(query, params=(), fetch=True):
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute(query, params)
    if fetch:
        data = c.fetchall()
        conn.close()
        return data
    else:
        conn.commit()
        conn.close()
        return None

def get_dataframe(query, params=()):
    conn = sqlite3.connect(DB_FILENAME)
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

# --- 이미지 처리 함수 (Base64 변환) ---
def image_to_base64(image_file):
    if image_file is not None:
        try:
            img = Image.open(image_file)
            img = img.convert('RGB')
            img.thumbnail((300, 300)) 
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            return base64.b64encode(buffered.getvalue()).decode()
        except Exception as e:
            return ""
    return ""

def get_local_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

# --- [NEW] 삭제 확인 팝업창 함수 ---
@st.dialog("🗑️ 삭제 확인")
def confirm_delete_dialog(ids, table_name, rerun_callback):
    st.warning(f"선택한 {len(ids)}개 항목을 정말 삭제하시겠습니까?")
    st.markdown("삭제 후에는 복구할 수 없습니다.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("확인 (삭제)", type="primary", use_container_width=True):
            for row_id in ids:
                run_query(f"DELETE FROM {table_name} WHERE id=?", (row_id,), fetch=False)
            st.success("삭제되었습니다.")
            rerun_callback()
    with col_b:
        if st.button("취소", use_container_width=True):
            st.rerun()

# --- 메인 앱 로직 ---
def main():
    init_db()

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

# 1. 물품 입고
def page_inbound():
    st.markdown("### 📥 물품 입고 (ADD ITEMS)")
    st.info("새로운 스파이더 용품이 들어왔을 때 이곳에 입력하세요.")
    col1, col2 = st.columns(2)
    with col1:
        i_date = st.date_input("입고 날짜", datetime.now())
        i_cat = st.selectbox("카테고리", CATEGORIES[1:])
        i_name = st.text_input("품명 (예: 반팔티)")
    with col2:
        if i_cat == "신발": i_size = st.selectbox("사이즈", SHOE_SIZES)
        else: i_size = st.selectbox("사이즈", CLOTHES_SIZES)
        i_qty = st.number_input("입고 수량", min_value=1, value=10)
        i_img = st.file_uploader("사진", type=['png', 'jpg'])

    if st.button("📥 입고 확정", use_container_width=True):
        if i_name:
            img_path = ""
            if i_img:
                img_path = image_to_base64(i_img)
            
            exist = run_query("SELECT id, quantity FROM inventory WHERE item_name=? AND size=? AND category=?", (i_name, i_size, i_cat))
            if exist:
                run_query("UPDATE inventory SET quantity=?, image_path=? WHERE id=?", (exist[0][1] + i_qty, img_path if img_path else None, exist[0][0]), fetch=False)
            else:
                run_query("INSERT INTO inventory (date, category, item_name, size, quantity, image_path) VALUES (?,?,?,?,?,?)", (i_date.strftime("%Y-%m-%d"), i_cat, i_name, i_size, i_qty, img_path), fetch=False)
            
            run_query("INSERT INTO inbound_logs (date, category, item_name, size, quantity) VALUES (?,?,?,?,?)", (i_date.strftime("%Y-%m-%d"), i_cat, i_name, i_size, i_qty), fetch=False)
            st.success(f"✅ {i_name} ({i_size}) {i_qty}개 입고 완료!")
        else: st.error("품명을 입력해주세요.")

# 2. 지급 페이지
def page_distribute():
    st.markdown("### 🎁 물품 지급 (DISTRIBUTE)")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown("#### 1. 대상 선택")
        t_type = st.radio("구분", ["선수", "스텝"], horizontal=True)
        names = [r[0] for r in run_query(f"SELECT name FROM {'players' if t_type=='선수' else 'staff'}")]
        t_name = st.selectbox("이름", names if names else ["없음"])
        
        if t_name != "없음":
            info = run_query(f"SELECT {'back_number' if t_type=='선수' else 'role'}, top_size, bottom_size, shoe_size, image_path FROM {'players' if t_type=='선수' else 'staff'} WHERE name=?", (t_name,))
            if info:
                img_html = ""
                try:
                    img_data = info[0][4]
                    if img_data and len(str(img_data)) > 50: 
                        img_html = f'<img src="data:image/jpeg;base64,{img_data}" style="width:120px; height:120px; object-fit:cover; border-radius:50%; border:3px solid white; margin-bottom:10px;">'
                    else:
                        img_html = '<div style="width:120px; height:120px; background-color:#ddd; border-radius:50%; border:3px solid white; display:flex; align-items:center; justify-content:center; margin:0 auto 10px auto; color:black; font-weight:bold; font-size:40px;">🏐</div>'
                except:
                    img_html = '<div style="width:120px; height:120px; background-color:#ddd; border-radius:50%; border:3px solid white; display:flex; align-items:center; justify-content:center; margin:0 auto 10px auto; color:black; font-weight:bold; font-size:40px;">🏐</div>'

                st.markdown(f"""
                <div style="background-color:#003399; padding:20px; border-radius:15px; box-shadow: 0 4px 8px rgba(0,0,0,0.5); border: 1px solid #333; text-align:center;">
                    {img_html}
                    <h2 style="color:white !important; margin:0; padding-bottom:10px; border-bottom:2px solid white;">{info[0][0]} {t_name}</h2>
                    <div style="margin-top:15px; text-align:left; padding-left:10px;">
                        <p style="color:white !important; font-size:1.2rem; margin:5px 0;">👕 상의: <b style="color:#FFD700;">{info[0][1]}</b></p>
                        <p style="color:white !important; font-size:1.2rem; margin:5px 0;">👖 하의: <b style="color:#FFD700;">{info[0][2]}</b></p>
                        <p style="color:white !important; font-size:1.2rem; margin:5px 0;">👟 신발: <b style="color:#FFD700;">{info[0][3]}</b></p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    with c2:
        st.markdown("#### 2. 물품 선택")
        c_filter = st.selectbox("카테고리 선택", CATEGORIES)
        sql_item = "SELECT DISTINCT item_name FROM inventory WHERE quantity > 0"
        if c_filter != "전체보기": sql_item += f" AND category='{c_filter}'"
        items = [r[0] for r in run_query(sql_item)]
        s_item = st.selectbox("품목 선택", items if items else ["재고 없음"])
        if s_item != "재고 없음":
            sql_size = "SELECT size, quantity, category FROM inventory WHERE item_name=? AND quantity > 0"
            if c_filter != "전체보기": sql_size += " AND category=?"
            params = (s_item,) if c_filter == "전체보기" else (s_item, c_filter)
            stock = run_query(sql_size, params)
            size_opts = {f"{r[0]} (재고: {r[1]})": r for r in stock}
            s_size_opt = st.selectbox("사이즈 선택", list(size_opts.keys()))
            qty = st.number_input("수량", 1, value=1)
            if st.button("🚀 지급 확정", use_container_width=True):
                r_size, r_qty, r_cat = size_opts[s_size_opt]
                if r_qty >= qty:
                    run_query("UPDATE inventory SET quantity=? WHERE item_name=? AND size=? AND category=?", (r_qty - qty, s_item, r_size, r_cat), fetch=False)
                    run_query("INSERT INTO logs (date, target_type, target_name, item_name, size, quantity) VALUES (?,?,?,?,?,?)", (datetime.now().strftime("%Y-%m-%d"), t_type, t_name, s_item, r_size, qty), fetch=False)
                    st.success("지급 완료!")
                    st.rerun()
                else: st.error("재고 부족")

# 3. 재고 현황
def page_inventory():
    st.markdown("### 📦 재고 현황")
    c1, c2 = st.columns(2)
    v_cat = c1.selectbox("카테고리", CATEGORIES)
    search = c2.text_input("검색")
    sql = "SELECT id, category as '구분', item_name as '품명', size as '사이즈', quantity as '수량' FROM inventory WHERE quantity > 0"
    params = []
    if v_cat != "전체보기": sql += " AND category=?"; params.append(v_cat)
    if search: sql += " AND item_name LIKE ?"; params.append(f"%{search}%")
    sql += " ORDER BY category, item_name"
    df = get_dataframe(sql, params)
    
    event = st.dataframe(df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")
    if len(event.selection.rows) > 0:
        selected_rows = df.iloc[event.selection.rows]
        ids_to_delete = selected_rows['id'].tolist()
        if st.button(f"🗑️ 선택한 {len(ids_to_delete)}개 항목 삭제", type="primary"):
            confirm_delete_dialog(ids_to_delete, "inventory", st.rerun)
    
    with st.expander("🛠️ 재고 정보 수정 (수량/품명 변경)"):
        edit_item = st.selectbox("수정할 품목 선택", [f"{r[0]}: {r[2]} - {r[3]}" for r in df.values.tolist()] if not df.empty else [])
        if edit_item:
            selected_id = int(edit_item.split(":")[0])
            curr = run_query("SELECT item_name, quantity FROM inventory WHERE id=?", (selected_id,))[0]
            new_name = st.text_input("품명 수정", value=curr[0])
            new_qty = st.number_input("수량 수정", min_value=0, value=curr[1])
            if st.button("수정 내용 저장"):
                run_query("UPDATE inventory SET item_name=?, quantity=? WHERE id=?", (new_name, new_qty, selected_id), fetch=False)
                st.success("수정 완료!")
                st.rerun()

# 4. 선수 명단 (수정 Key 추가 완료)
def page_players():
    st.markdown("### 🏐 선수 명단")
    with st.expander("➕ 선수 등록"):
        c1, c2, c3 = st.columns(3)
        p_num = c1.text_input("배번")
        p_name = c2.text_input("이름")
        p_shoe = c3.selectbox("신발", SHOE_SIZES)
        c4, c5 = st.columns(2)
        p_top = c4.selectbox("상의", CLOTHES_SIZES)
        p_bot = c5.selectbox("하의", CLOTHES_SIZES)
        p_img = st.file_uploader("프로필 사진", type=['png', 'jpg', 'jpeg'])
        
        if st.button("저장"):
            img_b64 = image_to_base64(p_img)
            run_query("INSERT INTO players (name, back_number, top_size, bottom_size, shoe_size, image_path) VALUES (?,?,?,?,?,?)", 
                      (p_name, p_num, p_top, p_bot, p_shoe, img_b64), fetch=False)
            st.rerun()
            
    df = get_dataframe("SELECT id, name as '이름', back_number as '배번', top_size as '상의', bottom_size as '하의', shoe_size as '신발' FROM players ORDER BY back_number")
    
    event = st.dataframe(df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")
    if len(event.selection.rows) > 0:
        selected_rows = df.iloc[event.selection.rows]
        ids_to_delete = selected_rows['id'].tolist()
        if st.button(f"🗑️ 선택한 {len(ids_to_delete)}명 삭제", type="primary"):
            confirm_delete_dialog(ids_to_delete, "players", st.rerun)

    # 선수 수정 (Key 추가)
    with st.expander("🛠️ 정보 수정"):
        edit_target = st.selectbox("수정 대상", df['이름'].tolist() if not df.empty else [])
        if edit_target:
            p_curr = run_query("SELECT * FROM players WHERE name=?", (edit_target,))[0]
            
            try:
                if p_curr[6] and len(str(p_curr[6])) > 50:
                    st.image(BytesIO(base64.b64decode(p_curr[6])), caption="현재 사진", width=100)
            except:
                st.warning("기존 이미지를 불러올 수 없습니다.")
            
            ec1, ec2 = st.columns(2)
            e_num = ec1.text_input("배번", value=p_curr[2], key="edit_p_num") # Key 추가
            e_shoe = ec2.selectbox("신발", SHOE_SIZES, index=SHOE_SIZES.index(p_curr[5]) if p_curr[5] in SHOE_SIZES else 0, key="edit_p_shoe") # Key 추가
            e_img = st.file_uploader("사진 변경 (선택)", type=['png', 'jpg', 'jpeg'], key="edit_p_img") # Key 수정
            
            if st.button("수정 완료", key="btn_p_edit"): # Key 추가
                new_img = image_to_base64(e_img) if e_img else p_curr[6]
                run_query("UPDATE players SET back_number=?, shoe_size=?, image_path=? WHERE id=?", (e_num, e_shoe, new_img, p_curr[0]), fetch=False)
                st.rerun()

# 5. 스텝 명단 (수정 Key 추가 완료)
def page_staff():
    st.markdown("### 👔 스텝 명단")
    with st.expander("➕ 스텝 등록"):
        c1, c2 = st.columns(2)
        s_role = c1.selectbox("직책", STAFF_ROLES)
        s_name = c2.text_input("이름")
        c3, c4, c5 = st.columns(3)
        s_top = c3.selectbox("상의", CLOTHES_SIZES, key="st")
        s_bot = c4.selectbox("하의", CLOTHES_SIZES, key="sb")
        s_shoe = c5.selectbox("신발", SHOE_SIZES, key="ss")
        s_img = st.file_uploader("프로필 사진", type=['png', 'jpg', 'jpeg'])
        
        if st.button("저장"):
            img_b64 = image_to_base64(s_img)
            run_query("INSERT INTO staff (name, role, top_size, bottom_size, shoe_size, image_path) VALUES (?,?,?,?,?,?)", 
                      (s_name, s_role, s_top, s_bot, s_shoe, img_b64), fetch=False)
            st.rerun()

    df = get_dataframe("SELECT id, role as '직책', name as '이름', top_size as '상의', bottom_size as '하의', shoe_size as '신발' FROM staff ORDER BY role")
    
    event = st.dataframe(df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")
    if len(event.selection.rows) > 0:
        selected_rows = df.iloc[event.selection.rows]
        ids_to_delete = selected_rows['id'].tolist()
        if st.button(f"🗑️ 선택한 {len(ids_to_delete)}명 삭제", type="primary"):
            confirm_delete_dialog(ids_to_delete, "staff", st.rerun)

    # 스텝 수정 (Key 추가)
    with st.expander("🛠️ 정보 수정"):
        edit_s_target = st.selectbox("수정 대상", df['이름'].tolist() if not df.empty else [])
        if edit_s_target:
            s_curr = run_query("SELECT * FROM staff WHERE name=?", (edit_s_target,))[0]
            
            try:
                if s_curr[6] and len(str(s_curr[6])) > 50:
                    st.image(BytesIO(base64.b64decode(s_curr[6])), caption="현재 사진", width=100)
            except:
                st.warning("기존 이미지를 불러올 수 없습니다.")

            ec1, ec2 = st.columns(2)
            # 여기서 Key 추가
            e_role = ec1.selectbox("직책", STAFF_ROLES, index=STAFF_ROLES.index(s_curr[2]) if s_curr[2] in STAFF_ROLES else 0, key="edit_s_role")
            e_name = ec2.text_input("이름", value=s_curr[1], key="edit_s_name")
            
            # 이미지 업로더에도 유니크한 Key 적용
            e_img = st.file_uploader("사진 변경 (선택)", type=['png', 'jpg', 'jpeg'], key="edit_s_img")
            
            if st.button("수정 완료", key="btn_s_edit"):
                new_img = image_to_base64(e_img) if e_img else s_curr[6]
                run_query("UPDATE staff SET name=?, role=?, image_path=? WHERE id=?", (e_name, e_role, new_img, s_curr[0]), fetch=False)
                st.rerun()

# 6. 전체 내역
def page_history():
    st.markdown("### 📋 전체 내역")
    t1, t2 = st.tabs(["📤 지급 내역", "📥 입고 내역"])
    with t1:
        search = st.text_input("이름 검색")
        sql = "SELECT id, date as '날짜', target_name as '이름', item_name as '품명', size as '사이즈', quantity as '수량' FROM logs WHERE 1=1"
        if search: sql += f" AND target_name LIKE '%{search}%'"
        sql += " ORDER BY id DESC"
        
        df_out = get_dataframe(sql)
        event_out = st.dataframe(df_out, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")
        if len(event_out.selection.rows) > 0:
            ids = df_out.iloc[event_out.selection.rows]['id'].tolist()
            if st.button(f"🗑️ 선택한 {len(ids)}개 지급 내역 삭제", type="primary"):
                confirm_delete_dialog(ids, "logs", st.rerun)

    with t2:
        sql_in = "SELECT id, date as '날짜', item_name as '품명', size as '사이즈', quantity as '수량' FROM inbound_logs ORDER BY id DESC"
        df_in = get_dataframe(sql_in)
        event_in = st.dataframe(df_in, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")
        if len(event_in.selection.rows) > 0:
            ids = df_in.iloc[event_in.selection.rows]['id'].tolist()
            if st.button(f"🗑️ 선택한 {len(ids)}개 입고 내역 삭제", type="primary"):
                confirm_delete_dialog(ids, "inbound_logs", st.rerun)

# 7. 비고
def page_memo():
    st.markdown("### 📝 비고")
    with st.form("memo"):
        c1, c2 = st.columns([1,2])
        d = c1.date_input("날짜"); c = c2.selectbox("구분", MEMO_CATS)
        t = st.text_area("내용")
        if st.form_submit_button("저장"):
            run_query("INSERT INTO memos (date, category, content) VALUES (?,?,?)", (d.strftime("%Y-%m-%d"), c, t), fetch=False)
            st.rerun()
    st.dataframe(get_dataframe("SELECT date as '날짜', category as '구분', content as '내용' FROM memos ORDER BY date DESC"), use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()

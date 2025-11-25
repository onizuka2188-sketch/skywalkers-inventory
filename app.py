import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
import base64

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

# --- [디자인] 스파이더 블랙 테마 (강제 고정) ---
st.markdown("""
    <style>
    /* 1. 전체 배경: 스파이더 블랙 */
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: #111111 !important;
    }
    
    /* 2. 모든 기본 글씨: 흰색 */
    h1, h2, h3, h4, h5, h6, p, span, div, label, li, input, textarea {
        color: #FFFFFF !important;
    }

    /* 3. 사이드바: 완전 검정 */
    [data-testid="stSidebar"] {
        background-color: #000000 !important;
        border-right: 1px solid #333333;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    /* 사이드바 캡션(제작자)만 회색 */
    [data-testid="stSidebar"] .stCaption { color: #999999 !important; font-size: 14px !important; }

    /* 4. 입력창(네모칸): 진한 회색 배경 */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stNumberInput input, .stDateInput input, .stTextArea textarea {
        background-color: #262730 !important;
        color: #FFFFFF !important;
        border: 1px solid #444444 !important;
    }
    
    /* 5. 드롭다운 메뉴 (목록) */
    div[data-baseweb="popover"], ul[data-baseweb="menu"] {
        background-color: #262730 !important;
        border: 1px solid #444444 !important;
    }
    ul[data-baseweb="menu"] li {
        background-color: #262730 !important;
        color: #FFFFFF !important;
    }
    /* 마우스 올렸을 때: 파란색 하이라이트 */
    ul[data-baseweb="menu"] li:hover {
        background-color: #003399 !important;
        color: #FFFFFF !important;
    }
    /* 선택된 값 */
    div[data-baseweb="select"] span {
        color: #FFFFFF !important;
    }

    /* 6. 버튼 스타일: 스카이워커스 블루 */
    .stButton > button {
        background-color: #003399 !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #FFFFFF !important;
        color: #003399 !important;
    }

    /* 7. 표(DataFrame) 스타일 */
    [data-testid="stDataFrame"] {
        background-color: #111111 !important;
    }
    [data-testid="stDataFrame"] th {
        background-color: #003399 !important;
        color: #FFFFFF !important;
    }
    [data-testid="stDataFrame"] td {
        background-color: #111111 !important;
        color: #FFFFFF !important;
        border-bottom: 1px solid #333 !important;
    }

    /* 8. 확장 패널 (Expander) */
    .streamlit-expanderHeader {
        background-color: #222222 !important;
        color: #FFFFFF !important;
        border: 1px solid #444;
    }
    .streamlit-expanderContent {
        background-color: #111111 !important;
        color: #FFFFFF !important;
        border-top: 1px solid #444;
    }

    /* 9. 헤더 로고 박스 (흰 배경 유지 - 로고 잘 보이게) */
    .main-header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #FFFFFF !important; 
        padding: 15px 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        border-bottom: 4px solid #003399;
    }
    /* 헤더 박스 안의 글씨는 검정 (흰 배경이니까) */
    .main-header-container h1 { color: #003399 !important; }
    .main-header-container p { color: #000000 !important; }
    .main-header-container span { color: #000000 !important; }

    /* 10. 달력 (Calendar) 강제 다크모드 */
    div[data-baseweb="calendar"] {
        background-color: #262730 !important;
        color: #FFFFFF !important;
    }
    div[data-baseweb="calendar"] button {
        color: #FFFFFF !important;
    }
    div[data-baseweb="calendar"] div {
        color: #FFFFFF !important;
    }
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

# 이미지 파일을 Base64 문자열로 변환하는 함수
def get_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

# --- 메인 앱 로직 ---
def main():
    init_db()

    # 세션 상태 초기화
    if 'current_menu' not in st.session_state:
        st.session_state.current_menu = '물품 입고'

    # 사이드바
    with st.sidebar:
        st.markdown("## 🏐 HYUNDAI CAPITAL")
        st.markdown("## SKYWALKERS")
        st.caption(f"제작자 : 네바아빠 | {datetime.now().strftime('%Y-%m-%d')}")
        st.markdown("---")

        # [수정] 1. 물품 및 지급 (위로 이동 + 전체내역 포함)
        st.markdown("### 📦 물품 및 지급")
        if st.button("📥 물품 입고", use_container_width=True): st.session_state.current_menu = "물품 입고"
        if st.button("🎁 지급 하기", use_container_width=True): st.session_state.current_menu = "지급 하기"
        if st.button("📦 재고 현황", use_container_width=True): st.session_state.current_menu = "재고 현황"
        if st.button("📋 전체 내역", use_container_width=True): st.session_state.current_menu = "전체 내역"

        # [수정] 2. 인원 및 기록 (아래로 이동)
        st.markdown("### 👥 인원 및 기록")
        if st.button("🏐 선수 명단", use_container_width=True): st.session_state.current_menu = "선수 명단"
        if st.button("👔 스텝 명단", use_container_width=True): st.session_state.current_menu = "스텝 명단"
        if st.button("📝 비고/연혁", use_container_width=True): st.session_state.current_menu = "비고/연혁"
        
        st.markdown("---")

    # 헤더 표시
    header_html = f"""
    <div class="main-header-container">
        <img src="data:image/png;base64,{get_image_base64('logo_skywalkers.png')}" style="height:60px;" alt="Skywalkers">
        <div style="text-align:center; flex-grow:1;">
            <h1 style="font-size:2rem; font-weight:900;">HYUNDAI CAPITAL SKYWALKERS</h1>
            <p style="margin:0; font-weight:bold;">EQUIPMENT MANAGEMENT SYSTEM <span>x SPYDER</span></p>
        </div>
        <img src="data:image/png;base64,{get_image_base64('logo_spyder.png')}" style="height:60px;" alt="Spyder">
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    # 메뉴 라우팅
    menu = st.session_state.current_menu
    
    if menu == "물품 입고": page_inbound()
    elif menu == "지급 하기": page_distribute()
    elif menu == "재고 현황": page_inventory()
    elif menu == "선수 명단": page_players()
    elif menu == "스텝 명단": page_staff()
    elif menu == "전체 내역": page_history()
    elif menu == "비고/연혁": page_memo()

# 1. 물품 입고 페이지
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
                save_dir = "item_images"
                file_path = os.path.join(save_dir, i_img.name)
                with open(file_path, "wb") as f: f.write(i_img.getbuffer())
                img_path = file_path
            
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
            info = run_query(f"SELECT {'back_number' if t_type=='선수' else 'role'}, top_size, bottom_size, shoe_size FROM {'players' if t_type=='선수' else 'staff'} WHERE name=?", (t_name,))
            if info:
                # 정보 카드 디자인 (다크모드 최적화)
                st.markdown(f"""
                <div style="background-color:#003399; padding:20px; border-radius:10px; box-shadow: 0 4px 8px rgba(0,0,0,0.5); border: 1px solid #333;">
                    <h3 style="color:white !important; border-bottom:2px solid white; padding-bottom:5px; margin-bottom:10px;">{info[0][0]} {t_name}</h3>
                    <p style="color:white !important; font-size:1.1rem; margin:5px 0;">👕 상의: <b>{info[0][1]}</b></p>
                    <p style="color:white !important; font-size:1.1rem; margin:5px 0;">👖 하의: <b>{info[0][2]}</b></p>
                    <p style="color:white !important; font-size:1.1rem; margin:5px 0;">👟 신발: <b>{info[0][3]}</b></p>
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
    
    sql = "SELECT category as '구분', item_name as '품명', size as '사이즈', quantity as '수량' FROM inventory WHERE quantity > 0"
    params = []
    if v_cat != "전체보기": 
        sql += " AND category=?"; params.append(v_cat)
    if search:
        sql += " AND item_name LIKE ?"; params.append(f"%{search}%")
    sql += " ORDER BY category, item_name"
    
    st.dataframe(get_dataframe(sql, params), use_container_width=True, hide_index=True)
    
    with st.expander("🗑️ 데이터 정리 (잘못된 입고 삭제)"):
        del_id = st.number_input("삭제할 ID (inventory 테이블)", 0)
        if st.button("삭제"):
            run_query("DELETE FROM inventory WHERE id=?", (del_id,), fetch=False)
            st.rerun()

# 4. 선수 명단
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
        if st.button("저장"):
            run_query("INSERT INTO players (name, back_number, top_size, bottom_size, shoe_size) VALUES (?,?,?,?,?)", (p_name, p_num, p_top, p_bot, p_shoe), fetch=False)
            st.rerun()
            
    df = get_dataframe("SELECT name as '이름', back_number as '배번', top_size as '상의', bottom_size as '하의', shoe_size as '신발' FROM players ORDER BY back_number")
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    with st.expander("🗑️ 삭제"):
        d_name = st.selectbox("선수 선택", df['이름'].tolist() if not df.empty else [])
        if st.button("삭제"):
            run_query("DELETE FROM players WHERE name=?", (d_name,), fetch=False)
            st.rerun()

# 5. 스텝 명단
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
        if st.button("저장"):
            run_query("INSERT INTO staff (name, role, top_size, bottom_size, shoe_size) VALUES (?,?,?,?,?)", (s_name, s_role, s_top, s_bot, s_shoe), fetch=False)
            st.rerun()

    df = get_dataframe("SELECT role as '직책', name as '이름', top_size as '상의', bottom_size as '하의', shoe_size as '신발' FROM staff ORDER BY role")
    st.dataframe(df, use_container_width=True, hide_index=True)

# 6. [수정] 전체 내역 (삭제 기능 추가)
def page_history():
    st.markdown("### 📋 전체 내역")
    t1, t2 = st.tabs(["📤 지급 내역 (OUT)", "📥 입고 내역 (IN)"])
    
    # [Tab 1] 지급 내역 삭제 기능 추가
    with t1:
        search = st.text_input("이름 검색")
        sql = "SELECT id, date as '날짜', target_name as '이름', item_name as '품명', size as '사이즈', quantity as '수량' FROM logs WHERE 1=1"
        if search: sql += f" AND target_name LIKE '%{search}%'"
        sql += " ORDER BY id DESC"
        
        df_out = get_dataframe(sql)
        st.dataframe(df_out, use_container_width=True, hide_index=True)
        
        with st.expander("🗑️ 지급 내역 삭제 (주의: 재고는 복구되지 않음)"):
            del_out_ids = st.multiselect("삭제할 기록 ID 선택", df_out['id'].tolist())
            if st.button("지급 기록 삭제"):
                for did in del_out_ids:
                    run_query("DELETE FROM logs WHERE id=?", (did,), fetch=False)
                st.success("삭제 완료")
                st.rerun()

    # [Tab 2] 입고 내역 삭제 기능 유지
    with t2:
        sql_in = "SELECT id, date as '날짜', item_name as '품명', size as '사이즈', quantity as '수량' FROM inbound_logs ORDER BY id DESC"
        df_in = get_dataframe(sql_in)
        st.dataframe(df_in, use_container_width=True, hide_index=True)
        
        with st.expander("🗑️ 입고 내역 삭제"):
            del_in_ids = st.multiselect("삭제할 ID 선택", df_in['id'].tolist())
            if st.button("입고 기록 삭제"):
                for did in del_in_ids:
                    run_query("DELETE FROM inbound_logs WHERE id=?", (did,), fetch=False)
                st.success("삭제 완료")
                st.rerun()

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

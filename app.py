import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
import shutil

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
    page_title="SKYWALKERS Manager",
    page_icon="🏐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 디자인 커스텀 (스파이더 블랙 & 스카이워커스 블루) ---
st.markdown("""
    <style>
    /* 전체 배경 */
    .stApp {background-color: #F5F7FA;}
    
    /* 사이드바 스타일 (스파이더 블랙) */
    [data-testid="stSidebar"] {
        background-color: #111111;
        color: white;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] p {
        color: #CCCCCC !important;
    }

    /* 메인 헤더 스타일 (스카이워커스 블루) */
    .main-header {
        font-size: 36px; 
        font-weight: 800; 
        color: #003399; /* Skywalkers Blue */
        border-bottom: 3px solid #000000;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    
    /* 버튼 스타일 */
    div.stButton > button:first-child {
        background-color: #003399; 
        color: white; 
        font-weight: bold;
        border-radius: 5px;
        border: none;
    }
    div.stButton > button:first-child:hover {
        background-color: #000000; /* Hover시 스파이더 블랙 */
        color: white;
    }
    
    /* 카드형 컨테이너 스타일 */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
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

# --- 메인 앱 로직 ---
def main():
    init_db()

    # 사이드바 (메뉴)
    with st.sidebar:
        # 로고 자리 (이미지가 있다면 표시, 없으면 텍스트)
        # st.image("logo.png", width=200) 
        st.markdown("# 🕷️ SPYDER")
        st.markdown("### SKYWALKERS V-EQ")
        st.markdown("---")
        
        # 메뉴 순서 변경: 입고 -> 지급 -> 재고
        menu = st.radio("MENU", [
            "📥 물품 입고 (Inbound)", 
            "🎁 지급 하기 (Distribute)", 
            "📦 재고 현황 (Inventory)", 
            "🏐 선수 명단 (Players)", 
            "👔 스텝 명단 (Staff)", 
            "📋 전체 내역 (History)", 
            "📝 비고/연혁 (Memo)"
        ])
        
        st.markdown("---")
        st.caption(f"Manager: 유영욱\nDate: {datetime.now().strftime('%Y-%m-%d')}")

    # 헤더 표시
    st.markdown('<div class="main-header">HYUNDAI CAPITAL SKYWALKERS <span style="font-size:20px; color:black;">x SPYDER</span></div>', unsafe_allow_html=True)

    # 메뉴 라우팅
    if "물품 입고" in menu:
        page_inbound()
    elif "지급 하기" in menu:
        page_distribute()
    elif "재고 현황" in menu:
        page_inventory()
    elif "선수 명단" in menu:
        page_players()
    elif "스텝 명단" in menu:
        page_staff()
    elif "전체 내역" in menu:
        page_history()
    elif "비고" in menu:
        page_memo()

# 1. [NEW] 물품 입고 페이지 (분리됨)
def page_inbound():
    st.markdown("### 📥 물품 입고 (ADD ITEMS)")
    st.info("새로운 스파이더 용품이 들어왔을 때 이곳에 입력하세요. 재고가 자동으로 합산됩니다.")

    with st.container():
        col1, col2 = st.columns([1, 1])
        
        with col1:
            i_date = st.date_input("입고 날짜", datetime.now())
            i_cat = st.selectbox("카테고리", CATEGORIES[1:]) # 전체보기 제외
            i_name = st.text_input("품명 (예: 24-25 트레이닝 자켓)")
        
        with col2:
            if i_cat == "신발":
                i_size = st.selectbox("사이즈", SHOE_SIZES)
            else:
                i_size = st.selectbox("사이즈", CLOTHES_SIZES)
            
            i_qty = st.number_input("입고 수량", min_value=1, value=10, step=1)
            i_img = st.file_uploader("제품 사진 업로드", type=['png', 'jpg', 'jpeg'])

        if st.button("📥 입고 확정 및 저장"):
            if i_name:
                # 이미지 저장 처리
                img_path = ""
                if i_img:
                    save_dir = "item_images"
                    file_path = os.path.join(save_dir, i_img.name)
                    with open(file_path, "wb") as f:
                        f.write(i_img.getbuffer())
                    img_path = file_path
                
                # 로직: 이미 있는 품목이면 수량 추가, 없으면 새로 생성
                exist = run_query("SELECT id, quantity FROM inventory WHERE item_name=? AND size=? AND category=?", (i_name, i_size, i_cat))
                if exist:
                    run_query("UPDATE inventory SET quantity=?, image_path=? WHERE id=?", 
                              (exist[0][1] + i_qty, img_path if img_path else None, exist[0][0]), fetch=False)
                else:
                    run_query("INSERT INTO inventory (date, category, item_name, size, quantity, image_path) VALUES (?,?,?,?,?,?)",
                              (i_date.strftime("%Y-%m-%d"), i_cat, i_name, i_size, i_qty, img_path), fetch=False)
                
                # 입고 로그 기록
                run_query("INSERT INTO inbound_logs (date, category, item_name, size, quantity) VALUES (?,?,?,?,?)",
                          (i_date.strftime("%Y-%m-%d"), i_cat, i_name, i_size, i_qty), fetch=False)
                
                st.success(f"✅ {i_name} ({i_size}) {i_qty}개 입고 완료! 재고에 반영되었습니다.")
            else:
                st.error("품명을 입력해주세요.")

# 2. 지급 페이지 (순서 변경)
def page_distribute():
    st.markdown("### 🎁 물품 지급 (DISTRIBUTE)")
    st.warning("선수나 스텝에게 물품을 지급합니다. 재고가 자동으로 차감됩니다.")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### 1. 받는 사람")
        target_type = st.radio("대상", ["선수", "스텝"], horizontal=True)
        
        if target_type == "선수":
            names = [r[0] for r in run_query("SELECT name FROM players")]
        else:
            names = [r[0] for r in run_query("SELECT name FROM staff")]
            
        target_name = st.selectbox("이름 검색", names if names else ["인원 없음"])
        
        # 사이즈 정보 카드 표시
        if target_name and target_name != "인원 없음":
            if target_type == "선수":
                info = run_query("SELECT back_number, top_size, bottom_size, shoe_size FROM players WHERE name=?", (target_name,))
                if info:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3 style="color:#003399;">No.{info[0][0]} {target_name}</h3>
                        <p>👕 상의: <b>{info[0][1]}</b></p>
                        <p>👖 하의: <b>{info[0][2]}</b></p>
                        <p>👟 신발: <b>{info[0][3]}</b></p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                info = run_query("SELECT role, top_size, bottom_size, shoe_size FROM staff WHERE name=?", (target_name,))
                if info:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3 style="color:#003399;">{info[0][0]} {target_name}</h3>
                        <p>👕 상의: <b>{info[0][1]}</b></p>
                        <p>👖 하의: <b>{info[0][2]}</b></p>
                        <p>👟 신발: <b>{info[0][3]}</b></p>
                    </div>
                    """, unsafe_allow_html=True)

    with col2:
        st.markdown("#### 2. 지급할 물품")
        cat_filter = st.selectbox("카테고리 선택", CATEGORIES)
        
        if cat_filter == "전체보기":
            items = [r[0] for r in run_query("SELECT DISTINCT item_name FROM inventory WHERE quantity > 0")]
        else:
            items = [r[0] for r in run_query("SELECT DISTINCT item_name FROM inventory WHERE category=? AND quantity > 0", (cat_filter,))]
            
        selected_item = st.selectbox("품목 선택", items if items else ["지급 가능한 재고 없음"])
        
        if selected_item and selected_item != "지급 가능한 재고 없음":
            # 재고 로직
            if cat_filter == "전체보기":
                 stock_data = run_query("SELECT size, quantity, category FROM inventory WHERE item_name=? AND quantity > 0", (selected_item,))
            else:
                 stock_data = run_query("SELECT size, quantity, category FROM inventory WHERE item_name=? AND category=? AND quantity > 0", (selected_item, cat_filter))
            
            size_opts = {f"{r[0]} (현재재고: {r[1]})": (r[0], r[1], r[2]) for r in stock_data}
            selected_size_opt = st.selectbox("사이즈 선택", list(size_opts.keys()))
            
            qty_to_give = st.number_input("지급 수량", min_value=1, value=1)
            
            if st.button("🚀 지급 확정"):
                real_size, current_qty, real_cat = size_opts[selected_size_opt]
                if current_qty >= qty_to_give:
                    run_query("UPDATE inventory SET quantity=? WHERE item_name=? AND size=? AND category=?", 
                              (current_qty - qty_to_give, selected_item, real_size, real_cat), fetch=False)
                    run_query("INSERT INTO logs (date, target_type, target_name, item_name, size, quantity) VALUES (?,?,?,?,?,?)",
                              (datetime.now().strftime("%Y-%m-%d"), target_type, target_name, selected_item, real_size, qty_to_give), fetch=False)
                    st.balloons()
                    st.success(f"✅ {target_name}님에게 지급 완료!")
                    st.rerun()
                else:
                    st.error(f"❌ 재고 부족! (남은 수량: {current_qty})")

# 3. 재고 현황 페이지 (수정됨: 뷰어 기능만)
def page_inventory():
    st.markdown("### 📦 현재 재고 현황 (STOCK STATUS)")
    st.info("현재 창고에 남아있는 실제 재고입니다. (입고량 - 지급량 = 잔여재고)")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        view_cat = st.selectbox("카테고리 필터", CATEGORIES)
    with col2:
        search_txt = st.text_input("품명 검색 (예: 티셔츠)")
    
    # SQL 조회
    sql = "SELECT id, category as '구분', item_name as '품명', size as '사이즈', quantity as '잔여수량' FROM inventory WHERE quantity > 0"
    params = []
    
    if view_cat != "전체보기":
        sql += " AND category=?"
        params.append(view_cat)
    if search_txt:
        sql += " AND item_name LIKE ?"
        params.append(f"%{search_txt}%")
    
    sql += " ORDER BY category, item_name"
    
    df = get_dataframe(sql, params)
    
    # 스타일링된 데이터프레임
    st.dataframe(
        df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "잔여수량": st.column_config.ProgressColumn(
                "잔여수량",
                help="현재 남은 재고",
                format="%d개",
                min_value=0,
                max_value=100, # 대략적인 Max
            ),
        }
    )
    
    # 0개인 재고 보기 옵션
    with st.expander("⚠️ 품절된 상품 보기 (수량 0)"):
        df_zero = get_dataframe("SELECT category, item_name, size FROM inventory WHERE quantity <= 0")
        st.dataframe(df_zero, use_container_width=True)

    # 삭제 기능 (실수로 잘못 넣은 것만)
    with st.expander("🗑️ 데이터 정리 (잘못된 입고 내역 삭제)"):
        st.caption("실제 재고 데이터를 삭제합니다. 신중하게 사용하세요.")
        del_id = st.number_input("삭제할 ID 입력", min_value=0)
        if st.button("해당 재고 데이터 영구 삭제"):
            run_query("DELETE FROM inventory WHERE id=?", (del_id,), fetch=False)
            st.warning("삭제되었습니다.")
            st.rerun()

# 4. 선수 명단
def page_players():
    st.markdown("### 🏐 선수 명단 (PLAYERS)")
    
    with st.expander("➕ 선수 신규 등록"):
        c1, c2, c3 = st.columns(3)
        p_num = c1.text_input("배번")
        p_name = c2.text_input("이름")
        p_shoe = c3.selectbox("신발", SHOE_SIZES)
        c4, c5 = st.columns(2)
        p_top = c4.selectbox("상의", CLOTHES_SIZES)
        p_bot = c5.selectbox("하의", CLOTHES_SIZES)
        
        if st.button("선수 저장"):
            if p_name:
                run_query("INSERT INTO players (name, back_number, top_size, bottom_size, shoe_size) VALUES (?,?,?,?,?)",
                          (p_name, p_num, p_top, p_bot, p_shoe), fetch=False)
                st.success(f"{p_name} 등록 완료")
                st.rerun()
    
    df = get_dataframe("SELECT id, back_number as '배번', name as '이름', top_size as '상의', bottom_size as '하의', shoe_size as '신발' FROM players ORDER BY back_number")
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    with st.expander("🗑️ 선수 삭제"):
        del_list = df['이름'].tolist()
        del_name = st.selectbox("삭제할 선수", del_list if del_list else ["없음"])
        if st.button("삭제 실행"):
            run_query("DELETE FROM players WHERE name=?", (del_name,), fetch=False)
            st.rerun()

# 5. 스텝 명단
def page_staff():
    st.markdown("### 👔 스텝 명단 (STAFF)")
    
    with st.expander("➕ 스텝 신규 등록"):
        c1, c2 = st.columns(2)
        s_role = c1.selectbox("직책", STAFF_ROLES)
        s_name = c2.text_input("이름")
        c3, c4, c5 = st.columns(3)
        s_top = c3.selectbox("상의", CLOTHES_SIZES, key="st")
        s_bot = c4.selectbox("하의", CLOTHES_SIZES, key="sb")
        s_shoe = c5.selectbox("신발", SHOE_SIZES, key="ss")
        
        if st.button("스텝 저장"):
            if s_name:
                run_query("INSERT INTO staff (name, role, top_size, bottom_size, shoe_size) VALUES (?,?,?,?,?)",
                          (s_name, s_role, s_top, s_bot, s_shoe), fetch=False)
                st.success("등록 완료")
                st.rerun()

    df = get_dataframe("SELECT id, role as '직책', name as '이름', top_size as '상의', bottom_size as '하의', shoe_size as '신발' FROM staff ORDER BY role")
    st.dataframe(df, use_container_width=True, hide_index=True)

# 6. 전체 내역
def page_history():
    st.markdown("### 📋 통합 입출고 내역 (HISTORY)")
    
    tab1, tab2 = st.tabs(["📤 지급 내역 (OUT)", "📥 입고 내역 (IN)"])
    
    with tab1:
        st.caption("누구에게 무엇을 지급했는지 확인합니다.")
        h_name = st.text_input("이름으로 검색", key="h_out")
        sql = "SELECT id, date as '날짜', target_type as '구분', target_name as '이름', item_name as '품명', size as '사이즈', quantity as '수량' FROM logs WHERE 1=1"
        if h_name:
            sql += f" AND target_name LIKE '%{h_name}%'"
        sql += " ORDER BY id DESC"
        st.dataframe(get_dataframe(sql), use_container_width=True, hide_index=True)

    with tab2:
        st.caption("언제 어떤 물품이 창고로 들어왔는지 확인합니다.")
        col1, col2 = st.columns(2)
        in_date = col1.text_input("날짜 검색 (YYYY-MM-DD)")
        in_item = col2.text_input("품명 검색")
        
        sql_in = "SELECT id, date as '날짜', category as '구분', item_name as '품명', size as '사이즈', quantity as '수량' FROM inbound_logs WHERE 1=1"
        if in_date: sql_in += f" AND date LIKE '%{in_date}%'"
        if in_item: sql_in += f" AND item_name LIKE '%{in_item}%'"
        sql_in += " ORDER BY id DESC"
        
        df_in = get_dataframe(sql_in)
        st.dataframe(df_in, use_container_width=True, hide_index=True)
        
        with st.expander("🗑️ 입고 내역 삭제 (재고 수량은 변하지 않음)"):
            del_ids = st.multiselect("삭제할 입고 기록 ID", df_in['id'].tolist())
            if st.button("기록 삭제"):
                for did in del_ids:
                    run_query("DELETE FROM inbound_logs WHERE id=?", (did,), fetch=False)
                st.success("삭제 완료")
                st.rerun()

# 7. 비고
def page_memo():
    st.markdown("### 📝 비고 및 팀 연혁 (MEMO)")
    
    with st.form("memo_form"):
        c1, c2 = st.columns([1, 2])
        m_date = c1.date_input("날짜")
        m_cat = c2.selectbox("구분", MEMO_CATS)
        m_content = st.text_area("내용")
        if st.form_submit_button("저장"):
            run_query("INSERT INTO memos (date, category, content) VALUES (?,?,?)", 
                      (m_date.strftime("%Y-%m-%d"), m_cat, m_content), fetch=False)
            st.rerun()
            
    df = get_dataframe("SELECT id, date as '날짜', category as '구분', content as '내용' FROM memos ORDER BY date DESC")
    st.dataframe(df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()

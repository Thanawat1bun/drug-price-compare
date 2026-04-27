import streamlit as st
import pandas as pd
import os
import re
import difflib
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm
import urllib.request

# 1. ตั้งค่าหน้าเพจ
st.set_page_config(page_title="ระบบเปรียบเทียบราคายา", page_icon="💊", layout="wide")

# 2. ตั้งค่าฟอนต์ภาษาไทยสำหรับกราฟ
@st.cache_resource
def set_thai_font():
    font_path = 'thsarabunnew-webfont.ttf'
    if not os.path.exists(font_path):
        try:
            urllib.request.urlretrieve('https://github.com/Phonbopit/sarabun-webfont/raw/master/fonts/thsarabunnew-webfont.ttf', font_path)
        except:
            pass
    if os.path.exists(font_path):
        fm.fontManager.addfont(font_path)
        mpl.rc('font', family='TH Sarabun New', size=14)

set_thai_font()

# 3. โหลดข้อมูล
@st.cache_data
def load_all_data():
    shops = ["VMDC", "MK", "SP", "TPD", "WELLEK", "CHAN"]
    data_dict = {}
    data_dir = "." 
    all_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    
    for shop in shops:
        shop_files = [f for f in all_files if shop.lower() in f.lower()]
        if shop_files:
            shop_files.sort(reverse=True)
            file_path = os.path.join(data_dir, shop_files[0])
            try:
                df = pd.read_csv(file_path, encoding='utf-8-sig')
                if 'ชื่อสินค้าที่ทำความสะอาดแล้ว' in df.columns:
                    df = df.rename(columns={'ชื่อสินค้าที่ทำความสะอาดแล้ว': 'ชื่อสินค้า'})
                elif 'ชื่อสินค้า (และรายละเอียด)' in df.columns:
                    df = df.rename(columns={'ชื่อสินค้า (และรายละเอียด)': 'ชื่อสินค้า'})
                
                if 'ชื่อสินค้า' in df.columns:
                    df['ชื่อสินค้า'] = df['ชื่อสินค้า'].astype(str).str.strip()
                data_dict[shop] = df
            except:
                data_dict[shop] = pd.DataFrame(columns=['ชื่อสินค้า', 'ราคา'])
        else:
            data_dict[shop] = pd.DataFrame(columns=['ชื่อสินค้า', 'ราคา'])
    return data_dict

def clean_price(p):
    if pd.isna(p): return None
    if isinstance(p, (int, float)): return float(p)
    try:
        match = re.search(r'\d+(?:,\d+)*(?:\.\d+)?', str(p))
        if match: return float(match.group().replace(',', ''))
        return None
    except:
        return None

data_dict = load_all_data()
shops = ["VMDC", "MK", "SP", "TPD", "WELLEK", "CHAN"]

# --- Session State ---
for shop in shops:
    if f"search_{shop}" not in st.session_state:
        st.session_state[f"search_{shop}"] = ""
    if f"sel_{shop}" not in st.session_state:
        st.session_state[f"sel_{shop}"] = "-"

def master_search_changed():
    ms_val = st.session_state.master_input
    for shop in shops:
        st.session_state[f"search_{shop}"] = ms_val
        st.session_state[f"sel_{shop}"] = "-"

def clear_search(shop_name):
    master_val = st.session_state.get("master_input", "")
    st.session_state[f"search_{shop_name}"] = master_val
    st.session_state[f"sel_{shop_name}"] = "-"

def auto_match_from_vmdc():
    selected_vmdc = st.session_state.sel_VMDC
    if selected_vmdc and selected_vmdc != "-":
        for shop in ["MK", "SP", "TPD", "WELLEK", "CHAN"]:
            df = data_dict[shop]
            if not df.empty and 'ชื่อสินค้า' in df.columns:
                choices = df['ชื่อสินค้า'].dropna().unique().tolist()
                matches = difflib.get_close_matches(selected_vmdc, choices, n=1, cutoff=0.1)
                st.session_state[f"sel_{shop}"] = matches[0] if matches else "-"

# 4. UI ค้นหา
st.markdown("### 🔍 ค้นหาและจับคู่สินค้าแยกตามร้านค้า")
st.text_input("🔍 ค้นหารวม (พิมพ์เพื่อลงทุกช่องอัตโนมัติ):", key="master_input", on_change=master_search_changed)
st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px;'>", unsafe_allow_html=True)

# 5. UI เลือกสินค้า
st.markdown("#### 🛒 เลือกสินค้าที่ต้องการเปรียบเทียบ")
selections = {}

for shop in shops:
    col1, col2, col3 = st.columns([1.5, 3.5, 0.8])
    df = data_dict[shop]
    
    with col1:
        search_val = st.text_input(f"ค้นหา {shop}:", key=f"search_{shop}")
        
    with col2:
        options = ["-"]
        if not df.empty and 'ชื่อสินค้า' in df.columns:
            all_items = df['ชื่อสินค้า'].dropna().unique().tolist()
            if search_val:
                search_term_lower = search_val.lower().strip()
                filtered = [item for item in all_items if search_term_lower in item.lower()]
                filtered.sort(key=lambda x: difflib.SequenceMatcher(None, search_term_lower, x.lower()).ratio(), reverse=True)
                options += filtered
            else:
                options += all_items
                
        current_sel = st.session_state[f"sel_{shop}"]
        if current_sel not in options:
            options = [current_sel] + options
            
        st.markdown("<div style='padding-top: 2px;'></div>", unsafe_allow_html=True)
        if shop == "VMDC":
            selected = st.selectbox(f"เลือกร้าน {shop}", options, key=f"sel_{shop}", label_visibility="collapsed", on_change=auto_match_from_vmdc)
        else:
            selected = st.selectbox(f"เลือกร้าน {shop}", options, key=f"sel_{shop}", label_visibility="collapsed")
        selections[shop] = selected
        
    with col3:
        st.markdown("<div style='padding-top: 2px;'></div>", unsafe_allow_html=True)
        st.button("ล้างค่า", key=f"btn_clear_{shop}", on_click=clear_search, args=(shop,))

# 6. เปรียบเทียบราคา
st.markdown("<br>", unsafe_allow_html=True)
if st.button("📊 เปรียบเทียบราคา", type="primary", use_container_width=True):
    compare_list = []
    prices_for_calc = []
    raw_prices_map = []
    
    for shop in shops:
        selected = selections[shop]
        price_display = "-"
        p_val = None
        
        if selected != "-":
            df = data_dict[shop]
            matched_row = df[df['ชื่อสินค้า'] == selected]
            if not matched_row.empty:
                raw_price = matched_row['ราคา'].values[0]
                price_display = str(raw_price)
                p_val = clean_price(raw_price)
                if p_val is not None:
                    prices_for_calc.append(p_val)
        
        display_shop_name = f"{shop} (อ้างอิง)" if shop == "VMDC" else shop
        compare_list.append({
            "ร้านค้า": display_shop_name,
            "ชื่อสินค้าที่เลือก": selected if selected != "-" else "-",
            "ราคา": price_display
        })
        raw_prices_map.append((display_shop_name, p_val))
        
    df_compare = pd.DataFrame(compare_list)
    st.markdown("### 📊 ผลการเปรียบเทียบราคา:")
    st.dataframe(df_compare, use_container_width=True)
    
    # 7. กราฟจุดใหม่ (คำนวณราคาแนะนำ 25% จาก Min-Max)
    if prices_for_calc:
        min_p = min(prices_for_calc)
        max_p = max(prices_for_calc)
        
        # --- ลอจิกใหม่: คำนวณจุด 25% ระหว่าง Min กับ Max ---
        p25 = min_p + 0.25 * (max_p - min_p)
        
        st.success(f"💡 **แนะนำราคาขาย (25% ของช่วงราคาตลาด): {p25:,.2f} บาท**")
        st.info(f"*(คำนวณจาก: ราคาต่ำสุด {min_p:,.2f} + 25% ของส่วนต่างราคาในตลาด)*")
        
        st.markdown("#### 📈 กราฟเปรียบเทียบราคา")
        
        # กรองเฉพาะร้านที่มีราคา
        valid_points = [(s, p) for s, p in raw_prices_map if p is not None]
        v_names = [x[0] for x in valid_points]
        v_prices = [x[1] for x in valid_points]
        
        # คำนวณตำแหน่ง % บนแกน Y (0-100)
        if max_p > min_p:
            y_percents = [(p - min_p) / (max_p - min_p) * 100 for p in v_prices]
        else:
            y_percents = [50] * len(v_prices)
            
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.set_ylim(-15, 115)
        ax.set_ylabel('ราคาเทียบ % (0=ถูกสุด, 100=แพงสุด)')
        
        # วาดจุดร้านค้า
        for i in range(len(v_names)):
            name = v_names[i]
            y_pos = y_percents[i]
            price = v_prices[i]
            
            color = 'green' if '(อ้างอิง)' in name else 'skyblue'
            ax.plot(name, y_pos, marker='o', color=color, markersize=12)
            ax.text(name, y_pos - 8, name, ha='center', va='top', fontsize=12, fontweight='bold', color=color)
            ax.text(name, y_pos + 5, f"{price:,.2f}", ha='center', va='bottom', fontsize=11)

        # วาดจุดแนะนำขาย (ล็อคที่ Y=25 เสมอ ซึ่งตอนนี้ค่า 811.25 จะอยู่ที่นี่พอดี)
        target_y_p25 = 25
        ax.plot('แนะนำขาย', target_y_p25, marker='o', color='red', markersize=12)
        ax.text('แนะนำขาย', target_y_p25 - 8, 'แนะนำขาย', ha='center', va='top', fontsize=12, fontweight='bold', color='red')
        ax.text('แนะนำขาย', target_y_p25 + 5, f"{p25:,.2f}", ha='center', va='bottom', fontsize=11, color='red')
        
        ax.axhline(y=target_y_p25, color='red', linestyle='--', alpha=0.3) 
        
        ax.set_xticks([])
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.warning("ไม่มีข้อมูลราคาที่เป็นตัวเลขเพียงพอสำหรับคำนวณและวาดกราฟ")
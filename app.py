import streamlit as st
import akshare as ak
import pandas as pd
import datetime

# 页面配置
st.set_page_config(page_title="基金智能分析助手", layout="wide")
st.title("📊 基金智能分析助手 (实时数据版)")
st.markdown("数据来源：AkShare 开源财经数据 | 更新频率：实时抓取")

# 侧边栏设置
st.sidebar.header("⚙️ 设置")
default_codes = "000652, 000991, 110011"
fund_codes = st.sidebar.text_input("输入基金代码 (逗号分隔)", value=default_codes)
refresh = st.sidebar.button("🔄 刷新数据")

# 核心分析逻辑
def analyze_fund(code):
    try:
        # 1. 获取基金实时净值数据 (东财接口)
        fund_df = ak.fund_etf_fund_info_em(fund="开放式基金")
        target = fund_df[fund_df['代码'] == code]
        
        if target.empty:
            return None
            
        name = target['名称'].values[0]
        net_value = float(target['单位净值'].values[0])
        growth = float(target['日增长率'].values[0])
        
        # 2. 获取历史数据计算 PE 百分位 (模拟逻辑，因免费接口限制，此处用近 1 年涨幅代替趋势)
        # 注意：真实的 PE 百分位需要付费数据源，这里用“近 1 年涨幅”作为趋势参考
        fund_hist = ak.fund_open_fund_info_em(fund=code, indicator="单位净值走势")
        if len(fund_hist) < 250:
            trend_score = "数据不足"
        else:
            # 简单计算：当前净值在过去 1 年的位置
            recent_nav = fund_hist['单位净值'].iloc[-1]
            year_ago_nav = fund_hist['单位净值'].iloc[-250]
            year_growth = (recent_nav - year_ago_nav) / year_ago_nav
            
            if year_growth < -0.1:
                trend_score = "低位 (可能低估)"
                signal = "✅ 关注买入"
                color = "green"
            elif year_growth > 0.3:
                trend_score = "高位 (可能高估)"
                signal = "⚠️ 注意风险"
                color = "red"
            else:
                trend_score = "震荡区间"
                signal = "⭕ 持有观望"
                color = "orange"

        return {
            "name": name,
            "code": code,
            "net_value": net_value,
            "growth": growth,
            "trend": trend_score,
            "signal": signal,
            "color": color
        }
    except Exception as e:
        return {"error": str(e)}

# 主界面
if refresh or 'data' not in st.session_state:
    with st.spinner('正在抓取真实数据...'):
        codes_list = [c.strip() for c in fund_codes.split(',')]
        results = []
        for code in codes_list:
            res = analyze_fund(code)
            if res and "error" not in res:
                results.append(res)
        st.session_state['data'] = results
        st.session_state['time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 显示结果
if 'data' in st.session_state:
    st.write(f"最后更新时间：{st.session_state['time']}")
    
    for item in st.session_state['data']:
        with st.expander(f"{item['name']} ({item['code']}) - {item['signal']}"):
            col1, col2, col3 = st.columns(3)
            col1.metric("单位净值", item['net_value'])
            col2.metric("日涨跌", f"{item['growth']}%", delta_color="normal")
            col3.metric("趋势判断", item['trend'])
            
            st.info(f"💡 **操作建议**: {item['signal']}")
            st.caption("注：建议基于近 1 年涨幅位置判断，仅供参考，不构成投资建议。")
else:
    st.warning("请输入基金代码并点击刷新")

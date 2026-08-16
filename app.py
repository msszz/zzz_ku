import io
import math
import socket
import statistics
from datetime import datetime

import qrcode
import streamlit as st


# ============================================================
# 0. 页面设置
# ============================================================
st.set_page_config(
    page_title="拉脱法表面张力实验智能误差分析系统",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    /* 整体：尽量接近 LabVIEW 灰色仪器面板 */
    .stApp {
        background: #d6d6d6;
    }

    .block-container {
        max-width: 1680px;
        padding-top: 0.7rem;
        padding-bottom: 1.2rem;
        padding-left: 1.0rem;
        padding-right: 1.0rem;
    }

    header[data-testid="stHeader"] {
        background: rgba(0,0,0,0);
        height: 0rem;
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    /* 面板 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #d0d0d0;
        border: 2px solid #666666 !important;
        border-radius: 2px;
        box-shadow: inset 0 0 0 1px #f5f5f5;
    }

    /* 输入框/文本框 */
    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div {
        background: #f1f1f1;
        border-radius: 0px;
    }

    input, textarea {
        font-size: 1rem !important;
    }

    /* 按钮 */
    .stButton > button,
    .stDownloadButton > button,
    .stFormSubmitButton > button {
        border-radius: 2px;
        border: 1px solid #666;
        background: linear-gradient(#f4f4f4, #c9c9c9);
        color: #111;
        font-weight: 600;
        min-height: 2.7rem;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover,
    .stFormSubmitButton > button:hover {
        border-color: #222;
        background: linear-gradient(#ffffff, #d7d7d7);
        color: #111;
    }

    /* 标题颜色 */
    .title-red {
        color: #ff1c1c;
        font-size: 1.72rem;
        line-height: 1.2;
        text-align: center;
        font-weight: 500;
        margin: 0.15rem 0 0.65rem 0;
    }

    .title-purple {
        color: #6d58ff;
        font-size: 1.34rem;
        text-align: center;
        font-weight: 500;
        margin: 0.15rem 0 0.55rem 0;
    }

    .title-blue {
        color: #2856ff;
        font-size: 1.36rem;
        text-align: center;
        font-weight: 500;
        margin: 0.25rem 0 0.55rem 0;
    }

    .big-red {
        color: #ff1c1c;
        font-size: 2.0rem;
        text-align: center;
        font-weight: 500;
        margin: 0.15rem 0 0.45rem 0;
    }

    .result-box {
        background: #ededed;
        border: 1px solid #bdbdbd;
        padding: 0.45rem 0.6rem;
        min-height: 2.3rem;
        margin-bottom: 0.55rem;
        text-align: center;
        font-size: 1rem;
    }

    .scene-box {
        background: #ededed;
        border: 1px solid #bdbdbd;
        min-height: 3.3rem;
        padding: 0.75rem 0.7rem;
        margin-bottom: 0.75rem;
        text-align: center;
        font-size: 1.05rem;
        font-weight: 650;
    }

    .question-box {
        background: #ededed;
        border: 1px solid #bdbdbd;
        min-height: 10.5rem;
        padding: 0.9rem 0.9rem;
        margin-bottom: 0.6rem;
        font-size: 1.02rem;
        line-height: 1.75;
    }

    .cause-box {
        background: #f1f1f1;
        border: 1px solid #bdbdbd;
        min-height: 5.5rem;
        padding: 0.9rem;
        font-size: 1.0rem;
        line-height: 1.7;
    }

    .small-label {
        font-size: 0.98rem;
        margin-bottom: 0.15rem;
        color: #222;
    }

    div[data-testid="stMetric"] {
        background: #ededed;
        border: 1px solid #bdbdbd;
        padding: 0.35rem 0.5rem;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 0.95rem;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.13rem;
    }

    @media (max-width: 900px) {
        .title-red { font-size: 1.4rem; }
        .big-red { font-size: 1.55rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 1. 误差问题库 / 原因库
# ============================================================
DIAGNOSIS_DB = {
    "数据整体偏小": {
        "questions": [
            "金属丝框是否没有用待测液体充分冲洗，导致金属丝框表面不够洁净？",
            "金属丝框表面是否存在干燥结块杂质，或残留了上次实验的其他液体？",
            "容器内待测液体是否过少，导致金属丝框无法完全浸入液面以下？",
            "提拉金属丝框全过程中，装置是否有倾斜，没有严格保持竖直？",
            "提拉速度是否过快，导致液膜瞬间被拉断，没有达到最大拉力？",
            "是否在液膜还没有完全破裂时就提前记录了拉力数值？",
            "拉起过程中金属丝框是否碰到容器壁，使液膜提前破裂？",
            "待测液体是否长时间敞口放置，发生明显挥发或混入杂质？",
            "实验液体温度是否明显高于参考温度，且没有进行温度修正？",
            "拉力传感器是否存在零点漂移、内部卡滞或示值偏小的情况？",
        ],
        "causes": [
            "金属丝框清洁或润洗不充分。金属丝框表面残留杂质会影响液膜形成，使液膜提前破裂，测得的最大拉力偏小。建议重新清洗金属丝框，并使用待测液充分润洗。",
            "金属丝框表面存在干燥结块杂质或其他液体残留。杂质会破坏液膜连续性，使最大拉力偏小。建议彻底清洗并重新润洗金属丝框。",
            "容器内待测液体过少，金属丝框浸润不充分。液膜形成不完整会使测得拉力偏小。建议补充待测液并保证金属丝框充分浸入。",
            "金属丝框在提拉过程中发生倾斜。受力方向改变会使液膜受力不均并提前破裂。建议保持装置竖直、金属丝框水平。",
            "提拉速度过快。液膜尚未充分伸展就发生破裂，导致记录的最大拉力偏小。建议匀速、缓慢提拉。",
            "读数时机过早。液膜尚未达到最大承载状态就记录数值，会使最大拉力偏小。建议在接近液膜破裂前记录峰值。",
            "金属丝框与容器壁发生接触。接触会扰动液膜并造成提前破裂。建议调整容器和金属丝框位置，避免接触。",
            "待测液挥发或混入杂质，使液体组成发生变化并影响表面张力。建议使用新鲜待测液并减少长时间敞口。",
            "实验温度高于参考温度而未修正。水的表面张力通常随温度升高而降低，因此可能出现测量值偏低。建议统一温度或采用对应温度标准值。",
            "拉力传感器存在零点漂移、机械卡滞或示值偏小。建议重新调零并检查测力装置工作状态。",
        ],
    },
    "数据整体偏大": {
        "questions": [
            "金属丝框拉起前，表面是否附着了明显的多余液滴或较厚液层？",
            "提拉速度是否过慢，使黏滞阻力或附加液体重量影响最大拉力？",
            "测力装置实验前是否没有正确调零，存在正向零点偏移？",
            "金属丝框的有效长度输入值是否可能偏小？",
            "拉力峰值是否受到瞬时冲击、振动或人为拉动影响而被读得过大？",
            "金属丝框是否有倾斜，使受力状态与理论模型不一致？",
            "实验温度是否低于所采用标准值对应的温度？",
            "待测液体中是否混入了会提高表面张力的成分或发生浓度变化？",
            "是否把非液膜表面张力产生的附加力也计入了最大拉力？",
            "测力传感器是否存在示值偏大的系统性误差？",
        ],
        "causes": [
            "金属丝框表面附着多余液滴或较厚液层，附加液体重量被计入拉力，使结果偏大。建议提拉前去除多余液滴并保持均匀润湿。",
            "提拉速度过慢时，黏滞作用或附加液体重量可能影响峰值，使测得拉力偏大。建议按统一速度提拉。",
            "测力装置零点存在正向偏移。所有拉力读数会系统性偏高。建议实验前重新调零。",
            "有效长度 L 输入偏小。由于 α=ΔF/(2L)，L 偏小会导致计算得到的 α 偏大。建议重新核对金属丝框尺寸。",
            "振动、冲击或人为扰动造成瞬时拉力峰值偏高。建议减小外界振动并平稳操作。",
            "金属丝框倾斜会使受力状态偏离理想模型，可能造成系统偏差。建议保持金属丝框姿态稳定。",
            "实验温度低于参考温度时，水的表面张力可能高于参考值。建议使用对应温度的标准值进行比较。",
            "待测液组成或浓度发生改变，可能使其表面张力高于预期。建议更换新鲜、成分明确的待测液。",
            "附加力被误认为表面张力贡献，使最大拉力被高估。建议检查操作过程和读数定义。",
            "测力传感器示值偏大。建议使用标准砝码或已知载荷进行校验。",
        ],
    },
    "数据波动、重复性差": {
        "questions": [
            "多次实验中的提拉速度是否不统一，存在有时较快、有时较慢的情况？",
            "每次实验中金属丝框的初始浸入深度是否不一致？",
            "每次记录最大拉力的时机是否不一致？",
            "实验过程中桌面、支架或测量装置是否存在明显振动？",
            "多次实验中金属丝框的倾斜角度或位置是否发生变化？",
            "金属丝框是否偶尔碰到容器壁或液面附近的其他部件？",
            "实验过程中待测液温度是否有明显变化？",
            "待测液是否发生挥发、污染或液面高度明显变化？",
            "拉力传感器读数是否存在跳动、零点漂移或回零不稳定？",
            "不同次实验之间的操作步骤、等待时间或读数方法是否不一致？",
        ],
        "causes": [
            "多次实验的提拉速度不统一，会造成液膜形成和破裂过程不同，使重复测量离散度增大。建议统一提拉速度。",
            "初始浸入深度不一致，使每次液膜形成状态不同。建议固定液面位置和浸入深度。",
            "最大拉力读数时机不一致，会直接造成峰值读数波动。建议统一判定峰值的操作标准。",
            "外界振动会叠加到测力信号中，使不同次实验峰值出现随机波动。建议使用稳定台面并减少操作扰动。",
            "金属丝框姿态和位置变化会改变液膜受力状态。建议固定夹具并保持几何位置一致。",
            "偶发接触容器壁会破坏液膜，导致个别数据异常。建议调整位置并保证提拉路径无接触。",
            "实验温度变化会引起表面张力变化。建议保持恒温并记录每次测量温度。",
            "挥发、污染或液面高度变化会导致不同次实验条件不一致。建议缩短实验时间并及时补充或更换待测液。",
            "拉力传感器读数跳动或零点漂移会降低重复性。建议重新调零、检查传感器和机械传动部分。",
            "操作步骤不一致属于人为随机误差来源。建议统一实验流程、等待时间和读数方法。",
        ],
    },
}


# ============================================================
# 2. 默认值 / Session State
# ============================================================
DEFAULT_F = [6.90, 6.95, 6.92, 6.98, 6.94]
DEFAULT_L = [51.10, 51.15, 51.20, 51.12, 51.18]

DEFAULT_WIDGETS = {
    "temp": 25.0,
    "aF": 0.1,
    "aL": 0.02,
    "alpha0": 0.07197,
    "error_limit": 5.0,
    "cv_limit": 5.0,
}

for i, v in enumerate(DEFAULT_F, 1):
    DEFAULT_WIDGETS[f"F{i}"] = v
for i, v in enumerate(DEFAULT_L, 1):
    DEFAULT_WIDGETS[f"L{i}"] = v

STATE_DEFAULTS = {
    "results": None,
    "q_index": 0,
    "diag_done": False,
    "confirmed_cause": "",
    "excluded": [],
    "diagnosis_scene": None,
    "last_temp": 25.0,
}

for k, v in {**DEFAULT_WIDGETS, **STATE_DEFAULTS}.items():
    if k not in st.session_state:
        st.session_state[k] = v


def reset_diagnosis(scene=None):
    st.session_state.q_index = 0
    st.session_state.diag_done = False
    st.session_state.confirmed_cause = ""
    st.session_state.excluded = []
    st.session_state.diagnosis_scene = scene


def clear_all():
    for key, value in DEFAULT_WIDGETS.items():
        st.session_state[key] = value
    st.session_state.results = None
    st.session_state.last_temp = 25.0
    reset_diagnosis(None)


# ============================================================
# 3. 计算函数
# ============================================================
def mean(values):
    return sum(values) / len(values)


def sample_std(values):
    if len(values) < 2:
        return 0.0
    return statistics.stdev(values)


def calculate_results(F, L, aF, aL, alpha0, error_limit, cv_limit):
    """
    F 单位 mN，L 单位 mm。
    数值上 mN/mm = N/m，因此 alpha = meanF / (2*meanL)。
    """
    nF = len(F)
    nL = len(L)

    meanF = mean(F)
    meanL = mean(L)

    if meanF <= 0:
        raise ValueError("ΔF 平均值必须大于 0。")
    if meanL <= 0:
        raise ValueError("L 平均值必须大于 0。")
    if alpha0 <= 0:
        raise ValueError("同温标准表面张力 α₀ 必须大于 0。")

    alpha = meanF / (2.0 * meanL)

    # A 类不确定度
    uAF = sample_std(F) / math.sqrt(nF) if nF > 1 else 0.0
    uAL = sample_std(L) / math.sqrt(nL) if nL > 1 else 0.0

    # B 类不确定度：矩形分布
    uBF = aF / math.sqrt(3.0)
    uBL = aL / math.sqrt(3.0)

    # 单个量合成标准不确定度
    uF = math.sqrt(uAF**2 + uBF**2)
    uL = math.sqrt(uAL**2 + uBL**2)

    # alpha 合成标准不确定度
    uc = alpha * math.sqrt((uF / meanF) ** 2 + (uL / meanL) ** 2)

    # 扩展不确定度 k=2
    U = 2.0 * uc

    # 有符号误差与相对误差
    Es = (alpha - alpha0) / alpha0 * 100.0
    rel_error = abs(Es)

    # CV：这里继续使用 ΔF 的样本标准差 / 平均值
    CV = sample_std(F) / meanF * 100.0

    # 场景判断：波动优先
    if CV >= cv_limit:
        scene = "数据波动、重复性差"
    elif Es <= -error_limit:
        scene = "数据整体偏小"
    elif Es >= error_limit:
        scene = "数据整体偏大"
    else:
        scene = "数据与标准值基本一致"

    return {
        "meanF": meanF,
        "meanL": meanL,
        "alpha": alpha,
        "uAF": uAF,
        "uBF": uBF,
        "uF": uF,
        "uAL": uAL,
        "uBL": uBL,
        "uL": uL,
        "uc": uc,
        "U": U,
        "Es": Es,
        "rel_error": rel_error,
        "CV": CV,
        "scene": scene,
        "error_limit": error_limit,
        "cv_limit": cv_limit,
        "alpha0": alpha0,
    }


def build_report(temp, r):
    cause = st.session_state.get("confirmed_cause", "")
    scene = r["scene"]

    if scene == "数据与标准值基本一致":
        diagnosis = "实验计算结果与同温标准值较为接近，暂未发现明显的数据整体偏大、偏小或重复性问题。"
    elif cause:
        diagnosis = cause
    elif st.session_state.get("diag_done", False):
        diagnosis = "误差来源排查已结束，但未确认具体误差来源。"
    else:
        diagnosis = "等待用户完成误差来源排查。"

    excluded = st.session_state.get("excluded", [])
    excluded_text = "；".join(excluded) if excluded else "暂无"

    return (
        "拉脱法表面张力实验综合分析报告\n"
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"实验温度：{temp:.1f} ℃\n"
        f"ΔF平均值：{r['meanF']:.5f} mN\n"
        f"L平均值：{r['meanL']:.5f} mm\n"
        f"表面张力系数：α = ({r['alpha']:.5f} ± {r['U']:.6f}) N/m（k=2）\n"
        f"同温标准值：α₀ = {r['alpha0']:.5f} N/m\n"
        f"有符号误差：{r['Es']:.2f} %\n"
        f"相对误差：{r['rel_error']:.2f} %\n"
        f"变异系数 CV：{r['CV']:.2f} %\n"
        f"实验结果判断：{scene}\n\n"
        f"已确定的误差来源：\n{diagnosis}\n\n"
        f"已排除的误差因素：\n{excluded_text}\n"
    )


def make_qr_png(text):
    img = qrcode.make(text)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def local_url():
    try:
        ip = socket.gethostbyname(socket.gethostname())
        return f"http://{ip}:8501"
    except Exception:
        return "http://localhost:8501"


def html_result(label, value):
    st.markdown(
        f'<div class="small-label">{label}</div>'
        f'<div class="result-box">{value}</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# 4. 顶部三大区域
# ============================================================
top_left, top_middle, top_right = st.columns([1.00, 1.32, 1.02], gap="small")


# ---------- 左：实验数据输入 ----------
with top_left:
    with st.container(border=True):
        st.markdown('<div class="title-red">1. 实验数据输入</div>', unsafe_allow_html=True)

        with st.form("analysis_form"):
            st.number_input(
                "实验温度（℃）",
                step=0.1,
                format="%.1f",
                key="temp",
            )

            st.markdown("**ΔF 测量值（10⁻³ N）**")
            fcols = st.columns(2)
            for i in range(1, 6):
                col = fcols[(i - 1) % 2]
                with col:
                    st.number_input(
                        f"ΔF{i}",
                        format="%.5f",
                        key=f"F{i}",
                    )

            st.markdown("**L 测量值（mm）**")
            lcols = st.columns(2)
            for i in range(1, 6):
                col = lcols[(i - 1) % 2]
                with col:
                    st.number_input(
                        f"L{i}",
                        format="%.5f",
                        key=f"L{i}",
                    )

            d1, d2 = st.columns(2)
            with d1:
                st.number_input(
                    "数显拉力仪分度值 aF（10⁻³ N）",
                    min_value=0.0,
                    format="%.4f",
                    key="aF",
                )
            with d2:
                st.number_input(
                    "长度仪器分度值 aL（mm）",
                    min_value=0.0,
                    format="%.4f",
                    key="aL",
                )

            alpha_col, blank_col = st.columns(2)
            with alpha_col:
                st.number_input(
                    "同温标准值 α₀（N/m）",
                    min_value=0.00001,
                    format="%.5f",
                    key="alpha0",
                )
            with blank_col:
                st.number_input(
                    "偏差阈值（%）",
                    min_value=0.0,
                    step=0.5,
                    format="%.1f",
                    key="error_limit",
                )

            st.number_input(
                "波动阈值 CV（%）",
                min_value=0.0,
                step=0.5,
                format="%.1f",
                key="cv_limit",
            )

            start_col, clear_col = st.columns(2)

            with start_col:
                submitted = st.form_submit_button(
                    "✅ 开始分析",
                    type="primary",
                    use_container_width=True,
                )

            with clear_col:
                clear_clicked = st.form_submit_button(
                    "🟥 清空",
                    use_container_width=True,
                )

        if submitted:
            try:
                F = [float(st.session_state[f"F{i}"]) for i in range(1, 6)]
                L = [float(st.session_state[f"L{i}"]) for i in range(1, 6)]

                r_new = calculate_results(
                    F=F,
                    L=L,
                    aF=float(st.session_state.aF),
                    aL=float(st.session_state.aL),
                    alpha0=float(st.session_state.alpha0),
                    error_limit=float(st.session_state.error_limit),
                    cv_limit=float(st.session_state.cv_limit),
                )

                st.session_state.results = r_new
                st.session_state.last_temp = float(st.session_state.temp)
                reset_diagnosis(r_new["scene"])
                st.rerun()
            except ValueError as e:
                st.error(str(e))

        if clear_clicked:
            clear_all()
            st.rerun()


r = st.session_state.results


# ---------- 中：计算结果 + 不确定度 ----------
with top_middle:
    with st.container(border=True):
        st.markdown(
            '<div class="title-red">2. 计算结果与误差诊断</div>',
            unsafe_allow_html=True,
        )

        result_col, unc_col = st.columns([1.02, 1.06], gap="small")

        with result_col:
            st.markdown(
                '<div class="title-purple">2.1 计算结果</div>',
                unsafe_allow_html=True,
            )

            if r is None:
                html_result("ΔF平均值（10⁻³ N）", "0.00000")
                html_result("L平均值（mm）", "0.00000")
                html_result("表面张力系数 α（N/m）", "0.00000")
                html_result("同温标准值 α₀（N/m）", f"{st.session_state.alpha0:.5f}")
                html_result("相对误差 |Es|（%）", "0.00")
                html_result("变异系数 CV（%）", "0.00")
            else:
                html_result("ΔF平均值（10⁻³ N）", f"{r['meanF']:.5f}")
                html_result("L平均值（mm）", f"{r['meanL']:.5f}")
                html_result("表面张力系数 α（N/m）", f"{r['alpha']:.5f}")
                html_result("同温标准值 α₀（N/m）", f"{r['alpha0']:.5f}")
                html_result("相对误差 |Es|（%）", f"{r['rel_error']:.2f}")
                html_result("变异系数 CV（%）", f"{r['CV']:.2f}")

        with unc_col:
            st.markdown(
                '<div class="title-purple">2.2 不确定度计算</div>',
                unsafe_allow_html=True,
            )

            if r is None:
                vals = {
                    "uA(ΔF)（10⁻³ N）": "0.0000000",
                    "uB(ΔF)（10⁻³ N）": "0.0000000",
                    "u(ΔF)（10⁻³ N）": "0.0000000",
                    "uA(L)（mm）": "0.0000000",
                    "uB(L)（mm）": "0.0000000",
                    "u(L)（mm）": "0.0000000",
                    "uc(α)（N/m）": "0.00000000",
                    "扩展不确定度 U（N/m）": "0.00000000",
                }
            else:
                vals = {
                    "uA(ΔF)（10⁻³ N）": f"{r['uAF']:.7f}",
                    "uB(ΔF)（10⁻³ N）": f"{r['uBF']:.7f}",
                    "u(ΔF)（10⁻³ N）": f"{r['uF']:.7f}",
                    "uA(L)（mm）": f"{r['uAL']:.7f}",
                    "uB(L)（mm）": f"{r['uBL']:.7f}",
                    "u(L)（mm）": f"{r['uL']:.7f}",
                    "uc(α)（N/m）": f"{r['uc']:.8f}",
                    "扩展不确定度 U（N/m）": f"{r['U']:.8f}",
                }

            for label, value in vals.items():
                html_result(label, value)


# ---------- 右：误差来源 ----------
with top_right:
    with st.container(border=True):
        st.markdown(
            '<div class="title-red">2.3 误差来源</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="title-blue">数据场景</div>',
            unsafe_allow_html=True,
        )

        if r is None:
            st.markdown(
                '<div class="scene-box">等待分析</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="scene-box">{r["scene"]}</div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div class="title-blue">误差分析</div>',
            unsafe_allow_html=True,
        )

        if r is None:
            st.markdown(
                '<div class="question-box">请先在左侧输入实验数据，然后点击“开始分析”。</div>',
                unsafe_allow_html=True,
            )

        elif r["scene"] == "数据与标准值基本一致":
            st.session_state.diag_done = True
            st.markdown(
                '<div class="question-box">'
                '实验结果与标准值较为接近，且重复性满足当前阈值设置，'
                '无需继续进行误差来源排查。'
                '</div>',
                unsafe_allow_html=True,
            )

        else:
            scene = r["scene"]
            db = DIAGNOSIS_DB[scene]
            questions = db["questions"]
            causes = db["causes"]
            q = min(st.session_state.q_index, len(questions) - 1)

            if st.session_state.confirmed_cause:
                st.markdown(
                    '<div class="question-box">'
                    '<b>已确定误差来源：</b><br><br>'
                    f'{st.session_state.confirmed_cause}'
                    '</div>',
                    unsafe_allow_html=True,
                )

            elif st.session_state.diag_done:
                st.markdown(
                    '<div class="question-box">'
                    '本轮误差来源排查已结束，尚未确认具体误差来源。'
                    '</div>',
                    unsafe_allow_html=True,
                )

            else:
                st.markdown(
                    '<div class="question-box">'
                    f'<b>问题 {q + 1}/{len(questions)}</b><br><br>'
                    f'{questions[q]}'
                    '</div>',
                    unsafe_allow_html=True,
                )

                yes_col, no_col = st.columns(2)

                with yes_col:
                    if st.button(
                        "✅ 是",
                        use_container_width=True,
                        key=f"yes_{scene}_{q}",
                    ):
                        st.session_state.confirmed_cause = causes[q]
                        st.session_state.diag_done = True
                        st.rerun()

                with no_col:
                    if st.button(
                        "❌ 否",
                        use_container_width=True,
                        key=f"no_{scene}_{q}",
                    ):
                        if questions[q] not in st.session_state.excluded:
                            st.session_state.excluded.append(questions[q])

                        if q + 1 < len(questions):
                            st.session_state.q_index = q + 1
                        else:
                            st.session_state.diag_done = True
                        st.rerun()

                if st.button(
                    "⏹ 手动结束排查",
                    use_container_width=True,
                    key=f"manual_{scene}_{q}",
                ):
                    st.session_state.diag_done = True
                    st.rerun()

            if st.session_state.excluded:
                with st.expander("查看已排除的误差因素"):
                    for i, item in enumerate(st.session_state.excluded, 1):
                        st.write(f"{i}. {item}")

            if st.session_state.diag_done:
                if st.button(
                    "🔄 重新排查",
                    use_container_width=True,
                    key="restart_diag",
                ):
                    reset_diagnosis(scene)
                    st.rerun()


# ============================================================
# 5. 综合报告
# ============================================================
st.markdown('<div class="big-red">3. 综合报告</div>', unsafe_allow_html=True)

with st.container(border=True):
    if r is None:
        report = "请先输入实验数据并点击“开始分析”。"
    else:
        report = build_report(st.session_state.last_temp, r)

    st.text_area(
        "实验数据分析",
        value=report,
        height=260,
        disabled=True,
        label_visibility="visible",
    )


# ============================================================
# 6. 已确定的误差来源 + 保存
# ============================================================
st.markdown(
    '<div class="title-red">已确定的误差来源</div>',
    unsafe_allow_html=True,
)

cause_col, action_col = st.columns([4.6, 0.85], gap="small")

with cause_col:
    with st.container(border=True):
        if r is None:
            cause_text = "尚未开始分析。"
        elif r["scene"] == "数据与标准值基本一致":
            cause_text = "当前实验数据与标准值基本一致，无需确认误差来源。"
        elif st.session_state.confirmed_cause:
            cause_text = st.session_state.confirmed_cause
        elif st.session_state.diag_done:
            cause_text = "本轮排查结束，但未确认具体误差来源。"
        else:
            cause_text = "等待完成“是 / 否”误差来源排查。"

        st.markdown(
            f'<div class="cause-box">{cause_text}</div>',
            unsafe_allow_html=True,
        )

with action_col:
    if r is not None:
        st.download_button(
            "💾 保存报告",
            data=report.encode("utf-8-sig"),
            file_name="表面张力实验分析报告.txt",
            mime="text/plain",
            use_container_width=True,
        )
    else:
        st.button(
            "💾 保存报告",
            disabled=True,
            use_container_width=True,
        )

    if st.button("🧹 清空全部", use_container_width=True, key="bottom_clear"):
        clear_all()
        st.rerun()


# ============================================================
# 7. 二维码访问（折叠，不占主界面）
# ============================================================
with st.expander("📱 扫码访问 / 二维码"):
    suggested_url = local_url()

    share_url = st.text_input(
        "输入要生成二维码的网址",
        value=suggested_url,
        help=(
            "局域网使用时，手机和电脑需连接同一个 Wi‑Fi；"
            "公网部署后，改成固定的 Streamlit 公网网址。"
        ),
        key="share_url",
    )

    if share_url.strip():
        qr_bytes = make_qr_png(share_url.strip())
        qr_col, info_col = st.columns([1, 2.5])

        with qr_col:
            st.image(qr_bytes, caption="手机扫码打开程序", width=230)

        with info_col:
            st.code(share_url.strip())
            st.write(
                "局域网访问：电脑和手机连接同一 Wi‑Fi，"
                "并确保 Windows 防火墙允许 Python/Streamlit 访问 8501 端口。"
            )
            st.write(
                "公网访问：部署到 Streamlit Community Cloud 等服务器后，"
                "把这里的网址替换为固定公网地址，再生成二维码。"
            )

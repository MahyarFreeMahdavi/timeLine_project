import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
import os

from core import (reflection_coefficient, vswr, input_impedance,
                  standing_wave_pattern, bounce_simulate)


# ==================== فونت BYekan ====================
def get_font_css():
    font_path = "fonts/BYekan.ttf"
    if os.path.exists(font_path):
        with open(font_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return (f"@font-face {{ font-family: 'BYekan'; "
                f"src: url(data:font/ttf;base64,{b64}) format('truetype'); }}",
                "local")
    return ("""
    @font-face {
        font-family: 'BYekan';
        src: url('https://cdn.jsdelivr.net/gh/font-store/font-BYekan@master/BYekan.ttf') format('truetype');
    }
    """, "cdn")


FONT_CSS, FONT_SOURCE = get_font_css()
PLOTLY_FONT = dict(family="BYekan, Tahoma, Segoe UI, sans-serif", size=13)


# ==================== تنظیمات صفحه ====================
st.set_page_config(page_title="آزمایشگاه تعاملی خط انتقال",
                   page_icon="⚡", layout="wide")


# ==================== CSS راست‌چین و ریسپانسیو ====================
st.markdown(f"""
<style>
{FONT_CSS}
html, body, .stApp, [class*="css"] {{
    font-family: 'BYekan', Tahoma, sans-serif !important;
    direction: rtl;
}}
.stApp * {{ text-align: right; }}
[data-testid="stSidebar"] * {{ direction: rtl; text-align: right; }}
[data-testid="stMetricLabel"] div {{ direction: rtl; text-align: right; }}
.stTabs [data-baseweb="tab"] {{ direction: rtl; }}
div[data-testid="stMetricValue"] {{ text-align: right; }}
code, pre, .katex {{ direction: ltr !important; text-align: left !important; }}
[data-testid="stPlotlyChart"] {{ direction: ltr !important; }}

/* ---------- تنظیمات مخصوص موبایل ---------- */
@media (max-width: 768px) {{
    /* حذف حاشیه سایدبار در موبایل تا محتوا کامل دیده شود */
    [data-testid="stAppViewContainer"] > section.main, 
    section.main {{
        margin-right: 0 !important;
        margin-left: 0 !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-top: 1rem !important;
    }}
    
    /* اسکرول افقی برای تب‌ها در موبایل */
    [data-baseweb="tab-list"] {{
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
        white-space: nowrap !important;
    }}
    
    /* کوچک کردن فونت متریک‌ها در موبایل */
    [data-testid="stMetricValue"] {{
        font-size: 1.2rem !important;
    }}
}}
</style>
""", unsafe_allow_html=True)


# ==================== عنوان ====================
st.title("⚡ آزمایشگاه تعاملی خط انتقال")
st.caption("با تغییر پارامترها، رفتار موج ولتاژ و جریان، بازتاب و تطبیق امپدانس را مشاهده کنید.")


# ==================== سایدبار ====================
st.sidebar.header("🔧 پارامترهای خط")
Z0 = st.sidebar.number_input("امپدانس مشخصه Z₀ (Ω)", 5.0, 1000.0, 50.0, 5.0)
ZL = st.sidebar.number_input("امپدانس بار Z_L (Ω)", 0.0, 5000.0, 100.0, 10.0)
Zs = st.sidebar.number_input("امپدانس منبع Z_s (Ω)", 0.0, 5000.0, 50.0, 10.0)
Vs = st.sidebar.number_input("ولتاژ منبع V_s (V)", 0.1, 100.0, 10.0, 0.5)
length = st.sidebar.number_input("طول خط l (m)", 0.1, 1000.0, 100.0, 1.0)
vp_frac = st.sidebar.slider("ضریب سرعت v_p/c", 0.10, 1.0, 0.66, 0.01)
freq_mhz = st.sidebar.number_input("فرکانس f (MHz)", 0.1, 5000.0, 100.0, 1.0)

st.sidebar.divider()
st.sidebar.header("🎨 نمایش")
reverse_x = st.sidebar.checkbox("نمودار: منبع در راست (RTL)", value=True)

st.sidebar.divider()
if FONT_SOURCE == "local":
    st.sidebar.caption("🔤 فونت: BYekan (محلی)")
else:
    st.sidebar.caption("🔤 فونت: BYekan (CDN)")


# ==================== محاسبات ====================
c = 3e8
vp = vp_frac * c
freq = freq_mhz * 1e6
lam = vp / freq
beta = 2 * np.pi / lam

GL = reflection_coefficient(ZL, Z0)
GS = reflection_coefficient(Zs, Z0)
swr = vswr(GL)
zin = input_impedance(Z0, ZL, beta * length)


# ==================== متریک‌ها ====================
c1, c2 = st.columns(2)
c1.metric("ضریب بازتاب بار Γ_L", f"{abs(GL):.3f} ∠{np.angle(GL, deg=True):.0f}°")
c2.metric("ضریب بازتاب منبع Γ_S", f"{abs(GS):.3f} ∠{np.angle(GS, deg=True):.0f}°")

c3, c4 = st.columns(2)
c3.metric("VSWR", "∞" if np.isinf(swr) else f"{swr:.2f}")
sign = "+" if zin.imag >= 0 else "−"
c4.metric("Z_in (Ω)", f"{zin.real:.1f} {sign} {abs(zin.imag):.1f}j")

if abs(GL) < 0.02:
    st.success("✅ تطبیق امپدانس برقرار است — هیچ بازتابی از بار وجود ندارد.")
elif abs(GL) > 0.9:
    st.error("⚠️ بازتاب شدید — موج ایستا با VSWR بالا شکل می‌گیرد.")
else:
    st.info(f"ℹ️ بازتاب جزئی — طول موج λ = {lam:.2f} m (خط = {length/lam:.2f}λ)")


# ==================== تب‌ها ====================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 الگوی موج ایستا",
    "🎬 انتشار گذرای موج",
    "🔁 دیاگرام بازتاب",
    "📚 راهنمای آموزشی",
])


# ---------- تب ۱: موج ایستا ----------
with tab1:
    st.subheader("توزیع دامنه ولتاژ و جریان در طول خط")
    z, V, I, lam = standing_wave_pattern(Z0, ZL, length, freq, vp)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        subplot_titles=("|V(z)| نرمال‌شده", "|I(z)|·Z₀"),
                        vertical_spacing=0.15)
    fig.add_trace(go.Scatter(x=z, y=np.abs(V), name="|V(z)|",
                             line=dict(color="#1565c0", width=3)),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=z, y=np.abs(I) * Z0, name="|I(z)|·Z₀",
                             line=dict(color="#c62828", width=3, dash="dash")),
                  row=2, col=1)
    fig.update_xaxes(title_text="موقعیت روی خط (m)", row=2, col=1)
    for col in (1, 2):
        fig.add_vline(x=0, line_dash="dot", line_color="gray", row=col, col=1)
        fig.add_vline(x=length, line_dash="dot", line_color="gray", row=col, col=1)
    if reverse_x:
        fig.update_xaxes(autorange="reversed")
    # ارتفاع نمودار کمی کوتاه‌تر شد تا در موبایل بهتر جا شود
    fig.update_layout(template="plotly_white", height=450, font=PLOTLY_FONT,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=1, xanchor="right"),
                      margin=dict(t=40, b=40))
    st.plotly_chart(fig, use_container_width=True)

    if abs(GL) > 0.02:
        vmax = 1 + abs(GL)
        vmin = 1 - abs(GL)
        st.caption(f"V_max = {vmax:.3f}  |  V_min = {vmin:.3f}  |  VSWR = {vmax/vmin:.2f}")


# ---------- تب ۲: انتشار گذرا ----------
with tab2:
    st.subheader("شبیه‌سازی زمانی انتشار جبهه موج و بازتاب‌ها")
    n_refl = st.slider("تعداد بازتاب‌ها", 5, 40, 20)

    @st.cache_data(show_spinner="در حال محاسبه…")
    def _bounce(Z0, ZL, Zs, Vs, length, vp, n_refl):
        return bounce_simulate(Z0, ZL, Zs, Vs, length, vp,
                               n_reflections=n_refl, n_frames=180, n_z=250)

    z_arr, t_arr, V_t, I_t, _, _ = _bounce(Z0, ZL, Zs, Vs, length, vp, n_refl)
    frame = st.slider("⏱ زمان", 0, len(t_arr) - 1, 0, format="فریم %d")
    t_now = t_arr[frame] * 1e9

    fig2 = make_subplots(rows=2, cols=1, shared_xaxes=True,
                         subplot_titles=("ولتاژ (V)", "جریان (A)"),
                         vertical_spacing=0.15)
    fig2.add_trace(go.Scatter(x=z_arr, y=V_t[frame], name="V(z,t)",
                              line=dict(color="#1565c0", width=3)), row=1, col=1)
    fig2.add_trace(go.Scatter(x=z_arr, y=I_t[frame] * Z0, name="I(z,t)·Z₀",
                              line=dict(color="#c62828", width=2, dash="dash")), row=2, col=1)
    fig2.update_xaxes(title_text=f"موقعیت (m)   |   t = {t_now:.2f} ns", row=2, col=1)
    for col in (1, 2):
        fig2.add_vline(x=0, line_dash="dot", line_color="gray", row=col, col=1)
        fig2.add_vline(x=length, line_dash="dot", line_color="gray", row=col, col=1)
    if reverse_x:
        fig2.update_xaxes(autorange="reversed")
    fig2.update_layout(template="plotly_white", height=450, font=PLOTLY_FONT,
                       legend=dict(orientation="h", yanchor="bottom", y=1.02, x=1, xanchor="right"),
                       margin=dict(t=40, b=40))
    st.plotly_chart(fig2, use_container_width=True)
    
    st.subheader("🗺️ نقشه انتشار موج")
    fig_heat = go.Figure(data=go.Heatmap(
        z=V_t, x=z_arr, y=t_arr * 1e9, colorscale="RdBu_r",
        colorbar=dict(title="V (volts)")))
    fig_heat.update_layout(template="plotly_white", height=350, font=PLOTLY_FONT,
                           xaxis_title="فاصله (m)", yaxis_title="زمان (ns)",
                           yaxis=dict(autorange="reversed"),
                           margin=dict(t=20, b=40))
    if reverse_x:
        fig_heat.update_xaxes(autorange="reversed")
    st.plotly_chart(fig_heat, use_container_width=True)


# ---------- تب ۳: دیاگرام بازتاب ----------
with tab3:
    st.subheader("دیاگرام بازتاب (Bounce Diagram)")
    T = length / vp
    fig3 = go.Figure()
    n_show = 6
    for k in range(n_show):
        t0 = 2 * k * T
        fig3.add_trace(go.Scatter(
            x=[0, length], y=[t0 * 1e9, (t0 + T) * 1e9],
            mode="lines", line=dict(color="#1565c0", width=2),
            showlegend=(k == 0), name="→ موج فرودی" if k == 0 else None))
        fig3.add_trace(go.Scatter(
            x=[length, 0], y=[(t0 + T) * 1e9, (t0 + 2 * T) * 1e9],
            mode="lines", line=dict(color="#c62828", width=2),
            showlegend=(k == 0), name="← موج بازتابی" if k == 0 else None))
    if reverse_x:
        fig3.update_xaxes(autorange="reversed")
    fig3.update_layout(template="plotly_white", height=450, font=PLOTLY_FONT,
                       xaxis_title="موقعیت (m)", yaxis_title="زمان (ns)",
                       legend=dict(orientation="h", yanchor="bottom", y=1.02, x=1, xanchor="right"),
                       margin=dict(t=40, b=40))
    st.plotly_chart(fig3, use_container_width=True)
    st.caption(f"زمان یک‌طرفه T = l/v_p = {T*1e9:.2f} ns — Γ_L = {abs(GL):.2f}∠{np.angle(GL,deg=True):.0f}°  |  Γ_S = {abs(GS):.2f}∠{np.angle(GS,deg=True):.0f}°")


# ---------- تب ۴: راهنما ----------
with tab4:
    st.markdown(f"""
### 🎯 آزمایش‌های پیشنهادی

**۱) تطبیق امپدانس**  
`Z_L = Z₀` قرار دهید (مثلاً ۵۰ Ω). مقدار Γ_L → ۰، VSWR = ۱ و موج ایستا یکنواخت می‌شود. در نمودار گذرا هیچ بازتابی از بار دیده نمی‌شود.

**۲) مدار باز (Open)**  
`Z_L` را بزرگ کنید (مثلاً ۵۰۰۰ Ω). Γ_L → +۱، بازتاب با همان قطب — ولتاژ در بار دو برابر می‌شود.

**۳) اتصال کوتاه (Short)**  
`Z_L = 0`. Γ_L = −۱، بازتاب با فاز معکوس — ولتاژ در بار صفر می‌شود.

**۴) اثر Γ_S**  
`Z_S ≠ Z₀` قرار دهید تا بازتاب چندباره بین منبع و بار ببینید. برای مشاهده پایدار، `Z_S = Z₀` را امتحان کنید.

---

### 📐 روابط کلیدی
- ضریب بازتاب: **Γ = (Z_L − Z₀)/(Z_L + Z₀)**
- نسبت موج ایستا: **VSWR = (1+|Γ|)/(1−|Γ|)**
- امپدانس ورودی: **Z_in = Z₀ · (Z_L + jZ₀tanβl) / (Z₀ + jZ_L tanβl)**

---

### 🔬 حالت فعلی
- λ = **{lam:.2f} m**، طول الکتریکی = **{length/lam:.2f} λ**
- Γ_L = **{abs(GL):.3f} ∠ {np.angle(GL,deg=True):.0f}°**
- Z_in = **{zin.real:.1f} {sign} {abs(zin.imag):.1f}j Ω**
""")

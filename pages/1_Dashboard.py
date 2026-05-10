# -*- coding: utf-8 -*-
import streamlit as st
import csv, io
from datetime import datetime

st.set_page_config(page_title="FlipFlow Dashboard", page_icon="📊", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600;700&display=swap');
:root { --bg:#0d0f14;--surface:#161922;--card:#1e2330;--border:#2a3040;--accent:#00e5a0;--accent2:#7c6af7;--warn:#f7a24a;--danger:#f75a5a;--text:#e8ecf4;--muted:#7a8499; }
html,body,[class*="css"]{font-family:'DM Sans',sans-serif!important;background-color:var(--bg)!important;color:var(--text)!important;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1.2rem!important;max-width:1280px;}
.ff-header{display:flex;align-items:center;gap:14px;padding:1.2rem 1.6rem;background:var(--card);border:1px solid var(--border);border-radius:14px;margin-bottom:1.5rem;}
.ff-logo{font-family:'Space Mono',monospace;font-size:1.4rem;font-weight:700;color:var(--accent);}
.ff-tagline{font-size:0.8rem;color:var(--muted);margin-top:2px;}
.ff-metrics{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:1.2rem;}
.ff-metric{flex:1;min-width:130px;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px 16px;}
.ff-metric-label{font-size:0.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;}
.ff-metric-value{font-family:'Space Mono',monospace;font-size:1.4rem;font-weight:700;}
.green{color:var(--accent);}.purple{color:var(--accent2);}.orange{color:var(--warn);}.red{color:var(--danger);}
.ff-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1.1rem 1.3rem;margin-bottom:0.8rem;}
.ff-section-label{font-family:'Space Mono',monospace;font-size:0.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.12em;margin-bottom:10px;}
.status-pill{display:inline-block;font-size:0.72rem;font-weight:700;padding:3px 10px;border-radius:20px;font-family:'Space Mono',monospace;}
.pill-listed{background:rgba(124,106,247,0.15);color:#7c6af7;border:1px solid #7c6af7;}
.pill-sold{background:rgba(0,229,160,0.15);color:#00e5a0;border:1px solid #00e5a0;}
.pill-not{background:rgba(122,132,153,0.15);color:#7a8499;border:1px solid #7a8499;}
.stButton>button{background:#00e5a0!important;color:#0d0f14!important;font-weight:700!important;border:none!important;border-radius:8px!important;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="ff-header">
  <div>
    <div class="ff-logo">📊 FlipFlow Dashboard</div>
    <div class="ff-tagline">Your permanent flip ledger</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Load data
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from sheets import sheets_available, load_from_sheets

use_sheets = sheets_available()

if use_sheets:
    if st.button("Refresh"):
        st.rerun()
    items = load_from_sheets()
else:
    items = st.session_state.get("batch_items", [])
    st.caption("Connect Google Sheets in Streamlit Secrets for permanent storage.")

if not items:
    st.markdown('<div style="background:#1e2330;border:2px dashed #2a3040;border-radius:12px;padding:2rem;text-align:center;color:#7a8499;">No inventory yet. Go to <strong style="color:#00e5a0">Browse Mode</strong> and start flipping!</div>', unsafe_allow_html=True)
    st.stop()

def num(val, default=0.0):
    try: return float(val) if val not in ("", None) else default
    except: return default

total_items  = len(items)
total_spent  = sum(num(i.get("actual_cost")) for i in items)
est_profit   = sum(num(i.get("est_profit")) for i in items)
sold_items   = [i for i in items if str(i.get("status","")).lower() == "sold"]
listed_items = [i for i in items if str(i.get("status","")).lower() == "listed"]
not_listed   = [i for i in items if str(i.get("status","")).lower() not in ("sold","listed")]
realized     = sum(num(i.get("real_profit")) for i in sold_items)
margins      = [num(i.get("margin_pct")) for i in items if i.get("margin_pct")]
avg_margin   = sum(margins)/len(margins) if margins else 0

st.markdown(f"""
<div class="ff-metrics">
  <div class="ff-metric"><div class="ff-metric-label">Total Items</div><div class="ff-metric-value">{total_items}</div></div>
  <div class="ff-metric"><div class="ff-metric-label">Total Spent</div><div class="ff-metric-value orange">${total_spent:,.2f}</div></div>
  <div class="ff-metric"><div class="ff-metric-label">Est. Profit</div><div class="ff-metric-value green">${est_profit:,.2f}</div></div>
  <div class="ff-metric"><div class="ff-metric-label">Realized Profit</div><div class="ff-metric-value purple">${realized:,.2f}</div></div>
  <div class="ff-metric"><div class="ff-metric-label">Sold</div><div class="ff-metric-value green">{len(sold_items)}</div></div>
  <div class="ff-metric"><div class="ff-metric-label">Listed</div><div class="ff-metric-value purple">{len(listed_items)}</div></div>
  <div class="ff-metric"><div class="ff-metric-label">Not Listed</div><div class="ff-metric-value orange">{len(not_listed)}</div></div>
  <div class="ff-metric"><div class="ff-metric-label">Avg Margin</div><div class="ff-metric-value">{avg_margin:.0f}%</div></div>
</div>
""", unsafe_allow_html=True)

try:
    import plotly.graph_objects as go
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="ff-section-label">Profit by Item (Sold)</div>', unsafe_allow_html=True)
        if sold_items:
            names  = [i.get("item_name","?")[:22] for i in sold_items]
            profit = [num(i.get("real_profit")) for i in sold_items]
            colors = ["#00e5a0" if p >= 0 else "#f75a5a" for p in profit]
            fig = go.Figure(go.Bar(x=names, y=profit, marker_color=colors))
            fig.update_layout(paper_bgcolor="#1e2330",plot_bgcolor="#1e2330",font_color="#e8ecf4",margin=dict(t=10,b=10,l=10,r=10),height=240,xaxis_tickangle=-30,yaxis=dict(gridcolor="#2a3040"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("No sold items yet.")
    with col2:
        st.markdown('<div class="ff-section-label">Inventory Status</div>', unsafe_allow_html=True)
        sc = {k:v for k,v in {"Not Listed":len(not_listed),"Listed":len(listed_items),"Sold":len(sold_items)}.items() if v>0}
        if sc:
            fig2 = go.Figure(go.Pie(labels=list(sc.keys()),values=list(sc.values()),marker_colors=["#7a8499","#7c6af7","#00e5a0"],hole=0.55))
            fig2.update_layout(paper_bgcolor="#1e2330",font_color="#e8ecf4",margin=dict(t=10,b=10,l=10,r=10),height=240,legend=dict(bgcolor="#1e2330"))
            st.plotly_chart(fig2, use_container_width=True)
except ImportError:
    pass

st.markdown("---")

for section, section_items, pill_cls in [
    ("Sold Items", sold_items, "pill-sold"),
    ("Listed Items", listed_items, "pill-listed"),
    ("Not Listed", not_listed, "pill-not"),
]:
    if not section_items: continue
    st.markdown(f'<div class="ff-section-label">{section} ({len(section_items)})</div>', unsafe_allow_html=True)
    for item in section_items:
        cost   = num(item.get("actual_cost"))
        price  = num(item.get("suggested_price"))
        ep     = num(item.get("est_profit"))
        rp     = num(item.get("real_profit"))
        status = item.get("status","")
        pval   = rp if status=="Sold" else ep
        plabel = "Real" if status=="Sold" else "Est."
        pcls   = "green" if pval>=0 else "red"
        cond   = item.get("condition","")
        name   = item.get("item_name","Unknown")
        date   = item.get("created_at","")
        margin = item.get("margin_pct","")
        st.markdown(f"""
        <div class="ff-card">
          <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
            <div><span style="font-weight:600">{name}</span>{"&nbsp;&nbsp;<span style='color:#7a8499;font-size:0.78rem'>"+cond+"</span>" if cond else ""}</div>
            <span class="status-pill {pill_cls}">{status}</span>
          </div>
          <div style="display:flex;gap:20px;flex-wrap:wrap;margin-top:8px;font-size:0.82rem;color:#7a8499;">
            <span>Cost: <strong style="color:#e8ecf4">${cost:.2f}</strong></span>
            <span>List: <strong style="color:#e8ecf4">${price:.2f}</strong></span>
            <span>{plabel} Profit: <strong class="{pcls}">${pval:.2f}</strong></span>
            <span>Margin: <strong style="color:#e8ecf4">{margin}%</strong></span>
            {"<span>Added: <strong style='color:#e8ecf4'>"+date+"</strong></span>" if date else ""}
          </div>
        </div>""", unsafe_allow_html=True)

st.markdown("---")
col_e, _ = st.columns([1,3])
with col_e:
    out = io.StringIO()
    fields = ["item_name","actual_cost","suggested_price","est_profit","real_profit","margin_pct","status","condition","created_at"]
    w = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(items)
    st.download_button("Export Full Ledger CSV", data=out.getvalue(), file_name=f"flipflow_ledger_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

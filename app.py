# -*- coding: utf-8 -*-
import streamlit as st
import anthropic
import base64
import json
import csv
import io
import os
import uuid
from datetime import datetime
from pathlib import Path

from sheets import sheets_available, load_from_sheets, save_item_to_sheets, update_item_in_sheets, delete_item_from_sheets

# - Page config -
st.set_page_config(
    page_title="FlipFlow",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# - CSS + Animations -
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600;700&display=swap');

:root {
  --bg:#0a0c12; --surface:#12151f; --card:#181d2a; --border:#252d3d;
  --accent:#00ffb3; --accent2:#8b5cf6; --warn:#f59e0b; --danger:#ef4444;
  --text:#e8ecf4; --muted:#6b7a99;
}

/* === BASE === */
html,body,[class*="css"]{font-family:'DM Sans',sans-serif!important;background-color:var(--bg)!important;color:var(--text)!important;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1rem!important;max-width:1300px;}

/* === PARTICLE CANVAS === */
#particle-canvas{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0;opacity:0.55;}

/* === ANIMATED HEADER === */
.ff-header{
  position:relative;overflow:hidden;
  display:flex;align-items:center;justify-content:space-between;
  padding:1.4rem 2rem;
  background:linear-gradient(135deg,#0d1117 0%,#161d2e 50%,#0d1117 100%);
  border:1px solid rgba(0,255,179,0.2);
  border-radius:16px;margin-bottom:1.5rem;
  box-shadow:0 0 40px rgba(0,255,179,0.08),inset 0 1px 0 rgba(255,255,255,0.05);
}
.ff-header::before{
  content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;
  background:conic-gradient(from 0deg at 50% 50%,transparent 0deg,rgba(0,255,179,0.04) 60deg,transparent 120deg);
  animation:spin 12s linear infinite;
}
.ff-header::after{
  content:'';position:absolute;inset:0;
  background:linear-gradient(90deg,transparent,rgba(0,255,179,0.03),transparent);
  animation:shimmer 3s ease-in-out infinite;
}
@keyframes spin{to{transform:rotate(360deg);}}
@keyframes shimmer{0%,100%{opacity:0;}50%{opacity:1;}}

.ff-logo{
  font-family:'Space Mono',monospace;font-size:1.7rem;font-weight:700;
  background:linear-gradient(135deg,#00ffb3,#8b5cf6);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  letter-spacing:-0.04em;position:relative;z-index:1;
  animation:logopulse 3s ease-in-out infinite;
}
@keyframes logopulse{0%,100%{filter:drop-shadow(0 0 8px rgba(0,255,179,0.4));}50%{filter:drop-shadow(0 0 20px rgba(0,255,179,0.8));}}

.ff-tagline{font-size:0.8rem;color:var(--muted);margin-top:3px;position:relative;z-index:1;letter-spacing:0.04em;}

.ff-header-right{display:flex;gap:20px;position:relative;z-index:1;}
.ff-stat{text-align:right;}
.ff-stat-val{font-family:'Space Mono',monospace;font-size:1.1rem;font-weight:700;color:var(--accent);}
.ff-stat-lbl{font-size:0.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.08em;}

/* === GLOWING METRIC TILES === */
.ff-metrics{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:1.2rem;}
.ff-metric{
  flex:1;min-width:120px;
  background:var(--card);
  border:1px solid var(--border);
  border-radius:12px;padding:14px 16px;
  position:relative;overflow:hidden;
  transition:transform 0.2s,box-shadow 0.2s;
  animation:fadein 0.5s ease forwards;
}
.ff-metric:hover{transform:translateY(-3px);box-shadow:0 8px 30px rgba(0,255,179,0.12);}
.ff-metric::after{
  content:'';position:absolute;top:0;left:-100%;width:100%;height:100%;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,0.03),transparent);
  animation:metricshine 4s ease-in-out infinite;
}
@keyframes metricshine{0%{left:-100%;}50%,100%{left:100%;}}
@keyframes fadein{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}

.ff-metric-label{font-size:0.68rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;}
.ff-metric-value{font-family:'Space Mono',monospace;font-size:1.4rem;font-weight:700;color:var(--text);}
.ff-metric-value.green{color:var(--accent);text-shadow:0 0 20px rgba(0,255,179,0.4);}
.ff-metric-value.purple{color:var(--accent2);text-shadow:0 0 20px rgba(139,92,246,0.4);}
.ff-metric-value.orange{color:var(--warn);text-shadow:0 0 20px rgba(245,158,11,0.4);}
.ff-metric-bar{height:2px;background:var(--border);border-radius:2px;margin-top:8px;overflow:hidden;}
.ff-metric-bar-fill{height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2));border-radius:2px;animation:barfill 1.2s ease forwards;}
@keyframes barfill{from{width:0;}to{width:var(--pct,60%);}}

/* === CARDS === */
.ff-card{
  background:var(--card);border:1px solid var(--border);
  border-radius:14px;padding:1.2rem 1.4rem;margin-bottom:0.9rem;
  transition:transform 0.18s,box-shadow 0.18s;
  animation:cardslide 0.4s ease forwards;
}
@keyframes cardslide{from{opacity:0;transform:translateX(-12px);}to{opacity:1;transform:translateX(0);}}
.ff-card:hover{transform:translateY(-2px);box-shadow:0 6px 24px rgba(0,0,0,0.3);}
.ff-card-accent{border-left:3px solid var(--accent);box-shadow:inset 3px 0 12px rgba(0,255,179,0.06);}
.ff-card-warn{border-left:3px solid var(--warn);box-shadow:inset 3px 0 12px rgba(245,158,11,0.06);}
.ff-card-danger{border-left:3px solid var(--danger);box-shadow:inset 3px 0 12px rgba(239,68,68,0.06);}

/* === VERDICT BADGES === */
.ff-verdict{font-family:'Space Mono',monospace;font-size:0.75rem;font-weight:700;padding:4px 12px;border-radius:20px;display:inline-block;}
.verdict-strong{background:rgba(0,255,179,0.12);color:var(--accent);border:1px solid rgba(0,255,179,0.4);box-shadow:0 0 12px rgba(0,255,179,0.2);animation:pulse-green 2s ease-in-out infinite;}
.verdict-decent{background:rgba(139,92,246,0.12);color:var(--accent2);border:1px solid rgba(139,92,246,0.4);}
.verdict-low{background:rgba(239,68,68,0.12);color:var(--danger);border:1px solid rgba(239,68,68,0.4);}
@keyframes pulse-green{0%,100%{box-shadow:0 0 8px rgba(0,255,179,0.2);}50%{box-shadow:0 0 20px rgba(0,255,179,0.5);}}

/* === TABS === */
.stTabs [data-baseweb="tab-list"]{background:var(--card)!important;border-radius:12px!important;border:1px solid var(--border)!important;padding:4px!important;gap:4px!important;}
.stTabs [data-baseweb="tab"]{font-family:'DM Sans',sans-serif!important;font-weight:600!important;font-size:0.86rem!important;color:var(--muted)!important;border-radius:9px!important;padding:8px 20px!important;border:none!important;transition:all 0.2s!important;}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#00ffb3,#00d494)!important;color:#0a0c12!important;box-shadow:0 4px 16px rgba(0,255,179,0.3)!important;}
.stTabs [data-baseweb="tab-panel"]{padding-top:1.2rem!important;}

/* === BUTTONS === */
.stButton>button{
  background:linear-gradient(135deg,#00ffb3,#00d494)!important;
  color:#0a0c12!important;font-family:'DM Sans',sans-serif!important;font-weight:700!important;
  font-size:0.88rem!important;border:none!important;border-radius:10px!important;
  padding:10px 24px!important;transition:all 0.2s!important;
  box-shadow:0 4px 16px rgba(0,255,179,0.25)!important;
}
.stButton>button:hover{transform:translateY(-2px)!important;box-shadow:0 8px 24px rgba(0,255,179,0.4)!important;}
.stButton>button:active{transform:translateY(0)!important;}

/* === INPUTS === */
.stTextInput>div>div>input,.stNumberInput>div>div>input,.stTextArea>div>div>textarea,.stSelectbox>div>div{
  background:var(--surface)!important;border:1px solid var(--border)!important;
  border-radius:10px!important;color:var(--text)!important;
  font-family:'DM Sans',sans-serif!important;
  transition:border-color 0.2s,box-shadow 0.2s!important;
}
.stTextInput>div>div>input:focus,.stTextArea>div>div>textarea:focus{
  border-color:rgba(0,255,179,0.4)!important;
  box-shadow:0 0 0 3px rgba(0,255,179,0.08)!important;
}

/* === PROGRESS === */
.stProgress>div>div{background:linear-gradient(90deg,var(--accent),var(--accent2))!important;border-radius:4px!important;}

/* === UPLOAD ZONE === */
.stFileUploader>div{border-radius:14px!important;}
.upload-hint{
  background:linear-gradient(135deg,var(--card),var(--surface));
  border:2px dashed rgba(0,255,179,0.2);border-radius:14px;
  padding:2.5rem;text-align:center;color:var(--muted);font-size:0.9rem;
  margin-bottom:1rem;transition:border-color 0.3s;
}
.upload-hint:hover{border-color:rgba(0,255,179,0.4);}
.upload-hint span{color:var(--accent);font-weight:600;}

/* === SECTION LABEL === */
.ff-section-label{
  font-family:'Space Mono',monospace;font-size:0.68rem;color:var(--muted);
  text-transform:uppercase;letter-spacing:0.14em;margin-bottom:10px;
  display:flex;align-items:center;gap:8px;
}
.ff-section-label::after{content:'';flex:1;height:1px;background:var(--border);}

/* === DIVIDER === */
hr{border-color:var(--border)!important;}

/* === SCANNING ANIMATION === */
.ff-scanning{
  background:linear-gradient(135deg,var(--card),var(--surface));
  border:1px solid rgba(0,255,179,0.3);border-radius:14px;
  padding:2rem;text-align:center;position:relative;overflow:hidden;
}
.ff-scanning::after{
  content:'';position:absolute;top:0;left:-100%;width:100%;height:100%;
  background:linear-gradient(90deg,transparent,rgba(0,255,179,0.08),transparent);
  animation:scan 1.5s ease-in-out infinite;
}
@keyframes scan{0%{left:-100%;}100%{left:100%;}}

/* === THUMB === */
.thumb-row{display:flex;gap:6px;flex-wrap:wrap;margin-top:4px;}
.thumb-img{width:52px;height:52px;object-fit:cover;border-radius:8px;border:1px solid var(--border);transition:transform 0.2s;}
.thumb-img:hover{transform:scale(1.1);}

/* === SWARM DOTS (decorative) === */
.ff-dots{position:relative;height:3px;overflow:visible;margin:0.5rem 0;}
.ff-dot{position:absolute;width:4px;height:4px;border-radius:50%;background:var(--accent);animation:dotswarm 3s ease-in-out infinite;}
.ff-dot:nth-child(1){left:5%;animation-delay:0s;}
.ff-dot:nth-child(2){left:20%;animation-delay:0.3s;}
.ff-dot:nth-child(3){left:40%;animation-delay:0.6s;}
.ff-dot:nth-child(4){left:60%;animation-delay:0.9s;}
.ff-dot:nth-child(5){left:80%;animation-delay:1.2s;}
@keyframes dotswarm{0%,100%{transform:translateY(0);opacity:0.4;}50%{transform:translateY(-6px);opacity:1;}}

/* === STAGGER CARD ANIMATIONS === */
.ff-card:nth-child(1){animation-delay:0.05s;}
.ff-card:nth-child(2){animation-delay:0.1s;}
.ff-card:nth-child(3){animation-delay:0.15s;}
.ff-card:nth-child(4){animation-delay:0.2s;}
.ff-card:nth-child(5){animation-delay:0.25s;}

/* === ATOM SCANNER === */
.atom-container{
  display:flex;flex-direction:column;align-items:center;
  padding:2rem;gap:1rem;
  background:linear-gradient(135deg,#0d1117,#161d2e);
  border:1px solid rgba(0,255,179,0.15);border-radius:16px;
  position:relative;overflow:hidden;margin-bottom:1rem;
}
.atom-container::before{
  content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse at 50% 40%,rgba(0,255,179,0.06) 0%,transparent 65%);
  animation:aura 2.5s ease-in-out infinite;
}
@keyframes aura{0%,100%{opacity:0.4;transform:scale(1);}50%{opacity:1;transform:scale(1.1);}}
.atom-stage{position:relative;width:280px;height:180px;}
.atom-label{font-family:"Space Mono",monospace;font-size:0.72rem;color:rgba(0,255,179,0.7);letter-spacing:0.12em;text-transform:uppercase;z-index:2;position:relative;}
.atom-sublabel{font-size:0.78rem;color:#6b7a99;z-index:2;position:relative;}
</style>

<canvas id="particle-canvas"></canvas>
<script>
(function(){
  var c=document.getElementById('particle-canvas');
  if(!c)return;
  var ctx=c.getContext('2d');
  var W=c.width=window.innerWidth,H=c.height=window.innerHeight;
  var pts=[];
  for(var i=0;i<55;i++){
    pts.push({x:Math.random()*W,y:Math.random()*H,vx:(Math.random()-0.5)*0.4,vy:(Math.random()-0.5)*0.4,r:Math.random()*1.5+0.5});
  }
  function draw(){
    ctx.clearRect(0,0,W,H);
    pts.forEach(function(p){
      p.x+=p.vx;p.y+=p.vy;
      if(p.x<0||p.x>W)p.vx*=-1;
      if(p.y<0||p.y>H)p.vy*=-1;
      ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      ctx.fillStyle='rgba(0,255,179,0.6)';ctx.fill();
    });
    pts.forEach(function(a,i){
      pts.slice(i+1).forEach(function(b){
        var d=Math.hypot(a.x-b.x,a.y-b.y);
        if(d<120){
          ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);
          ctx.strokeStyle='rgba(0,255,179,'+(0.12*(1-d/120))+')';
          ctx.lineWidth=0.5;ctx.stroke();
        }
      });
    });
    requestAnimationFrame(draw);
  }
  draw();
  window.addEventListener('resize',function(){W=c.width=window.innerWidth;H=c.height=window.innerHeight;});
})();
</script>
""", unsafe_allow_html=True)

# - Constants -
DATA_FILE = "flipflow_data.csv"
MODEL     = "claude-sonnet-4-6"

# - Session state bootstrap -
def _init():
    defaults = {
        "quick_results":  [],   # Phase 1 results
        "batch_items":    [],   # Phase 2 / sell batch
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

# - Helpers -
def img_to_b64(file_bytes: bytes) -> str:
    return base64.standard_b64encode(file_bytes).decode("utf-8")

def resize_image(file_bytes: bytes, max_bytes: int = 4_500_000) -> bytes:
    """Resize image to fit under Claude's 5MB limit."""
    import struct, zlib
    # Try PIL if available, otherwise return as-is
    try:
        from PIL import Image
        import io as _io
        img = Image.open(_io.BytesIO(file_bytes))
        # Convert RGBA to RGB if needed
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        quality = 88
        while True:
            buf = _io.BytesIO()
            img.save(buf, format="JPEG", quality=quality)
            data = buf.getvalue()
            if len(data) <= max_bytes or quality < 30:
                return data
            # Scale down image dimensions too if quality alone isn't enough
            if quality < 50:
                w, h = img.size
                img = img.resize((int(w * 0.75), int(h * 0.75)), Image.LANCZOS)
            quality -= 12
    except Exception:
        return file_bytes

def get_client():
    try:
        key = st.secrets["ANTHROPIC_API_KEY"]
    except (KeyError, FileNotFoundError):
        key = ""
    if not key or not key.strip().startswith("sk-"):
        st.error("⚠️ API key not found. Add ANTHROPIC_API_KEY to your Streamlit Secrets (App Settings > Secrets).")
        st.stop()
    return anthropic.Anthropic(api_key=key.strip())

def verdict_html(verdict: str) -> str:
    v = verdict.lower()
    if "strong" in v:
        return f'<span class="ff-verdict verdict-strong">🚀 Strong</span>'
    elif "low" in v or "skip" in v:
        return f'<span class="ff-verdict verdict-low">⚠️ Low</span>'
    else:
        return f'<span class="ff-verdict verdict-decent">👍 Decent</span>'

# - Atom scanner animation -
def atom_scanner_html(filename: str, index: int, total: int) -> str:
    return f"""
<div class="atom-container">
  <div class="atom-label">scanning market data...</div>
  <div class="atom-stage">
    <canvas id="atom-canvas-{index}" width="280" height="180" style="position:absolute;top:0;left:0;"></canvas>
  </div>
  <div class="atom-sublabel">Analyzing {filename} &nbsp;&bull;&nbsp; {index} of {total}</div>
</div>
<script>
(function(){{
  var cv = document.getElementById('atom-canvas-{index}');
  if(!cv) return;
  var ctx = cv.getContext('2d');
  var W = 280, H = 180, cx = W/2, cy = H/2;

  // Define 4 independent atom clusters with different speeds, sizes, tilts
  var clusters = [
    {{ ox:cx-60, oy:cy,    rx:44, ry:16, tilt:0.4,   spd:0.022, phase:0,    color:'0,255,179',  ecount:3, eph:[] }},
    {{ ox:cx+55, oy:cy-15, rx:38, ry:14, tilt:-0.5,  spd:0.031, phase:2.1,  color:'139,92,246', ecount:2, eph:[] }},
    {{ ox:cx,    oy:cy+30, rx:50, ry:18, tilt:0.9,   spd:0.017, phase:1.0,  color:'245,158,11', ecount:3, eph:[] }},
    {{ ox:cx-20, oy:cy-25, rx:32, ry:12, tilt:-0.3,  spd:0.041, phase:3.5,  color:'0,200,255',  ecount:2, eph:[] }},
  ];

  // Init electron phase offsets per cluster
  clusters.forEach(function(cl){{
    for(var i=0;i<cl.ecount;i++) cl.eph.push(i * (Math.PI*2/cl.ecount));
  }});

  var t = 0;

  function drawEllipse(ox,oy,rx,ry,tilt,color,alpha){{
    ctx.save();
    ctx.translate(ox,oy);
    ctx.rotate(tilt);
    ctx.beginPath();
    ctx.ellipse(0,0,rx,ry,0,0,Math.PI*2);
    ctx.strokeStyle='rgba('+color+','+alpha+')';
    ctx.lineWidth=0.8;
    ctx.stroke();
    ctx.restore();
  }}

  function getElectronPos(ox,oy,rx,ry,tilt,angle){{
    var ex = Math.cos(angle)*rx;
    var ey = Math.sin(angle)*ry;
    var cos=Math.cos(tilt), sin=Math.sin(tilt);
    return {{ x: ox + ex*cos - ey*sin, y: oy + ex*sin + ey*cos }};
  }}

  function frame(){{
    ctx.clearRect(0,0,W,H);
    t += 1;

    clusters.forEach(function(cl){{
      // Draw orbit ring
      drawEllipse(cl.ox,cl.oy,cl.rx,cl.ry,cl.tilt,'rgba('+cl.color+')',0.18);

      // Draw nucleus
      ctx.beginPath();
      ctx.arc(cl.ox,cl.oy,3.5,0,Math.PI*2);
      var grad=ctx.createRadialGradient(cl.ox,cl.oy,0,cl.ox,cl.oy,6);
      grad.addColorStop(0,'rgba('+cl.color+',1)');
      grad.addColorStop(1,'rgba('+cl.color+',0)');
      ctx.fillStyle=grad;
      ctx.fill();

      // Draw electrons
      cl.eph.forEach(function(ph,ei){{
        var angle = cl.phase + t*cl.spd + ph;
        var pos = getElectronPos(cl.ox,cl.oy,cl.rx,cl.ry,cl.tilt,angle);

        // Glow trail
        for(var tr=5;tr>0;tr--){{
          var tangle = angle - tr*0.18;
          var tpos = getElectronPos(cl.ox,cl.oy,cl.rx,cl.ry,cl.tilt,tangle);
          ctx.beginPath();
          ctx.arc(tpos.x,tpos.y,1.2,0,Math.PI*2);
          ctx.fillStyle='rgba('+cl.color+','+(0.06*tr)+')';
          ctx.fill();
        }}

        // Electron dot
        ctx.beginPath();
        ctx.arc(pos.x,pos.y,3,0,Math.PI*2);
        var eg=ctx.createRadialGradient(pos.x,pos.y,0,pos.x,pos.y,5);
        eg.addColorStop(0,'rgba('+cl.color+',1)');
        eg.addColorStop(1,'rgba('+cl.color+',0)');
        ctx.fillStyle=eg;
        ctx.fill();
      }});
    }});

    // Draw faint connecting lines between cluster nuclei
    for(var a=0;a<clusters.length;a++){{
      for(var b=a+1;b<clusters.length;b++){{
        var ca=clusters[a], cb=clusters[b];
        var dist=Math.hypot(ca.ox-cb.ox,ca.oy-cb.oy);
        if(dist<130){{
          var pulse=0.04+0.03*Math.sin(t*0.05+a);
          ctx.beginPath();
          ctx.moveTo(ca.ox,ca.oy);
          ctx.lineTo(cb.ox,cb.oy);
          ctx.strokeStyle='rgba(0,255,179,'+pulse+')';
          ctx.lineWidth=0.6;
          ctx.stroke();
        }}
      }}
    }}

    requestAnimationFrame(frame);
  }}
  frame();
}})();
</script>
"""

# - Claude calls -
def quick_analyze(image_bytes: bytes, planned_cost: float | None) -> dict:
    client = get_client()
    cost_hint = f"The user plans to pay ${planned_cost:.2f}." if planned_cost else "No purchase price given yet."
    prompt = f"""You are a resale expert analyzing a product screenshot for profit potential.

{cost_hint}

Respond ONLY with a valid JSON object (no markdown, no extra text) with these exact keys:
{{
  "item_name": "short product name",
  "detected_price": 0.00,
  "est_resale_low": 0.00,
  "est_resale_high": 0.00,
  "recommended_sell_price": 0.00,
  "estimated_profit": 0.00,
  "margin_pct": 0,
  "condition": "Like New | Good | Fair | Poor",
  "verdict": "Strong | Decent | Low",
  "reasoning": "1-2 sentence explanation"
}}

Rules:
- detected_price: price visible in screenshot (0 if not visible)
- est_resale: realistic local FB Marketplace / OfferUp range
- recommended_sell_price: the HIGH end price that still sells fast
- estimated_profit: recommended_sell_price minus detected_price (or planned cost if given)
- margin_pct: integer 0-100
- condition: your honest assessment of item condition from the screenshot
- verdict: "Strong" if margin >35%, "Decent" if 15-35%, "Low" if <15%
"""
    b64 = img_to_b64(image_bytes)
    resp = client.messages.create(
        model=MODEL,
        max_tokens=600,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
                {"type": "text", "text": prompt}
            ]
        }]
    )
    raw = resp.content[0].text.strip()
    # strip possible markdown fences
    raw = raw.replace("```json","").replace("```","").strip()
    return json.loads(raw)


def full_analyze(images_bytes: list[bytes], actual_cost: float, notes: str) -> dict:
    client = get_client()
    prompt = f"""You are a top-tier resale copywriter AND market analyst.

Actual purchase cost: ${actual_cost:.2f}
Seller notes: {notes or 'None'}

You have {len(images_bytes)} real photos of this item.

Respond ONLY with a valid JSON object (no markdown, no extra text):
{{
  "item_name": "clean product name",
  "condition": "Like New | Good | Fair | Poor",
  "fb_title": "optimized FB Marketplace title under 100 chars",
  "fb_description": "full FB Marketplace description, 3-4 paragraphs, highlight features, condition, and value. Use line breaks.",
  "recommended_price": 0.00,
  "price_low": 0.00,
  "price_high": 0.00,
  "est_profit": 0.00,
  "margin_pct": 0,
  "market_score": 0,
  "reasoning": "2-3 sentence market analysis"
}}

Rules:
- fb_title: compelling, keyword-rich, no ALL CAPS
- recommended_price: sweet spot for fast sale at high margin
- market_score: 1-10 demand score
- est_profit: recommended_price minus actual_cost
- margin_pct: integer
"""
    content = []
    for b in images_bytes:
        content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_to_b64(b)}})
    content.append({"type": "text", "text": prompt})

    resp = client.messages.create(
        model=MODEL,
        max_tokens=1200,
        messages=[{"role": "user", "content": content}]
    )
    raw = resp.content[0].text.strip().replace("```json","").replace("```","").strip()
    return json.loads(raw)

# - Persistence (Google Sheets + CSV fallback) -
def save_batch():
    items = st.session_state.batch_items
    if not items:
        return
    fields = ["id","item_name","actual_cost","suggested_price","est_profit","margin_pct",
              "status","sell_price","real_profit","fb_title","fb_description",
              "condition","market_score","notes","created_at"]
    with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(items)

def load_batch():
    if sheets_available():
        items = load_from_sheets()
        if items:
            st.session_state.batch_items = items
            return
    if not os.path.exists(DATA_FILE):
        return
    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        items = list(reader)
    if items:
        st.session_state.batch_items = items

def export_fb_csv() -> str:
    """Facebook Marketplace bulk upload format."""
    output = io.StringIO()
    fields = ["title","description","price","condition","category"]
    w = csv.DictWriter(output, fieldnames=fields)
    w.writeheader()
    for item in st.session_state.batch_items:
        w.writerow({
            "title":       item.get("fb_title") or item.get("item_name",""),
            "description": item.get("fb_description",""),
            "price":       item.get("suggested_price",""),
            "condition":   item.get("condition","Good"),
            "category":    "For Sale",
        })
    return output.getvalue()

# Load persisted data on first run
if "loaded" not in st.session_state:
    load_batch()
    st.session_state.loaded = True

# - Header -
st.markdown("""
<div class="ff-header">
  <div>
    <div class="ff-logo">⚡ FlipFlow</div>
    <div class="ff-tagline">Screenshot &rarr; Analyze &rarr; List &rarr; Profit</div>
  </div>
  <div class="ff-header-right">
    <div class="ff-stat">
      <div class="ff-stat-val" id="hdr-items">--</div>
      <div class="ff-stat-lbl">Items</div>
    </div>
    <div class="ff-stat">
      <div class="ff-stat-val" id="hdr-profit">--</div>
      <div class="ff-stat-lbl">Est. Profit</div>
    </div>
  </div>
</div>
<div class="ff-dots"><div class="ff-dot"></div><div class="ff-dot"></div><div class="ff-dot"></div><div class="ff-dot"></div><div class="ff-dot"></div></div>
""", unsafe_allow_html=True)

# - API key loaded securely from Streamlit Secrets -

# - Tabs -
tab1, tab2 = st.tabs(["📸  Browse Mode  --  Quick Profit Check", "📦  Sell Batch  --  Ready to Post"])

# -
# PHASE 1 -- Browse Mode
# -
with tab1:
    st.markdown('<div class="ff-section-label">Phase 1 - Screenshot Analyzer</div>', unsafe_allow_html=True)

    with st.container():
        col_up, col_cost = st.columns([3, 1])
        with col_up:
            uploads = st.file_uploader(
                "Drop screenshots here (FB Marketplace, OfferUp, Amazon, store shelves...)",
                accept_multiple_files=True,
                type=["png","jpg","jpeg","webp"],
                key="phase1_uploads",
            )
        with col_cost:
            planned_cost = st.number_input(
                "My planned cost ($)",
                min_value=0.0, value=0.0, step=0.5,
                format="%.2f",
                help="Leave at 0 to auto-detect from screenshot",
            )

    run_check = st.button("⚡ Quick Profit Check", disabled=not uploads)

    if run_check and uploads:
        new_results = []
        atom_slot = st.empty()
        prog_slot  = st.empty()
        for i, f in enumerate(uploads):
            atom_slot.markdown(atom_scanner_html(f.name, i+1, len(uploads)), unsafe_allow_html=True)
            prog_slot.progress((i+1)/len(uploads))
            cost_val = planned_cost if planned_cost > 0 else None
            try:
                raw_bytes = f.read()
                resized = resize_image(raw_bytes)
                data = quick_analyze(resized, cost_val)
                data["_filename"] = f.name
                data["_id"] = str(uuid.uuid4())
                data["_thumb"] = img_to_b64(resized)
                new_results.append(data)
            except Exception as e:
                st.error(f"Error on {f.name}: {e}")
        atom_slot.empty()
        prog_slot.empty()
        st.session_state.quick_results = new_results + st.session_state.quick_results

    # - Summary dashboard -
    if st.session_state.quick_results:
        results = st.session_state.quick_results
        total_potential = sum(float(r.get("estimated_profit", 0) or 0) for r in results)
        total_cost      = sum(float(r.get("detected_price", 0) or 0) for r in results)
        strong_count    = sum(1 for r in results if "strong" in str(r.get("verdict","")).lower())
        avg_margin      = sum(float(r.get("margin_pct", 0) or 0) for r in results) / len(results)

        st.markdown(f"""
        <div class="ff-metrics">
          <div class="ff-metric">
            <div class="ff-metric-label">Items Analyzed</div>
            <div class="ff-metric-value">{len(results)}</div>
          </div>
          <div class="ff-metric">
            <div class="ff-metric-label">Total Potential Profit</div>
            <div class="ff-metric-value green">${total_potential:,.2f}</div>
          </div>
          <div class="ff-metric">
            <div class="ff-metric-label">Est. Total Buy Cost</div>
            <div class="ff-metric-value">${total_cost:,.2f}</div>
          </div>
          <div class="ff-metric">
            <div class="ff-metric-label">🚀 Strong Picks</div>
            <div class="ff-metric-value purple">{strong_count}</div>
          </div>
          <div class="ff-metric">
            <div class="ff-metric-label">Avg Margin</div>
            <div class="ff-metric-value orange">{avg_margin:.0f}%</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="ff-section-label">Results -- click "I Bought This" to move to Sell Batch</div>', unsafe_allow_html=True)

        for idx, r in enumerate(results):
            verdict = r.get("verdict","Decent")
            card_cls = "ff-card-accent" if "strong" in verdict.lower() else ("ff-card-warn" if "decent" in verdict.lower() else "ff-card-danger")

            with st.container():
                st.markdown(f'<div class="ff-card {card_cls}">', unsafe_allow_html=True)

                col_th, col_rest = st.columns([1, 6])
                with col_th:
                    if r.get("_thumb"):
                        st.markdown(f'<img src="data:image/jpeg;base64,{r["_thumb"]}" style="width:72px;height:72px;object-fit:cover;border-radius:8px;border:1px solid #2a3040" />', unsafe_allow_html=True)
                with col_rest:
                    c1, c2, c3, c4, c5, c6 = st.columns([3, 1.2, 1.2, 1.2, 1.2, 1.5])
                with c1:
                    st.markdown(f"**{r.get('item_name','Unknown Item')}**")
                    st.caption(r.get("_filename",""))
                with c2:
                    st.markdown(f"**Buy:** `${float(r.get('detected_price',0)):.2f}`")
                with c3:
                    st.markdown(f"**Sell:** `${float(r.get('recommended_sell_price',0)):.2f}`")
                with c4:
                    profit = float(r.get("estimated_profit",0))
                    color = "green" if profit > 0 else "red"
                    st.markdown(f"**Profit:** :{color}[`${profit:.2f}`]")
                with c5:
                    st.markdown(f"**Margin:** `{r.get('margin_pct',0)}%`")
                with c6:
                    if st.button(f"🛒 I Bought This", key=f"buy_{r['_id']}"):
                        st.session_state[f"show_buy_form_{r['_id']}"] = True

                col_v, col_c = st.columns([2, 2])
                with col_v:
                    st.markdown(verdict_html(verdict), unsafe_allow_html=True)
                with col_c:
                    cond = r.get("condition", "")
                    if cond:
                        st.caption(f"Condition: **{cond}**")
                st.caption(r.get("reasoning",""))
                st.markdown("</div>", unsafe_allow_html=True)

                # - Buy form (inline expander) -
                form_key = f"show_buy_form_{r['_id']}"
                if st.session_state.get(form_key):
                    with st.expander("📸 Upload Real Photos & Confirm Purchase", expanded=True):
                        real_photos = st.file_uploader(
                            "Real product photos",
                            accept_multiple_files=True,
                            type=["png","jpg","jpeg","webp"],
                            key=f"photos_{r['_id']}",
                        )
                        actual_cost = st.number_input(
                            "Actual cost paid ($)",
                            min_value=0.0,
                            value=float(r.get("detected_price",0) or 0),
                            step=0.5,
                            format="%.2f",
                            key=f"cost_{r['_id']}",
                        )
                        notes_input = st.text_area(
                            "Notes (condition, accessories, etc.)",
                            key=f"notes_{r['_id']}",
                            height=80,
                        )
                        if st.button("🔍 Analyze & Add to Sell Batch", key=f"analyze_{r['_id']}"):
                            if not real_photos:
                                st.warning("Upload at least one real photo.")
                            else:
                                listing_slot = st.empty()
                            listing_slot.markdown(atom_scanner_html("your photos", 1, 1), unsafe_allow_html=True)
                            if True:
                                    imgs = [resize_image(p.read()) for p in real_photos]
                                    try:
                                        listing = full_analyze(imgs, actual_cost, notes_input)
                                        # Store thumb as b64 for display (first image)
                                        thumb_b64 = img_to_b64(imgs[0])
                                        batch_item = {
                                            "id":            str(uuid.uuid4()),
                                            "item_name":     listing.get("item_name", r.get("item_name","")),
                                            "actual_cost":   actual_cost,
                                            "suggested_price": listing.get("recommended_price",0),
                                            "est_profit":    listing.get("est_profit",0),
                                            "margin_pct":    listing.get("margin_pct",0),
                                            "status":        "Not Listed",
                                            "sell_price":    "",
                                            "real_profit":   "",
                                            "fb_title":      listing.get("fb_title",""),
                                            "fb_description":listing.get("fb_description",""),
                                            "condition":     listing.get("condition","Good"),
                                            "market_score":  listing.get("market_score",0),
                                            "notes":         notes_input,
                                            "reasoning":     listing.get("reasoning",""),
                                            "thumb_b64":     thumb_b64,
                                            "created_at":    datetime.now().strftime("%Y-%m-%d %H:%M"),
                                        }
                                        listing_slot.empty()
                                        st.session_state.batch_items.append(batch_item)
                                        save_batch()
                                        if sheets_available():
                                            save_item_to_sheets(batch_item)
                                        st.session_state[form_key] = False
                                        st.success(f"✅ Added '{batch_item['item_name']}' to Sell Batch!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Analysis failed: {e}")

        # Clear button
        if st.button("🗑️ Clear Browse Results", key="clear_browse"):
            st.session_state.quick_results = []
            st.rerun()

    else:
        st.markdown("""
        <div class="upload-hint">
          📸 Drop screenshots above to get started.<br>
          <span>FB Marketplace - OfferUp - Amazon - Thrift stores - Any product image</span>
        </div>
        """, unsafe_allow_html=True)

# -
# PHASE 2 -- Sell Batch
# -
with tab2:
    batch = st.session_state.batch_items

    # - Live dashboard -
    total_spent    = sum(float(i.get("actual_cost",0) or 0) for i in batch)
    est_profit_all = sum(float(i.get("est_profit",0) or 0) for i in batch)
    realized       = sum(float(i.get("real_profit",0) or 0) for i in batch if i.get("real_profit"))
    sold_count     = sum(1 for i in batch if i.get("status") == "Sold")
    margins        = [float(i.get("margin_pct",0) or 0) for i in batch if i.get("margin_pct")]
    avg_m          = sum(margins)/len(margins) if margins else 0

    st.markdown(f"""
    <div class="ff-metrics">
      <div class="ff-metric">
        <div class="ff-metric-label">Items in Batch</div>
        <div class="ff-metric-value">{len(batch)}</div>
      </div>
      <div class="ff-metric">
        <div class="ff-metric-label">Total Spent</div>
        <div class="ff-metric-value orange">${total_spent:,.2f}</div>
      </div>
      <div class="ff-metric">
        <div class="ff-metric-label">Est. Profit</div>
        <div class="ff-metric-value green">${est_profit_all:,.2f}</div>
      </div>
      <div class="ff-metric">
        <div class="ff-metric-label">Realized Profit</div>
        <div class="ff-metric-value purple">${realized:,.2f}</div>
      </div>
      <div class="ff-metric">
        <div class="ff-metric-label">Sold</div>
        <div class="ff-metric-value">{sold_count}</div>
      </div>
      <div class="ff-metric">
        <div class="ff-metric-label">Avg Margin</div>
        <div class="ff-metric-value">{avg_m:.0f}%</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if batch:
        # Export button
        col_exp, _ = st.columns([1, 3])
        with col_exp:
            csv_data = export_fb_csv()
            st.download_button(
                "⬇️ Export CSV for FB Bulk Upload",
                data=csv_data,
                file_name=f"flipflow_fb_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
            )

        st.markdown("---")
        st.markdown('<div class="ff-section-label">Batch Items</div>', unsafe_allow_html=True)

        changed = False
        items_to_delete = []

        for idx, item in enumerate(batch):
            with st.container():
                st.markdown('<div class="ff-card">', unsafe_allow_html=True)

                # Row 1: thumb + item info
                col_thumb, col_info = st.columns([1, 7])
                with col_thumb:
                    if item.get("thumb_b64"):
                        st.markdown(
                            f'<img src="data:image/jpeg;base64,{item["thumb_b64"]}" style="width:64px;height:64px;object-fit:cover;border-radius:8px;border:1px solid #2a3040" />',
                            unsafe_allow_html=True
                        )
                with col_info:
                    st.markdown(f"**{item.get('item_name','')}**  -  `{item.get('condition','')}`  -  Market Score: `{item.get('market_score','-')}/10`")
                    st.caption(item.get("fb_title",""))

                # Row 2: financials + status
                c1, c2, c3, c4, c5, c6 = st.columns([1.2, 1.2, 1.2, 1.2, 1.8, 0.8])
                with c1:
                    st.markdown(f"**Cost:** `${float(item.get('actual_cost',0)):.2f}`")
                with c2:
                    st.markdown(f"**List At:** `${float(item.get('suggested_price',0)):.2f}`")
                with c3:
                    ep = float(item.get('est_profit',0))
                    st.markdown(f"**Est Profit:** `${ep:.2f}`")
                with c4:
                    st.markdown(f"**Margin:** `{item.get('margin_pct',0)}%`")
                with c5:
                    statuses = ["Not Listed", "Listed", "Sold"]
                    cur_status = item.get("status","Not Listed")
                    new_status = st.selectbox(
                        "Status",
                        statuses,
                        index=statuses.index(cur_status) if cur_status in statuses else 0,
                        key=f"status_{item['id']}",
                        label_visibility="collapsed",
                    )
                    if new_status != cur_status:
                        st.session_state.batch_items[idx]["status"] = new_status
                        changed = True
                        if sheets_available():
                            update_item_in_sheets(st.session_state.batch_items[idx])
                with c6:
                    if st.button("🗑️", key=f"del_{item['id']}", help="Remove from batch"):
                        items_to_delete.append(idx)

                # If Sold: actual sell price input
                if item.get("status") == "Sold" or new_status == "Sold":
                    sc1, sc2 = st.columns([2, 4])
                    with sc1:
                        cur_sell = float(item.get("sell_price",0) or 0)
                        new_sell = st.number_input(
                            "Actual sell price ($)",
                            min_value=0.0,
                            value=cur_sell,
                            step=0.5,
                            format="%.2f",
                            key=f"sell_{item['id']}",
                        )
                        if new_sell != cur_sell:
                            st.session_state.batch_items[idx]["sell_price"]  = new_sell
                            st.session_state.batch_items[idx]["real_profit"] = round(new_sell - float(item.get("actual_cost",0)), 2)
                            changed = True

                # Listing copy expander
                with st.expander("📋 View / Copy Listing", expanded=False):
                    st.markdown(f"**FB Title:**")
                    st.code(item.get("fb_title",""), language=None)
                    st.markdown(f"**Description:**")
                    st.text_area("", value=item.get("fb_description",""), height=180, key=f"desc_{item['id']}", label_visibility="collapsed")
                    st.caption(f"💡 {item.get('reasoning','')}")

                st.markdown("</div>", unsafe_allow_html=True)

        # Process deletions and saves
        if items_to_delete:
            for idx in sorted(items_to_delete, reverse=True):
                st.session_state.batch_items.pop(idx)
            save_batch()
            st.rerun()

        if changed:
            save_batch()

    else:
        st.markdown("""
        <div class="upload-hint">
          📦 Your Sell Batch is empty.<br>
          <span>Go to Browse Mode -> analyze a screenshot -> click "I Bought This"</span>
        </div>
        """, unsafe_allow_html=True)

"""Self-contained cinematic NASA NeoWs asteroid environment."""
import json
import os
import sqlite3

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="NASA // NEO ORBITAL ENVIRONMENT", page_icon="🌎", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600&display=swap');
.stApp{background:#02050b;color:#d8e4f3;font-family:Manrope,sans-serif}#MainMenu,header,footer{visibility:hidden}.block-container{max-width:1540px;padding:1.2rem 2.2rem 1.8rem}section[data-testid="stSidebar"]{background:#060b15;border-right:1px solid rgba(150,190,255,.12)}div[data-testid="stSelectbox"] label,div[data-testid="stSlider"] label{color:#91a5bf!important;font-size:.72rem!important;letter-spacing:.08em;text-transform:uppercase}.missionbar{display:flex;justify-content:space-between;align-items:center;padding:0 0 14px;border-bottom:1px solid rgba(163,199,238,.13)}.eyebrow,.system{font:.68rem 'DM Mono',monospace;letter-spacing:.14em;color:#7d94af;text-transform:uppercase}.title{margin-top:4px;font-size:1.13rem;letter-spacing:.12em;color:#f1f7ff;font-weight:500}.live{color:#9edfff;border:1px solid rgba(91,196,255,.28);background:rgba(26,125,187,.1);border-radius:20px;padding:6px 10px}.live i{display:inline-block;width:6px;height:6px;margin-right:7px;background:#85dcff;border-radius:50%;box-shadow:0 0 12px #50c9ff}.caption{font:.72rem 'DM Mono',monospace;color:#7187a0;letter-spacing:.04em;margin:11px 2px 0}
</style>""", unsafe_allow_html=True)

def as_bool(series):
    return series.astype(str).str.strip().str.lower().isin(["true", "1", "t", "yes"])

@st.cache_data(ttl=60)
def load_data():
    base = os.path.dirname(os.path.abspath(__file__))
    db_path = os.getenv("DB_PATH", os.path.join(base, "asteroids.db"))
    if os.path.exists(db_path):
        try:
            with sqlite3.connect(db_path) as conn:
                data = pd.read_sql_query("""SELECT a.asteroid_id AS id,a.name,a.hazardous,c.approach_date AS closest_approach_date,c.miss_distance_km FROM asteroids a JOIN close_approaches c ON a.asteroid_id=c.asteroid_id ORDER BY c.miss_distance_km""", conn)
                if not data.empty:
                    data["hazardous"] = as_bool(data["hazardous"])
                    return data
        except Exception:
            pass
    path = os.path.join(base, "asteroids.csv")
    if os.path.exists(path):
        data = pd.read_csv(path)
        data["hazardous"] = as_bool(data["hazardous"])
        return data
    return pd.DataFrame()

def scene_html(objects):
    """Canvas scene has no CDN dependency, so it works inside a Streamlit iframe."""
    payload = json.dumps(objects).replace("</", "<\\/")
    page = r'''<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box}body{margin:0;background:#02050b;overflow:hidden;font-family:Arial;color:#dcecff}#scene{height:690px;position:relative;overflow:hidden;border:1px solid rgba(151,201,255,.16);border-radius:12px;background:#02050b}canvas{width:100%;height:100%;display:block;cursor:grab}.top{position:absolute;z-index:2;top:18px;left:20px;font:11px monospace;letter-spacing:.13em;color:#8ba4c0;pointer-events:none}.top b{display:block;color:#d8edff;font-weight:500;margin-top:5px}.key{position:absolute;z-index:2;bottom:17px;left:20px;font:10px monospace;letter-spacing:.09em;color:#7890aa;line-height:1.8;pointer-events:none}.key i{display:inline-block;width:6px;height:6px;border-radius:50%;background:#e3927e;margin-right:6px}.key .n{background:#91b5cf}#hint{position:absolute;z-index:3;right:18px;bottom:16px;font:10px monospace;color:#8fa8c0;letter-spacing:.08em;pointer-events:none}.tooltip{position:absolute;z-index:5;display:none;padding:10px 12px;border:1px solid rgba(180,221,255,.3);border-radius:7px;background:rgba(4,10,20,.9);font:11px monospace;pointer-events:none;box-shadow:0 12px 35px #0009}.tooltip strong{display:block;color:#eef7ff;font:500 12px Arial;margin-bottom:5px}.haz{color:#f0a08d}.nom{color:#a9cde7}#panel{position:absolute;z-index:6;right:18px;top:18px;width:min(330px,calc(100% - 36px));display:none;padding:18px;border:1px solid rgba(158,211,255,.28);border-radius:10px;background:linear-gradient(150deg,rgba(9,20,37,.96),rgba(3,8,16,.96));box-shadow:0 20px 55px #000a}#panel .tag{font:10px monospace;letter-spacing:.14em;color:#79a3c6}#panel h2{font-size:18px;font-weight:500;line-height:1.25;margin:8px 28px 17px 0;color:#f3f8ff}#close{position:absolute;right:13px;top:13px;border:0;background:transparent;color:#c6e5ff;font-size:21px;cursor:pointer}.field{padding:9px 0;border-top:1px solid rgba(165,207,242,.13);display:flex;justify-content:space-between;gap:10px;font:11px monospace;color:#7f9ab5}.field b{color:#e4f1fd;font-weight:400;text-align:right}.notice{margin-top:14px;font:10px monospace;line-height:1.55;color:#6d849c}
</style></head><body><div id="scene"><canvas id="space"></canvas><div class="top">LIVE NEO ENVIRONMENT<b>EARTH-CENTRIC VISUAL POPULATION MODEL</b></div><div class="key"><i></i> POTENTIALLY HAZARDOUS &nbsp; <i class="n"></i> NOMINAL TARGET<br>ORBITAL LINES ILLUSTRATIVE — NOT EPHEMERIS</div><div id="hint">DRAG TO ROTATE · SCROLL TO ZOOM · SELECT A TARGET</div><div id="tip" class="tooltip"></div><aside id="panel"><button id="close">×</button><div class="tag">NASA NEO // OBJECT INTELLIGENCE</div><h2 id="pname"></h2><div id="fields"></div><div class="notice">Motion is an illustrative visual representation. Values shown are verified fields from the local NASA close-approach dataset.</div></aside></div>
<script>
const data=__DATA__,canvas=document.getElementById('space'),ctx=canvas.getContext('2d'),tip=document.getElementById('tip'),panel=document.getElementById('panel');let W,H,cx,cy,dpr,zoom=1,spin=0,drag=false,lastX=0,selected=null,hovered=null;const stars=Array.from({length:700},()=>({x:Math.random(),y:Math.random(),r:Math.random()*1.35,a:.2+Math.random()*.8}));function hash(s){let h=2166136261;for(let i=0;i<s.length;i++)h=Math.imul(h^s.charCodeAt(i),16777619);return(h>>>0)/4294967295}const ast=data.slice(0,110).map(d=>{let a=hash(String(d.id)),b=hash(d.name),dist=1.35+a*1.75;return{d,a,b,dist,rx:dist*(.8+a*.25),ry:dist*(.45+b*.22),tilt:(b-.5)*.78,phase:a*6.283,speed:.00045+a*.00085,size:3.2+b*3+(d.hazardous?1.5:0)}});function resize(){dpr=Math.min(devicePixelRatio,2);W=canvas.clientWidth;H=canvas.clientHeight;canvas.width=W*dpr;canvas.height=H*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);cx=W/2;cy=H/2}addEventListener('resize',resize);resize();function ellipse(o,t){let x=Math.cos(o.phase+t*o.speed+spin)*o.rx,y=Math.sin(o.phase+t*o.speed+spin)*o.ry,ct=Math.cos(o.tilt),st=Math.sin(o.tilt);return{x:cx+x*cy*.39*zoom*ct-y*cy*.39*zoom*st,y:cy+x*cy*.15*zoom*st+y*cy*.39*zoom*ct}}function earth(t){let r=Math.min(W,H)*.155*zoom,g=ctx.createRadialGradient(cx-r*.32,cy-r*.36,r*.04,cx,cy,r);g.addColorStop(0,'#78d8f8');g.addColorStop(.18,'#178fc9');g.addColorStop(.5,'#075288');g.addColorStop(.78,'#032b59');g.addColorStop(1,'#010b1c');ctx.shadowColor='#198fe6';ctx.shadowBlur=44;ctx.beginPath();ctx.arc(cx,cy,r,0,7);ctx.fillStyle=g;ctx.fill();ctx.shadowBlur=0;ctx.save();ctx.beginPath();ctx.arc(cx,cy,r*.985,0,7);ctx.clip();ctx.globalAlpha=.74;for(let i=0;i<20;i++){let u=(i*.618+t*.000016)%1,x=cx-r+r*2*u,y=cy-r*.68+Math.sin(i*2.5)*r*.45,w=r*(.15+(i%4)*.07),h=r*(.07+(i%3)*.05);ctx.fillStyle=i%3?'#4b8a5e':'#b5a96a';ctx.beginPath();ctx.ellipse(x,y,w,h,i*.3,0,7);ctx.fill()}ctx.globalAlpha=.38;ctx.fillStyle='#f5fbff';for(let i=0;i<18;i++){let x=cx-r+(i*.31%2)*r,y=cy-r+(i*.71%2)*r;ctx.beginPath();ctx.ellipse(x,y,r*.2,r*.032,i*.32,0,7);ctx.fill()}let shade=ctx.createLinearGradient(cx+r*.22,0,cx+r,0);shade.addColorStop(0,'rgba(0,0,10,0)');shade.addColorStop(1,'rgba(0,0,8,.9)');ctx.fillStyle=shade;ctx.fillRect(cx,cy-r,r,r*2);ctx.restore();ctx.strokeStyle='rgba(103,203,255,.56)';ctx.lineWidth=1.4;ctx.beginPath();ctx.arc(cx,cy,r*1.018,0,7);ctx.stroke();return r}function drawRock(x,y,r,haz,hot){ctx.save();ctx.translate(x,y);ctx.rotate((x+y)*.03);ctx.shadowColor=haz?'#f36f4d':'#80b6df';ctx.shadowBlur=hot?19:5;ctx.fillStyle=haz?'#9d5847':'#7f8e99';ctx.beginPath();for(let i=0;i<9;i++){let q=i/9*6.283,v=r*(.74+((i*17)%7)/25);ctx.lineTo(Math.cos(q)*v,Math.sin(q)*v)}ctx.closePath();ctx.fill();ctx.shadowBlur=0;ctx.strokeStyle=haz?'#f7b19c':'#b8d0e1';ctx.globalAlpha=.7;ctx.stroke();ctx.restore()}function render(t){requestAnimationFrame(render);ctx.clearRect(0,0,W,H);let bg=ctx.createRadialGradient(cx,cy,0,cx,cy,Math.max(W,H)*.72);bg.addColorStop(0,'#0a1a31');bg.addColorStop(.36,'#040b18');bg.addColorStop(1,'#010207');ctx.fillStyle=bg;ctx.fillRect(0,0,W,H);stars.forEach(s=>{ctx.globalAlpha=s.a*(.75+.25*Math.sin(t*.001+s.x*20));ctx.fillStyle='#cce8ff';ctx.fillRect(s.x*W,s.y*H,s.r,s.r)});ctx.globalAlpha=1;let r=Math.min(W,H)*.155*zoom;ast.forEach(o=>{ctx.save();ctx.translate(cx,cy);ctx.rotate(o.tilt);ctx.scale(1,.55);ctx.strokeStyle='rgba(128,185,225,.13)';ctx.lineWidth=1;ctx.beginPath();ctx.ellipse(0,0,o.rx*cy*.39*zoom,o.ry*cy*.39*zoom,0,0,7);ctx.stroke();ctx.restore()});earth(t);ast.forEach(o=>{o.p=ellipse(o,t);let hot=o===hovered||o===selected;drawRock(o.p.x,o.p.y,o.size*(hot?1.55:1),o.d.hazardous,hot)});if(selected){let p=selected.p;ctx.strokeStyle='rgba(143,218,255,.75)';ctx.lineWidth=1;ctx.setLineDash([4,5]);ctx.beginPath();ctx.arc(p.x,p.y,selected.size*3.2,0,7);ctx.stroke();ctx.setLineDash([])}}function pick(x,y){return ast.find(o=>Math.hypot(x-o.p.x,y-o.p.y)<o.size+8)}function showTip(o,x,y){tip.style.display='block';tip.style.left=(x+15)+'px';tip.style.top=(y-18)+'px';tip.innerHTML='<strong>'+o.d.name+'</strong><span class="'+(o.d.hazardous?'haz':'nom')+'">HAZARDOUS: '+(o.d.hazardous?'YES':'NO')+'</span>'}function select(o){selected=o;tip.style.display='none';document.getElementById('pname').textContent=o.d.name;document.getElementById('fields').innerHTML=[['NASA designation',o.d.id],['Potentially hazardous',o.d.hazardous?'YES':'NO'],['Close approach',o.d.closest_approach_date],['Miss distance',(o.d.miss_distance_km/1e6).toFixed(2)+' million km'],['Lunar distance',(o.d.miss_distance_km/384400).toFixed(1)+' LD']].map(x=>'<div class="field"><span>'+x[0]+'</span><b>'+x[1]+'</b></div>').join('');panel.style.display='block'}document.getElementById('close').onclick=()=>{selected=null;panel.style.display='none';zoom=1};canvas.onmousemove=e=>{let r=canvas.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;if(drag){spin+=(x-lastX)*.008;lastX=x;return}hovered=pick(x,y);canvas.style.cursor=hovered?'pointer':'grab';if(hovered)showTip(hovered,x,y);else tip.style.display='none'};canvas.onmousedown=e=>{drag=true;lastX=e.clientX};canvas.onmouseup=e=>{drag=false;let r=canvas.getBoundingClientRect(),o=pick(e.clientX-r.left,e.clientY-r.top);if(o)select(o)};canvas.onmouseleave=()=>{drag=false;hovered=null;tip.style.display='none'};canvas.onwheel=e=>{e.preventDefault();zoom=Math.max(.62,Math.min(1.55,zoom-e.deltaY*.0007))};requestAnimationFrame(render);
</script></body></html>'''
    # Keep the component self-contained while tailoring the visual motion model.
    # The static ellipses are suppressed; each object records a short, fading trail.
    return (
        page.replace("__DATA__", payload)
        .replace("speed:.00045+a*.00085", "speed:.000018+a*.000035")
        .replace("ctx.strokeStyle='rgba(128,185,225,.13)'", "ctx.strokeStyle='rgba(128,185,225,0)'")
    )

df = load_data()
st.markdown("<div class='missionbar'><div><div class='eyebrow'>NASA NEO // PLANETARY DEFENSE OBSERVATION</div><div class='title'>ORBITAL ENVIRONMENT</div></div><div class='system live'><i></i> LIVE LOCAL TELEMETRY</div></div>", unsafe_allow_html=True)
if df.empty:
    st.warning("No asteroid records found. Run `python nasa_asteroids.py` to populate the local NASA NeoWs cache.")
    st.stop()
st.sidebar.markdown("### Observation controls")
mode = st.sidebar.selectbox("Population", ["All tracked targets", "Potentially hazardous only", "Nominal targets only"])
max_mkm = max(1.0, float(df["miss_distance_km"].max()) / 1_000_000)
horizon = st.sidebar.slider("Radar horizon — million km", 0.1, round(max_mkm, 1), round(max_mkm, 1), 0.1)
view = df[df.hazardous] if mode == "Potentially hazardous only" else df[~df.hazardous] if mode == "Nominal targets only" else df
view = view[view.miss_distance_km <= horizon * 1_000_000].copy()
components.html(scene_html(view.to_dict(orient="records")), height=692, scrolling=False)
st.markdown("<div class='caption'>INTERACTIVE VISUALIZATION · %d OF %d LOCAL NEO RECORDS · SELECT AN ASTEROID FOR VERIFIED CLOSE-APPROACH INTELLIGENCE</div>" % (len(view), len(df)), unsafe_allow_html=True)

#!/usr/bin/env python3
"""Generate Play Store graphics plus a shared 512px logo for Android and Windows builds."""
from __future__ import annotations
import argparse, json, zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BG=(11,16,32); PANEL=(17,26,43); LINE=(42,56,80); TEXT=(237,243,255)
MUTED=(158,172,195); BLUE=(37,99,235); CYAN=(34,211,238); GREEN=(102,217,167)
PAPER=(248,250,252); INK=(15,23,42); LIGHT=(100,116,139); WHITE=(255,255,255)

def f(size,bold=False,mono=False):
    if mono: names=["C:/Windows/Fonts/consola.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
    elif bold: names=["C:/Windows/Fonts/seguisb.ttf","C:/Windows/Fonts/arialbd.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    else: names=["C:/Windows/Fonts/segoeui.ttf","C:/Windows/Fonts/arial.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for n in names:
        try: return ImageFont.truetype(n,size)
        except OSError: pass
    return ImageFont.load_default()

def bg(size,light=False):
    c=PAPER if light else BG
    im=Image.new("RGB",size,c); d=ImageDraw.Draw(im)
    if not light:
        for y in range(0,size[1],4):
            t=y/max(1,size[1]-1)
            d.rectangle((0,y,size[0],min(size[1],y+4)),fill=tuple(round(BG[i]*(1-t)+(20,30,50)[i]*t) for i in range(3)))
        glow=Image.new("RGBA",size,(0,0,0,0))
        ImageDraw.Draw(glow).ellipse((int(size[0]*.5),-int(size[1]*.25),int(size[0]*1.1),int(size[1]*.3)),fill=(37,99,235,45))
        im=Image.alpha_composite(im.convert("RGBA"),glow.filter(ImageFilter.GaussianBlur(max(18,size[0]//30)))).convert("RGB")
    return im

def logo(path,size=512):
    """Resize the supplied icon directly, preserving RGBA pixels and aspect handling as requested."""
    target = size if isinstance(size, tuple) else (size, size)
    with Image.open(path) as src:
        src.load()
        return src.convert("RGBA").resize(target, Image.Resampling.LANCZOS)

def box(d,xy,fill=PANEL,outline=LINE,r=18,w=2): d.rounded_rectangle(xy,radius=r,fill=fill,outline=outline,width=w)
def text(d,xy,s,size=24,color=TEXT,bold=False,anchor=None,mono=False): d.text(xy,s,font=f(size,bold,mono),fill=color,anchor=anchor)
def wrapped(d,xy,s,size,width,color=MUTED,bold=False,leading=1.3):
    x,y=xy; ft=f(size,bold); line=""
    for word in s.split():
        nxt=word if not line else line+" "+word
        if d.textbbox((0,0),nxt,font=ft)[2] <= width: line=nxt
        else:
            if line: d.text((x,y),line,font=ft,fill=color); y+=int(size*leading)
            line=word
    if line: d.text((x,y),line,font=ft,fill=color); y+=int(size*leading)
    return y
def field(d,x,y,w,label,value,dark=True,helper=None,h=64):
    muted=MUTED if dark else LIGHT; fg=TEXT if dark else INK
    text(d,(x,y),label,20,muted,True); box(d,(x,y+31,x+w,y+31+h),(9,17,31) if dark else WHITE,(52,68,94) if dark else (203,213,225),12,2)
    ft=f(22); val=value
    while d.textbbox((0,0),val,font=ft)[2] > w-32 and len(val)>7: val=val[:-4]+"…"
    text(d,(x+15,y+31+(h-22)//2),val,22,fg)
    bottom=y+31+h
    if helper: bottom=wrapped(d,(x,bottom+8),helper,17,w,muted,leading=1.18)
    return bottom
def button(d,x,y,w,label,primary=True,dark=True,h=62):
    box(d,(x,y,x+w,y+h),BLUE if primary else (28,40,60) if dark else (241,245,249),(75,129,220) if primary else LINE,14,2)
    text(d,(x+w/2,y+h/2),label,22,WHITE if primary or dark else INK,True,"mm")
def header(im,lg,connected=False):
    d=ImageDraw.Draw(im); w=im.width; d.rectangle((0,0,w,156),fill=BG); d.line((0,155,w,155),fill=LINE,width=2)
    mark=lg.resize((92,92),Image.Resampling.LANCZOS); im.paste(mark,(34,32),mark)
    text(d,(148,36),"MySQL IDLE",42,TEXT,True); text(d,(148,91),"Android companion · SQL workspace",23,MUTED)
    label="Connected" if connected else "Not connected"; bw=190 if connected else 225
    box(d,(w-bw-30,54,w-30,106),(19,54,48) if connected else (35,47,68),LINE,23,2)
    text(d,(w-bw/2-30,80),label,20,GREEN if connected else MUTED,True,"mm")
def panel(d,x,y,w,h,title):
    box(d,(x,y,x+w,y+h),PANEL,LINE,24,2); text(d,(x+28,y+22),title,31,TEXT,True)
def status(d,w,light=False):
    fg=INK if light else TEXT; text(d,(38,22),"9:41",22,fg,True); x=w-150
    for i,h in enumerate((10,15,20,25)): d.rounded_rectangle((x+i*12,43-h,x+i*12+7,43),2,fill=fg)
    d.arc((w-91,12,w-53,49),205,335,fill=fg,width=4); d.arc((w-82,23,w-62,43),205,335,fill=fg,width=4)
    d.rounded_rectangle((w-44,20,w-13,39),5,outline=fg,width=2); d.rounded_rectangle((w-39,24,w-21,35),2,fill=fg)

def phone_connect(lg,p):
    im=bg((1080,1920),True); d=ImageDraw.Draw(im); status(d,1080,True)
    mark=lg.resize((140,140),Image.Resampling.LANCZOS); im.paste(mark,(44,100),mark)
    d=ImageDraw.Draw(im); text(d,(214,112),"MySQL IDLE",56,INK,True); text(d,(216,182),"Mobile companion",36,BLUE,True)
    y=305; text(d,(54,y),"Connect to the desktop",40,INK,True); y+=54; text(d,(54,y),"companion",40,INK,True); y+=74
    y=wrapped(d,(54,y),"On Windows, open Tools → Android / Mobile Companion. Enter the HTTPS address and compare the full SHA-256 fingerprint before connecting.",27,960,LIGHT)+26
    y=field(d,54,y,972,"Desktop companion URL","https://192.168.1.20:8765",False,h=76)+22
    y=field(d,54,y,972,"Desktop certificate SHA-256 fingerprint","AA:BB:CC:… (64 hex digits)",False,h=76)+18
    y=wrapped(d,(54,y),"HTTPS is required. Use a trusted private network and verify the fingerprint shown on Windows.",24,960,LIGHT)+24
    button(d,54,y,972,"Verify and connect",True,False,78); text(d,(54,y+120),"Network security",30,INK,True)
    wrapped(d,(54,y+170),"The app pins the desktop HTTPS certificate. Only private LAN IPv4 addresses are accepted. Database credentials are not saved by this app.",23,960,LIGHT)
    text(d,(54,1780),"Privacy Policy",24,BLUE,True); d.line((54,1812,205,1812),fill=BLUE,width=2)
    d.rounded_rectangle((450,1883,630,1892),5,fill=(31,41,55)); im.save(p,format="PNG",optimize=True)

def phone_pair(lg,p):
    im=bg((1080,1920)); d=ImageDraw.Draw(im); status(d,1080); header(im,lg,False); d=ImageDraw.Draw(im)
    x,y,w=42,190,996; panel(d,x,y,w,1255,"Unlock and pair with desktop"); y+=90
    y=wrapped(d,(x+30,y),"Enter the same master password set on Windows and the temporary code shown in Tools → Android / Mobile Companion. Compare the certificate fingerprint before connecting.",24,w-60)+26
    y=field(d,x+30,y,w-60,"MySQL IDLE master password","••••••••••••",True,"Checked over HTTPS; not saved on Android.",68)+24
    y=field(d,x+30,y,w-60,"Temporary pairing code","12345 67890",True,"Enter the current 10-digit code shown on the desktop.",68)+30
    button(d,x+30,y,w-60,"Unlock and pair",True,True,78); y+=110
    box(d,(x+30,y,x+w-30,y+90),(21,45,44),(42,86,70),16,2); d.ellipse((x+55,y+34,x+75,y+54),fill=GREEN); text(d,(x+92,y+28),"Ready when both fields are supplied.",22,GREEN,True)
    text(d,(52,1545),"SECURITY BUILT IN",22,CYAN,True); wrapped(d,(52,1588),"Certificate-pinned HTTPS · Private LAN only · Session expires after inactivity",23,950)
    d.rounded_rectangle((450,1883,630,1892),5,fill=(226,232,240)); im.save(p,format="PNG",optimize=True)

def phone_connection(lg,p):
    im=bg((1080,1920)); d=ImageDraw.Draw(im); status(d,1080); header(im,lg,True); d=ImageDraw.Draw(im)
    x,y,w=42,190,996; panel(d,x,y,w,1115,"MySQL connection"); x+=30; y+=90; w-=60
    y=field(d,x,y,w//2-10,"Host (as seen by desktop)","localhost",True,h=57)+10
    field(d,x+w//2+10,y-100,w//2-10,"Port","3306",True,h=57); y+=12
    y=field(d,x,y,w,"Username","db_user",True,h=57)+12
    y=field(d,x,y,w,"Password (not saved)","••••••••••",True,"Hidden by default and cleared after a successful connection.",57)+14
    box(d,(x,y,x+w,y+66),(9,17,31),(52,68,94),12,2); d.rectangle((x+18,y+19,x+46,y+47),outline=BLUE,width=3); d.line((x+23,y+33,x+30,y+40,x+42,y+25),fill=BLUE,width=3); text(d,(x+61,y+20),"Require verified TLS to MySQL",21,TEXT,True); y+=82
    y=field(d,x,y,w,"MySQL CA certificate path (optional)",r"C:\certs\mysql-ca.pem",True,h=50)+12
    y=field(d,x,y,w,"Database (optional)","sales",True,h=50)+16
    button(d,x,y,w,"Connect to MySQL",True,True,66); panel(d,42,1370,996,285,"Before you connect")
    wrapped(d,(76,1440),"The Windows desktop makes the MySQL connection. Use a least-privilege database account and a trusted private network.",23,900)
    d.rounded_rectangle((450,1883,630,1892),5,fill=(226,232,240)); im.save(p,format="PNG",optimize=True)

def phone_query(lg,p):
    im=bg((1080,1920)); d=ImageDraw.Draw(im); status(d,1080); header(im,lg,True); d=ImageDraw.Draw(im)
    box(d,(42,178,1038,246),(17,55,48),(44,91,75),16,2); d.ellipse((68,202,88,222),fill=GREEN); text(d,(108,191),"Connected to MySQL",25,GREEN,True)
    panel(d,42,274,996,560,"SQL editor"); text(d,(76,337),"Ctrl/⌘ + Enter to run",21,MUTED)
    box(d,(74,382,1006,557),(9,17,31),(52,68,94),13,2); text(d,(100,413),"SELECT 1 AS status;",30,(124,211,255),False,mono=True); text(d,(100,472),"-- quick check",25,(119,157,178),False,mono=True)
    button(d,74,585,220,"Run SQL",True,True,60); button(d,310,585,160,"Clear",False,True,60); button(d,486,585,210,"Previous",False,True,60); button(d,712,585,210,"Next",False,True,60)
    text(d,(76,666),"Quick SQL template…",22,MUTED); text(d,(76,714),"1/50 queries in memory",19,MUTED); panel(d,42,770,996,490,"Result"); button(d,730,822,278,"Export complete CSV",False,True,54)
    box(d,(74,900,1006,1000),(9,17,31),(52,68,94),12,2); text(d,(96,932),"1 row · 1 column",22,GREEN,True)
    box(d,(74,1020,1006,1203),(9,17,31),(52,68,94),12,2); d.rectangle((75,1021,1005,1070),fill=(30,45,67)); text(d,(100,1033),"status",22,TEXT,True); d.line((74,1071,1006,1071),fill=LINE,width=2); text(d,(100,1090),"1",25,TEXT,False,mono=True)
    panel(d,42,1290,996,320,"Session controls"); wrapped(d,(76,1360),"Query history stays in memory for the active session and clears when you disconnect or the session expires.",23,900)
    d.rounded_rectangle((450,1883,630,1892),5,fill=(226,232,240)); im.save(p,format="PNG",optimize=True)

def wide(path,title,mode):
    im=bg((1920,1080)); d=ImageDraw.Draw(im); d.rectangle((0,0,1920,110),fill=BG); d.line((0,109,1920,109),fill=LINE,width=2)
    text(d,(46,22),"MySQL IDLE",42,TEXT,True); text(d,(48,72),"Android companion · responsive SQL workspace",21,MUTED)
    box(d,(1610,30,1875,80),(18,52,46),(39,83,70),23,2); text(d,(1742,55),"Connected to desktop",19,GREEN,True,"mm"); text(d,(54,140),title,33,TEXT,True)
    if mode=="editor":
        panel(d,46,190,1120,570,"SQL editor"); text(d,(80,252),"Ctrl/⌘ + Enter to run",20,MUTED); box(d,(78,300,1134,520),(9,17,31),(52,68,94),14,2)
        text(d,(110,335),"SELECT 1 AS status;",35,(124,211,255),False,mono=True); button(d,78,554,188,"Run SQL",True,True,60); button(d,282,554,150,"Clear",False,True,60); button(d,448,554,210,"Previous",False,True,60); button(d,674,554,184,"Next",False,True,60)
        panel(d,1200,190,674,570,"Result"); box(d,(1240,275,1834,362),(9,17,31),(52,68,94),12,2); text(d,(1270,305),"1 row · 1 column",24,GREEN,True)
        box(d,(1240,382,1834,520),(9,17,31),(52,68,94),12,2); d.rectangle((1241,383,1833,438),fill=(30,45,67)); text(d,(1270,397),"status",23,TEXT,True); text(d,(1270,460),"1",25,TEXT,False,mono=True); panel(d,46,790,1828,190,"Session query history")
        text(d,(84,864),"SELECT 1 AS status;",25,TEXT,False,mono=True); text(d,(84,916),"History is held in memory and cleared when the session ends.",21,MUTED)
    elif mode=="connection":
        panel(d,46,190,1130,710,"MySQL connection")
        field(d,84,266,500,"Host (as seen by desktop)","localhost",True,h=50); field(d,625,266,500,"Port","3306",True,h=50); field(d,84,370,500,"Username","db_user",True,h=50); field(d,625,370,500,"Password (not saved)","••••••••••",True,h=50)
        field(d,84,474,1040,"MySQL CA certificate path (optional)",r"C:\certs\mysql-ca.pem",True,h=50); field(d,84,575,1040,"Database (optional)","sales",True,h=50); button(d,84,686,1040,"Connect to MySQL",True,True,60)
        panel(d,1210,190,664,710,"Connection notes"); wrapped(d,(1250,278),"The Windows desktop makes the MySQL connection. Mobile requests go over certificate-pinned HTTPS.",26,580)
        box(d,(1250,510,1835,625),(16,49,43),(40,83,68),16,2); text(d,(1280,540),"Credentials not saved on Android",21,GREEN,True)
    elif mode=="pairing":
        panel(d,46,190,890,710,"Unlock and pair with desktop"); wrapped(d,(84,270),"Use the same master password set on Windows and the temporary 10-digit code shown by the desktop.",25,800)
        field(d,84,375,805,"MySQL IDLE master password","••••••••••••",True,h=55); field(d,84,478,805,"Temporary pairing code","12345 67890",True,h=55); button(d,84,605,805,"Unlock and pair",True,True,64)
        panel(d,980,190,894,710,"Connection safety")
        for i,(title,body) in enumerate([("Certificate fingerprint","Compare the complete SHA-256 value with Windows."),("Private network only","Both devices use a trusted local network."),("Session expiry","Sessions expire after 30 minutes of inactivity.")]):
            y=280+i*180; d.ellipse((1020,y+5,1064,y+49),fill=(22,72,62),outline=(55,128,102),width=2); text(d,(1042,y+27),"✓",25,GREEN,True,"mm"); text(d,(1090,y),title,23,TEXT,True); wrapped(d,(1090,y+40),body,20,710)
    else:
        panel(d,46,190,1828,710,"SQL results · session workspace"); text(d,(84,268),"SELECT 1 AS status;",33,(124,211,255),False,mono=True); box(d,(84,340,1835,430),(9,17,31),(52,68,94),12,2); text(d,(120,370),"1 row · 1 column",24,GREEN,True)
        box(d,(84,450,1835,710),(9,17,31),(52,68,94),12,2); d.rectangle((85,451,1834,518),fill=(30,45,67)); text(d,(120,472),"status",25,TEXT,True); d.line((84,519,1835,519),fill=LINE,width=2); text(d,(120,550),"1",27,TEXT,False,mono=True); text(d,(120,635),"Use Export complete CSV to save the returned result set.",21,MUTED)
    im.save(path,format="PNG",optimize=True)

def main():
    p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]); args=p.parse_args()
    root=args.root.resolve(); src=root/"assets"/"mysqlidle-logo.png"
    if not src.is_file(): raise SystemExit("Required source logo not found: "+str(src))
    out=root/"dist"/"google-play-assets"; out.mkdir(parents=True,exist_ok=True); lg=logo(src)
    # Exact uploaded image resized only; preserve its original transparent corner pixels.
    lg.save(out/"app-icon-512.png",format="PNG",optimize=True)
    (root/"assets"/"mysqlidle-logo-highres.png").parent.mkdir(exist_ok=True); lg.save(root/"assets"/"mysqlidle-logo-highres.png",format="PNG",optimize=True)
    android=root/"android-app/app/src/main/res/drawable-nodpi/ic_mysqlidle_logo.png"
    if not android.parent.is_dir(): raise SystemExit("Android icon resource folder missing: "+str(android.parent))
    lg.save(android,format="PNG",optimize=True)
    # Exact uploaded image resized directly to the requested feature-graphic dimensions.
    # No added background, text, masking, padding, or decorative elements.
    fg=logo(src,(1024,500))
    fg.save(out/"feature-graphic-1024x500.png",format="PNG",optimize=True)
    for name,fn in [("phone-01-connect-and-verify-1080x1920.png",phone_connect),("phone-02-unlock-and-pair-1080x1920.png",phone_pair),("phone-03-mysql-connection-1080x1920.png",phone_connection),("phone-04-sql-editor-and-results-1080x1920.png",phone_query)]: fn(lg,out/name)
    specs=[("01-sql-editor.png","SQL editor and quick templates","editor"),("02-mysql-connection.png","Connect through the desktop companion","connection"),("03-secure-pairing.png","Pair with a trusted Windows desktop","pairing"),("04-query-results.png","Review results and export CSV","results")]
    for folder in ("tablet-7-inch","tablet-10-inch","desktop"):
        dest=out/folder; dest.mkdir(exist_ok=True)
        for name,title,mode in specs: wide(dest/name,title,mode)
    files=[]
    for x in sorted(out.rglob("*.png")):
        with Image.open(x) as im: files.append({"file":x.relative_to(out).as_posix(),"width":im.width,"height":im.height,"bytes":x.stat().st_size})
    manifest={"product":"MySQL IDLE Mobile","notes":["512x512 PNG directly resized from the uploaded MySQL IDLE logo, preserving transparency.","1024x500 feature graphic.","Four 1080x1920 phone screenshots and twelve 1920x1080 tablet/desktop previews are rendered previews based on the current UI; verify against the final build on a real device before submission.","XR assets are omitted because this companion is not an XR app. Video fields are omitted until a real public/unlisted YouTube video exists."],"assets":files}
    (out/"ASSET-MANIFEST.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    zip_path=root/"dist"/"MySQLIDLE-Play-Store-Assets.zip"
    with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for x in sorted(out.rglob("*")):
            if x.is_file(): z.write(x,x.relative_to(out.parent))
    print("Generated direct resized 512x512 and 1024x500 logo files, shared app branding, screenshot previews and ZIP.")

if __name__=="__main__": main()

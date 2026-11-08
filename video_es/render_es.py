import subprocess, sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
V=sys.argv[1]; OUT=sys.argv[2]
W,H,FPS=1080,1920,30
END=84.9
SUBS=[
(0.0,4.5,"Es tal que, si una persona estudia las letras del *idioma* *inglés*,"),
(4.5,7.0,"ni hablar de aprender a formar *oraciones* con las palabras,"),
(7.0,10.5,"se vuelve *orgullosa* y *presumida*."),
(10.5,16.8,"Es más, algunos enseñan a sus *hijos* el *idioma* *inglés*."),
(16.8,20.2,"Si el niño quiere dar el *salam*, su padre le dice:"),
(20.2,24.1,"«No, no digas *As-Salamu* *Alaikum*, di *bye* *bye*»."),
(24.1,27.0,"¿Qué es *«bye* *bye»*?"),
(27.0,29.8,"Esto es porque «bye bye» es el *idioma* de la gente"),
(29.8,33.0,"que tiene la *superioridad* que posee,"),
(33.0,35.8,"mientras que nosotros somos *débiles*."),
(35.8,38.5,"¿Hemos llegado a *este* *nivel*?..."),
(38.5,41.3,"En vez de *Ma'a* *Salama* o *As-Salamu* *Alaikum*, el niño dice:"),
(41.3,44.0,"...*bye* *bye*, *bye* *bye*..."),
(44.0,48.4,"(Y es a *Allah* a quien se pide ayuda) ¿Por qué pasa esto? Porque su *padre* se lo enseñó,"),
(48.4,52.6,"y el niño vive según lo que su *padre* le *enseña*."),
(52.6,57.2,"En todo caso, oh hermanos, digo: es *obligatorio* buscar *fuerza* y *poder* a través de nuestra *religión*,"),
(57.2,61.3,"porque el *poder* pertenece a *Allah*, a Su *Mensajero* (la paz sea con él)"),
(61.3,69.1,"y a los *creyentes*. Y no debemos seguirlos en asuntos que *no* *traen* *beneficio*."),
(69.1,77.3,"En cuanto a seguirlos en asuntos *industriales* y en lo que *Allah* ha puesto en la *tierra*,"),
(77.3,END,"esto no se critica; al contrario, se *fomenta*, y podemos ser *líderes* en ello junto con establecer nuestra *religión*."),
]
FB="/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
font=ImageFont.truetype(FB,58)
fontS=ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",30)
DARK=(20,20,24); ACC=(196,140,24); ACC2=(15,118,110)
BOX=(250,585)  # y-range to clean
MAXW=960; LH=74

def word_img(txt,hl):
    f=font
    bb=f.getbbox(txt)
    w=bb[2]+8; h=LH
    im=Image.new("RGBA",(w+20,h+20),(0,0,0,0)); d=ImageDraw.Draw(im)
    if txt=="ﷺ":
        f2=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",50)
        try: d.text((10,18),"ﷺ",font=f2,fill=ACC)
        except Exception: pass
    else:
        d.text((10,10),txt,font=f,fill=ACC if hl else DARK)
    return im, w

def layout(text):
    toks=[]
    for t in text.split():
        hl=t.startswith("*") and t.rstrip(".,:;!?»…").endswith("*") or ("*" in t)
        toks.append((t.replace("*",""),hl))
    space=font.getlength(" ")
    imgs=[(word_img(t,h)) for t,h in toks]
    lines=[[]]; cw=0
    for i,(im,w) in enumerate(imgs):
        if lines[-1] and cw+space+w>MAXW: lines.append([]); cw=0
        cw+= (space if lines[-1] else 0)+w; lines[-1].append(i)
    # shrink if too many lines handled by MAXW; compute positions
    n=len(lines); top=BOX[0]+ (BOX[1]-BOX[0]-n*LH)//2
    pos=[None]*len(imgs)
    for li,line in enumerate(lines):
        lw=sum(imgs[i][1] for i in line)+space*(len(line)-1)
        x=(W-lw)/2
        for i in line:
            pos[i]=(x,top+li*LH); x+=imgs[i][1]+space
    return imgs,pos,n

LAY=[(s,e,*layout(t)) for s,e,t in SUBS]
for s,e,imgs,pos,n in LAY:
    assert n<=4,(n,s)

def ease(x): x=max(0,min(1,x)); return 1-(1-x)**3
def back(x):
    x=max(0,min(1,x)); c=1.7; return 1+(c+1)*(x-1)**3+c*(x-1)**2

name=Image.new("RGBA",(W,60),(0,0,0,0)); dn=ImageDraw.Draw(name)
nt="Sheij Muhammad ibn al-Uzaimín"; nw=fontS.getlength(nt)
dn.text(((W-nw)/2,10),nt,font=fontS,fill=ACC2)

dec=subprocess.Popen(["ffmpeg","-v","error","-i",V,"-f","rawvideo","-pix_fmt","rgb24","-"],stdout=subprocess.PIPE)
enc=subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
    "-i",V,"-map","0:v","-map","1:a","-c:v","libx264","-preset","medium","-crf","19","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-shortest","-movflags","+faststart",OUT],stdin=subprocess.PIPE)
fi=0
while True:
    raw=dec.stdout.read(W*H*3)
    if len(raw)<W*H*3: break
    t=fi/FPS; fi+=1
    if t>=END-0.02:
        enc.stdin.write(raw); continue
    fr=Image.frombytes("RGB",(W,H),raw).convert("RGBA")
    d=ImageDraw.Draw(fr)
    d.rectangle([0,BOX[0],W,BOX[1]],fill=(255,255,255,255))
    # name label under arabic header
    a=ease(t/0.8)
    nm=name.copy(); nm.putalpha(Image.eval(nm.getchannel("A"),lambda v:int(v*a)))
    fr.alpha_composite(nm,(0,int(150+(1-a)*20)))
    # progress bar
    p=min(1,t/END)
    d.rounded_rectangle([60,212,60+int((W-120)*p),218],radius=3,fill=ACC+(255,))
    for s,e,imgs,pos,n in LAY:
        if not (s<=t<e): continue
        dur=e-s; k=len(imgs)
        span=min(dur*0.55, 0.11*k+0.2)
        out=ease((e-t)/0.18) if e-t<0.18 else 1
        for i,(im,w) in enumerate(imgs):
            st=s+span*i/max(1,k)
            x=(t-st)/0.28
            if x<=0: continue
            a=ease(x)*out; sc=0.6+0.4*back(x)
            wi=im
            if abs(sc-1)>0.005:
                wi=im.resize((max(1,int(im.width*sc)),max(1,int(im.height*sc))),Image.BICUBIC)
            if a<1:
                wi=wi.copy(); wi.putalpha(Image.eval(wi.getchannel("A"),lambda v,a=a:int(v*a)))
            px,py=pos[i]; cx=px-10+im.width/2; cy=py-10+im.height/2+(1-ease(x))*18
            fr.alpha_composite(wi,(int(cx-wi.width/2),int(cy-wi.height/2)))
        # underline accent that grows
        ul=ease((t-s)/0.5)*out
        lastY=pos[-1][1]+LH+6
        d.rounded_rectangle([W/2-60*ul,lastY,W/2+60*ul,lastY+6],radius=3,fill=ACC2+(int(255*out),))
    enc.stdin.write(fr.convert("RGB").tobytes())
enc.stdin.close(); enc.wait(); print("frames",fi)

/* ===== LOI: cat kich ban + can theo SRT, ep dung so anh ===== */
const KEEP='0123456789aàáảãạăằắẳẵặâầấẩẫậbcdđeèéẻẽẹêềếểễệfghiìíỉĩịjklmnoòóỏõọôồốổỗộơờớởỡợpqrstuùúủũụưừứửữựvwxyỳýỷỹỵz';
function nz(w){let r='';w=w.toLowerCase();for(const c of w) if(KEEP.includes(c)) r+=c; return r;}

function docSRT(txt){
  const W=[];
  txt.replace(/\r/g,'').split(/\n\s*\n/).forEach(kh=>{
    const d=kh.split('\n'), i=d.findIndex(x=>x.includes('-->'));
    if(i<0) return;
    const p=d[i].split('-->').map(x=>{
      const m=x.trim().match(/(\d+):(\d+):(\d+)[,.](\d+)/); if(!m) return null;
      return +m[1]*3600+ +m[2]*60+ +m[3]+ (+m[4])/1000;
    });
    if(p[0]==null||p[1]==null) return;
    const ws=d.slice(i+1).join(' ').trim().split(/\s+/).filter(Boolean);
    ws.forEach((w,k)=>W.push({w:nz(w), t:p[0]+(p[1]-p[0])*k/ws.length}));
  });
  return W.filter(x=>x.w);
}

function cauCoBan(t){
  const s=(t.replace(/\s+/g,' ').match(/[^.?!]+[.?!]?/g)||[]).map(x=>x.trim()).filter(Boolean);
  const m=[];
  s.forEach(x=>{
    if(m.length && x.split(' ').length<6 && m[m.length-1].split(' ').length<14) m[m.length-1]+=' '+x;
    else m.push(x);
  });
  return m;
}
function tachDoi(s){
  const w=s.split(' '); let b=null;
  w.forEach((x,i)=>{ if(/[,:;]$/.test(x)&&i>2&&i<w.length-2){
    if(b===null||Math.abs(i-w.length/2)<Math.abs(b-w.length/2)) b=i; }});
  if(b===null) b=Math.floor(w.length/2)-1;
  if(b<0) b=0;
  return [w.slice(0,b+1).join(' '), w.slice(b+1).join(' ')];
}
function epSoCanh(sents,N){
  let s=sents.slice();
  let guard=0;
  while(s.length<N && guard++<20000){
    let i=0; for(let k=1;k<s.length;k++) if(s[k].split(' ').length>s[i].split(' ').length) i=k;
    if(s[i].split(' ').length<4) break;
    const p=tachDoi(s[i]); s.splice(i,1,p[0],p[1]);
  }
  guard=0;
  while(s.length>N && guard++<20000){
    let i=0,best=1e9;
    for(let k=0;k<s.length-1;k++){
      const v=s[k].split(' ').length+s[k+1].split(' ').length;
      if(v<best){best=v;i=k;}
    }
    s.splice(i,2,s[i]+' '+s[i+1]);
  }
  return s;
}
/* Hunt-Szymanski: tim chuoi tu chung dai nhat giua kich ban va SRT */
function neo(kw,SW){
  const pos=new Map();
  SW.forEach((w,j)=>{ if(!pos.has(w)) pos.set(w,[]); pos.get(w).push(j); });
  const cand=[];
  kw.forEach((w,i)=>{
    const ls=pos.get(w); if(!ls||ls.length>12) return;
    for(let k=ls.length-1;k>=0;k--) cand.push([i,ls[k]]);
  });
  const tail=[],idx=[],par=[];
  cand.forEach(([i,j],c)=>{
    let lo=0,hi=tail.length;
    while(lo<hi){ const mid=(lo+hi)>>1; if(tail[mid]<j) lo=mid+1; else hi=mid; }
    tail[lo]=j; idx[lo]=c; par[c]= lo>0? idx[lo-1] : -1;
  });
  const mp=new Map();
  let c= tail.length? idx[tail.length-1] : -1;
  while(c>=0){ mp.set(cand[c][0],cand[c][1]); c=par[c]; }
  return mp;
}
function canhTho(kichBan, srtText, N){
  /* cat cau + can vao SRT + noi suy, KHONG ep do dai toi thieu. Tra ve
     {sc, st, W} de tinhCanh va tinhCanhTheoBanDo dung chung. */
  const W=docSRT(srtText);
  if(!W.length) throw new Error('SRT rỗng hoặc sai định dạng');
  const SW=W.map(x=>x.w);
  let sc=cauCoBan(kichBan);
  if(N>0) sc=epSoCanh(sc,N);
  const kw=[],owner=[];
  sc.forEach((c,i)=>c.split(' ').forEach(w=>{const n=nz(w); if(n){kw.push(n);owner.push(i);}}));
  const mp=neo(kw,SW);
  const first=new Map();
  owner.forEach((o,i)=>{ if(mp.has(i)&&!first.has(o)) first.set(o,W[mp.get(i)].t); });
  const soTu=sc.map(c=>c.split(' ').length);
  const cong=[0]; soTu.forEach(v=>cong.push(cong[cong.length-1]+v));
  const ENDW=W[W.length-1].t+0.6;
  const st=[];
  for(let i=0;i<sc.length;i++){
    if(first.has(i)){ st.push(first.get(i)); continue; }
    let a=i-1; while(a>=0 && !first.has(a)) a--;
    let b=i+1; while(b<sc.length && !first.has(b)) b++;
    const ta=a>=0?first.get(a):0, tb=b<sc.length?first.get(b):ENDW;
    const wa=a>=0?cong[a]:0, wb=b<sc.length?cong[b]:cong[sc.length];
    const r=(wb-wa)>0 ? (cong[i]-wa)/(wb-wa) : 0.5;
    st.push(ta+(tb-ta)*r);
  }
  let prev=0;
  for(let i=0;i<st.length;i++){ if(st[i]<prev) st[i]=prev; prev=st[i]; }
  return {sc, st, W, thieu: sc.length-first.size};
}
function epToiThieu(fr, MINF){
  for(let i=0;i<fr.length;i++){
    if(fr[i]>=MINF) continue;
    let need=MINF-fr[i];
    [i+1,i-1].forEach(k=>{
      if(need<=0||k<0||k>=fr.length) return;
      const spare=fr[k]-Math.round(MINF*1.3), take=Math.min(need,Math.max(spare,0));
      if(take>0){ fr[k]-=take; fr[i]+=take; need-=take; }
    });
    if(need>0) fr[i]+=need;
  }
  return fr;
}
function tinhCanh(kichBan, srtText, N, fps, minGiay){
  const {sc, st, W, thieu} = canhTho(kichBan, srtText, N);
  const MINF=Math.max(1,Math.round(minGiay*fps));
  const END=W[W.length-1].t+0.6;
  const fr=st.map(v=>Math.round(v*fps));
  for(let i=1;i<fr.length;i++) if(fr[i]<=fr[i-1]) fr[i]=fr[i-1]+1;
  const ef=Math.max(Math.round(END*fps), fr[fr.length-1]+MINF);
  let ds=fr.map((v,i)=>(i+1<fr.length?fr[i+1]:ef)-v);
  ds=epToiThieu(ds, MINF);
  return {canh:sc.map((t,i)=>({t,f:ds[i]})), thieu};
}

/* ===== CHE DO BAN DO: storyboard co san, moi cau ung voi vaiAnh[i] tam anh =====
   Dung khi storyboard da duoc ve truoc va khong theo cung quy tac cat cau.
   vaiAnh la mang cung do dai voi so cau goc (N=0 cua tinhCanh), vaiAnh[i] = so
   anh minh hoa cho cau i. Tong vaiAnh phai bang tong so anh that su co. */
function tinhCanhTheoBanDo(kichBan, srtText, vaiAnh, fps, minGiay){
  const {sc, st, W} = canhTho(kichBan, srtText, 0);
  if(sc.length !== vaiAnh.length)
    throw new Error('Ban do co '+vaiAnh.length+' dong nhung kich ban cat ra '+sc.length+' cau. Chay --lietke de xem lai danh sach cau roi sua ban do.');
  const END=W[W.length-1].t+0.6;
  const fr=st.map(v=>Math.round(v*fps));
  for(let i=1;i<fr.length;i++) if(fr[i]<=fr[i-1]) fr[i]=fr[i-1]+1;
  const ef=Math.max(Math.round(END*fps), fr[fr.length-1]+1);
  const durCau=fr.map((v,i)=>(i+1<fr.length?fr[i+1]:ef)-v);
  const MINF = Math.max(1, Math.round(minGiay*fps));
  const out=[];
  sc.forEach((t,i)=>{
    const k = Math.max(1, vaiAnh[i]|0), c=durCau[i];
    const base = Math.floor(c/k), du = c - base*k;
    for(let j=0;j<k;j++) out.push({f: base+(j<du?1:0), t, cau:i+1, phan:j+1, tong:k});
  });
  // don anh qua ngan bang cach muon tu anh ke ben, uu tien trong cung mot cau,
  // roi moi muon xuyen cau neu can (giu nguyen thu tu, khong dao canh)
  for(let i=0;i<out.length;i++){
    if(out[i].f>=MINF) continue;
    let need=MINF-out[i].f;
    [i+1,i-1].forEach(k=>{
      if(need<=0||k<0||k>=out.length) return;
      const spare=out[k].f-Math.round(MINF*1.2), take=Math.min(need,Math.max(spare,0));
      if(take>0){ out[k].f-=take; out[i].f+=take; need-=take; }
    });
    if(need>0) out[i].f+=need;
  }
  return out; // [{f, t, cau, phan, tong}, ...] dung 1 phan tu = 1 anh, theo dung thu tu
}

if(typeof module!=='undefined') module.exports = { docSRT, cauCoBan, epSoCanh, tinhCanh, tinhCanhTheoBanDo, nz };

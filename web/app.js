(function(){
  "use strict";
  var D = JSON.parse(document.getElementById("site-data").textContent);
  var $ = function(s){return document.querySelector(s);};
  function esc(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];});}
  function eur(v,d){return v==null?"—":"€"+Number(v).toFixed(d==null?2:d);}
  function variant(v){return esc(String(v||"").replace(/(\d)\s*x\s*(\d)/gi,"$1×$2"));}
  function p100(v){return v==null?"—":'<b class="p100 num">'+eur(v)+'<span class="u100">/100g</span></b>';}
  function shortDate(iso){var p=iso.split("-");return (+p[1])+"/"+(+p[2]);}
  var ARROW='<svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M13.2 5.3a1 1 0 0 1 1.4 0l6 6a1 1 0 0 1 0 1.4l-6 6a1 1 0 1 1-1.4-1.4l4.3-4.3H4a1 1 0 1 1 0-2h13.5l-4.3-4.3a1 1 0 0 1 0-1.4z"/></svg>';
  var CHEV='<svg class="chev" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M6.3 9.3a1 1 0 0 1 1.4 0L12 13.6l4.3-4.3a1 1 0 1 1 1.4 1.4l-5 5a1 1 0 0 1-1.4 0l-5-5a1 1 0 0 1 0-1.4z"/></svg>';
  var PLACEHOLDER="data:image/svg+xml,"+encodeURIComponent("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' fill='#f6efe8'/><text x='50' y='62' font-size='40' text-anchor='middle'>🐱</text></svg>");

  $("#updated").innerHTML = "<b>"+esc(D.updated_zh.replace(/^\d+年/,""))+" 更新</b>下次約 "+esc(D.next_zh)+"（荷蘭時間）";

  var html = [];

  // 目標
  D.products.forEach(function(p){
    var t=p.target; if(!t) return;
    var u=p.unit_word, h=t.per100g!=null;
    var tv=h?t.per100g:t.unit, bv=h?p.best.per100g:p.best.unit, gv=h?t.gap_per100g:t.gap_unit, un=h?'100g':u;
    var fill=Math.min(100, tv/bv*100);
    html.push('<section class="target" aria-label="目標價">'+
      '<div class="row"><h2>🎯 '+esc(p.brand)+' 目標：<strong class="num">'+eur(tv)+'</strong>/'+esc(un)+'<span class="sec">（'+t.units+' '+esc(u)+' '+eur(t.price_eur,0)+'）</span></h2>'+
      (t.reached?'<span class="status yes">已達成</span>':'<span class="status no">尚未達成</span>')+'</div>'+
      '<p class="big">'+(t.reached
        ? '目前最低 <strong class="num">'+eur(bv)+'</strong>/'+esc(un)+'，已低於目標！'
        : '目前最低 <strong class="num">'+eur(bv)+'</strong>/'+esc(un)+'，還差 <strong class="num">'+eur(gv)+'</strong>/'+esc(un)+'（'+t.gap_pct.toFixed(0)+'%）')+
      (h?'<span class="sec">'+eur(p.best.unit)+'/'+esc(u)+'・'+t.units+' '+esc(u)+'約 '+eur(t.equiv_pack)+'</span>':'')+'</p>'+
      (t.reached?'':'<div class="bar" role="img" aria-label="目標價占目前價格的比例"><i style="width:'+fill.toFixed(1)+'%"></i></div>'+
      '<div class="bar-legend"><span>目標 '+eur(tv)+'/'+esc(un)+'</span><span>差 '+eur(gv)+'/'+esc(un)+'</span></div>')+
    '</section>');
  });

  html.push('<h2 class="section-title">各商品目前最低價</h2><div class="grid">');
  D.products.forEach(function(p,i){ html.push(card(p,i)); });
  html.push('</div>');

  if(D.promos.length){
    html.push('<h2 class="section-title">全站優惠</h2><div class="promos">');
    D.promos.forEach(function(x){ html.push('<div class="promo"><b>'+esc(x.shop)+'</b><span>'+esc(x.text)+'</span></div>'); });
    html.push('</div>');
  }

  html.push(details());
  $("#app").innerHTML = html.join("");
  $("#foot").innerHTML = '<p>價格取「優惠價（定期配送、折扣）」與「返現後價格」中較低者，兩者不疊加。返現以既有客戶費率計算。</p><p>所有商店皆可寄送至鹿特丹；實際價格以商店頁面為準。網站產生時間 '+esc(D.generated_zh)+'（阿姆斯特丹時間）。</p>';

  document.querySelectorAll(".toggle").forEach(function(b){
    b.addEventListener("click",function(){
      var c=b.closest(".card"); var open=c.classList.toggle("open");
      b.setAttribute("aria-expanded",open?"true":"false");
    });
  });
  document.querySelectorAll(".more").forEach(function(b){
    b.addEventListener("click",function(){
      var list=b.previousElementSibling; var showing=list.classList.toggle("all");
      list.querySelectorAll(".offer.dim").forEach(function(li){li.hidden=!showing;});
      b.textContent = showing ? "只顯示有庫存、已核實的商店" : b.getAttribute("data-label");
    });
  });

  function card(p,i){
    var b=p.best, u=p.unit_word;
    var img = p.image ? esc(p.image) : PLACEHOLDER;
    var s = '<article class="card" id="'+esc(p.id)+'">';
    s += '<div class="card-main">';
    s += '<div class="thumb"><img src="'+img+'" alt="'+esc(p.brand+" "+p.name)+' 商品圖" width="112" height="112" '+(i>1?'loading="lazy" ':'')+'decoding="async"></div>';
    s += '<div class="ptitle"><div class="brandname">'+esc(p.brand)+'</div><h3>'+esc(p.name)+'</h3><div class="desc">'+esc(p.desc)+(p.pack?'・'+esc(p.pack):'')+'</div>';
    if(p.badge) s += '<div class="badges"><span class="badge '+esc(p.badge.kind)+'">'+esc(p.badge.text)+'</span></div>';
    s += '</div>';
    if(!b){
      s += '<div class="where">目前沒有已核實、有庫存的報價。</div></div>';
    } else {
      s += '<div class="deal"><div class="price">'+(b.per100g!=null
        ? '<div class="lbl">每 100g 最低價</div><div class="val num">'+eur(b.per100g)+'<small>/100g</small></div><div class="per num">'+eur(b.unit)+'/'+esc(u)+'（'+esc(b.unit_g)+'g）</div>'
        : '<div class="lbl">最低每'+esc(u)+'</div><div class="val num">'+eur(b.unit)+'<small>/'+esc(u)+'</small></div>')+'</div>';
      s += '<a class="buy" href="'+esc(b.url)+'" target="_blank" rel="noopener nofollow">前往 '+esc(b.shop)+' '+ARROW+'</a></div>';
      s += '<div class="where"><b>'+esc(b.shop)+'</b>・'+variant(b.variant)+'・'+esc(b.basis)+' <span class="num">'+eur(b.price)+'</span><span class="cond">'+esc(b.conditions.join("・"))+'</span></div>';
      if(p.one_time_best){
        var o=p.one_time_best;
        s += '<div class="alt">不想訂閱？單次購買最低：<a href="'+esc(o.url)+'" target="_blank" rel="noopener nofollow">'+esc(o.shop)+'</a> '+variant(o.variant)+' '+(o.per100g!=null?p100(o.per100g):'<span class="num">'+eur(o.unit)+'</span>/'+esc(u))+'</div>';
      }
      s += '</div>';
    }
    var others = p.offers.filter(function(o){return !(o.in_stock&&o.verified);}).length;
    s += '<button class="toggle" type="button" aria-expanded="false">比較 '+p.shop_count+' 家商店與價格走勢'+CHEV+'</button>';
    s += '<div class="drill">'+chart(p)+'<h4>商店排名（依每 100g 最低價）</h4><ol class="offers">';
    var groups=[], byShop={};
    p.offers.forEach(function(o){
      var main=o.in_stock&&o.verified;
      if(!main){ groups.push({main:false,items:[o]}); return; }
      if(!byShop[o.shop]){ byShop[o.shop]={main:true,items:[]}; groups.push(byShop[o.shop]); }
      byShop[o.shop].items.push(o);
    });
    groups.sort(function(a,b){return (a.main===b.main)?0:(a.main?-1:1);});
    var rank=0;
    groups.forEach(function(g){
      var o=g.items[0], main=g.main;
      if(main) rank++;
      var tags = o.conditions.map(function(c){return '<span class="tag">'+esc(c)+'</span>';}).join("");
      if(o.new_customer) tags += '<span class="tag nc">新客首單 '+(o.new_customer.per100g!=null?eur(o.new_customer.per100g)+'/100g':eur(o.new_customer.unit)+'/'+esc(u))+'</span>';
      if(o.one_time_unit) tags += '<span class="tag">單次 '+(o.one_time_per100g!=null?eur(o.one_time_per100g)+'/100g':eur(o.one_time_unit)+'/'+esc(u))+'</span>';
      var st = !o.in_stock ? "缺貨" : (o.status==="partly_verified" ? "部分核實" : (o.verified ? "" : "未核實"));
      var rest = g.items.slice(1).map(function(x){return variant(x.variant)+' '+(x.per100g!=null?'<b class="num">'+eur(x.per100g)+'</b>/100g':eur(x.unit)+'/'+esc(u));}).join("、");
      var bigv = o.per100g!=null ? eur(o.per100g)+'<span class="h">/100g</span>' : eur(o.unit)+'<span class="h">/'+esc(u)+'</span>';
      var smallv = o.per100g!=null ? eur(o.unit)+'/'+esc(u)+'（'+esc(o.unit_g)+'g）' : '';
      s += '<li class="offer'+(main?'':' dim')+(main&&rank===1?' top':'')+'"'+(main?'':' hidden')+'>'+
        '<span class="rank">'+(main?rank:'–')+'</span>'+
        '<div class="o-name"><div class="s">'+esc(o.shop)+(st?' <span class="st">'+st+'</span>':'')+'</div>'+
        '<div class="v">'+variant(o.variant)+'・'+esc(o.basis)+' <span class="num">'+eur(o.price)+'</span></div>'+
        '<div class="c">'+tags+'</div>'+
        (rest?'<div class="r">其他規格：'+rest+'</div>':'')+'</div>'+
        '<div class="o-price"><div class="u num">'+bigv+'</div><div class="h num">'+smallv+'</div>'+
        '<a href="'+esc(o.url)+'" target="_blank" rel="noopener nofollow">前往 ›</a></div></li>';
    });
    s += '</ol>';
    if(others>0){ var lbl='顯示其他 '+others+' 筆（缺貨或未完全核實）'; s += '<button class="more" type="button" data-label="'+esc(lbl)+'">'+esc(lbl)+'</button>'; }
    s += '</div></article>';
    return s;
  }

  function chart(p){
    var u=p.unit_word, use100=p.history.every(function(x){return x.per100g!=null;});
    var h=p.history.map(function(x){return {date:x.date, v:use100?x.per100g:x.unit};});
    var un=use100?'100g':u;
    var tgt=p.target?(use100?p.target.per100g:p.target.unit):null;
    var s='<div class="chart"><h4>每 '+esc(un)+' 最低價走勢</h4>';
    if(h.length<2){
      var last=h[h.length-1];
      s+='<div class="empty">目前只有 '+(last?shortDate(last.date)+' 一天':'')+'的資料'+(last?'（<b class="num">'+eur(last.v)+'</b>/'+esc(un)+'）':'')+'，累積更多天數後會顯示價格走勢。</div></div>';
      return s;
    }
    var W=340,H=130,L=40,R=10,T=12,B=22;
    var vals=h.map(function(x){return x.v;});
    if(tgt!=null) vals.push(tgt);
    var mn=Math.min.apply(null,vals), mx=Math.max.apply(null,vals);
    var pad=(mx-mn)*0.15||0.1; mn-=pad; mx+=pad;
    var x=function(i){return L+(W-L-R)*(h.length===1?0.5:i/(h.length-1));};
    var y=function(v){return T+(H-T-B)*(1-(v-mn)/(mx-mn));};
    var pts=h.map(function(d,i){return x(i).toFixed(1)+","+y(d.v).toFixed(1);});
    var g='<svg viewBox="0 0 '+W+' '+H+'" role="img" aria-label="價格走勢圖">';
    [mn+pad, (mn+mx)/2, mx-pad].forEach(function(v){
      g+='<line x1="'+L+'" x2="'+(W-R)+'" y1="'+y(v).toFixed(1)+'" y2="'+y(v).toFixed(1)+'" stroke="#efe7df"/>';
      g+='<text x="'+(L-6)+'" y="'+(y(v)+4).toFixed(1)+'" font-size="10" text-anchor="end" fill="#8a807a">€'+v.toFixed(2)+'</text>';
    });
    if(tgt!=null){ var ty=y(tgt).toFixed(1); g+='<line x1="'+L+'" x2="'+(W-R)+'" y1="'+ty+'" y2="'+ty+'" stroke="#0f7a55" stroke-dasharray="4 4"/><text x="'+(W-R)+'" y="'+(ty-4)+'" font-size="10" text-anchor="end" fill="#0f7a55">目標</text>'; }
    g+='<polyline fill="none" stroke="#e8573a" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round" points="'+pts.join(" ")+'"/>';
    h.forEach(function(d,i){ g+='<circle cx="'+x(i).toFixed(1)+'" cy="'+y(d.v).toFixed(1)+'" r="3.5" fill="#fff" stroke="#e8573a" stroke-width="2"><title>'+d.date+'：€'+d.v.toFixed(2)+'/'+un+'</title></circle>'; });
    var step=Math.max(1,Math.ceil(h.length/6));
    h.forEach(function(d,i){ if(i%step===0||i===h.length-1) g+='<text x="'+x(i).toFixed(1)+'" y="'+(H-6)+'" font-size="10" text-anchor="middle" fill="#8a807a">'+shortDate(d.date)+'</text>'; });
    g+='</svg>';
    return s+g+'</div>';
  }

  function details(){
    var d=D.details, s='<details class="more-info"><summary>詳細資料</summary><div class="body">';
    if(d.assumptions) s+='<h5>計算方式</h5><p>'+esc(d.assumptions)+'</p>';
    if(d.promos_other && d.promos_other.length){
      s+='<h5>未完全核實的優惠</h5><ul>'+d.promos_other.map(function(x){return '<li>'+esc(x.shop)+'：'+esc(x.text)+'</li>';}).join("")+'</ul>';
    }
    var notes=[];
    D.products.forEach(function(p){ p.offers.forEach(function(o){ if(o.detail) notes.push('<li>'+esc(p.brand)+'・'+esc(o.shop)+' '+variant(o.variant)+'：'+esc(o.detail)+'</li>'); }); });
    if(notes.length) s+='<h5>各商店備註</h5><ul>'+notes.join("")+'</ul>';
    if(d.unverified && d.unverified.length) s+='<h5>無法核實的線索（未列入比價）</h5><ul>'+d.unverified.map(function(x){return '<li>'+esc(x)+'</li>';}).join("")+'</ul>';
    return s+'</div></details>';
  }
})();

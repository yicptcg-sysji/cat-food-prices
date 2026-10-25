#!/usr/bin/env python3
"""幼貓濕食比價網站產生器。

讀取價格追蹤資料 (prices.json)，產生 docs/ 靜態網站：
  docs/index.html  （內嵌資料，首屏無需額外請求）
  docs/data.json   （同一份資料，方便除錯或其他用途）
  docs/assets/...  （商品圖片、CSS、JS）

用法： python3 build.py [--source <prices.json 所在資料夾>]
只讀取來源資料，不會修改它。
"""
import argparse, datetime as dt, json, re, shutil, sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs"
TZ = ZoneInfo("Europe/Amsterdam")

BASIS_LABEL = {
    "autoship": "定期配送價",
    "herhaalgemak": "定期配送價",
    "cart discount (abd)": "購物車折扣",
    "cashback": "含返現",
    "list price": "單次購買",
}
AUTOSHIP_BASES = {"autoship", "herhaalgemak"}


def num(v):
    try:
        return None if v is None else float(v)
    except (TypeError, ValueError):
        return None


def strip_paren(s):
    return re.sub(r"[（(][^）)]*[）)]", "", s or "").strip(" ；;，,")


def basis_key(b):
    return (b or "").strip().lower()


def basis_label(b):
    k = basis_key(b)
    if k in BASIS_LABEL:
        return BASIS_LABEL[k]
    if k.startswith("含運費"):
        return "含運費"
    return strip_paren(b) or "單次購買"


def clean_shipping(s):
    s = s or ""
    parts = []
    m = re.search(r"免運門檻\s*€\s*([\d.,]+)", s)
    if m:
        parts.append(f"滿 €{m.group(1)} 免運")
    for m in re.finditer(r"(取貨點|宅配)免運\s*€\s*([\d.,]+)", s):
        parts.append(f"{m.group(1)}滿 €{m.group(2)} 免運")
    m = re.search(r"(?<!免)運費\s*€\s*([\d.,]+)", s)
    if m:
        parts.append(f"運費 €{m.group(1)}")
    m = re.search(r"最低訂單\s*€\s*([\d.,]+)", s)
    if m:
        parts.append(f"最低訂單 €{m.group(1)}")
    if not parts:
        t = strip_paren(s)
        if t in ("", "未核實"):
            return "運費未知"
        return t
    return "・".join(parts)


def short_portal(p):
    return strip_paren(p) if p else None


def eff_unit_price(o):
    """回傳 (每份價, 每100g價, 總價, 計價基礎)：優惠價與返現後取較低者，不疊加。"""
    bu, b100, bp = num(o.get("best_eur_per_unit")), num(o.get("best_eur_per_100g")), num(o.get("best_price_eur"))
    if bu is not None and b100 is not None:
        return bu, b100, bp, o.get("best_basis") or "list price"
    # 舊格式後備：取 effective_* 或標價
    cands = []
    if num(o.get("effective_eur_per_unit")) is not None:
        cands.append((num(o["effective_eur_per_unit"]), num(o.get("effective_eur_per_100g")), num(o.get("effective_price_eur")), o.get("effective_note") or "折扣"))
    if num(o.get("after_cashback_eur_per_unit")) is not None:
        cands.append((num(o["after_cashback_eur_per_unit"]), num(o.get("after_cashback_eur_per_100g")), num(o.get("after_cashback_price_eur")), "cashback"))
    if num(o.get("eur_per_unit")) is not None:
        cands.append((num(o["eur_per_unit"]), num(o.get("eur_per_100g")), num(o.get("price_eur")), "list price"))
    if not cands:
        return None, None, None, None
    u, h, p, b = min(cands, key=lambda c: c[0])
    if h is None and o.get("unit_g"):
        h = u / float(o["unit_g"]) * 100
    return u, h, p, b


def one_time_unit(o):
    """單次購買（不需定期配送）的每份價：標價、購物車折扣或返現後取較低者。"""
    u, _, _, b = eff_unit_price(o)
    if basis_key(b) not in AUTOSHIP_BASES:
        return u
    c = [num(o.get(f)) for f in ("after_cashback_eur_per_unit", "eur_per_unit") if num(o.get(f)) is not None]
    return min(c) if c else None


def is_main(o):
    return o.get("stock") == "in_stock" and o.get("status") == "verified"


def offer_view(o, unit_word):
    u, h, p, b = eff_unit_price(o)
    k = basis_key(b)
    conds = []
    conds.append(clean_shipping(o.get("shipping")))
    if k in AUTOSHIP_BASES:
        conds.append("需訂閱定期配送")
    if k == "cashback" and o.get("cashback_portal"):
        cb = num(o.get("cashback_eur"))
        conds.append(f"經 {short_portal(o['cashback_portal'])} 返現" + (f" €{cb:.2f}" if cb else ""))
    nc = o.get("cashback_new_customer")
    new_cust = None
    if isinstance(nc, dict) and num(nc.get("after_cashback_eur_per_unit")) is not None:
        new_cust = {
            "portal": short_portal(nc.get("portal")),
            "rate_pct": num(nc.get("rate_pct")),
            "unit": num(nc.get("after_cashback_eur_per_unit")),
            "price": num(nc.get("after_cashback_price_eur")),
        }
    ot = one_time_unit(o)
    return {
        "shop": o.get("shop"),
        "variant": o.get("variant"),
        "units": o.get("units"),
        "unit_g": o.get("unit_g"),
        "list_price": num(o.get("price_eur")),
        "price": p,
        "unit": u,
        "per100g": h,
        "basis": basis_label(b),
        "autoship": k in AUTOSHIP_BASES,
        "one_time_unit": ot if (ot is not None and u is not None and ot > u + 1e-9) else None,
        "conditions": [c for c in conds if c],
        "new_customer": new_cust,
        "in_stock": o.get("stock") == "in_stock",
        "verified": o.get("status") == "verified",
        "status": o.get("status"),
        "url": o.get("url"),
        "detail": "；".join(x for x in (o.get("promo"), o.get("note")) if x),
    }


def fmt_date_zh(d):
    return f"{d.year}年{d.month}月{d.day}日"


def build(src: Path):
    cfg = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))
    data = json.loads((src / "prices.json").read_text(encoding="utf-8"))
    obs = [o for o in data.get("observations", []) if o.get("product") and o.get("date")]
    dates = sorted({o["date"] for o in obs})
    latest = data.get("last_updated") or (dates[-1] if dates else None)
    latest_obs_date = dates[-1] if dates else latest

    # 商品清單：設定檔順序優先，新商品自動附加
    pids = [p for p in cfg.get("product_order", []) if p in {o["product"] for o in obs} or p in data.get("products", {})]
    for p in list(data.get("products", {}).keys()) + [o["product"] for o in obs]:
        if p not in pids:
            pids.append(p)

    OUT.mkdir(exist_ok=True)
    (OUT / "assets" / "products").mkdir(parents=True, exist_ok=True)

    products = []
    for pid in pids:
        meta = cfg.get("products", {}).get(pid, {})
        pdata = data.get("products", {}).get(pid, {})
        unit_word = meta.get("unit_word", "份")
        pobs = [o for o in obs if o["product"] == pid]
        if not pobs:
            continue
        pdates = sorted({o["date"] for o in pobs})
        cur_date = pdates[-1]
        cur = [offer_view(o, unit_word) for o in pobs if o["date"] == cur_date]
        cur = [c for c in cur if c["unit"] is not None]
        cur.sort(key=lambda c: (not (c["in_stock"] and c["verified"]), c["per100g"] if c["per100g"] is not None else 9e9))
        main = [c for c in cur if c["in_stock"] and c["verified"]]
        best = main[0] if main else None

        # 價格歷史：每日 in_stock+verified 最低有效單價
        hist = []
        for d in pdates:
            day = [o for o in pobs if o["date"] == d and is_main(o)]
            vals = [eff_unit_price(o) for o in day]
            vals = [v for v in vals if v[0] is not None]
            if not vals:
                continue
            bu = min(vals, key=lambda v: v[1] if v[1] is not None else 9e9)
            ot = [one_time_unit(o) for o in day]
            ot = [x for x in ot if x is not None]
            hist.append({"date": d, "unit": round(bu[0], 3), "per100g": round(bu[1], 3) if bu[1] else None,
                         "one_time_unit": round(min(ot), 3) if ot else None})

        # 新低價徽章
        badge = None
        if best:
            prev = [h["per100g"] for h in hist if h["date"] < cur_date and h["per100g"]]
            ever = num((pdata.get("lowest_unit_price_ever") or {}).get("eur_per_100g"))
            prev_min = min(prev) if prev else None
            if prev_min is None:
                badge = {"kind": "first", "text": "首次紀錄"}
            elif best["per100g"] < prev_min - 1e-6:
                badge = {"kind": "new_low", "text": "新低價", "prev": prev_min}
            elif abs(best["per100g"] - prev_min) <= 1e-6:
                badge = {"kind": "at_low", "text": "持平歷史低價"}
            else:
                pct = (best["per100g"] / prev_min - 1) * 100
                badge = {"kind": "above", "text": f"比歷史低價高 {pct:.0f}%", "prev": prev_min}
            if ever and badge["kind"] in ("above",) and best["per100g"] <= ever + 1e-6:
                badge = {"kind": "at_low", "text": "持平歷史低價"}

        # 單次購買最低（不需訂閱）
        ot_best = None
        for c in main:
            v = c["unit"] if not c["autoship"] else c["one_time_unit"]
            if v is not None and (ot_best is None or v / (c["unit_g"] or 1) < ot_best["unit"] / (ot_best["unit_g"] or 1)):
                ot_best = {"shop": c["shop"], "variant": c["variant"], "unit": v, "unit_g": c["unit_g"], "url": c["url"]}

        target = None
        if meta.get("target") and best:
            t = meta["target"]
            tu = t["price_eur"] / t["units"]
            gap = best["unit"] - tu
            target = {"units": t["units"], "price_eur": t["price_eur"], "unit": round(tu, 3),
                      "reached": gap <= 1e-9, "gap_unit": round(gap, 3),
                      "gap_pct": round(gap / tu * 100, 1),
                      "equiv_pack": round(best["unit"] * t["units"], 2)}

        img = meta.get("image")
        img_out = None
        if img and (ROOT / img).exists():
            shutil.copy2(ROOT / img, OUT / img)
            img_out = img
        else:
            print(f"警告：{pid} 沒有商品圖片，使用預設圖", file=sys.stderr)

        name = meta.get("name") or pdata.get("product_name") or pid
        products.append({
            "id": pid,
            "brand": meta.get("brand", ""),
            "name": name,
            "desc": meta.get("desc", ""),
            "pack": meta.get("pack", ""),
            "unit_word": unit_word,
            "image": img_out,
            "date": cur_date,
            "best": best,
            "one_time_best": ot_best if (ot_best and best and ot_best["unit"] > best["unit"] + 1e-9) else None,
            "badge": badge,
            "target": target,
            "history": hist,
            "offers": cur,
            "main_count": len(main),
            "shop_count": len({c["shop"] for c in main}),
            "mixed_sizes": len({c["unit_g"] for c in cur}) > 1,
        })

    promos_all = [p for p in data.get("sitewide_promos", []) if p.get("date") == max((x.get("date", "") for x in data.get("sitewide_promos", [])), default="")]
    promos = [{"shop": p["shop"], "text": strip_paren(p.get("promo"))} for p in promos_all if p.get("status") == "verified"]
    promos_other = [{"shop": p["shop"], "text": p.get("promo"), "status": p.get("status")} for p in promos_all if p.get("status") != "verified"]

    now = dt.datetime.now(TZ)
    upd = dt.date.fromisoformat(latest) if latest else now.date()
    nxt = upd + dt.timedelta(days=cfg.get("update_interval_days", 2))
    site = {
        "title": cfg.get("site_title", "幼貓濕食比價"),
        "updated": latest,
        "updated_zh": fmt_date_zh(upd),
        "next_zh": f"{nxt.month}月{nxt.day}日",
        "generated_zh": now.strftime("%Y-%m-%d %H:%M"),
        "location": "鹿特丹",
        "products": products,
        "promos": promos,
        "details": {
            "promos_other": promos_other,
            "unverified": data.get("unverified", []),
            "assumptions": (data.get("cashback") or {}).get("assumptions"),
        },
    }
    js = json.dumps(site, ensure_ascii=False, separators=(",", ":"))
    (OUT / "data.json").write_text(json.dumps(site, ensure_ascii=False, indent=1), encoding="utf-8")
    for f in ("style.css", "app.js"):
        shutil.copy2(ROOT / "web" / f, OUT / "assets" / f)
    ver = now.strftime("%Y%m%d%H%M")
    html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    html = html.replace("__DATA__", js.replace("</", "<\\/")).replace("__VER__", ver)
    html = html.replace("__TITLE__", site["title"]).replace("__UPDATED__", site["updated_zh"])
    (OUT / "index.html").write_text(html, encoding="utf-8")
    (OUT / ".nojekyll").write_text("")
    print(f"完成：{len(products)} 項商品，資料日期 {latest}，輸出 {OUT}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", help="prices.json 所在資料夾")
    a = ap.parse_args()
    cfg = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))
    build(Path(a.source or cfg["source_dir"]))

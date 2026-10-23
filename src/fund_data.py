"""Fund data sources (basic facts, risk rating, asset allocation, NAV history).

Sources are pluggable so that the analysis does not depend on one provider:

  fuyao      course-provided API (https://fuyao.aicubes.cn/, Tonghuashun data).
             Primary source; needs FUYAO_API_KEY and the host fuyao.aicubes.cn.
  eastmoney  public Eastmoney / Tiantian Fund endpoints (fallback).
  csv        hand-imported files: data/nav/<code>.csv with columns
             date,return_index (a dividend-adjusted total-return index).

Every raw response is saved under data/fund_sources/raw/ with a UTC timestamp
so that each number used in the analysis can be traced to its source.

Self-test (prints parsed fields; run after network access is enabled):
  python src/fund_data.py --source eastmoney --probe 110020
"""

import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "fund_sources" / "raw"
RISK_TEXT = {"低风险": "R1", "中低风险": "R2", "中风险": "R3", "中高风险": "R4", "高风险": "R5"}
UA = {"User-Agent": "Mozilla/5.0 (academic research; synthetic-investor audit)"}


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def save_raw(source: str, code: str, kind: str, text: str) -> str:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{source}_{code}_{kind}_{stamp()}.txt"
    path.write_text(text, encoding="utf-8")
    return str(path.relative_to(ROOT))


class FuyaoSource:
    """Course-provided data service (Tonghuashun financial data, fuyao.aicubes.cn).

    Confirmed from the documentation (https://fuyao.aicubes.cn/docs/api-reference/overview/
    and its fund pages, read on 2026-10-23):
      * Base URL https://fuyao.aicubes.cn; every /api/ request carries the header X-api-key.
      * Response envelope {code, message, request_id, data}; code 0 = success, 2001 = key
        missing or invalid, 2003 = no permission, 1001-1003 = parameter errors, HTTP 429 or
        code 4001 = throttled (back off, do not retry immediately).
      * Funds are identified by thscode with its market suffix, e.g. 110020.OF for OTC funds.
      * GET /api/fund/profile/detail?thscode=   -> data.item[]: fund_name, estab_date, mgmt_name, ...
      * GET /api/fund/performance/nav?thscode=&range=&nav_type=unit,adj -> series ascending by
        nav_date with unit_nav and adj_nav (adjusted NAV; not the cumulative NAV);
        range is one of week, month, tmonth, hyear, year, twoyear, tyear, fyear.
      * GET /api/fund/portfolio/holdings?thscode= -> includes total_stock_ratio_pct.
      * GET /api/fund/diagnostics/detail?thscode= -> diagnostic dimensions.
    Confirmed only at the first live call (`python src/fund_data.py --source fuyao --probe 110020`
    prints the raw responses): which field carries the product risk rating, the span of
    range=fyear, the nav_date format, and adj_nav behaviour for money market funds.
    """
    name = "fuyao"
    base_url = "https://fuyao.aicubes.cn"
    RISK_WORDS = {"低风险": "R1", "中低风险": "R2", "中风险": "R3", "中高风险": "R4", "高风险": "R5"}

    def __init__(self):
        self.key = os.environ.get("FUYAO_API_KEY", "").strip()

    @staticmethod
    def thscode(code: str) -> str:
        return code if "." in code else f"{code}.OF"

    def _get(self, path: str, code: str, kind: str, **params) -> tuple[dict, str]:
        headers = {**UA}
        if self.key:
            headers["X-api-key"] = self.key
        url = self.base_url + path
        for attempt in range(4):
            resp = requests.get(url, headers=headers, params={"thscode": self.thscode(code), **params}, timeout=30)
            raw = save_raw(self.name, code, kind, resp.text)
            body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            throttled = resp.status_code == 429 or body.get("code") == 4001
            if throttled and attempt < 3:
                time.sleep(2 ** (attempt + 1))
                continue
            if resp.status_code != 200 or body.get("code") != 0:
                raise RuntimeError(f"fuyao {path} HTTP {resp.status_code} code={body.get('code')} "
                                   f"message={body.get('message')} (raw: {raw})")
            return body.get("data") or {}, raw
        raise RuntimeError(f"fuyao {path}: throttled after retries")

    @staticmethod
    def _items(data) -> list:
        if isinstance(data, dict):
            items = data.get("item", data.get("items", data))
            return items if isinstance(items, list) else [items]
        return data if isinstance(data, list) else []

    def _find_risk(self, obj):
        """Search a response for a field whose name mentions risk and whose value is a rating."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if "risk" in k.lower() and isinstance(v, (str, int)):
                    val = str(v).strip()
                    m = re.fullmatch(r"R?([1-5])", val.upper())
                    if m:
                        return f"R{m.group(1)}", k, val
                    for word, r in sorted(self.RISK_WORDS.items(), key=lambda x: -len(x[0])):
                        if word in val:
                            return r, k, val
                found = self._find_risk(v)
                if found:
                    return found
        elif isinstance(obj, list):
            for v in obj:
                found = self._find_risk(v)
                if found:
                    return found
        return None

    def basic_info(self, code: str) -> dict:
        info = {"code": code, "source": self.name, "retrieved_utc": stamp(), "thscode": self.thscode(code)}
        try:
            data, raw = self._get("/api/fund/profile/detail", code, "profile")
            info["raw_profile"] = raw
            item = (self._items(data) or [{}])[0]
            info.update({"name": item.get("fund_name"), "inception": item.get("estab_date"),
                         "manager": item.get("mgmt_name"),
                         "type": item.get("fund_type") or item.get("type_name") or item.get("invest_type")})
            found = self._find_risk(item)
            if found:
                info["risk_rating"], info["risk_field"], info["risk_value_raw"] = found
        except Exception as exc:
            info["profile_error"] = str(exc)
        if not info.get("risk_rating"):
            try:
                data, raw = self._get("/api/fund/diagnostics/detail", code, "diagnostics")
                info["raw_diagnostics"] = raw
                found = self._find_risk(data)
                if found:
                    info["risk_rating"], info["risk_field"], info["risk_value_raw"] = found
            except Exception as exc:
                info["diagnostics_error"] = str(exc)
        try:
            data, raw = self._get("/api/fund/portfolio/holdings", code, "holdings")
            info["raw_holdings"] = raw
            item = (self._items(data) or [{}])[0]
            for k in ("total_stock_ratio_pct", "stock_ratio_pct"):
                if k in item:
                    info["reported_equity_pct"] = item[k]
                    break
            for k in ("report_date", "end_date", "rpt_date"):
                if k in item:
                    info["allocation_report_date"] = item[k]
                    break
        except Exception as exc:
            info["holdings_error"] = str(exc)
        return info

    def nav_history(self, code: str, start: str, end: str) -> pd.DataFrame:
        data, raw = self._get("/api/fund/performance/nav", code, "nav", range="fyear", nav_type="unit,adj")
        df = pd.DataFrame(self._items(data))
        if df.empty or "nav_date" not in df:
            raise RuntimeError(f"fuyao nav: no series returned for {code} (raw: {raw})")
        d = df["nav_date"]
        df["date"] = (pd.to_datetime(d, unit="ms") if pd.api.types.is_numeric_dtype(d)
                      else pd.to_datetime(d)).dt.tz_localize(None).dt.normalize()
        level = pd.to_numeric(df.get("adj_nav"), errors="coerce")
        if level is None or level.isna().all():
            level = pd.to_numeric(df["unit_nav"], errors="coerce")
        df["return_index"] = level / level.dropna().iloc[0]
        df = df.dropna(subset=["return_index"]).sort_values("date")
        df = df[(df["date"] >= start) & (df["date"] <= end)][["date", "return_index"]]
        df.attrs.update({"source": self.name, "raw_file": raw})
        return df


class EastmoneySource:
    name = "eastmoney"

    def _get(self, url: str, **kw) -> requests.Response:
        resp = requests.get(url, headers={**UA, **kw.pop("headers", {})}, timeout=30, **kw)
        resp.raise_for_status()
        return resp

    def basic_info(self, code: str) -> dict:
        info = {"code": code, "source": self.name, "retrieved_utc": stamp()}
        url = ("https://fundmobapi.eastmoney.com/FundMNewApi/FundMNNBasicInformation"
               f"?FCODE={code}&deviceid=Wap&plat=Wap&product=EFund&version=6.0.0")
        try:
            r = self._get(url)
            info["raw_basic"] = save_raw(self.name, code, "basic", r.text)
            d = (r.json() or {}).get("Datas") or {}
            info.update({"name": d.get("SHORTNAME"), "type": d.get("FTYPE"),
                         "manager": d.get("JJGS"), "inception": d.get("ESTABDATE"),
                         "risk_level_raw": d.get("RISKLEVEL"), "basic_url": url})
            lvl = str(d.get("RISKLEVEL", "")).strip()
            if lvl in {"1", "2", "3", "4", "5"}:
                info["risk_rating"] = f"R{lvl}"
        except Exception as exc:  # recorded, not hidden
            info["basic_error"] = f"{type(exc).__name__}: {exc}"
        if not info.get("risk_rating"):
            page = f"https://fund.eastmoney.com/{code}.html"
            try:
                r = self._get(page)
                r.encoding = "utf-8"
                info["raw_page"] = save_raw(self.name, code, "page", r.text)
                m = re.search(r"(中低风险|中高风险|低风险|中风险|高风险)", r.text)
                if m:
                    info["risk_rating"] = RISK_TEXT[m.group(1)]
                    info["risk_rating_text"] = m.group(1)
                    info["risk_url"] = page
            except Exception as exc:
                info["page_error"] = f"{type(exc).__name__}: {exc}"
        try:
            pz = self._get(f"https://fund.eastmoney.com/pingzhongdata/{code}.js")
            info["raw_pingzhong"] = save_raw(self.name, code, "pingzhongdata", pz.text)
            m = re.search(r"var Data_assetAllocation\s*=\s*(\{.*?\});", pz.text, re.S)
            if m:
                alloc = json.loads(m.group(1))
                cats = alloc.get("categories") or []
                for s in alloc.get("series", []):
                    if s.get("name") == "股票占净比" and cats:
                        info["reported_equity_pct"] = s["data"][-1]
                        info["allocation_report_date"] = cats[-1]
        except Exception as exc:
            info["allocation_error"] = f"{type(exc).__name__}: {exc}"
        return info

    def nav_history(self, code: str, start: str, end: str) -> pd.DataFrame:
        """Daily total-return index from Eastmoney's daily growth rates
        (equityReturn, which accounts for distributions). Money market funds
        are handled through income per 10,000 units."""
        r = self._get(f"https://fund.eastmoney.com/pingzhongdata/{code}.js")
        raw = save_raw(self.name, code, "nav", r.text)
        m = re.search(r"var Data_netWorthTrend\s*=\s*(\[.*?\]);", r.text, re.S)
        rows = json.loads(m.group(1)) if m else []
        df = pd.DataFrame(rows)
        if not df.empty and df["y"].nunique() > 1:
            df["date"] = pd.to_datetime(df["x"], unit="ms").dt.tz_localize(None).dt.normalize()
            df["ret"] = pd.to_numeric(df["equityReturn"], errors="coerce").fillna(0) / 100
        else:  # money market fund: NAV fixed at 1, use income per 10k units
            m2 = re.search(r"var Data_millionCopiesIncome\s*=\s*(\[.*?\]);", r.text, re.S)
            inc = pd.DataFrame(json.loads(m2.group(1)) if m2 else [], columns=["x", "income"])
            df = inc.assign(date=pd.to_datetime(inc["x"], unit="ms").dt.normalize(),
                            ret=pd.to_numeric(inc["income"], errors="coerce").fillna(0) / 10_000)
        df = df.sort_values("date")
        df["return_index"] = (1 + df["ret"]).cumprod()
        df = df[(df["date"] >= start) & (df["date"] <= end)][["date", "return_index"]]
        df.attrs.update({"source": self.name, "raw_file": raw})
        return df


class CSVSource:
    name = "csv"

    def basic_info(self, code: str) -> dict:
        path = ROOT / "data" / "fund_ratings_manual.csv"
        if path.exists():
            m = pd.read_csv(path, dtype=str).set_index("code")
            if code in m.index:
                return {"code": code, "source": self.name, **m.loc[code].to_dict()}
        return {"code": code, "source": self.name, "basic_error": "not in data/fund_ratings_manual.csv"}

    def nav_history(self, code: str, start: str, end: str) -> pd.DataFrame:
        df = pd.read_csv(ROOT / "data" / "nav" / f"{code}.csv", parse_dates=["date"])
        return df[(df["date"] >= start) & (df["date"] <= end)][["date", "return_index"]]


SOURCES = {"fuyao": FuyaoSource, "eastmoney": EastmoneySource, "csv": CSVSource}


def get_source(name: str):
    return SOURCES[name]()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="fuyao", choices=list(SOURCES))
    ap.add_argument("--probe", default="110020")
    a = ap.parse_args()
    src = get_source(a.source)
    print(json.dumps(src.basic_info(a.probe), ensure_ascii=False, indent=2))
    nav = src.nav_history(a.probe, "2021-10-01", "2026-09-30")
    print(nav.head(), nav.tail(), len(nav), sep="\n")

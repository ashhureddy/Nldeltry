"""
N2E NL Delete — core logic. Data source is the CIQ's Nokia_Info tab exclusively (no
Pre-checks, no kget-all). Reuses nl_delete_commands.py's build_lte_scenario/build_5g_scenario
unchanged — only the ID source differs from Legacy (Nokia_Info fields instead of kget-all).
"""
import re


def parse_nokia_info(ciq_wb):
    """Returns a list of row dicts from the Nokia_Info tab, keyed by its own column headers."""
    if "Nokia_Info" not in ciq_wb.sheetnames:
        return []
    ws = ciq_wb["Nokia_Info"]
    headers = [c.value for c in ws[1]]
    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not any(v is not None for v in row):
            continue
        rows.append(dict(zip(headers, row)))
    return rows


def filter_rows_for_mode(rows, mode, order_numbers=None):
    """mode: 'cold' or 'last_day' -> every row, Order of swap ignored entirely.
    mode: 'sector' -> only rows whose 'Order of swap' matches any of order_numbers (a set of
    strings/ints, whatever the engineer typed — not restricted to any fixed range)."""
    if mode in ("cold", "last_day"):
        return list(rows)
    if mode == "sector":
        wanted = {str(n).strip() for n in (order_numbers or [])}
        return [r for r in rows if str(r.get("Order of swap", "")).strip() in wanted]
    raise ValueError(f"unknown mode: {mode}")


def group_by_node_and_tech(rows):
    """Groups Nokia_Info rows by (Nokia Node Name, Technology). Returns a dict:
    {(node_name, tech): {"id_value": eNBId_or_gNBId, "gnodeb_name": node_name (5G only),
    "cells": [{"cell_id": Nokia_Cell_Id, "cell_name": Nokia_cell_name}, ...]}}
    Technology is normalized to 'LTE' or '5G' matching the rest of the NL Delete tool's
    convention (Nokia_Info uses '4G'/'5G')."""
    grouped = {}
    for row in rows:
        raw_tech = str(row.get("Technology", "")).strip().upper()
        tech = "LTE" if raw_tech == "4G" else ("5G" if raw_tech == "5G" else None)
        if not tech:
            continue
        node_name = row.get("Nokia Node Name")
        id_value = row.get("Nokia gNBId/eNBId")
        cell_name = row.get("Nokia FDD/TDD")  # confirmed: this column actually holds the cell name
        cell_id = row.get("Nokia Cell Id")
        if not (node_name and id_value):
            continue
        key = (str(node_name).strip(), tech)
        entry = grouped.setdefault(key, {"id_value": str(id_value).strip(), "gnodeb_name": str(node_name).strip(), "cells": []})
        if cell_id is not None:
            entry["cells"].append({"cell_id": str(cell_id).strip(), "cell_name": str(cell_name).strip() if cell_name else None})
    return grouped


def build_n2e_scenarios(ciq_wb, mode, order_numbers=None):
    """Returns a list of scenario dicts matching Legacy's exact shape — {"node", "tech",
    "status", "id_value", "identity_name", "cells"} — so the existing command-generation and
    assembly functions (build_lte_scenario/build_5g_scenario/assemble_outputs) work completely
    unchanged. status is 'deletes' (full node+sector deletion) for cold/last_day modes, and
    'survives' (sector-only, no TermPoint — matching Legacy's sector-only scenario type exactly)
    for the 'sector' warm-swap mode, per the confirmed rule."""
    rows = parse_nokia_info(ciq_wb)
    filtered = filter_rows_for_mode(rows, mode, order_numbers)
    grouped = group_by_node_and_tech(filtered)
    status = "survives" if mode == "sector" else "deletes"

    scenarios = []
    for (node_name, tech), entry in grouped.items():
        scenarios.append({
            "node": node_name, "tech": tech, "status": status,
            "id_value": entry["id_value"], "identity_name": node_name,
            "primary_tech": None,  # N2E has no primary/secondary concept — every row is its own node+tech
            "cells": entry["cells"],
        })
    return scenarios

import streamlit as st
import openpyxl
import io

import nl_delete_core as core
from nl_delete_commands import lte_sector_discovery_command, lte_node_discovery_command, gnb_sector_discovery_command, gnb_node_discovery_command
from nl_delete_assemble import assemble_outputs

st.set_page_config(page_title="NL Delete", layout="wide")

st.markdown("""
<style>
  .stApp {
      background: linear-gradient(180deg, #eef3fa 0%, #f7f9fc 100%);
  }
  .qkx-topbar {
      position: sticky; top: 0; z-index: 999;
      display: flex; justify-content: space-between; align-items: center;
      padding: 0.9rem 1.75rem; margin: -1rem -1rem 1.5rem -1rem;
      background: linear-gradient(90deg, #011b36 0%, #012a4e 100%);
      border-bottom: 1px solid rgba(255,91,36,0.55);
      box-shadow: 0 4px 18px rgba(0,0,0,0.2);
  }
  .qkx-topbar .qkx-logo { font-size: 1.4rem; font-weight: 900; color: #ffffff; letter-spacing: 1px; }
  .qkx-topbar .qkx-logo span { color: #ffffff; }
  .qkx-topbar .qkx-credit { font-size: 0.78rem; color: #cfe0f5; text-align: right; line-height: 1.3; }

  div[data-testid="stButton"] button {
      border-radius: 10px; font-weight: 700; border: 1.5px solid #013a6b;
      background: linear-gradient(135deg, #024ea4, #013a6b); color: #ffffff;
      box-shadow: 0 3px 8px rgba(1,42,78,0.25);
      transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
  }
  div[data-testid="stButton"] button:hover {
      border-color: #ff5b24; color: #ffffff; transform: translateY(-1px);
      box-shadow: 0 6px 14px rgba(255,91,36,0.35);
  }
  div[data-testid="stButton"] button:active { transform: translateY(0); }

  div[data-testid="stVerticalBlockBorderWrapper"] {
      background: #ffffff !important;
      border: 1px solid #dde5ef !important;
      border-radius: 12px !important;
      box-shadow: 0 2px 10px rgba(1,42,78,0.06);
  }

  .qkx-scenario-card { border: 1px solid #d8dee8; border-radius: 8px; padding: 14px 18px; margin-bottom: 14px; background: #fbfcfe; }
  .qkx-scenario-title { font-weight: 700; font-size: 1.05rem; }
  .qkx-badge-delete { background:#fdeaea; color:#b3261e; padding:2px 10px; border-radius:12px; font-size:0.78rem; font-weight:600; }
  .qkx-badge-survive { background:#e8f1fd; color:#1a56b0; padding:2px 10px; border-radius:12px; font-size:0.78rem; font-weight:600; }

  /* Legacy vs N2E scope choice — same brand palette as the rest of MASTEC, Endeavour blue vs Orange accent */
  .qkx-scope-legacy button { background: linear-gradient(135deg, #024ea4, #013a6b) !important; border: 1.5px solid #013a6b !important; }
  .qkx-scope-n2e button { background: linear-gradient(135deg, #ff5b24, #c73f12) !important; border: 1.5px solid #c73f12 !important; }
</style>
<div class="qkx-topbar">
  <div class="qkx-logo">MAS<span>TEC</span></div>
  <div class="qkx-credit">Made by <b>AKSHATHA KALLUR</b><br>Powered by <b>MASTEC</b></div>
</div>
""", unsafe_allow_html=True)

st.title("NL Delete Tool")
st.caption("Neighbor Relation deletion — sector moves/deletes and full identity deletions, LTE + 5G")

if "nl_scenarios" not in st.session_state:
    st.session_state.nl_scenarios = None
if "nl_user_inputs" not in st.session_state:
    st.session_state.nl_user_inputs = {}
if "nl_scope" not in st.session_state:
    st.session_state.nl_scope = None

if st.session_state.nl_scope is None:
    st.subheader("Choose scope")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="qkx-scope-legacy">', unsafe_allow_html=True)
        if st.button("Legacy", use_container_width=True, key="nl_scope_legacy"):
            st.session_state.nl_scope = "Legacy"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="qkx-scope-n2e">', unsafe_allow_html=True)
        if st.button("N2E", use_container_width=True, key="nl_scope_n2e"):
            st.session_state.nl_scope = "N2E"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

if st.button("\u2190 Back", key="nl_scope_back"):
    st.session_state.nl_scope = None
    st.session_state.nl_scenarios = None
    st.session_state.nl_user_inputs = {}
    st.rerun()

def render_generate_section(scenarios, scope_label, suppress_node_existence_check=False):
    """Shared 'Generate' section for both Legacy and N2E — same assemble_outputs() call,
    same three download options, same preview expanders."""
    st.subheader("3. Generate")
    if st.button("Generate NL Delete output files \u2192", type="primary", key=f"gen_{scope_label}"):
        set_text, get_text = assemble_outputs(scenarios, st.session_state.nl_user_inputs,
                                               suppress_node_existence_check=suppress_node_existence_check)
        st.success("Generated.")

        site_tag = "_".join(sorted({s["node"] for s in scenarios}))
        set_filename = f"NL_Delete_SET_{site_tag}.txt"
        get_filename = f"NL_Delete_GET_{site_tag}.txt"

        c1, c2 = st.columns(2)
        with c1:
            st.download_button("Download SET/Delete commands", set_text, file_name=set_filename, key=f"dl_set_{scope_label}")
        with c2:
            st.download_button("Download GET (verification) commands", get_text, file_name=get_filename, key=f"dl_get_{scope_label}")

        import zipfile
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(set_filename, set_text)
            zf.writestr(get_filename, get_text)
        st.download_button(
            "Download both (SET + GET) as .zip",
            zip_buf.getvalue(),
            file_name=f"NL_Delete_{site_tag}.zip",
            mime="application/zip",
            key=f"dl_zip_{scope_label}",
        )

        with st.expander("Preview SET/Delete commands"):
            st.code(set_text, language=None)
        with st.expander("Preview GET commands"):
            st.code(get_text, language=None)


def render_scenarios_grouped(scenarios, render_fn):
    """Groups scenarios by physical node (so LTE + 5G for the same site render together in
    one card) and renders each with the given per-scenario render function. Shared by
    Legacy and N2E."""
    by_site = {}
    for s in scenarios:
        by_site.setdefault(s["node"], []).append(s)

    for site, site_scenarios in by_site.items():
        with st.container(border=True):
            st.markdown(f'<div class="qkx-scenario-title">{site}</div>', unsafe_allow_html=True)
            if len(site_scenarios) > 1:
                cols = st.columns(len(site_scenarios))
                for col, s in zip(cols, site_scenarios):
                    with col:
                        render_fn(s)
            else:
                render_fn(site_scenarios[0])


def render_enm_log_uploader(scenarios, widget_key, session_sig_key, parsed_key, sl_key_prefix, kgetall_key="nl_kgetall_texts"):
    """Shared 'upload ENM CLI session log' block for both Legacy and N2E. The engineer runs
    every Site List discovery command the tool prints (for every scenario) in one ENM CLI
    session and saves the whole transcript as one .txt log; uploading it here parses it once
    and presets each scenario's Site List 1 / Site List 2 widget state directly from it, so
    the text areas render pre-filled instead of the engineer pasting each result by hand.
    A scenario the log has no match for is left exactly as it was (empty, or whatever the
    engineer already typed) -- manual entry always still works as a fallback.

    Returns the parsed log dict (or None if nothing has been uploaded yet)."""
    with st.container(border=True):
        st.markdown(
            "**ENM CLI session log (optional)** — run every Site List discovery command "
            "shown below in one ENM CLI session, save the transcript, and upload it here "
            "to auto-fill Site List 1 / Site List 2 instead of pasting each result by hand."
        )
        log_file = st.file_uploader("ENM CLI session log (.txt)", type=["txt", "log"], key=widget_key)
        if log_file is not None:
            log_bytes = log_file.getvalue()
            log_sig = (log_file.name, len(log_bytes))
            if st.session_state.get(session_sig_key) != log_sig:
                log_text = log_bytes.decode("utf-8", errors="replace")
                parsed_log = core.parse_enm_execution_log(log_text)
                st.session_state[parsed_key] = parsed_log
                st.session_state[session_sig_key] = log_sig
                kgetall_texts = st.session_state.get(kgetall_key, [])
                filled = 0
                for sc in scenarios:
                    key = (sc["node"], sc["tech"])
                    id_val = sc.get("id_value") or core.find_own_id_in_any_kgetall(kgetall_texts, sc["node"], sc["tech"])
                    if not id_val:
                        continue
                    sl1 = core.site_list_1_from_log(parsed_log, sc["tech"], id_val)
                    if sl1:
                        st.session_state[f"{sl_key_prefix}sl1_{key}"] = sl1
                        filled += 1
                    if sc["status"] == "deletes":
                        sl2 = core.site_list_2_from_log(parsed_log, sc["tech"], id_val, gnodeb_name=sc["identity_name"])
                        if sl2:
                            st.session_state[f"{sl_key_prefix}sl2_{key}"] = sl2
                            filled += 1
                if filled:
                    st.success(f"ENM log parsed — auto-filled {filled} Site List field(s) below.")
                else:
                    st.warning("ENM log parsed, but no matching eNBId/gNBId discovery results were found in it.")
    return st.session_state.get(parsed_key)


def render_site_list_status(parsed_key, list_num, tech, id_val, gnodeb_name=None):
    """Shows the ENM-log status for one Site List field, if a log has been uploaded --
    three distinct states, not a silent blank box:
      - found:   auto-filled, with how many sites.
      - zero:    the command ran and genuinely found 0 instances (nothing to clean up here).
      - missing: the command never appears in the uploaded log at all -- FLAGGED, since this
                 usually means the engineer forgot to run it, ran it for the wrong ID, or the
                 uploaded log doesn't cover this scenario yet.
    Shows nothing if no log has been uploaded (falls back to the plain manual-entry flow)."""
    parsed_log = st.session_state.get(parsed_key)
    if not parsed_log or not id_val:
        return
    if list_num == 1:
        status, text = core.site_list_1_status(parsed_log, tech, id_val)
    else:
        status, text = core.site_list_2_status(parsed_log, tech, id_val, gnodeb_name=gnodeb_name)

    if status == core.SITE_LIST_FOUND:
        count = len(text.split(";")) if text else 0
        st.caption(f"✓ Auto-filled from uploaded ENM log ({count} site(s)) — edit below if needed.")
    elif status == core.SITE_LIST_ZERO:
        st.warning("Zero instances found for this command in the ENM log — nothing to clean up here.")
    elif status == core.SITE_LIST_MISSING:
        st.error("⚠️ Command not found in the uploaded ENM CLI session log — run it in ENM and "
                  "re-upload the log, or paste the result manually below.")


if st.session_state.nl_scope == "Legacy":
    with st.container(border=True):
        st.subheader("1. Inputs")
        c1, c2, c3 = st.columns(3)
        with c1:
            ciq_file = st.file_uploader("CIQ (.xlsx)", type=["xlsx"])
        with c2:
            precheck_file = st.file_uploader("Pre-checks (.pdf)", type=["pdf"])
        with c3:
            kgetall_files = st.file_uploader(
                "Pre 'kget all' logs (one per node, any that apply)",
                type=["log", "txt"], accept_multiple_files=True,
            )
        analyze = st.button("Analyze \u2192", type="primary", disabled=not (ciq_file and precheck_file))

    if analyze:
        st.session_state.nl_kgetall_texts = [
            f.read().decode("utf-8", errors="replace") for f in (kgetall_files or [])
        ]
        import pdfplumber
        ciq_wb = openpyxl.load_workbook(io.BytesIO(ciq_file.read()), data_only=True)
        with pdfplumber.open(io.BytesIO(precheck_file.read())) as pdf:
            precheck_text = "\n".join(p.extract_text() or "" for p in pdf.pages)

        pre_state = core.parse_precheck_pre_state(precheck_text)
        post_state = core.parse_ciq_post_state(ciq_wb)
        move_rows = core.parse_sector_del_movement(ciq_wb)
        scenarios = core.build_scenarios(pre_state, post_state, move_rows)
        pre_line, post_line = core.build_pre_post_config_lines(pre_state, post_state)

        st.session_state.nl_scenarios = scenarios
        st.session_state.nl_pre_line = pre_line
        st.session_state.nl_post_line = post_line
        st.session_state.nl_user_inputs = {}
        if not scenarios:
            st.warning("No sector moves/deletes or identity deletions detected between Pre-checks and the CIQ.")

    scenarios = st.session_state.nl_scenarios


    def render_scenario_inputs(s):
        """Renders the input widgets for one (node, tech) scenario and returns nothing —
        writes into st.session_state.nl_user_inputs as a side effect, same as before."""
        key = (s["node"], s["tech"])
        is_deletion = s["status"] == "deletes"
        badge = '<span class="qkx-badge-delete">FULL IDENTITY DELETION</span>' if is_deletion else '<span class="qkx-badge-survive">SECTOR MOVE/DELETE</span>'
        st.markdown(f'<div class="qkx-scenario-title">[{s["tech"]}] &nbsp;{s["identity_name"]}&nbsp; {badge}</div>', unsafe_allow_html=True)
        st.caption(f'{len(s["cells"])} cell(s): ' + ", ".join(str(c.get("cell_id")) for c in s["cells"]))

        ui = st.session_state.nl_user_inputs.setdefault(key, {})

        if is_deletion:
            id_label = "eNBId" if s["tech"] == "LTE" else "gNBId"
            kgetall_texts = st.session_state.get("nl_kgetall_texts", [])
            id_val = core.find_own_id_in_any_kgetall(kgetall_texts, s["node"], s["tech"])
            if id_val:
                st.success(f"{id_label} for {s['node']}: **{id_val}**")
            else:
                st.warning(f"No uploaded kget all log contains the {id_label} for {s['node']}.")
            ui["id_value"] = id_val
            ui["gnodeb_name"] = s["identity_name"]
            ui["delete_node_site_id"] = s["identity_name"]
            if s["tech"] == "5G":
                st.caption(f"gNodeB Name: **{s['identity_name']}**")
            st.caption(f"Delete Node Site ID: **{s['identity_name']}**")

            if id_val:
                st.markdown("**Run for Site List 1 (sector-level):**")
                if s["tech"] == "LTE":
                    st.code(lte_sector_discovery_command(id_val), language=None)
                else:
                    st.code(gnb_sector_discovery_command(id_val), language=None)
                sl1_key = f"sl1_{key}"
                render_site_list_status("nl_enm_log_parsed", 1, s["tech"], id_val)
                sl1_raw = st.text_area("Site List 1 result (sector-level)", key=sl1_key, height=80)
                ui["site_list_1"] = core.dedupe_site_list_entries(sl1_raw)
                dupes1 = core.find_duplicate_site_list_entries(sl1_raw)
                if dupes1:
                    st.info(f"Removed duplicate Site IDs: {', '.join(dupes1)}")

                st.markdown("**Run for Site List 2 (node-level):**")
                if s["tech"] == "LTE":
                    st.code(lte_node_discovery_command(id_val), language=None)
                else:
                    st.code(gnb_node_discovery_command(ui.get("gnodeb_name", s["identity_name"]), id_val), language=None)
                sl2_key = f"sl2_{key}"
                render_site_list_status("nl_enm_log_parsed", 2, s["tech"], id_val, gnodeb_name=ui.get("gnodeb_name", s["identity_name"]))
                sl2_raw = st.text_area("Site List 2 result (node-level)", key=sl2_key, height=80)
                ui["site_list_2"] = core.dedupe_site_list_entries(sl2_raw)
                dupes = core.find_duplicate_site_list_entries(sl2_raw)
                if dupes:
                    st.info(f"Removed duplicate Site IDs: {', '.join(dupes)}")
            else:
                st.info("Enter the ID above to reveal the Site List discovery commands.")

        else:
            id_val = s["id_value"]
            ui["id_value"] = id_val
            if s["tech"] == "5G":
                ui["gnodeb_name"] = s["identity_name"]
                st.caption(f"gNodeB Name: **{s['identity_name']}**")
                st.code(gnb_sector_discovery_command(id_val), language=None)
            else:
                st.code(lte_sector_discovery_command(id_val), language=None)
            sl1_key = f"sl1_{key}"
            render_site_list_status("nl_enm_log_parsed", 1, s["tech"], id_val, gnodeb_name=ui.get("gnodeb_name"))
            sl1_raw = st.text_area("Site List 1 (result)", key=sl1_key, height=80)
            ui["site_list_1"] = core.dedupe_site_list_entries(sl1_raw)
            dupes1 = core.find_duplicate_site_list_entries(sl1_raw)
            if dupes1:
                st.info(f"Removed duplicate Site IDs: {', '.join(dupes1)}")


    if scenarios:
        with st.container(border=True):
            st.markdown(f"**Pre Configuration:** {st.session_state.get('nl_pre_line', '')}")
            st.markdown(f"**Post Configuration:** {st.session_state.get('nl_post_line', '')}")

        render_enm_log_uploader(
            scenarios, widget_key="nl_enm_log_upload", session_sig_key="nl_enm_log_sig",
            parsed_key="nl_enm_log_parsed", sl_key_prefix="",
        )

        st.subheader("2. Detected scenarios")
        render_scenarios_grouped(scenarios, render_scenario_inputs)
        render_generate_section(scenarios, "legacy")

elif st.session_state.nl_scope == "N2E":
    # ============================================================
    # N2E — data source is the CIQ's Nokia_Info tab exclusively (no Pre-checks, no kget-all).
    # Row selection depends on the engineer's chosen swap mode:
    #   Cold Swap        -> every row, Order of swap ignored entirely
    #   Warm Swap/Sector  -> only rows whose Order of swap matches any of the given numbers,
    #                        sector-level only (no TermPoint) -- confirmed matches Legacy's
    #                        sector-only scenario type exactly
    #   Warm Swap/Last day -> every row, same as Cold Swap
    # Commands reuse Legacy's build_lte_scenario/build_5g_scenario/assemble_outputs completely
    # unchanged -- only the ID source differs (Nokia_Info fields instead of kget-all).
    # ============================================================

    def render_n2e_scenario_inputs(s):
        """Like render_scenario_inputs, but the ID is always already known directly from
        Nokia_Info -- no kget-all lookup needed at all, for either survives or deletes scenarios.
        Site List 2 (node-level) only shown when status == 'deletes' (Cold Swap / Last day)."""
        key = (s["node"], s["tech"])
        is_deletion = s["status"] == "deletes"
        badge = '<span class="qkx-badge-delete">FULL IDENTITY DELETION</span>' if is_deletion else '<span class="qkx-badge-survive">SECTOR-LEVEL ONLY</span>'
        st.markdown(f'<div class="qkx-scenario-title">[{s["tech"]}] &nbsp;{s["identity_name"]}&nbsp; {badge}</div>', unsafe_allow_html=True)
        st.caption(f'{len(s["cells"])} cell(s): ' + ", ".join(str(c.get("cell_id")) for c in s["cells"]))

        ui = st.session_state.nl_user_inputs.setdefault(key, {})
        id_val = s["id_value"]
        ui["id_value"] = id_val
        ui["gnodeb_name"] = s["identity_name"]
        ui["delete_node_site_id"] = s["identity_name"]
        if s["tech"] == "5G":
            st.caption(f"gNodeB Name: **{s['identity_name']}**")
        st.caption(f"eNBId/gNBId (from Nokia_Info): **{id_val}**")

        st.markdown("**Run for Site List 1 (sector-level):**")
        if s["tech"] == "LTE":
            st.code(lte_sector_discovery_command(id_val), language=None)
        else:
            st.code(gnb_sector_discovery_command(id_val), language=None)
        n2e_sl1_key = f"n2e_sl1_{key}"
        render_site_list_status("n2e_enm_log_parsed", 1, s["tech"], id_val, gnodeb_name=ui.get("gnodeb_name"))
        n2e_sl1_raw = st.text_area("Site List 1 result (sector-level)", key=n2e_sl1_key, height=80)
        ui["site_list_1"] = core.dedupe_site_list_entries(n2e_sl1_raw)
        n2e_dupes1 = core.find_duplicate_site_list_entries(n2e_sl1_raw)
        if n2e_dupes1:
            st.info(f"Removed duplicate Site IDs: {', '.join(n2e_dupes1)}")

        if is_deletion:
            st.markdown("**Run for Site List 2 (node-level):**")
            if s["tech"] == "LTE":
                st.code(lte_node_discovery_command(id_val), language=None)
            else:
                st.code(gnb_node_discovery_command(ui.get("gnodeb_name", s["identity_name"]), id_val), language=None)
            n2e_sl2_key = f"n2e_sl2_{key}"
            render_site_list_status("n2e_enm_log_parsed", 2, s["tech"], id_val, gnodeb_name=ui.get("gnodeb_name"))
            sl2_raw = st.text_area("Site List 2 result (node-level)", key=n2e_sl2_key, height=80)
            ui["site_list_2"] = core.dedupe_site_list_entries(sl2_raw)
            dupes = core.find_duplicate_site_list_entries(sl2_raw)
            if dupes:
                st.info(f"Removed duplicate Site IDs: {', '.join(dupes)}")


    if "n2e_scenarios" not in st.session_state:
        st.session_state.n2e_scenarios = None

    with st.container(border=True):
        st.subheader("1. Inputs")
        n2e_ciq_file = st.file_uploader("CIQ (.xlsx)", type=["xlsx"], key="n2e_ciq")

        st.markdown("**Swap mode**")
        n2e_mode_label = st.radio(
            "Swap mode", ["Cold Swap", "Warm Swap — Sector level", "Warm Swap — Last day of cutover"],
            key="n2e_mode", label_visibility="collapsed",
        )
        n2e_order_numbers = []
        if n2e_mode_label == "Warm Swap — Sector level":
            n2e_order_input = st.text_input("Order of swap number(s), comma-separated (e.g. 1 or 1,2)", key="n2e_order_input")
            n2e_order_numbers = [n.strip() for n in n2e_order_input.split(",") if n.strip()]

        n2e_mode = {"Cold Swap": "cold", "Warm Swap — Sector level": "sector", "Warm Swap — Last day of cutover": "last_day"}[n2e_mode_label]
        n2e_analyze_disabled = not n2e_ciq_file or (n2e_mode == "sector" and not n2e_order_numbers)
        n2e_analyze = st.button("Analyze →", type="primary", disabled=n2e_analyze_disabled, key="n2e_analyze")

    if n2e_analyze:
        n2e_ciq_wb = openpyxl.load_workbook(io.BytesIO(n2e_ciq_file.read()), data_only=True)
        import n2e_delete_core
        n2e_scenarios = n2e_delete_core.build_n2e_scenarios(n2e_ciq_wb, mode=n2e_mode, order_numbers=n2e_order_numbers)
        st.session_state.n2e_scenarios = n2e_scenarios
        st.session_state.nl_user_inputs = {}
        if not n2e_scenarios:
            st.warning("No matching rows found in Nokia_Info for this swap mode/selection.")

    n2e_scenarios = st.session_state.n2e_scenarios

    if n2e_scenarios:
        render_enm_log_uploader(
            n2e_scenarios, widget_key="n2e_enm_log_upload", session_sig_key="n2e_enm_log_sig",
            parsed_key="n2e_enm_log_parsed", sl_key_prefix="n2e_",
        )

        st.subheader("2. Detected scenarios")
        render_scenarios_grouped(n2e_scenarios, render_n2e_scenario_inputs)
        render_generate_section(n2e_scenarios, "n2e", suppress_node_existence_check=True)

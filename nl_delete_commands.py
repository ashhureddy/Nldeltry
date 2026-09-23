"""
NL Delete tool — command generation.

Builds the exact command text from the 4 confirmed templates:
  - LTE sector move/delete (Site List 1 only)
  - LTE full identity deletion (Site List 1 + Site List 2, superset of the above)
  - 5G sector move/delete (Site List 1 only)
  - 5G full identity deletion (Site List 1 + Site List 2, superset of the above)

Each returns three blocks of text: prechecks_get, set_delete, get_verify_and_postchecks —
matching the templates' Step 1 (Prechecks) / Step 2 (Execution, incl. its own embedded GET
verification) / Step 3+ (Postchecks, plus node-deletion's extra auto-cleanup sub-step).

The final assembly splits these into the two confirmed output files: SET/Delete commands
(everything except pure "get" blocks) and GET commands (every verification query, at all
three stages) — built by the caller from these pieces.

FIELD-LEVEL SKIP RULE: any individual missing/blank field only removes the command lines
that depend on that specific field — it never blanks out the whole scenario. Concretely:
  - site_list_1 missing  -> skip prechecks/set_delete/get_verify/site_list_1-based postchecks
                             entirely; node-existence check and discovery commands still print.
  - site_list_2 missing  -> skip only node_step3 (Site List 2 node-level cleanup).
  - delete_node_site_id missing -> skip only the ComConnectivityInformation /
                             NetworkElement,CmFunction existence-check lines.
  - gnodeb_name missing (5G only) -> skip only the gnodeb_name-based lines; the
                             gnbid-numeric-based lines still print.
"""

import re

SITE_A_TO_Z = "A*;B*;C*;D*;E*;F*;G*;H*;I*;J*;K*;L*;M*;N*;O*;P*;Q*;R*;S*;T*;U*;V*;W*;X*;Y*;Z*"


def _split_sites(site_list_text):
    """Splits a Site List 2 string (semicolon/comma/newline separated) into individual
    site/node names, for building one full-FDN command per site."""
    parts = re.split(r'[;,\n]+', site_list_text or "")
    return [p.strip() for p in parts if p.strip()]


def lte_sector_discovery_command(enbid):
    return f"cmedit get {SITE_A_TO_Z} ExternalEnodeBFunction.(enBID=={enbid}) -t"


def lte_node_discovery_command(enbid):
    return f"cmedit get {SITE_A_TO_Z} ExternalenodeBFunction.(eNodeBId=={enbid}) -t"


def gnb_sector_discovery_command(gnbid):
    return f"cmedit get {SITE_A_TO_Z} ExternalGnodeBFunction.(gNodeBId=={gnbid}) -t"


def gnb_node_discovery_command(gnodeb_name, gnbid):
    return (
        f"cmedit get {SITE_A_TO_Z} ExternalGNBCUCPFunction.(ExternalGNBCUCPFunctionId=={gnodeb_name}) -t\n"
        f"cmedit get {SITE_A_TO_Z} ExternalGNBCUCPFunction.gnbid=={gnbid} -t"
    )


def build_lte_scenario(enbid, site_list_1, cells, is_deletion, site_list_2=None, delete_node_site_id=None, include_node_existence_check=True):
    """cells: [{"cell_id":...}]. Returns {"prechecks_get","set_delete","get_verify","node_step3","postchecks_get"}."""
    cell_ids = [c["cell_id"] for c in cells]
    site_list_1 = (site_list_1 or "").strip()
    site_list_2 = (site_list_2 or "").strip() or None
    delete_node_site_id = (delete_node_site_id or "").strip() or None

    prechecks, set_delete, get_verify, postchecks, node_step3 = [], [], [], [], []

    if site_list_1:
        for cid in cell_ids:
            prechecks.append(f"cmedit get {site_list_1}  ExternalEUtranCellFDD.(ExternalEUtranCellFDDid==310410-{enbid}-{cid}) –t")
        for cid in cell_ids:
            prechecks.append(f"cmedit get {site_list_1} EUtranCellRelation.(eUtranCellRelationId==310410-{enbid}-{cid}) -t")
        if is_deletion:
            prechecks.append(f"cmedit get {site_list_1} ExternalEnodeBFunction.(ExternalENodeBFunctionId==310410-{enbid}) -t")
        prechecks.append(f"cmedit get {site_list_1} TermPointToENB.(administrativeState,usedipAddress,operationalState,availabilityStatus,termpointtoenbId==310410-{enbid}) -t")

        set_delete.append(f"cmedit get {site_list_1} TermPointToENB.(administrativeState,usedipAddress,operationalState,availabilityStatus,termpointtoenbId==310410-{enbid}) -t")
        set_delete.append(f"cmedit set {site_list_1} Termpointtoenb.(termpointtoenbId==310410-{enbid}) administrativestate=LOCKED")
        for cid in cell_ids:
            set_delete.append(f"cmedit delete {site_list_1} EUtranCellRelation.(eUtranCellRelationId==310410-{enbid}-{cid}) --force -ALL")
        for cid in cell_ids:
            set_delete.append(f"cmedit delete {site_list_1}  ExternalEUtranCellFDD.(ExternalEUtranCellFDDid==310410-{enbid}-{cid}) --force -ALL")
        if is_deletion:
            set_delete.append(f"cmedit delete {site_list_1} Termpointtoenb.(termpointtoenbId==310410-{enbid}) --force -ALL")
            set_delete.append(f"cmedit delete {site_list_1} ExternalEnodeBFunction.(ExternalENodeBFunctionId==310410-{enbid}) --force -ALL")

        for cid in cell_ids:
            get_verify.append(f"cmedit get {site_list_1}  ExternalEUtranCellFDD.(ExternalEUtranCellFDDid==310410-{enbid}-{cid}) –t")
        for cid in cell_ids:
            get_verify.append(f"cmedit get {site_list_1} EUtranCellRelation.(eUtranCellRelationId==310410-{enbid}-{cid}) -t")
        if is_deletion:
            get_verify.append(f"cmedit get {site_list_1} TermPointToENB.(administrativeState,usedipAddress,operationalState,availabilityStatus,termpointtoenbId==310410-{enbid}) -t")
            get_verify.append(f"cmedit get {site_list_1} ExternalEnodeBFunction.(ExternalENodeBFunctionId==310410-{enbid}) -t")
        else:
            set_delete.append(f"cmedit set {site_list_1} Termpointtoenb.(termpointtoenbId==310410-{enbid}) administrativestate=UNLOCKED")
            get_verify.append(f"cmedit get {site_list_1} TermPointToENB.(administrativeState,usedipAddress,operationalState,availabilityStatus,termpointtoenbId==310410-{enbid}) -t")

        for cid in cell_ids:
            postchecks.append(f"cmedit get {site_list_1}  ExternalEUtranCellFDD.(ExternalEUtranCellFDDid==310410-{enbid}-{cid}) –t")
        for cid in cell_ids:
            postchecks.append(f"cmedit get {site_list_1} EUtranCellRelation.(eUtranCellRelationId==310410-{enbid}-{cid}) -t")
        postchecks.append(f"cmedit get {site_list_1} TermPointToENB.(administrativeState,usedipAddress,operationalState,availabilityStatus,termpointtoenbId==310410-{enbid}) -t")
        if is_deletion:
            postchecks.append(f"cmedit get {site_list_1} ExternalEnodeBFunction.(ExternalENodeBFunctionId==310410-{enbid}) -t")

    if is_deletion:
        postchecks.append(lte_node_discovery_command(enbid))
        postchecks.append(lte_sector_discovery_command(enbid))
        if include_node_existence_check and delete_node_site_id:
            postchecks.append(f"\ncmedit get {delete_node_site_id} ComConnectivityInformation.*")
            postchecks.append(f"cmedit get NetworkElement={delete_node_site_id},CmFunction=1")

        if site_list_2:
            sites = _split_sites(site_list_2)
            # wide flat GET across the whole site list -- BEFORE
            node_step3.append(f"cmedit get {site_list_2} TermPointToENodeB.(termPointToENodeBId,administrativeState,operationalState) -t")
            # full-FDN GET, one per site -- BEFORE
            for site in sites:
                node_step3.append(f"cmedit get SubNetwork=ONRM_ROOT_MO,MeContext={site},ManagedElement={site},ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=auto310_410_3_{enbid},TermPointToENodeB=auto1 -t")
            # full-FDN SET LOCKED, one per site
            for site in sites:
                node_step3.append(f"cmedit set SubNetwork=ONRM_ROOT_MO,MeContext={site},ManagedElement={site},ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=auto310_410_3_{enbid},TermPointToENodeB=auto1 administrativestate:LOCKED --force")
            # full-FDN GET, one per site -- AFTER
            for site in sites:
                node_step3.append(f"cmedit get SubNetwork=ONRM_ROOT_MO,MeContext={site},ManagedElement={site},ENodeBFunction=1,EUtraNetwork=1,ExternalENodeBFunction=auto310_410_3_{enbid},TermPointToENodeB=auto1 -t")
            # wide flat GET across the whole site list -- AFTER
            node_step3.append(f"cmedit get {site_list_2} TermPointToENodeB.(termPointToENodeBId,administrativeState,operationalState) -t")
            node_step3.append(f"cmedit delete {site_list_2}  ExternalENodeBFunction.(ExternalENodeBFunctionID==auto310_410_3_{enbid}) -ALL")

    return {
        "prechecks_get": "\n".join(prechecks),
        "set_delete": "\n".join(set_delete),
        "get_verify": "\n".join(get_verify),
        "node_step3": "\n".join(node_step3),
        "postchecks_get": "\n".join(postchecks),
    }


def build_5g_scenario(gnbid, gnodeb_name, site_list_1, cells, is_deletion, site_list_2=None, delete_node_site_id=None, include_node_existence_check=True):
    """cells: [{"cell_id":..., "cell_name":...}]."""
    cell_ids = [c["cell_id"] for c in cells]
    cell_names = [c["cell_name"] for c in cells]
    site_list_1 = (site_list_1 or "").strip()
    site_list_2 = (site_list_2 or "").strip() or None
    delete_node_site_id = (delete_node_site_id or "").strip() or None
    gnodeb_name = (gnodeb_name or "").strip() or None

    tpgnb_num = f"TermPointToGNB.(administrativeState,usedipAddress,operationalState,availabilityStatus,termpointtognbId==310410-000000{gnbid})"
    tpgnb_name = f"TermPointToGNB.(administrativeState,usedipAddress,operationalState,availabilityStatus,termpointtognbId=={gnodeb_name})" if gnodeb_name else None
    # TermPointToGNodeB (distinct MO from TermPointToGNB above, keyed by gNodeB Name only --
    # no numeric-ID form for this one) -- LOCK/UNLOCK for sector move, LOCK/DELETE for full
    # identity deletion, appended after the TermPointToGNB pair for both scenario types.
    tpgnodeb_name = f"TermPointToGNodeB.(TermPointToGNodeBID=={gnodeb_name})" if gnodeb_name else None

    prechecks, set_delete, get_verify, postchecks, node_step3 = [], [], [], [], []

    if site_list_1:
        for cid in cell_ids:
            prechecks.append(f"cmedit get {site_list_1}  ExternalGUtranCell.(externalGUtranCellId==310410-000000{gnbid}-{cid}) -t")
        for cid in cell_ids:
            prechecks.append(f"cmedit get {site_list_1}  GUtranCellRelation.(gUtranCellRelationId==310410-000000{gnbid}-{cid}) -t")
        for cn in cell_names:
            prechecks.append(f"cmedit get {site_list_1}  NRCellRelation.(NRCellRelationId=={cn}) -t")
        for cn in cell_names:
            prechecks.append(f"cmedit get {site_list_1} externalnrcellcu.(externalnrcellcuid=={cn}) -t")
        prechecks.append(f"cmedit get {site_list_1} {tpgnb_num} -t")
        if tpgnb_name:
            prechecks.append(f"cmedit get {site_list_1} {tpgnb_name} -t")
        if tpgnodeb_name:
            prechecks.append(f"cmedit get {site_list_1} {tpgnodeb_name} -t")
        if is_deletion:
            prechecks.append(f"cmedit get {site_list_1} {gnb_sector_discovery_command(gnbid).split('cmedit get ')[-1]}")

        set_delete.append(f"cmedit get {site_list_1} {tpgnb_num} -t")
        if tpgnb_name:
            set_delete.append(f"cmedit get {site_list_1} {tpgnb_name} -t")
        set_delete.append(f"cmedit set {site_list_1} TermPointToGNB.(termpointtognbId==310410-000000{gnbid}) administrativestate=LOCKED")
        if gnodeb_name:
            set_delete.append(f"cmedit set {site_list_1} TermPointToGNB.(termpointtognbId=={gnodeb_name}) administrativestate=LOCKED")
        if tpgnodeb_name:
            set_delete.append(f"cmedit set {site_list_1} {tpgnodeb_name} administrativestate=LOCKED")
        for cid in cell_ids:
            set_delete.append(f"cmedit delete {site_list_1}  GUtranCellRelation.(gUtranCellRelationId==310410-000000{gnbid}-{cid}) --force -ALL")
        for cid in cell_ids:
            set_delete.append(f"cmedit delete {site_list_1}  ExternalGUtranCell.(externalGUtranCellId==310410-000000{gnbid}-{cid}) --force -ALL")
        for cn in cell_names:
            set_delete.append(f"cmedit delete {site_list_1}  NRCellRelation.(NRCellRelationId=={cn}) --force -ALL")
        for cn in cell_names:
            set_delete.append(f"cmedit delete {site_list_1} externalnrcellcu.(externalnrcellcuid=={cn}) --force -ALL")
        if is_deletion:
            set_delete.append(f"cmedit delete {site_list_1} TermPointToGNB.(termpointtognbId==310410-000000{gnbid}) --force -ALL")
            if gnodeb_name:
                set_delete.append(f"cmedit delete {site_list_1} TermPointToGNB.(termpointtognbId=={gnodeb_name}) --force -ALL")
            if tpgnodeb_name:
                set_delete.append(f"cmedit delete {site_list_1} {tpgnodeb_name} --force -ALL")
            set_delete.append(f"cmedit delete {site_list_1} ExternalGnodeBFunction.(gNodeBId=={gnbid}) --force -ALL")
        else:
            set_delete.append(f"cmedit set {site_list_1} TermPointToGNB.(termpointtognbId==310410-000000{gnbid}) administrativestate=UNLOCKED")
            if gnodeb_name:
                set_delete.append(f"cmedit set {site_list_1} TermPointToGNB.(termpointtognbId=={gnodeb_name}) administrativestate=UNLOCKED")
            if tpgnodeb_name:
                set_delete.append(f"cmedit set {site_list_1} {tpgnodeb_name} administrativestate=UNLOCKED")

        for cid in cell_ids:
            get_verify.append(f"cmedit get {site_list_1}  ExternalGUtranCell.(externalGUtranCellId==310410-000000{gnbid}-{cid}) -t")
        for cid in cell_ids:
            get_verify.append(f"cmedit get {site_list_1}  GUtranCellRelation.(gUtranCellRelationId==310410-000000{gnbid}-{cid}) -t")
        for cn in cell_names:
            get_verify.append(f"cmedit get {site_list_1}  NRCellRelation.(NRCellRelationId=={cn}) -t")
        for cn in cell_names:
            get_verify.append(f"cmedit get {site_list_1} externalnrcellcu.(externalnrcellcuid=={cn}) -t")
        get_verify.append(f"cmedit get {site_list_1} {tpgnb_num} -t")
        if tpgnb_name:
            get_verify.append(f"cmedit get {site_list_1} {tpgnb_name} -t")
        if tpgnodeb_name:
            get_verify.append(f"cmedit get {site_list_1} {tpgnodeb_name} -t")
        if is_deletion:
            get_verify.append(f"cmedit get {site_list_1} ExternalGnodeBFunction.(gNodeBId=={gnbid}) -t")

        for cid in cell_ids:
            postchecks.append(f"cmedit get {site_list_1}  ExternalGUtranCell.(externalGUtranCellId==310410-000000{gnbid}-{cid}) -t")
        for cid in cell_ids:
            postchecks.append(f"cmedit get {site_list_1}  GUtranCellRelation.(gUtranCellRelationId==310410-000000{gnbid}-{cid}) -t")
        for cn in cell_names:
            postchecks.append(f"cmedit get {site_list_1}  NRCellRelation.(NRCellRelationId=={cn}) -t")
        for cn in cell_names:
            postchecks.append(f"cmedit get {site_list_1} externalnrcellcu.(externalnrcellcuid=={cn}) -t")
        postchecks.append(f"cmedit get {site_list_1} {tpgnb_num} -t")
        if tpgnb_name:
            postchecks.append(f"cmedit get {site_list_1} {tpgnb_name} -t")
        if tpgnodeb_name:
            postchecks.append(f"cmedit get {site_list_1} {tpgnodeb_name} -t")

    if is_deletion:
        if gnodeb_name:
            postchecks.append(gnb_node_discovery_command(gnodeb_name, gnbid))
        postchecks.append(gnb_sector_discovery_command(gnbid))
        if include_node_existence_check and delete_node_site_id:
            postchecks.append(f"\ncmedit get {delete_node_site_id} ComConnectivityInformation.*")
            postchecks.append(f"cmedit get NetworkElement={delete_node_site_id},CmFunction=1")

        if site_list_2:
            sites = _split_sites(site_list_2)
            # wide flat GET across the whole site list -- BEFORE
            node_step3.append(f"cmedit get {site_list_2} TermPointToGNodeB.(TermPointToGNodeBId,administrativeState,operationalState) -t")
            # full-FDN GET, one per site, both ID variants -- BEFORE
            for site in sites:
                node_step3.append(f"cmedit get SubNetwork=ONRM_ROOT_MO,MeContext={site},ManagedElement={site},GNBCUCPFunction=1,NRNetwork=1,ExternalGNBCUCPFunction=auto310_410_3_{gnbid},TermPointToGNodeB=auto1 -t")
                if delete_node_site_id:
                    node_step3.append(f"cmedit get SubNetwork=ONRM_ROOT_MO,MeContext={site},ManagedElement={site},GNBCUCPFunction=1,NRNetwork=1,ExternalGNBCUCPFunction={delete_node_site_id},TermPointToGNodeB=auto1 -t")
            # full-FDN SET LOCKED, one per site, both ID variants
            for site in sites:
                node_step3.append(f"cmedit set SubNetwork=ONRM_ROOT_MO,MeContext={site},ManagedElement={site},GNBCUCPFunction=1,NRNetwork=1,ExternalGNBCUCPFunction=auto310_410_3_{gnbid},TermPointToGNodeB=auto1 administrativestate:LOCKED --force")
                if delete_node_site_id:
                    node_step3.append(f"cmedit set SubNetwork=ONRM_ROOT_MO,MeContext={site},ManagedElement={site},GNBCUCPFunction=1,NRNetwork=1,ExternalGNBCUCPFunction={delete_node_site_id},TermPointToGNodeB=auto1 administrativestate:LOCKED --force")
            # full-FDN GET, one per site, both ID variants -- AFTER
            for site in sites:
                node_step3.append(f"cmedit get SubNetwork=ONRM_ROOT_MO,MeContext={site},ManagedElement={site},GNBCUCPFunction=1,NRNetwork=1,ExternalGNBCUCPFunction=auto310_410_3_{gnbid},TermPointToGNodeB=auto1 -t")
                if delete_node_site_id:
                    node_step3.append(f"cmedit get SubNetwork=ONRM_ROOT_MO,MeContext={site},ManagedElement={site},GNBCUCPFunction=1,NRNetwork=1,ExternalGNBCUCPFunction={delete_node_site_id},TermPointToGNodeB=auto1 -t")
            # wide flat GET across the whole site list -- AFTER
            node_step3.append(f"cmedit get {site_list_2} TermPointToGNodeB.(TermPointToGNodeBId,administrativeState,operationalState) -t")
            node_step3.append(f"cmedit delete {site_list_2} ExternalGNBCUCPFunction.gnbid=={gnbid} --force -ALL")

    return {
        "prechecks_get": "\n".join(prechecks),
        "set_delete": "\n".join(set_delete),
        "get_verify": "\n".join(get_verify),
        "node_step3": "\n".join(node_step3),
        "postchecks_get": "\n".join(postchecks),
    }

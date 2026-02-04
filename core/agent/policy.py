def requires_po_approval(po_summary: dict) -> bool:
    # policy: PO lines > 10 OR total_qty > 80
    return po_summary.get("po_lines", 0) > 10 or po_summary.get("total_qty", 0) > 80

def requires_overflow_approval(alloc_summary: dict) -> bool:
    # policy: unassigned repairs > 10
    return alloc_summary.get("unassigned_repairs", 0) > 10

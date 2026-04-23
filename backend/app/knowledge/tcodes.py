"""
SAP transaction code catalog used as context for the AI and rule engine.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TCode:
    code: str
    module: str
    description: str
    category: str
    related_tables: list[str] = field(default_factory=list)
    related_tcodes: list[str] = field(default_factory=list)


SAP_TCODES: dict[str, TCode] = {
    # ── MM – Purchase Orders ─────────────────────────────────────────────────
    "ME21N": TCode("ME21N", "MM", "Create Purchase Order", "purchasing",
                   ["EKKO", "EKPO"], ["ME22N", "ME23N"]),
    "ME22N": TCode("ME22N", "MM", "Change Purchase Order", "purchasing",
                   ["EKKO", "EKPO"], ["ME21N", "ME23N"]),
    "ME23N": TCode("ME23N", "MM", "Display Purchase Order", "purchasing",
                   ["EKKO", "EKPO"], ["ME21N", "ME22N"]),
    "ME2M":  TCode("ME2M",  "MM", "Purchase Orders by Material", "purchasing",
                   ["EKKO", "EKPO"], ["ME2L", "ME2N"]),
    "ME2L":  TCode("ME2L",  "MM", "Purchase Orders by Vendor", "purchasing",
                   ["EKKO", "EKPO"], ["ME2M"]),

    # ── MM – Goods Movements ────────────────────────────────────────────────
    "MIGO":  TCode("MIGO", "MM", "Goods Movement (General)", "inventory",
                   ["MKPF", "MSEG", "MARD"], ["MB51", "MB52"]),
    "MB1A":  TCode("MB1A", "MM", "Goods Withdrawal", "inventory",
                   ["MKPF", "MSEG"], ["MIGO"]),
    "MB1C":  TCode("MB1C", "MM", "Other Goods Receipts", "inventory",
                   ["MKPF", "MSEG"], ["MIGO"]),
    "MB51":  TCode("MB51", "MM", "Material Document List", "inventory",
                   ["MKPF", "MSEG"], ["MIGO"]),
    "MB52":  TCode("MB52", "MM", "Warehouse Stocks of Material", "inventory",
                   ["MARD", "MARM"], []),
    "MMBE":  TCode("MMBE", "MM", "Stock Overview", "inventory",
                   ["MARD", "MCHB", "MSKA"], []),

    # ── MM – Invoice Verification ───────────────────────────────────────────
    "MIRO":  TCode("MIRO", "MM", "Enter Incoming Invoice", "invoice",
                   ["RBKPF", "RBDRSEG", "EKKO"], ["MIR4", "MR11", "MRBR"]),
    "MIR4":  TCode("MIR4",  "MM", "Display Invoice Document", "invoice",
                   ["RBKPF", "RBDRSEG"], ["MIRO"]),
    "MR11":  TCode("MR11",  "MM", "GR/IR Account Maintenance", "invoice",
                   ["EKKO", "EKPO", "WRX"], ["MIRO", "MR8M"]),
    "MR8M":  TCode("MR8M",  "MM", "Cancel Invoice Document", "invoice",
                   ["RBKPF"], ["MIRO"]),
    "MRBR":  TCode("MRBR",  "MM", "Release Blocked Invoices", "invoice",
                   ["RBKPF"], ["MIRO", "MIR4"]),
    "MIR6":  TCode("MIR6",  "MM", "Invoice Overview", "invoice",
                   ["RBKPF"], []),

    # ── MM – Vendor ─────────────────────────────────────────────────────────
    "MK01":  TCode("MK01", "MM", "Create Vendor (Purchasing)", "vendor",
                   ["LFA1", "LFB1", "LFM1"], ["MK02", "MK03"]),
    "MK02":  TCode("MK02", "MM", "Change Vendor (Purchasing)", "vendor",
                   ["LFA1", "LFB1"], ["MK01"]),
    "XK05":  TCode("XK05", "MM", "Block/Unblock Vendor", "vendor",
                   ["LFA1"], ["MK02"]),

    # ── SD – Sales Orders ───────────────────────────────────────────────────
    "VA01":  TCode("VA01", "SD", "Create Sales Order", "sales",
                   ["VBAK", "VBAP"], ["VA02", "VA03"]),
    "VA02":  TCode("VA02", "SD", "Change Sales Order", "sales",
                   ["VBAK", "VBAP"], ["VA01", "VA03"]),
    "VA03":  TCode("VA03", "SD", "Display Sales Order", "sales",
                   ["VBAK", "VBAP"], ["VA01", "VA02"]),
    "VA05":  TCode("VA05", "SD", "List of Sales Orders", "sales",
                   ["VBAK"], []),

    # ── SD – Delivery ───────────────────────────────────────────────────────
    "VL01N": TCode("VL01N", "SD", "Create Outbound Delivery", "delivery",
                   ["LIKP", "LIPS"], ["VL02N", "VL03N"]),
    "VL02N": TCode("VL02N", "SD", "Change Outbound Delivery", "delivery",
                   ["LIKP", "LIPS"], ["VL01N", "VL03N"]),
    "VL03N": TCode("VL03N", "SD", "Display Outbound Delivery", "delivery",
                   ["LIKP", "LIPS"], ["VL02N"]),
    "VL10":  TCode("VL10",  "SD", "Delivery Due List", "delivery",
                   ["VBAP", "LIPS"], []),

    # ── SD – Billing ────────────────────────────────────────────────────────
    "VF01":  TCode("VF01", "SD", "Create Billing Document", "billing",
                   ["VBRK", "VBRP"], ["VF02", "VF03"]),
    "VF02":  TCode("VF02", "SD", "Change Billing Document", "billing",
                   ["VBRK", "VBRP"], ["VF01", "VF03"]),
    "VF03":  TCode("VF03", "SD", "Display Billing Document", "billing",
                   ["VBRK", "VBRP"], ["VF02"]),
    "VF04":  TCode("VF04", "SD", "Billing Due List", "billing",
                   ["VBRK"], []),

    # ── SD – Credit Management ──────────────────────────────────────────────
    "VKM1":  TCode("VKM1", "SD", "Blocked SD Documents (Credit Mgmt)", "credit",
                   ["VBAK", "KNKK"], ["VKM3", "FD32"]),
    "VKM3":  TCode("VKM3", "SD", "Released SD Documents", "credit",
                   ["VBAK"], ["VKM1"]),
    "FD32":  TCode("FD32", "SD", "Change Customer Credit Management", "credit",
                   ["KNKK"], ["VKM1"]),

    # ── SD – Pricing ────────────────────────────────────────────────────────
    "VK11":  TCode("VK11", "SD", "Create Condition Record", "pricing",
                   ["KONP", "KONH"], ["VK12", "VK13"]),
    "VK12":  TCode("VK12", "SD", "Change Condition Record", "pricing",
                   ["KONP", "KONH"], ["VK11"]),
}


def get_tcode(code: str) -> TCode | None:
    return SAP_TCODES.get(code.upper())


def get_tcodes_for_module(module: str) -> list[TCode]:
    return [t for t in SAP_TCODES.values() if t.module == module.upper()]

# build_unified_key_discoveries.py
"""
Builds the unified Key Discoveries (#keydiscoveries) tab page:
1. Top Section: Exact visual layout from WhatsApp reference image:
   - Header banner with trust strip (no mode switchers)
   - 60-second Finding Map table
   - Row 1: Cards 1, 2, 3 (Fabric Exposure heatmap, Concurrency metrics, Long Context slope chart)
   - Section "Optimization & Reuse": Cards 4, 5, 6, 7 (Prefix Reuse table, Parallelism Pareto frontier chart, Prompt Token dual bars, Runtime Knob tables)
   - Section "Evidence Chain & Operational Traps": Cards 8, 9, 10 (TP Decode 4-stage chain, Busy GPU != Efficient Serving table, KV vs VRAM table)
   - Trust footer strip
2. Divider: Transition to Detailed 10-Finding Explorer
3. Bottom Section: Persistent left rail + 10 deep finding subpages with interactive Chart.js graphs
4. Floating Modal Popup: Clicking "View Details →" opens the 10-page explorer modal focused on that finding
"""
import os
import sys
import json
import re

# Load canonical 10 pages from scratch/build_v5_subpages.py
with open("scratch/build_v5_subpages.py", "r", encoding="utf-8") as f:
    code = f.read()

ns = {}
exec(code, ns)
PAGES = ns["PAGES"]
print(f"Loaded {len(PAGES)} pages.")

# CSS for the unified page
CSS_KEY_DISCOVERIES = """
/* === UNIFIED KEY DISCOVERIES (WHATSAPP IMAGE LAYOUT + EMBEDDED 10-PAGE EXPLORER + MODAL) === */
.kd-container {
    display: flex;
    flex-direction: column;
    gap: 14px;
    color: #e2e8f0;
}

/* Header Banner & Trust Strip */
.kd-header-banner {
    background: linear-gradient(180deg, #0b172a 0%, #081225 100%);
    border: 1px solid #1a2a44;
    border-radius: 8px;
    padding: 16px 20px;
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.kd-header-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}
.kd-title-group h1 {
    font-size: 24px;
    font-weight: 850;
    color: #ffffff;
    margin: 0 0 4px 0;
    letter-spacing: -0.4px;
}
.kd-title-group p {
    font-size: 12px;
    color: #94a3b8;
    margin: 0;
    line-height: 1.4;
}
.kd-trust-strip {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    padding-top: 10px;
    border-top: 1px solid #16263e;
    font-size: 11px;
}
.kd-model-pill {
    background: #0f1c30;
    border: 1px solid #233857;
    color: #38bdf8;
    padding: 4px 10px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 10.5px;
}
.kd-stat-item {
    display: flex;
    align-items: baseline;
    gap: 5px;
}
.kd-stat-num {
    font-size: 13px;
    font-weight: 800;
    color: #38bdf8;
}
.kd-stat-label {
    font-size: 10px;
    color: #94a3b8;
}
.kd-badge-validated {
    background: #062b1b;
    border: 1px solid #10b981;
    color: #34d399;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 800;
    display: flex;
    align-items: center;
    gap: 4px;
}
.kd-badge-warning {
    background: #2e1805;
    border: 1px solid #f59e0b;
    color: #fbbf24;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 800;
    display: flex;
    align-items: center;
    gap: 4px;
}
.kd-transport-info {
    color: #94a3b8;
    font-size: 10.5px;
    margin-left: auto;
}

/* 60-Second Finding Map Table */
.kd-map-card {
    background: #081225;
    border: 1px solid #1a2a44;
    border-radius: 8px;
    padding: 12px 16px;
    overflow-x: auto;
}
.kd-map-title {
    font-size: 12.5px;
    font-weight: 800;
    color: #cbd5e1;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.kd-map-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 11px;
}
.kd-map-table th {
    background: #0d1a30;
    color: #94a3b8;
    padding: 7px 10px;
    text-align: left;
    font-weight: 700;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    border-bottom: 1px solid #1e3352;
}
.kd-map-table td {
    padding: 8px 10px;
    border-bottom: 1px solid #142238;
    color: #cbd5e1;
    vertical-align: middle;
}
.kd-map-table tr {
    transition: background 0.15s ease;
}
.kd-map-table tr:hover {
    background: #0d1e38;
}
.kd-map-table .num {
    font-weight: 800;
    color: #38bdf8;
    font-size: 11px;
    width: 24px;
}
.kd-map-table .finding {
    font-weight: 700;
    color: #fff;
    white-space: nowrap;
}
.kd-map-table .surprise {
    color: #e2e8f0;
    font-family: monospace;
    font-size: 10.5px;
}
.kd-map-table .decision {
    color: #94a3b8;
    font-size: 10.5px;
}

/* Visual Signal Cards & Grids */
.kd-grid-3 {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
}
.kd-grid-4 {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
}
.kd-section-divider-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 6px;
    margin-bottom: 2px;
}
.kd-sec-pill {
    background: #1e3352;
    color: #93c5fd;
    font-size: 10.5px;
    font-weight: 800;
    padding: 4px 10px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.kd-sec-label {
    font-size: 12px;
    font-weight: 700;
    color: #cbd5e1;
}

.kd-v-card {
    background: #081225;
    border: 1px solid #1a2a44;
    border-radius: 8px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 10px;
}
.kd-v-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 8px;
}
.kd-v-card-title-row {
    display: flex;
    align-items: baseline;
    gap: 8px;
}
.kd-v-card-num {
    background: #1d4ed8;
    color: #fff;
    font-size: 11px;
    font-weight: 800;
    border-radius: 50%;
    width: 20px;
    height: 20px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.kd-v-card-title {
    font-size: 12.5px;
    font-weight: 800;
    color: #ffffff;
    margin: 0;
}
.kd-v-card-sub {
    font-size: 10px;
    color: #94a3b8;
    line-height: 1.35;
    margin-top: 3px;
}
.kd-v-card-btn {
    background: #0f1c30;
    border: 1px solid #233857;
    color: #60a5fa;
    font-size: 10px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 4px;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.15s ease;
}
.kd-v-card-btn:hover {
    background: #1d4ed8;
    color: #ffffff;
    border-color: #3b82f6;
}

/* Big Hero Stat inside Card */
.kd-v-hero-stat-box {
    text-align: center;
    background: #0b172a;
    border: 1px solid #16263e;
    border-radius: 6px;
    padding: 8px 10px;
}
.kd-v-hero-stat-val {
    font-size: 16px;
    font-weight: 850;
    color: #f87171;
    font-family: monospace;
}
.kd-v-hero-stat-ctx {
    font-size: 9.5px;
    color: #94a3b8;
    margin-top: 2px;
}

/* Card mini tables */
.kd-mini-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 10px;
}
.kd-mini-table th {
    background: #0d1a30;
    color: #94a3b8;
    padding: 4px 6px;
    text-align: center;
    font-size: 9px;
    font-weight: 700;
    border: 1px solid #16263e;
}
.kd-mini-table td {
    padding: 5px 6px;
    border: 1px solid #16263e;
    text-align: center;
    font-family: monospace;
}
.kd-cell-heat-red-strong { background: rgba(239, 68, 68, 0.45); color: #fca5a5; font-weight: 800; }
.kd-cell-heat-red-med { background: rgba(239, 68, 68, 0.25); color: #fecaca; }
.kd-cell-heat-blue { background: rgba(59, 130, 246, 0.15); color: #93c5fd; }
.kd-cell-heat-dark { background: rgba(15, 28, 48, 0.6); color: #94a3b8; }

/* Decision box */
.kd-decision-callout {
    background: #0b1524;
    border-left: 3px solid #f59e0b;
    padding: 6px 8px;
    border-radius: 0 4px 4px 0;
    font-size: 9.5px;
    line-height: 1.35;
    color: #cbd5e1;
}
.kd-decision-callout b {
    color: #fbbf24;
}

/* Footer of card */
.kd-v-card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 6px;
    border-top: 1px solid #16263e;
    font-size: 9px;
}

/* 4-Stage Horizontal Chain */
.kd-h-chain {
    display: flex;
    align-items: center;
    gap: 4px;
    background: #091322;
    border: 1px solid #16263e;
    border-radius: 6px;
    padding: 6px;
}
.kd-h-stage {
    flex: 1;
    background: #0d1a30;
    border: 1px solid #1e3352;
    border-radius: 4px;
    padding: 6px 8px;
    font-size: 9px;
}
.kd-h-stage-num {
    font-size: 8px;
    color: #38bdf8;
    font-weight: 800;
    text-transform: uppercase;
}
.kd-h-stage-title {
    font-weight: 700;
    color: #fff;
    margin: 1px 0;
}
.kd-h-stage-body {
    color: #94a3b8;
    line-height: 1.25;
}
.kd-h-arrow {
    color: #60a5fa;
    font-size: 14px;
    font-weight: 900;
    padding: 0 2px;
}

/* SECTION 2 DIVIDER / JUMP TO EXPLORER */
.kd-explorer-transition-bar {
    background: linear-gradient(90deg, #0b172a 0%, #172554 50%, #0b172a 100%);
    border: 1px solid #2563eb;
    border-radius: 8px;
    padding: 12px 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 8px;
    box-shadow: 0 4px 16px rgba(37, 99, 235, 0.15);
}
.kd-explorer-transition-title {
    font-size: 14px;
    font-weight: 850;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 8px;
}
.kd-explorer-transition-sub {
    font-size: 11px;
    color: #93c5fd;
    margin-top: 2px;
}

/* 10-Page Explorer Split Layout (Bottom Section) */
.kd-subpage-container {
    display: flex;
    gap: 14px;
    align-items: stretch;
    min-height: 750px;
}
.kd-subnav-rail {
    width: 260px;
    min-width: 260px;
    max-width: 260px;
    background: #081225;
    border: 1px solid #1a2a44;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}
.kd-subnav-header {
    padding: 12px 14px;
    background: #0c182e;
    border-bottom: 1px solid #1a2a44;
    font-size: 11px;
    font-weight: 800;
    color: #cbd5e1;
    display: flex;
    justify-content: space-between;
    align-items: center;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.kd-subnav-list {
    flex: 1;
    overflow-y: auto;
    padding: 6px;
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.kd-subnav-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 9px 10px;
    border-radius: 6px;
    border: 1px solid transparent;
    background: transparent;
    cursor: pointer;
    transition: all 0.15s ease;
    text-align: left;
}
.kd-subnav-item:hover {
    background: #0f1c30;
    border-color: #1e3352;
}
.kd-subnav-item.active {
    background: #11223d;
    border-color: #3b82f6;
    box-shadow: 0 0 10px rgba(59, 130, 246, 0.25);
}
.kd-subnav-num {
    font-size: 11px;
    font-weight: 800;
    color: #38bdf8;
    background: #0a1628;
    border: 1px solid #1e3352;
    border-radius: 4px;
    width: 22px;
    height: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.kd-subnav-item.active .kd-subnav-num {
    background: #1d4ed8;
    color: #fff;
    border-color: #3b82f6;
}
.kd-subnav-info {
    flex: 1;
    min-width: 0;
}
.kd-subnav-title {
    font-size: 11px;
    font-weight: 700;
    color: #e2e8f0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.3;
}
.kd-subnav-item.active .kd-subnav-title {
    color: #60a5fa;
}
.kd-subnav-cat {
    font-size: 9px;
    color: #64748b;
    margin-top: 2px;
}
.kd-subnav-stat {
    font-size: 9.5px;
    color: #94a3b8;
    margin-top: 3px;
    font-family: monospace;
}

/* Main Finding Sub-Page Area */
.kd-subpage-content {
    flex: 1;
    min-width: 0;
    background: #081225;
    border: 1px solid #1a2a44;
    border-radius: 8px;
    padding: 16px 20px;
    display: flex;
    flex-direction: column;
    gap: 14px;
}

/* Page Header */
.kd-page-header {
    border-bottom: 1px solid #16263e;
    padding-bottom: 12px;
}
.kd-page-header-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}
.kd-page-title-row {
    display: flex;
    align-items: center;
    gap: 10px;
}
.kd-page-title {
    font-size: 20px;
    font-weight: 850;
    color: #ffffff;
    margin: 0;
    letter-spacing: -0.3px;
}
.kd-category-chip {
    background: #0f1c30;
    border: 1px solid #233857;
    color: #38bdf8;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 9.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.kd-page-one-line {
    font-size: 13px;
    color: #cbd5e1;
    font-weight: 600;
    line-height: 1.45;
    margin: 0;
}

/* Row A: Key Finding, Why It Matters, Confidence */
.kd-row-a {
    display: grid;
    grid-template-columns: 1.2fr 1.3fr 0.9fr;
    gap: 12px;
}
.kd-card-hero {
    background: #0b172a;
    border: 1px solid #1e3352;
    border-radius: 8px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.kd-card-hero-header {
    font-size: 10px;
    font-weight: 800;
    color: #38bdf8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.kd-hero-points {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.kd-hero-point-row {
    display: flex;
    align-items: baseline;
    gap: 10px;
}
.kd-hero-val {
    font-size: 20px;
    font-weight: 850;
    font-family: monospace;
    min-width: 80px;
}
.kd-hero-desc {
    flex: 1;
}
.kd-hero-label {
    font-size: 11px;
    font-weight: 700;
    color: #fff;
    line-height: 1.3;
}
.kd-hero-sub {
    font-size: 9.5px;
    color: #94a3b8;
    margin-top: 1px;
}

.kd-card-why {
    background: #0b172a;
    border: 1px solid #1e3352;
    border-radius: 8px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 11.5px;
    line-height: 1.5;
    color: #cbd5e1;
}
.kd-card-why-title {
    font-size: 10px;
    font-weight: 800;
    color: #f59e0b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.kd-card-conf {
    background: #0b172a;
    border: 1px solid #1e3352;
    border-radius: 8px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 8px;
}
.kd-conf-title {
    font-size: 10px;
    font-weight: 800;
    color: #10b981;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.kd-conf-badges {
    display: flex;
    flex-direction: column;
    gap: 6px;
}
.kd-conf-badge-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 10px;
}
.kd-conf-note {
    font-size: 9px;
    color: #94a3b8;
    line-height: 1.35;
    border-top: 1px dashed #16263e;
    padding-top: 6px;
}

/* Row B: Scope & Quick Comparison */
.kd-row-b {
    display: grid;
    grid-template-columns: 1fr 1.6fr;
    gap: 12px;
}
.kd-card-scope {
    background: #0b172a;
    border: 1px solid #1e3352;
    border-radius: 8px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.kd-scope-sec-title {
    font-size: 10px;
    font-weight: 800;
    color: #cbd5e1;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}
.kd-scope-dots-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 6px;
}
.kd-scope-dot-pill {
    background: #0f1c30;
    border: 1px solid #1a2a44;
    border-radius: 4px;
    padding: 4px 8px;
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 10px;
}
.kd-scope-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
}
.kd-scope-dot.measured { background: #10b981; box-shadow: 0 0 6px #10b981; }
.kd-scope-dot.not-measured { background: #475569; }

.kd-card-comp {
    background: #0b172a;
    border: 1px solid #1e3352;
    border-radius: 8px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}
.kd-comp-title {
    font-size: 10px;
    font-weight: 800;
    color: #38bdf8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.kd-comp-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 10.5px;
}
.kd-comp-table th {
    background: #0f1c30;
    color: #94a3b8;
    padding: 5px 8px;
    text-align: left;
    font-weight: 700;
    border-bottom: 1px solid #1e3352;
}
.kd-comp-table td {
    padding: 6px 8px;
    border-bottom: 1px solid #16263e;
    color: #e2e8f0;
    font-family: monospace;
    font-size: 10px;
}
.kd-comp-table tr:hover {
    background: #0f1e36;
}

/* Row C: Visuals (Primary + Secondary Charts) */
.kd-row-c {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}
.kd-row-c.full-width {
    grid-template-columns: 1fr;
}
.kd-card-visual {
    background: #0b172a;
    border: 1px solid #1e3352;
    border-radius: 8px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.kd-visual-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.kd-visual-title {
    font-size: 11px;
    font-weight: 800;
    color: #fff;
}
.kd-chart-container {
    position: relative;
    height: 250px;
    width: 100%;
}

/* Row D: Takeaways & Decision Changed */
.kd-row-d {
    display: grid;
    grid-template-columns: 1.2fr 1fr;
    gap: 12px;
}
.kd-card-takeaways {
    background: #0b172a;
    border: 1px solid #1e3352;
    border-radius: 8px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}
.kd-takeaways-title {
    font-size: 10px;
    font-weight: 800;
    color: #38bdf8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.kd-takeaways-list {
    margin: 0;
    padding-left: 16px;
    font-size: 10.5px;
    line-height: 1.5;
    color: #cbd5e1;
}
.kd-takeaways-list li {
    margin-bottom: 4px;
}

.kd-card-decision {
    background: linear-gradient(135deg, #1e1b4b 0%, #0b172a 100%);
    border: 1px solid #4338ca;
    border-radius: 8px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 8px;
}
.kd-decision-header {
    font-size: 10.5px;
    font-weight: 850;
    color: #a5b4fc;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.kd-decision-text {
    font-size: 11.5px;
    font-weight: 600;
    color: #ffffff;
    line-height: 1.45;
}
.kd-boundary-text {
    font-size: 9.5px;
    color: #94a3b8;
    border-top: 1px dashed #312e81;
    padding-top: 6px;
    line-height: 1.35;
}

/* Floating Modal Subpage */
#kd-deep-subpage-backdrop {
    display: none;
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(4, 9, 20, 0.85);
    backdrop-filter: blur(5px);
    z-index: 99998 !important;
}
#kd-deep-subpage-backdrop.open { display: block !important; }
#kd-deep-subpage-modal {
    display: none;
    position: fixed;
    top: 3%; left: 4%; width: 92%; height: 94%;
    background: #081225;
    border: 1px solid #3b82f6;
    border-radius: 12px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.8), 0 0 20px rgba(59, 130, 246, 0.3);
    z-index: 99999 !important;
    flex-direction: column;
    overflow: hidden;
}
#kd-deep-subpage-modal.open { display: flex !important; }
.kd-modal-top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 16px;
    background: #0b172a;
    border-bottom: 1px solid #1a2a44;
}
"""

def generate_subnav_items(container_prefix=""):
    items_html = ""
    for p in PAGES:
        items_html += f"""
        <button class="kd-subnav-item {'active' if p['id'] == 1 else ''}" id="{container_prefix}subnav-item-{p['id']}" onclick="openFindingSubPage({p['id']}, '{container_prefix}')">
          <div class="kd-subnav-num">{p['num']}</div>
          <div class="kd-subnav-info">
            <div class="kd-subnav-title">{p['title']}</div>
            <div class="kd-subnav-cat">{p['category']}</div>
            <div class="kd-subnav-stat">{p['hero_points'][0]['label']}: <b style="color:{p['hero_points'][0]['color']}">{p['hero_points'][0]['val']}</b></div>
          </div>
        </button>
        """
    return items_html

def render_finding_html(p, prefix=""):
    # Header
    html = f"""
    <div class="kd-page-header">
      <div class="kd-page-header-top">
        <div class="kd-page-title-row">
          <h2 class="kd-page-title">{p['num']}. {p['title']}</h2>
          <span class="kd-category-chip">{p['category']}</span>
        </div>
      </div>
      <p class="kd-page-one-line">{p['one_line']}</p>
    </div>
    """

    # Row A: Key Finding, Why It Matters, Confidence
    hero_rows = ""
    for hp in p['hero_points']:
        hero_rows += f"""
        <div class="kd-hero-point-row">
          <div class="kd-hero-val" style="color:{hp['color']}">{hp['val']}</div>
          <div class="kd-hero-desc">
            <div class="kd-hero-label">{hp['label']}</div>
            <div class="kd-hero-sub">{hp['sub']}</div>
          </div>
        </div>
        """
    
    html += f"""
    <div class="kd-row-a">
      <div class="kd-card-hero">
        <div class="kd-card-hero-header">
          <span>Key Measured Finding</span>
          <span style="font-size:8.5px;color:#94a3b8">{p['hero_label']}</span>
        </div>
        <div class="kd-hero-points">{hero_rows}</div>
      </div>
      <div class="kd-card-why">
        <div class="kd-card-why-title">Why It Matters</div>
        <div>{p['why_matters']}</div>
      </div>
      <div class="kd-card-conf">
        <div>
          <div class="kd-conf-title">Confidence Semantics</div>
          <div class="kd-conf-badges">
            <div class="kd-conf-badge-item">
              <span style="color:#94a3b8">Evidence Metric:</span>
              <span class="badge b-green">{p['confidence']['evidence']}</span>
            </div>
            <div class="kd-conf-badge-item">
              <span style="color:#94a3b8">Causal Mechanism:</span>
              <span class="badge b-amber">{p['confidence']['cause']}</span>
            </div>
          </div>
        </div>
        <div class="kd-conf-note">{p['confidence']['notes']}</div>
      </div>
    </div>
    """

    # Row B: Scope & Quick Comparison
    scope_dots = ""
    for c in p['scope']['contexts']:
        dot_class = "measured" if c['status'] == "MEASURED" else "not-measured"
        scope_dots += f"""
        <div class="kd-scope-dot-pill">
          <span class="kd-scope-dot {dot_class}"></span>
          <span style="font-weight:700;color:#fff">{c['ctx']}</span>
          <span style="font-size:8.5px;color:#94a3b8">{c['label']}</span>
        </div>
        """

    topo_pills = " · ".join([f"<span style='color:#38bdf8'>{t}</span>" for t in p['scope']['topologies']])
    net_pills = " · ".join([f"<span>{n['name']} (<b>{n['iperf']}</b>)</span>" for n in p['scope']['network']])

    th_cols = "".join([f"<th>{h}</th>" for h in p['quick_comp']['headers']])
    tr_rows = ""
    for r in p['quick_comp']['rows']:
        tds = "".join([f"<td>{cell}</td>" for cell in r[:-1]])
        ev_id = r[-1]
        btn = f"<button class='chip' style='padding:2px 6px;cursor:pointer' onclick=\"window.openEvidencePopup('{ev_id}')\">{ev_id} →</button>"
        tr_rows += f"<tr>{tds}<td style='text-align:right'>{btn}</td></tr>"

    html += f"""
    <div class="kd-row-b">
      <div class="kd-card-scope">
        <div>
          <div class="kd-scope-sec-title">Scope — Context Lengths Evaluated</div>
          <div class="kd-scope-dots-grid">{scope_dots}</div>
        </div>
        <div style="font-size:10px;line-height:1.4;border-top:1px dashed #16263e;padding-top:6px">
          <span style="color:#94a3b8">Topologies:</span> {topo_pills}
        </div>
        <div style="font-size:9.5px;color:#94a3b8;border-top:1px dashed #16263e;padding-top:6px">
          <span style="color:#cbd5e1">Transport Provenance:</span> {net_pills}
        </div>
      </div>
      <div class="kd-card-comp">
        <div class="kd-comp-title">
          <span>{p['quick_comp']['title']}</span>
          <span style="font-size:9px;color:#38bdf8">Canonical V8 Verified</span>
        </div>
        <table class="kd-comp-table">
          <thead><tr>{th_cols}</tr></thead>
          <tbody>{tr_rows}</tbody>
        </table>
      </div>
    </div>
    """

    # Row C: Visuals
    cid1 = f"{prefix}chart-p{p['id']}-primary"
    cid2 = f"{prefix}chart-p{p['id']}-secondary"

    if p['id'] == 7:
        # Full width 3-stage chain for #7
        html += f"""
        <div class="kd-row-c full-width">
          <div class="kd-card-visual">
            <div class="kd-visual-header">
              <div class="kd-visual-title">Full 3-Stage Cross-Tool Evidence Chain</div>
              <span class="badge b-purple">Mechanism Traced</span>
            </div>
            <div class="kd-chain-container">
              <div class="kd-chain-steps" style="display:flex;gap:6px;align-items:center;background:#091322;padding:8px;border-radius:6px;border:1px solid #16263e">
                <div class="kd-chain-card" style="flex:1;background:#0d1a30;padding:6px 8px;border-radius:4px;border:1px solid #1e3352">
                  <div style="font-size:8px;color:#38bdf8;font-weight:800">Stage 1: Microbench</div>
                  <div style="font-size:10px;font-weight:700;color:#fff">NCCL AllReduce Test</div>
                  <div style="font-size:9px;color:#94a3b8;margin-top:2px">Small-message latency increases from <b>~19µs</b> (TP4) to <b>~37µs</b> (TP8) due to dual-socket PCIe bridge traversal (~1.9–2.2× latency).</div>
                </div>
                <div style="color:#60a5fa;font-size:14px;font-weight:900">→</div>
                <div class="kd-chain-card" style="flex:1;background:#0d1a30;padding:6px 8px;border-radius:4px;border:1px solid #1e3352">
                  <div style="font-size:8px;color:#38bdf8;font-weight:800">Stage 2: PyTorch Profiler @ 8K</div>
                  <div style="font-size:10px;font-weight:700;color:#fff">nccl:all_reduce Self CUDA</div>
                  <div style="font-size:9px;color:#94a3b8;margin-top:2px">Rises from <b>251.529 ms</b> (TP4) to <b>583.866 ms</b> (TP8) with exact same <b>7,040 AllReduce calls</b> (~2.32× overhead).</div>
                </div>
                <div style="color:#60a5fa;font-size:14px;font-weight:900">→</div>
                <div class="kd-chain-card" style="flex:1;background:#0d1a30;padding:6px 8px;border-radius:4px;border:1px solid #1e3352">
                  <div style="font-size:8px;color:#38bdf8;font-weight:800">Stage 3: E2E Serving</div>
                  <div style="font-size:10px;font-weight:700;color:#fff">Interactive TPOT Penalty</div>
                  <div style="font-size:9px;color:#94a3b8;margin-top:2px">Direct user penalty: <b>+41.9%</b> at 8K (4.48ms → 6.35ms), <b>+39.0%</b> at 128K, <b>+25.0%</b> at 512K, <b>+17.9%</b> at 1M.</div>
                </div>
              </div>
              <div style="margin-top:10px">
                <div class="kd-visual-title" style="margin-bottom:6px">{p['chart_secondary_title']}</div>
                <div class="kd-chart-container" style="height:210px">
                  <canvas id="{cid2}"></canvas>
                </div>
              </div>
            </div>
          </div>
        </div>
        """
    else:
        html += f"""
        <div class="kd-row-c">
          <div class="kd-card-visual">
            <div class="kd-visual-header">
              <div class="kd-visual-title">{p['chart_primary_title']}</div>
              <span class="badge b-cyan">Primary Visual</span>
            </div>
            <div class="kd-chart-container">
              <canvas id="{cid1}"></canvas>
            </div>
          </div>
          <div class="kd-card-visual">
            <div class="kd-visual-header">
              <div class="kd-visual-title">{p['chart_secondary_title']}</div>
              <span class="badge b-green">Secondary Evidence</span>
            </div>
            <div class="kd-chart-container">
              <canvas id="{cid2}"></canvas>
            </div>
          </div>
        </div>
        """

    # Row D: Takeaways & Decision Changed
    takeaways_li = "".join([f"<li>{t}</li>" for t in p['takeaways']])
    html += f"""
    <div class="kd-row-d">
      <div class="kd-card-takeaways">
        <div class="kd-takeaways-title">Key Architectural Takeaways</div>
        <ul class="kd-takeaways-list">{takeaways_li}</ul>
      </div>
      <div class="kd-card-decision">
        <div>
          <div class="kd-decision-header">
            <span>&#9889;</span> Architectural Decision Changed
          </div>
          <div class="kd-decision-text">{p['decision_changed']}</div>
        </div>
        <div class="kd-boundary-text">
          <b style="color:#f87171">Boundary:</b> {p['boundary']}
        </div>
      </div>
    </div>
    """
    return html

def generate_keydiscoveries_tab_html():
    nav_rail_html = generate_subnav_items(container_prefix="")
    modal_rail_html = generate_subnav_items(container_prefix="modal-")
    p1_initial_content = render_finding_html(PAGES[0], prefix="")

    markup = f"""
<!-- KEY DISCOVERIES TAB (UNIFIED SINGLE-PAGE SIGNAL LAYOUT & EMBEDDED 10-PAGE EXPLORER) -->
<section class="tabpage" id="keydiscoveries">
  <div class="kd-container">

    <!-- 1. HEADER BANNER & TRUST STRIP -->
    <div class="kd-header-banner">
      <div class="kd-header-top">
        <div class="kd-title-group">
          <h1>Key Deployment Findings</h1>
          <p>Ten evidence-backed findings from the V8 characterization campaign. Start with the measured signal, scroll down to explore deep empirical pages, or click any card for immediate modal inspection.</p>
        </div>
      </div>
      <div class="kd-trust-strip">
        <div class="kd-model-pill">Kimi-Linear 48B surrogate &middot; BF16 &middot; 16&times; RTX PRO 6000 Blackwell</div>
        <div class="kd-stat-item">
          <span class="kd-stat-num">119/126</span>
          <span class="kd-stat-label">application rows complete</span>
        </div>
        <div class="kd-stat-item">
          <span class="kd-stat-num">14/22</span>
          <span class="kd-stat-label">distributed profiles complete</span>
        </div>
        <div class="kd-badge-validated">
          <span>&#10004;</span> E2E RUN MATRIX VALIDATED
        </div>
        <div class="kd-badge-warning">
          <span>&#9888;</span> STRICT SUITE SIGN-OFF INCOMPLETE
        </div>
        <div class="kd-transport-info">
          Measured transport: <b>Native 173.58 Gb/s</b> &middot; <b>100G 56.84 Gb/s</b> &middot; <b>20G 16.48 Gb/s</b>
        </div>
      </div>
    </div>

    <!-- 2. 60-SECOND FINDING MAP TABLE -->
    <div class="kd-map-card">
      <div class="kd-map-title">
        <span>&#128506;</span> 60-second Finding Map (Click any row to open full 10-page explorer)
      </div>
      <table class="kd-map-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Finding</th>
            <th>Measured surprise</th>
            <th>Decision</th>
            <th style="text-align:right">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr onclick="openFindingModal(1)" style="cursor:pointer">
            <td class="num">1</td>
            <td class="finding">Fabric Exposure</td>
            <td class="surprise">1M/20G: TP16/PP1 +276.7% TTFT vs TP4/PP4 +3.9%</td>
            <td class="decision">Topology controls exposed fabric risk</td>
            <td style="text-align:right"><button class="chip" onclick="event.stopPropagation(); openFindingModal(1)">View Details &rarr;</button></td>
          </tr>
          <tr onclick="openFindingModal(2)" style="cursor:pointer">
            <td class="num">2</td>
            <td class="finding">Concurrency</td>
            <td class="surprise">1M TP4 c1&rarr;c4: +1.52% output TPS, 2.48&times; TTFT, 26.15&times; TPOT</td>
            <td class="decision">Admission from queue/latency SLO, not memory fit</td>
            <td style="text-align:right"><button class="chip" onclick="event.stopPropagation(); openFindingModal(2)">View Details &rarr;</button></td>
          </tr>
          <tr onclick="openFindingModal(3)" style="cursor:pointer">
            <td class="num">3</td>
            <td class="finding">Long Context</td>
            <td class="surprise">128K&rarr;512K: Attention ~15.7&times;, NCCL ~2.18&times;, KDA ~3.9&times;, MoE ~3.8&times;</td>
            <td class="decision">Optimization target shifts with context</td>
            <td style="text-align:right"><button class="chip" onclick="event.stopPropagation(); openFindingModal(3)">View Details &rarr;</button></td>
          </tr>
          <tr onclick="openFindingModal(4)" style="cursor:pointer">
            <td class="num">4</td>
            <td class="finding">Prefix Reuse</td>
            <td class="surprise">1M: first/cold 94.2272 s &rarr; repeat-hit median 2.6140 s (~36.0&times;)</td>
            <td class="decision">Repeated-prefix traffic is a different latency regime</td>
            <td style="text-align:right"><button class="chip" onclick="event.stopPropagation(); openFindingModal(4)">View Details &rarr;</button></td>
          </tr>
          <tr onclick="openFindingModal(5)" style="cursor:pointer">
            <td class="num">5</td>
            <td class="finding">Prompt Tokens</td>
            <td class="surprise">High-load normalized input rate: 8K ~27.5K tok/s vs 128K ~24.2K tok/s</td>
            <td class="decision">Compare prefill-heavy demand in tokens/s, not only req/s</td>
            <td style="text-align:right"><button class="chip" onclick="event.stopPropagation(); openFindingModal(5)">View Details &rarr;</button></td>
          </tr>
          <tr onclick="openFindingModal(6)" style="cursor:pointer">
            <td class="num">6</td>
            <td class="finding">Parallelism Frontier</td>
            <td class="surprise">1M GPU-s/request frontier: TP4/PP1 373.0 &rarr; TP4/PP2 420.2 &rarr; TP4/PP4 457.1</td>
            <td class="decision">Show latency/resource frontier, not one winner</td>
            <td style="text-align:right"><button class="chip" onclick="event.stopPropagation(); openFindingModal(6)">View Details &rarr;</button></td>
          </tr>
          <tr onclick="openFindingModal(7)" style="cursor:pointer">
            <td class="num">7</td>
            <td class="finding">TP Decode</td>
            <td class="surprise">Same 7040 AllReduce calls; TP8 rank-local Self CUDA 583.866 ms vs TP4 251.529 ms; 8K TPOT 6.3500 ms vs 4.4748 ms</td>
            <td class="decision">Wider TP can hurt interactive decode</td>
            <td style="text-align:right"><button class="chip" onclick="event.stopPropagation(); openFindingModal(7)">View Details &rarr;</button></td>
          </tr>
          <tr onclick="openFindingModal(8)" style="cursor:pointer">
            <td class="num">8</td>
            <td class="finding">Runtime Knobs</td>
            <td class="surprise">max_num_seqs 4/8/16: 232.342 / 233.364 / 232.250 s; chunk 4K&rarr;8K&rarr;16K: 122.049 &rarr; 93.277 &rarr; 88.951 s</td>
            <td class="decision">Tune only knobs with measured derivative</td>
            <td style="text-align:right"><button class="chip" onclick="event.stopPropagation(); openFindingModal(8)">View Details &rarr;</button></td>
          </tr>
          <tr onclick="openFindingModal(9)" style="cursor:pointer">
            <td class="num">9</td>
            <td class="finding">Busy GPU</td>
            <td class="surprise">1M: TP4/PP4 62.8% util @ 28.568 s vs TP16/PP1 80.6% util @ 68.197 s</td>
            <td class="decision">GPU busy &ne; efficient serving</td>
            <td style="text-align:right"><button class="chip" onclick="event.stopPropagation(); openFindingModal(9)">View Details &rarr;</button></td>
          </tr>
          <tr onclick="openFindingModal(10)" style="cursor:pointer">
            <td class="num">10</td>
            <td class="finding">KV vs VRAM</td>
            <td class="surprise">1M TP4/PP4: 2.75% peak KV vs 88.83 GiB peak GPU memory</td>
            <td class="decision">KV pressure and VRAM headroom are different metrics</td>
            <td style="text-align:right"><button class="chip" onclick="event.stopPropagation(); openFindingModal(10)">View Details &rarr;</button></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 3. ROW 1: CARDS 1, 2, 3 (FABRIC EXPOSURE, CONCURRENCY, LONG CONTEXT) -->
    <div class="kd-grid-3">
      <!-- Card 1: Fabric Exposure Fingerprint -->
      <div class="kd-v-card">
        <div>
          <div class="kd-v-card-header">
            <div>
              <div class="kd-v-card-title-row">
                <span class="kd-v-card-num">1</span>
                <h3 class="kd-v-card-title">Fabric Exposure Fingerprint</h3>
              </div>
              <div class="kd-v-card-sub">The same measured fabric constraint produces radically different TTFT damage depending on topology.</div>
            </div>
            <button class="kd-v-card-btn" onclick="openFindingModal(1)">View Details &rarr;</button>
          </div>

          <div class="kd-v-hero-stat-box" style="margin:8px 0">
            <div class="kd-v-hero-stat-val">+276.7% vs +3.9% TTFT</div>
            <div class="kd-v-hero-stat-ctx">1M c1 TTFT degradation under 20G condition</div>
          </div>

          <!-- Heatmap Table -->
          <div style="font-size:9.5px;font-weight:700;color:#94a3b8;margin-bottom:4px">20G TTFT Degradation vs Native (&Delta;%)</div>
          <table class="kd-mini-table" style="margin-bottom:8px">
            <thead>
              <tr>
                <th style="text-align:left">Config</th>
                <th>128K</th>
                <th>512K</th>
                <th>1M</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style="text-align:left;font-weight:700">TP4/PP2</td>
                <td class="kd-cell-heat-blue">+8.0%</td>
                <td class="kd-cell-heat-blue">+2.4%</td>
                <td class="kd-cell-heat-blue">+1.1%</td>
              </tr>
              <tr>
                <td style="text-align:left;font-weight:700">TP8/PP2</td>
                <td class="kd-cell-heat-blue">+0.8%</td>
                <td class="kd-cell-heat-dark">-0.2%</td>
                <td class="kd-cell-heat-dark">-0.1%</td>
              </tr>
              <tr>
                <td style="text-align:left;font-weight:700">TP4/PP4</td>
                <td class="kd-cell-heat-blue">+14.7%</td>
                <td class="kd-cell-heat-blue">+8.9%</td>
                <td class="kd-cell-heat-blue">+3.9%</td>
              </tr>
              <tr>
                <td style="text-align:left;font-weight:700;color:#f87171">TP16/PP1</td>
                <td class="kd-cell-heat-red-strong">+383.7%</td>
                <td class="kd-cell-heat-red-strong">+333.0%</td>
                <td class="kd-cell-heat-red-strong">+276.7%</td>
              </tr>
            </tbody>
          </table>

          <!-- Transport Measurements -->
          <div style="font-size:9px;font-weight:700;color:#94a3b8;margin-bottom:4px">Transport Layer Measurements</div>
          <table class="kd-mini-table">
            <thead>
              <tr>
                <th style="text-align:left">Condition</th>
                <th>Native</th>
                <th>100G</th>
                <th>20G</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style="text-align:left">Measured iperf (Gb/s)</td>
                <td>173.58</td>
                <td>56.84</td>
                <td>16.48</td>
              </tr>
              <tr>
                <td style="text-align:left">Measured 256M SendRecv</td>
                <td>~7.11 GB/s</td>
                <td>~5.54 GB/s</td>
                <td>~2.04 GB/s</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div>
          <div class="kd-decision-callout" style="margin-top:6px">
            <b>Decision changed:</b> Choose scale-out topology from measured application exposure to transport degradation, not from NIC/iperf alone.
          </div>
          <div class="kd-v-card-footer">
            <span class="badge b-green">Evidence HIGH</span>
            <span class="badge b-amber">Cause MED-HIGH</span>
            <button class="chip" style="cursor:pointer" onclick="scrollToKdExplorer(1)">Inspect Evidence &darr;</button>
          </div>
        </div>
      </div>

      <!-- Card 2: Concurrency Value Destruction -->
      <div class="kd-v-card">
        <div>
          <div class="kd-v-card-header">
            <div>
              <div class="kd-v-card-title-row">
                <span class="kd-v-card-num">2</span>
                <h3 class="kd-v-card-title">Concurrency Value Destruction</h3>
              </div>
              <div class="kd-v-card-sub">At 1M, concurrency spends latency but buys almost no output throughput.</div>
            </div>
            <button class="kd-v-card-btn" onclick="openFindingModal(2)">View Details &rarr;</button>
          </div>

          <div class="kd-v-hero-stat-box" style="margin:8px 0">
            <div class="kd-v-hero-stat-val">+1.52% Output TPS &middot; 2.48&times; TTFT</div>
            <div class="kd-v-hero-stat-ctx" style="color:#fbbf24;font-weight:700">26.15&times; TPOT &middot; 134.43 s Queue</div>
          </div>

          <!-- Concurrency Table -->
          <table class="kd-mini-table" style="margin-bottom:8px">
            <thead>
              <tr>
                <th style="text-align:left">Metric</th>
                <th>c1</th>
                <th>c2</th>
                <th>c4</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style="text-align:left">Output TPS</td>
                <td>0.34147</td>
                <td>0.34486 (+0.99%)</td>
                <td style="color:#4ade80;font-weight:700">0.34666 (+1.52%)</td>
              </tr>
              <tr>
                <td style="text-align:left">TTFT</td>
                <td>93.395 s</td>
                <td>139.374 s (1.49&times;)</td>
                <td style="color:#f87171;font-weight:700">231.268 s (2.48&times;)</td>
              </tr>
              <tr>
                <td style="text-align:left">TPOT</td>
                <td>10.228 ms</td>
                <td>181.974 ms (17.79&times;)</td>
                <td style="color:#f87171;font-weight:700">267.411 ms (26.15&times;)</td>
              </tr>
              <tr>
                <td style="text-align:left">Queue time</td>
                <td>~0 s</td>
                <td>44.340 s</td>
                <td style="color:#f87171;font-weight:700">134.428 s</td>
              </tr>
              <tr>
                <td style="text-align:left">Peak KV usage</td>
                <td>12.29%</td>
                <td>15.52%</td>
                <td>15.51%</td>
              </tr>
            </tbody>
          </table>

          <!-- Queue Accounting Closure -->
          <div style="background:#091322;border:1px solid #16263e;border-radius:4px;padding:5px 8px;font-size:9px">
            <span style="color:#94a3b8;font-weight:700">Queue-accounting closure (measured vs predicted):</span>
            <div style="display:flex;justify-content:space-between;margin-top:3px;font-family:monospace;color:#38bdf8">
              <span>TP4 c2: <b>96.4%</b></span>
              <span>TP4 c4: <b>97.5%</b></span>
              <span>TP8 c2: <b>95.7%</b></span>
              <span>TP8 c4: <b>97.2%</b></span>
            </div>
          </div>
        </div>

        <div>
          <div class="kd-decision-callout" style="margin-top:6px">
            <b>Decision changed:</b> Define admission from TTFT/TPOT/queue SLOs; 'fits in KV' is not the production-capacity criterion.
          </div>
          <div class="kd-v-card-footer">
            <span class="badge b-green">Evidence HIGH</span>
            <span class="badge b-amber">Cause HIGH / MED</span>
            <button class="chip" style="cursor:pointer" onclick="scrollToKdExplorer(2)">Inspect Evidence &darr;</button>
          </div>
        </div>
      </div>

      <!-- Card 3: Long-Context Resource-Pressure Shift -->
      <div class="kd-v-card">
        <div>
          <div class="kd-v-card-header">
            <div>
              <div class="kd-v-card-title-row">
                <span class="kd-v-card-num">3</span>
                <h3 class="kd-v-card-title">Long-Context Resource-Pressure Shift</h3>
              </div>
              <div class="kd-v-card-sub">As context grows, full-attention work accelerates much faster than KDA, MoE, or NCCL in matched profiles.</div>
            </div>
            <button class="kd-v-card-btn" onclick="openFindingModal(3)">View Details &rarr;</button>
          </div>

          <!-- SVG Growth Slope Chart -->
          <div style="background:#070f1e;border:1px solid #16263e;border-radius:6px;padding:8px;margin:6px 0">
            <div style="display:flex;justify-content:space-between;align-items:center;font-size:9.5px;font-weight:700;color:#94a3b8;margin-bottom:4px">
              <span>GPU Work Growth (128K &rarr; 512K)</span>
              <span style="font-size:8px;color:#38bdf8">Log scale</span>
            </div>
            <svg viewBox="0 0 320 135" style="width:100%;height:135px;display:block">
              <!-- Grid lines -->
              <line x1="45" y1="20" x2="310" y2="20" stroke="#16263e" stroke-dasharray="2,2"/>
              <line x1="45" y1="65" x2="310" y2="65" stroke="#16263e" stroke-dasharray="2,2"/>
              <line x1="45" y1="110" x2="310" y2="110" stroke="#16263e"/>
              <!-- Axis labels -->
              <text x="35" y="24" fill="#64748b" font-size="8.5" text-anchor="end" font-family="monospace">100x</text>
              <text x="35" y="69" fill="#64748b" font-size="8.5" text-anchor="end" font-family="monospace">10x</text>
              <text x="35" y="113" fill="#64748b" font-size="8.5" text-anchor="end" font-family="monospace">1x</text>
              <text x="65" y="126" fill="#94a3b8" font-size="9" text-anchor="middle">128K</text>
              <text x="210" y="126" fill="#94a3b8" font-size="9" text-anchor="middle">512K</text>
              <!-- 1. Full attention: 1x -> 15.7x (exp 1.99) -->
              <line x1="65" y1="110" x2="210" y2="35" stroke="#ef4444" stroke-width="2.5"/>
              <circle cx="65" cy="110" r="3" fill="#ef4444"/>
              <circle cx="210" cy="35" r="3.5" fill="#ef4444"/>
              <text x="216" y="38" fill="#ef4444" font-size="8.5" font-weight="bold">Full attention 15.7&times; (exp 1.99)</text>
              <!-- 2. GEMM family: 1x -> 5.25x (exp 1.20) -->
              <line x1="65" y1="110" x2="210" y2="60" stroke="#3b82f6" stroke-width="2"/>
              <circle cx="210" cy="60" r="3" fill="#3b82f6"/>
              <text x="216" y="63" fill="#60a5fa" font-size="8.5">GEMM 5.25&times; (exp 1.20)</text>
              <!-- 3. KDA: 1x -> 3.9x (exp 0.99) -->
              <line x1="65" y1="110" x2="210" y2="76" stroke="#10b981" stroke-width="1.8"/>
              <circle cx="210" cy="76" r="3" fill="#10b981"/>
              <text x="216" y="79" fill="#34d399" font-size="8.5">KDA 3.9&times; (exp 0.99)</text>
              <!-- 4. MoE: 1x -> 3.8x (exp 0.96) -->
              <line x1="65" y1="110" x2="210" y2="88" stroke="#a855f7" stroke-width="1.8"/>
              <circle cx="210" cy="88" r="3" fill="#a855f7"/>
              <text x="216" y="91" fill="#c084fc" font-size="8.5">MoE 3.8&times; (exp 0.96)</text>
              <!-- 5. NCCL: 1x -> 2.18x (exp 0.56) -->
              <line x1="65" y1="110" x2="210" y2="99" stroke="#eab308" stroke-width="1.8"/>
              <circle cx="210" cy="99" r="3" fill="#eab308"/>
              <text x="216" y="102" fill="#facc15" font-size="8.5">NCCL 2.18&times; (exp 0.56)</text>
            </svg>
            <div style="font-size:8px;color:#94a3b8;margin-top:2px">&#9432; Aggregate GPU work &ne; exclusive request wall-clock critical path</div>
          </div>
        </div>

        <div>
          <div class="kd-decision-callout" style="margin-top:6px">
            <b>Decision changed:</b> Do not tune long-context serving from a single 128K profile; re-evaluate optimization target as context increases.
          </div>
          <div class="kd-v-card-footer">
            <span class="badge b-green">Evidence HIGH</span>
            <span class="badge b-amber">Cause MEDIUM</span>
            <button class="chip" style="cursor:pointer" onclick="scrollToKdExplorer(3)">Inspect Evidence &darr;</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 4. SECTION 2: OPTIMIZATION & REUSE (CARDS 4, 5, 6, 7) -->
    <div class="kd-section-divider-bar">
      <span class="kd-sec-pill"><span>&#9881;</span> Optimization &amp; Reuse</span>
      <span class="kd-sec-label">Prefix Caching, Pareto Trade-offs, Token Rates &amp; Knobs (Findings 4 &ndash; 7)</span>
    </div>

    <div class="kd-grid-4">
      <!-- Card 4: Prefix Reuse Changes the Curve -->
      <div class="kd-v-card">
        <div>
          <div class="kd-v-card-header">
            <div>
              <div class="kd-v-card-title-row">
                <span class="kd-v-card-num">4</span>
                <h3 class="kd-v-card-title">Prefix Reuse Changes Curve</h3>
              </div>
              <div class="kd-v-card-sub">Repeated-prefix traffic is a completely different latency regime.</div>
            </div>
            <button class="kd-v-card-btn" onclick="openFindingModal(4)">View Details &rarr;</button>
          </div>

          <table class="kd-mini-table" style="margin:8px 0">
            <thead>
              <tr>
                <th style="text-align:left">Context</th>
                <th>Cold TTFT</th>
                <th>Repeat Hit</th>
                <th>Speedup</th>
                <th>Counters</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style="text-align:left;font-weight:700">128K</td>
                <td>4.8965 s</td>
                <td>0.3307 s</td>
                <td style="color:#4ade80;font-weight:700">~14.8&times;</td>
                <td>87.33%</td>
              </tr>
              <tr>
                <td style="text-align:left;font-weight:700">512K</td>
                <td>32.5762 s</td>
                <td>1.1679 s</td>
                <td style="color:#4ade80;font-weight:700">~27.9&times;</td>
                <td>49.98%</td>
              </tr>
              <tr>
                <td style="text-align:left;font-weight:700;color:#38bdf8">1M</td>
                <td>94.2272 s</td>
                <td style="color:#4ade80;font-weight:700">2.6140 s</td>
                <td style="color:#4ade80;font-weight:800">~36.0&times;</td>
                <td>49.97%</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div>
          <div class="kd-decision-callout">
            <b>Decision changed:</b> Treat repeated-prefix traffic as a distinct workload class.
          </div>
          <div class="kd-v-card-footer">
            <span class="badge b-green">Evidence HIGH</span>
            <button class="chip" style="cursor:pointer" onclick="scrollToKdExplorer(4)">Inspect &darr;</button>
          </div>
        </div>
      </div>

      <!-- Card 5: Parallelism Frontier (Pareto Chart) -->
      <div class="kd-v-card">
        <div>
          <div class="kd-v-card-header">
            <div>
              <div class="kd-v-card-title-row">
                <span class="kd-v-card-num">5</span>
                <h3 class="kd-v-card-title">Parallelism Frontier</h3>
              </div>
              <div class="kd-v-card-sub">Show latency/resource frontier, not one winner.</div>
            </div>
            <button class="kd-v-card-btn" onclick="openFindingModal(6)">View Details &rarr;</button>
          </div>

          <!-- SVG Pareto Scatter & Frontier Chart -->
          <div style="background:#070f1e;border:1px solid #16263e;border-radius:6px;padding:6px;margin:6px 0">
            <div style="display:flex;justify-content:space-between;font-size:8.5px;color:#94a3b8;margin-bottom:2px">
              <span>1M TTFT (s) vs GPU-s per request</span>
              <span style="color:#f97316;font-weight:700">&#9670; Pareto Frontier</span>
            </div>
            <svg viewBox="0 0 240 120" style="width:100%;height:115px;display:block">
              <!-- Grid & axes -->
              <line x1="30" y1="15" x2="230" y2="15" stroke="#16263e" stroke-dasharray="2,2"/>
              <line x1="30" y1="55" x2="230" y2="55" stroke="#16263e" stroke-dasharray="2,2"/>
              <line x1="30" y1="95" x2="230" y2="95" stroke="#16263e"/>
              <text x="25" y="18" fill="#64748b" font-size="7.5" text-anchor="end" font-family="monospace">100s</text>
              <text x="25" y="58" fill="#64748b" font-size="7.5" text-anchor="end" font-family="monospace">50s</text>
              <text x="25" y="98" fill="#64748b" font-size="7.5" text-anchor="end" font-family="monospace">10s</text>
              <text x="75" y="110" fill="#64748b" font-size="7.5" text-anchor="middle" font-family="monospace">400</text>
              <text x="145" y="110" fill="#64748b" font-size="7.5" text-anchor="middle" font-family="monospace">800</text>
              <text x="215" y="110" fill="#64748b" font-size="7.5" text-anchor="middle" font-family="monospace">1200</text>

              <!-- Pareto Frontier Line: TP4/PP1(373, 93.2) -> TP4/PP2(420, 52.5) -> TP4/PP4(457, 28.6) -->
              <polyline points="70,22 79,53 85,77" fill="none" stroke="#f97316" stroke-width="2"/>
              <!-- Frontier Diamond Points -->
              <polygon points="70,18 73,22 70,26 67,22" fill="#f97316"/>
              <text x="74" y="20" fill="#fed7aa" font-size="7">TP4/PP1 (373s)</text>
              <polygon points="79,49 82,53 79,57 76,53" fill="#f97316"/>
              <text x="83" y="52" fill="#fed7aa" font-size="7">TP4/PP2 (420s)</text>
              <polygon points="85,73 88,77 85,81 82,77" fill="#f97316"/>
              <text x="89" y="80" fill="#fed7aa" font-size="7">TP4/PP4 (457s)</text>

              <!-- Dominated Points -->
              <circle cx="110" cy="38" r="3" fill="#3b82f6"/>
              <text x="115" y="38" fill="#93c5fd" font-size="7">TP8/PP1 (598s)</text>
              <circle cx="140" cy="57" r="3" fill="#3b82f6"/>
              <text x="145" y="58" fill="#93c5fd" font-size="7">TP8/PP2 (767s)</text>
              <circle cx="196" cy="43" r="3" fill="#3b82f6"/>
              <text x="160" y="34" fill="#93c5fd" font-size="7">TP16/PP1 (1091s)</text>
            </svg>
            <div style="font-size:8px;color:#94a3b8;display:flex;justify-content:space-between">
              <span>&#9670; Frontier (TP4/PP1 &rarr; PP2 &rarr; PP4)</span>
              <span>&#9679; Other measured points</span>
            </div>
          </div>
        </div>

        <div>
          <div class="kd-decision-callout">
            <b>Decision changed:</b> Expose latency/resource trade-off instead of naming a universal winner.
          </div>
          <div class="kd-v-card-footer">
            <span class="badge b-green">Evidence HIGH</span>
            <button class="chip" style="cursor:pointer" onclick="scrollToKdExplorer(6)">Inspect &darr;</button>
          </div>
        </div>
      </div>

      <!-- Card 6: Prompt-Token Admission Fingerprint -->
      <div class="kd-v-card">
        <div>
          <div class="kd-v-card-header">
            <div>
              <div class="kd-v-card-title-row">
                <span class="kd-v-card-num">6</span>
                <h3 class="kd-v-card-title">Prompt-Token Admission</h3>
              </div>
              <div class="kd-v-card-sub">Compare prefill-heavy demand in tokens/s, not only req/s.</div>
            </div>
            <button class="kd-v-card-btn" onclick="openFindingModal(5)">View Details &rarr;</button>
          </div>

          <!-- Dual Mini Bar Charts -->
          <div style="background:#070f1e;border:1px solid #16263e;border-radius:6px;padding:6px;margin:6px 0;display:flex;flex-direction:column;gap:6px">
            <div>
              <div style="font-size:8.5px;color:#94a3b8;display:flex;justify-content:space-between">
                <span>Achieved request rate (req/s)</span>
                <span style="color:#f87171;font-weight:700">~18.2&times; gap</span>
              </div>
              <div style="margin-top:3px;display:flex;flex-direction:column;gap:3px">
                <div style="display:flex;align-items:center;gap:6px;font-size:9px">
                  <span style="width:30px;color:#94a3b8">8K</span>
                  <div style="flex:1;background:#0d1a30;height:12px;border-radius:2px;overflow:hidden">
                    <div style="width:85%;background:#38bdf8;height:100%"></div>
                  </div>
                  <span style="width:40px;font-family:monospace;font-weight:700">3.3586</span>
                </div>
                <div style="display:flex;align-items:center;gap:6px;font-size:9px">
                  <span style="width:30px;color:#94a3b8">128K</span>
                  <div style="flex:1;background:#0d1a30;height:12px;border-radius:2px;overflow:hidden">
                    <div style="width:5%;background:#38bdf8;height:100%"></div>
                  </div>
                  <span style="width:40px;font-family:monospace">0.1846</span>
                </div>
              </div>
            </div>

            <div style="border-top:1px dashed #16263e;padding-top:4px">
              <div style="font-size:8.5px;color:#94a3b8;display:flex;justify-content:space-between">
                <span>Achieved input token rate (tok/s)</span>
                <span style="color:#4ade80;font-weight:700">Collapses to ~1.14&times;</span>
              </div>
              <div style="margin-top:3px;display:flex;flex-direction:column;gap:3px">
                <div style="display:flex;align-items:center;gap:6px;font-size:9px">
                  <span style="width:30px;color:#94a3b8">8K</span>
                  <div style="flex:1;background:#0d1a30;height:12px;border-radius:2px;overflow:hidden">
                    <div style="width:75%;background:#10b981;height:100%"></div>
                  </div>
                  <span style="width:45px;font-family:monospace;font-weight:700">~27.5K</span>
                </div>
                <div style="display:flex;align-items:center;gap:6px;font-size:9px">
                  <span style="width:30px;color:#94a3b8">128K</span>
                  <div style="flex:1;background:#0d1a30;height:12px;border-radius:2px;overflow:hidden">
                    <div style="width:66%;background:#10b981;height:100%"></div>
                  </div>
                  <span style="width:45px;font-family:monospace;font-weight:700">~24.2K</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div>
          <div class="kd-decision-callout">
            <b>Decision changed:</b> Normalize prefill-heavy demand into prompt tokens/s.
          </div>
          <div class="kd-v-card-footer">
            <span class="badge b-green">Evidence HIGH</span>
            <button class="chip" style="cursor:pointer" onclick="scrollToKdExplorer(5)">Inspect &darr;</button>
          </div>
        </div>
      </div>

      <!-- Card 7: Runtime-Knob Derivative -->
      <div class="kd-v-card">
        <div>
          <div class="kd-v-card-header">
            <div>
              <div class="kd-v-card-title-row">
                <span class="kd-v-card-num">7</span>
                <h3 class="kd-v-card-title">Runtime-Knob Derivative</h3>
              </div>
              <div class="kd-v-card-sub">Tune only knobs with a measured derivative.</div>
            </div>
            <button class="kd-v-card-btn" onclick="openFindingModal(8)">View Details &rarr;</button>
          </div>

          <!-- Two Sub-tables -->
          <div style="margin:6px 0;display:flex;flex-direction:column;gap:6px">
            <div>
              <div style="font-size:8.5px;color:#94a3b8;font-weight:700">max_num_seqs at 1M c4 (TTFT)</div>
              <table class="kd-mini-table">
                <thead>
                  <tr>
                    <th>Value</th>
                    <th>4</th>
                    <th>8</th>
                    <th>16</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style="font-weight:700">TTFT (s)</td>
                    <td>232.342</td>
                    <td>233.364</td>
                    <td>232.250</td>
                  </tr>
                </tbody>
              </table>
              <div style="font-size:8px;color:#64748b;margin-top:1px">&rarr; Non-binding here (0.049% spread).</div>
            </div>

            <div>
              <div style="font-size:8.5px;color:#94a3b8;font-weight:700">Chunk size at 1M c1 (TTFT)</div>
              <table class="kd-mini-table">
                <thead>
                  <tr>
                    <th>Value</th>
                    <th>4K</th>
                    <th>8K</th>
                    <th>16K</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style="font-weight:700">TTFT (s)</td>
                    <td style="color:#f87171">122.049</td>
                    <td>93.277</td>
                    <td style="color:#4ade80;font-weight:700">88.951</td>
                  </tr>
                </tbody>
              </table>
              <div style="font-size:8px;color:#38bdf8;margin-top:1px">&rarr; Higher leverage here (-27.1% gain).</div>
            </div>
          </div>
        </div>

        <div>
          <div class="kd-decision-callout">
            <b>Decision changed:</b> Tune only knobs with a measured derivative in target regime.
          </div>
          <div class="kd-v-card-footer">
            <span class="badge b-green">Evidence HIGH</span>
            <button class="chip" style="cursor:pointer" onclick="scrollToKdExplorer(8)">Inspect &darr;</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 5. SECTION 3: EVIDENCE CHAIN & OPERATIONAL TRAPS (CARDS 8, 9, 10) -->
    <div class="kd-section-divider-bar">
      <span class="kd-sec-pill"><span>&#128196;</span> Evidence Chain &amp; Operational Traps</span>
      <span class="kd-sec-label">Cross-Tool Synchronizations, Utilization Traps &amp; Memory Semantics (Findings 8 &ndash; 10)</span>
    </div>

    <div class="kd-grid-3">
      <!-- Card 8: TP Decode Evidence Chain -->
      <div class="kd-v-card">
        <div>
          <div class="kd-v-card-header">
            <div>
              <div class="kd-v-card-title-row">
                <span class="kd-v-card-num">8</span>
                <h3 class="kd-v-card-title">TP Decode Evidence Chain</h3>
              </div>
              <div class="kd-v-card-sub">Wider TP can hurt interactive decode via small-message collective overhead.</div>
            </div>
            <button class="kd-v-card-btn" onclick="openFindingModal(7)">View Details &rarr;</button>
          </div>

          <!-- 4-Stage Horizontal Flow -->
          <div class="kd-h-chain" style="margin:8px 0">
            <div class="kd-h-stage">
              <div class="kd-h-stage-num">Stage 1: NCCL</div>
              <div class="kd-h-stage-title">Microbench</div>
              <div class="kd-h-stage-body">Small-message TP8 latency <b>~1.9–2.2&times;</b> TP4.</div>
            </div>
            <div class="kd-h-arrow">&rarr;</div>
            <div class="kd-h-stage">
              <div class="kd-h-stage-num">Stage 2: Profiler</div>
              <div class="kd-h-stage-title">Self CUDA</div>
              <div class="kd-h-stage-body">Exact 7,040 calls: <b>251.5 ms &rarr; 583.9 ms</b>.</div>
            </div>
            <div class="kd-h-arrow">&rarr;</div>
            <div class="kd-h-stage">
              <div class="kd-h-stage-num">Stage 3: Nsight</div>
              <div class="kd-h-stage-title">Work Dominance</div>
              <div class="kd-h-stage-body">AllReduce is dominant aggregate GPU work.</div>
            </div>
            <div class="kd-h-arrow">&rarr;</div>
            <div class="kd-h-stage">
              <div class="kd-h-stage-num">Stage 4: E2E</div>
              <div class="kd-h-stage-title">TPOT Penalty</div>
              <div class="kd-h-stage-body">8K TPOT: <b>4.47ms &rarr; 6.35ms (+41.9%)</b>.</div>
            </div>
          </div>
        </div>

        <div>
          <div class="kd-decision-callout">
            <b>Decision changed:</b> Wider TP can hurt short interactive decode.
          </div>
          <div class="kd-v-card-footer">
            <span class="badge b-green">Evidence HIGH</span>
            <button class="chip" style="cursor:pointer" onclick="scrollToKdExplorer(7)">Inspect &darr;</button>
          </div>
        </div>
      </div>

      <!-- Card 9: Busy GPU != Efficient Serving -->
      <div class="kd-v-card">
        <div>
          <div class="kd-v-card-header">
            <div>
              <div class="kd-v-card-title-row">
                <span class="kd-v-card-num">9</span>
                <h3 class="kd-v-card-title">Busy GPU &ne; Efficient Serving</h3>
              </div>
              <div class="kd-v-card-sub">GPU busy &ne; efficient serving. SM activity measures barrier stall, not user work.</div>
            </div>
            <button class="kd-v-card-btn" onclick="openFindingModal(9)">View Details &rarr;</button>
          </div>

          <!-- Comparison Table -->
          <table class="kd-mini-table" style="margin:8px 0">
            <thead>
              <tr>
                <th rowspan="2" style="vertical-align:middle;text-align:left">Context</th>
                <th colspan="2" style="background:#0f243a;color:#38bdf8">TP4/PP4 (Efficient)</th>
                <th colspan="2" style="background:#2d1515;color:#f87171">TP16/PP1 (Busy Trap)</th>
              </tr>
              <tr>
                <th>Utilization</th>
                <th>TTFT</th>
                <th>Utilization</th>
                <th>TTFT</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style="text-align:left;font-weight:700">128K</td>
                <td>35.2%</td>
                <td style="color:#4ade80;font-weight:700">1.710 s</td>
                <td style="color:#f87171;font-weight:700">63.2%</td>
                <td style="color:#f87171">6.420 s (3.75&times;)</td>
              </tr>
              <tr>
                <td style="text-align:left;font-weight:700">1M</td>
                <td>62.8%</td>
                <td style="color:#4ade80;font-weight:800">28.568 s</td>
                <td style="color:#f87171;font-weight:800">80.6%</td>
                <td style="color:#f87171;font-weight:800">68.197 s (2.39&times;)</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div>
          <div class="kd-decision-callout">
            <b>Decision changed:</b> Never use GPU utilization alone to choose topology.
          </div>
          <div class="kd-v-card-footer">
            <span class="badge b-green">Evidence HIGH</span>
            <button class="chip" style="cursor:pointer" onclick="scrollToKdExplorer(9)">Inspect &darr;</button>
          </div>
        </div>
      </div>

      <!-- Card 10: KV Headroom != VRAM Headroom -->
      <div class="kd-v-card">
        <div>
          <div class="kd-v-card-header">
            <div>
              <div class="kd-v-card-title-row">
                <span class="kd-v-card-num">10</span>
                <h3 class="kd-v-card-title">KV Headroom &ne; VRAM Headroom</h3>
              </div>
              <div class="kd-v-card-sub">KV pressure and VRAM headroom are completely different metrics.</div>
            </div>
            <button class="kd-v-card-btn" onclick="openFindingModal(10)">View Details &rarr;</button>
          </div>

          <!-- Memory Table -->
          <table class="kd-mini-table" style="margin:8px 0">
            <thead>
              <tr>
                <th style="text-align:left">Topology</th>
                <th>Peak KV usage</th>
                <th>Peak memory (GiB)</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style="text-align:left;font-weight:700">TP4/PP1</td>
                <td>12.29%</td>
                <td>88.39 GiB</td>
              </tr>
              <tr>
                <td style="text-align:left;font-weight:700">TP4/PP2</td>
                <td>5.91%</td>
                <td>88.69 GiB</td>
              </tr>
              <tr>
                <td style="text-align:left;font-weight:700;color:#38bdf8">TP4/PP4</td>
                <td style="color:#38bdf8;font-weight:700">2.75%</td>
                <td style="font-weight:700">88.83 GiB</td>
              </tr>
              <tr>
                <td style="text-align:left;font-weight:700">TP16/PP1</td>
                <td>12.13%</td>
                <td>86.71 GiB</td>
              </tr>
            </tbody>
          </table>
          <div style="font-size:8px;color:#94a3b8">&#9432; Raw device capacity reported in preflight: 97,887 MiB per GPU</div>
        </div>

        <div>
          <div class="kd-decision-callout">
            <b>Decision changed:</b> Use KV% for cache pressure and memory telemetry for true VRAM headroom.
          </div>
          <div class="kd-v-card-footer">
            <span class="badge b-green">Evidence HIGH</span>
            <button class="chip" style="cursor:pointer" onclick="scrollToKdExplorer(10)">Inspect &darr;</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 6. FOOTER TRUST & CONFORMANCE STRIP FOR SIGNALS -->
    <div style="background:#091322;border:1px solid #1a2a44;border-radius:6px;padding:8px 14px;font-size:9.5px;color:#94a3b8;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
      <div>
        &#8505; All values shown above are taken from canonical V8 run data, HTML evidence, or validated profiler traces. Derived values are explicitly labeled.
      </div>
      <div style="display:flex;gap:8px;align-items:center">
        <span>Evidence: <b style="color:#4ade80">&#9679; HIGH</b> <b style="color:#facc15">&#9679; MEDIUM</b> <b style="color:#f87171">&#9679; LOW</b></span>
        <span>&middot;</span>
        <span>Cause confidence: <b style="color:#4ade80">&#9679; HIGH</b> <b style="color:#facc15">&#9679; MEDIUM</b> <b style="color:#f87171">&#9679; LOW</b></span>
      </div>
    </div>

    <!-- 7. DIVIDER & TRANSITION BAR (ON SCROLL DOWN) -->
    <div class="kd-explorer-transition-bar" id="kd-deep-explorer-section">
      <div>
        <div class="kd-explorer-transition-title">
          <span>&#128202;</span> Detailed 10-Finding Explorer (Deep-Dive Analysis &amp; Charts)
        </div>
        <div class="kd-explorer-transition-sub">
          Explore complete empirical scope matrices, A/B matched comparisons, and interactive telemetry charts for all 10 discoveries below.
        </div>
      </div>
      <div style="display:flex;gap:8px;align-items:center">
        <span style="font-size:10.5px;color:#93c5fd">Active Finding:</span>
        <span class="badge b-cyan" id="kd-active-finding-badge">#1 Fabric Exposure</span>
        <button class="chip" style="cursor:pointer;padding:4px 10px;background:#1e3a8a;border-color:#3b82f6" onclick="openFindingModal(window.kdActivePage || 1)">
          <span>&#x26F6;</span> Open in Floating Modal &rarr;
        </button>
      </div>
    </div>

    <!-- 8. 10-FINDING DEEP EXPLORER (PERSISTENT LEFT RAIL + SUBPAGE CONTENT) -->
    <div class="kd-subpage-container">
      <!-- Persistent Left Rail -->
      <div class="kd-subnav-rail">
        <div class="kd-subnav-header">
          <span>Findings Navigation</span>
          <span style="font-size:9.5px;color:#38bdf8">10 Pages</span>
        </div>
        <div class="kd-subnav-list">
          {nav_rail_html}
        </div>
      </div>

      <!-- Active Sub-Page Content Area -->
      <div class="kd-subpage-content" id="kd-subpage-active-content">
        {p1_initial_content}
      </div>
    </div>

  </div>
</section>

<!-- FULL-SCREEN SUB-POPUP MODAL (FLOATING 10-FINDING DEEP EXPLORER) -->
<div id="kd-deep-subpage-backdrop" onclick="closeFindingModal()"></div>
<div id="kd-deep-subpage-modal">
  <div class="kd-modal-top-bar">
    <div style="display:flex;align-items:center;gap:12px">
      <span style="font-size:13px;font-weight:800;color:#fff">&#128202; Deep Finding Explorer &middot; Dedicated Sub-Page Modal</span>
      <span class="badge b-cyan" id="kd-modal-active-badge">#1 Fabric Exposure</span>
    </div>
    <div style="display:flex;gap:8px;align-items:center">
      <button class="chip" onclick="scrollToKdExplorer(window.kdActivePage || 1); closeFindingModal();" style="cursor:pointer">Scroll to Explorer Below &darr;</button>
      <button onclick="closeFindingModal()" style="background:#132238;border:1px solid #233857;color:#cbd5e1;font-size:16px;width:28px;height:28px;border-radius:4px;cursor:pointer">&times;</button>
    </div>
  </div>
  <div style="display:flex;flex:1;overflow:hidden;padding:12px;gap:12px;background:#060d18">
    <div class="kd-subnav-rail" style="width:250px;min-width:250px">
      <div class="kd-subnav-header">
        <span>Findings Navigation</span>
        <span style="font-size:9.5px;color:#38bdf8">10 Pages</span>
      </div>
      <div class="kd-subnav-list">
        {modal_rail_html}
      </div>
    </div>
    <div class="kd-subpage-content" id="kd-modal-subpage-active-content" style="overflow-y:auto;flex:1">
      <!-- Injected dynamically on open -->
    </div>
  </div>
</div>
"""
    return markup

print("Unified Key Discoveries Tab HTML generated successfully.")

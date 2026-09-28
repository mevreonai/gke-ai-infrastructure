# build_full_key_discoveries.py
import os
import sys
import json
import re

# Import the 10 pages data
with open("scratch/build_v5_subpages.py", "r", encoding="utf-8") as f:
    code = f.read()

ns = {}
exec(code, ns)
PAGES = ns["PAGES"]

print(f"Loaded {len(PAGES)} pages for generation.")

# 1. Generate the CSS for the 10-Finding Deep Explorer and Sub-Popup Modal
CSS_EXTRA = """
/* === 10-FINDING DEEP EXPLORER (V5 MULTI-PAGE ARCHITECTURE) === */
.kd-view-switch-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #091322;
    border: 1px solid #1a2a44;
    border-radius: 8px;
    padding: 8px 14px;
    margin-bottom: 12px;
}
.kd-view-pills {
    display: flex;
    gap: 6px;
}
.kd-view-pill {
    padding: 6px 16px;
    font-size: 11px;
    font-weight: 700;
    border-radius: 6px;
    border: 1px solid #233857;
    background: #0f1c30;
    color: #94a3b8;
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
    gap: 6px;
}
.kd-view-pill.active {
    background: #1d4ed8;
    color: #ffffff;
    border-color: #3b82f6;
    box-shadow: 0 0 12px rgba(59, 130, 246, 0.4);
}
.kd-view-pill:hover:not(.active) {
    background: #15263f;
    color: #cbd5e1;
}

/* 10-Page Explorer Split Layout */
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
    padding: 10px 10px;
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
    justify-content: space-between;
    padding: 4px 0;
    border-bottom: 1px dashed #16263e;
}
.kd-hero-point-row:last-child {
    border-bottom: none;
}
.kd-hero-val {
    font-size: 20px;
    font-weight: 900;
    line-height: 1;
}
.kd-hero-desc {
    text-align: right;
}
.kd-hero-label {
    font-size: 11px;
    font-weight: 700;
    color: #e2e8f0;
}
.kd-hero-sub {
    font-size: 9.5px;
    color: #94a3b8;
}

.kd-card-why {
    background: #0b172a;
    border: 1px solid #1e3352;
    border-radius: 8px;
    padding: 12px 14px;
    font-size: 11.5px;
    color: #cbd5e1;
    line-height: 1.5;
}
.kd-card-why-title {
    font-size: 10px;
    font-weight: 800;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}

.kd-card-conf {
    background: #0b172a;
    border: 1px solid #1e3352;
    border-radius: 8px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.kd-conf-title {
    font-size: 10px;
    font-weight: 800;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}
.kd-conf-badges {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-bottom: 6px;
}
.kd-conf-badge-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 10.5px;
    background: #070e1b;
    padding: 4px 8px;
    border-radius: 4px;
    border: 1px solid #16263e;
}
.kd-conf-note {
    font-size: 9.5px;
    color: #64748b;
    line-height: 1.35;
}

/* Row B: Scope & Quick Comparison */
.kd-row-b {
    display: grid;
    grid-template-columns: 1fr 1.5fr;
    gap: 12px;
}
.kd-card-scope {
    background: #0b172a;
    border: 1px solid #1e3352;
    border-radius: 8px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 10px;
}
.kd-scope-sec-title {
    font-size: 10px;
    font-weight: 800;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}
.kd-scope-dots-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 6px;
}
.kd-scope-dot-pill {
    background: #070e1b;
    border: 1px solid #16263e;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 10px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.kd-scope-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
}
.kd-scope-dot.measured { background: #4ade80; box-shadow: 0 0 6px rgba(74, 222, 128, 0.6); }
.kd-scope-dot.not-measured { background: #64748b; }

.kd-card-comp {
    background: #0b172a;
    border: 1px solid #1e3352;
    border-radius: 8px;
    padding: 12px 14px;
    overflow-x: auto;
}
.kd-comp-title {
    font-size: 10px;
    font-weight: 800;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
    display: flex;
    justify-content: space-between;
}
.kd-comp-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 10.5px;
}
.kd-comp-table th {
    background: #070e1b;
    color: #94a3b8;
    text-align: left;
    padding: 6px 8px;
    border-bottom: 1px solid #1a2a44;
    font-size: 9.5px;
    font-weight: 700;
    text-transform: uppercase;
}
.kd-comp-table td {
    padding: 6px 8px;
    border-bottom: 1px solid #122035;
    color: #cbd5e1;
}
.kd-comp-table tr:hover td {
    background: rgba(255, 255, 255, 0.02);
}

/* Row C: Visuals / Real Charts */
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
}
.kd-visual-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}
.kd-visual-title {
    font-size: 11px;
    font-weight: 800;
    color: #cbd5e1;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.kd-chart-container {
    position: relative;
    height: 250px;
    width: 100%;
}

/* 3-Stage Evidence Chain for Finding #7 */
.kd-chain-container {
    display: flex;
    flex-direction: column;
    gap: 10px;
}
.kd-chain-steps {
    display: grid;
    grid-template-columns: 1fr auto 1fr auto 1.2fr;
    gap: 8px;
    align-items: center;
}
.kd-chain-card {
    background: #070e1b;
    border: 1px solid #1a2a44;
    border-radius: 6px;
    padding: 10px 12px;
}
.kd-chain-arrow {
    font-size: 16px;
    color: #38bdf8;
    font-weight: 900;
}
.kd-chain-step-num {
    font-size: 9px;
    font-weight: 800;
    color: #38bdf8;
    text-transform: uppercase;
    margin-bottom: 2px;
}
.kd-chain-step-title {
    font-size: 11px;
    font-weight: 700;
    color: #fff;
    margin-bottom: 4px;
}
.kd-chain-step-body {
    font-size: 10px;
    color: #94a3b8;
    line-height: 1.4;
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
}
.kd-takeaways-title {
    font-size: 10px;
    font-weight: 800;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}
.kd-takeaways-list {
    margin: 0;
    padding-left: 18px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 11px;
    color: #cbd5e1;
    line-height: 1.45;
}
.kd-card-decision {
    background: linear-gradient(135deg, rgba(234, 179, 8, 0.08), rgba(202, 138, 4, 0.03));
    border: 1px solid rgba(234, 179, 8, 0.35);
    border-radius: 8px;
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.kd-decision-header {
    font-size: 10px;
    font-weight: 800;
    color: #facc15;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.kd-decision-text {
    font-size: 12.5px;
    font-weight: 700;
    color: #fef08a;
    line-height: 1.45;
    margin-bottom: 8px;
}
.kd-boundary-text {
    font-size: 9.5px;
    color: #94a3b8;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    padding-top: 6px;
    line-height: 1.35;
}

/* Sub-Popup Modal (Fullscreen or Large Floating Sub-Page Modal) */
#kd-deep-subpage-modal {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) scale(0.98);
    width: 1400px;
    max-width: 96vw;
    height: 88vh;
    background: #07101f;
    border: 2px solid #233c5e;
    border-radius: 12px;
    box-shadow: 0 25px 80px rgba(0, 0, 0, 0.95);
    z-index: 100005;
    display: none;
    flex-direction: column;
    overflow: hidden;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
#kd-deep-subpage-modal.open {
    display: flex;
    transform: translate(-50%, -50%) scale(1);
}
#kd-deep-subpage-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(4, 9, 18, 0.85);
    backdrop-filter: blur(5px);
    z-index: 100004;
    display: none;
}
#kd-deep-subpage-backdrop.open {
    display: block;
}
.kd-modal-top-bar {
    padding: 10px 18px;
    background: #0c182e;
    border-bottom: 1px solid #1a2a44;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
"""

print("CSS generated.")

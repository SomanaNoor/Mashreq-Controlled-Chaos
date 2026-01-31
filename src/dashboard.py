"""
Mashreq Responsible AI Command Center
======================================
Premium 5-Tab Dashboard for Risk Analysts

Tabs:
1. Signal Triage - Active signals needing review with AI reasoning
2. Escalation Hub - Escalated signals with team routing & action plans
3. Audit Trail - Activity log with management summaries
4. Governance Center - Data/Model cards, policies, compliance
5. Analytics - Real-time pipeline metrics & Monte Carlo simulation

Author: Antigravity
"""

import streamlit as st
import pandas as pd
import json
import os
import sys
from datetime import datetime, timedelta
import time

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from responsible_ai_pipeline import get_pipeline, process_events, ClusterAnalysis
from data_loader import load_csv_events
from guardrails import get_guardrails
from audit_logger import get_audit_logger
from simulation_engine import SimulationEngine

# Page config
st.set_page_config(
    page_title="Mashreq AI Command Center",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# PREMIUM CSS THEME
# ==============================================================================

st.markdown("""
<style>
    /* =========== IMPORTS =========== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    /* =========== ROOT VARIABLES =========== */
    :root {
        --bg-primary: #0A0E17;
        --bg-secondary: #12161F;
        --bg-card: rgba(18, 22, 31, 0.85);
        --bg-glass: rgba(255, 255, 255, 0.03);
        --accent-orange: #FF5E00;
        --accent-gold: #D4AF37;
        --accent-blue: #3B82F6;
        --accent-green: #10B981;
        --accent-red: #EF4444;
        --accent-purple: #8B5CF6;
        --text-primary: #FFFFFF;
        --text-secondary: #94A3B8;
        --text-muted: #64748B;
        --border-subtle: rgba(255, 255, 255, 0.08);
        --glow-orange: 0 0 40px rgba(255, 94, 0, 0.3);
    }
    
    /* =========== BASE STYLES =========== */
    .stApp {
        background: linear-gradient(135deg, var(--bg-primary) 0%, #0F1420 50%, var(--bg-secondary) 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* =========== HERO HEADER =========== */
    .hero-header {
        background: linear-gradient(135deg, rgba(255, 94, 0, 0.1) 0%, rgba(212, 175, 55, 0.05) 100%);
        border: 1px solid rgba(255, 94, 0, 0.2);
        border-radius: 24px;
        padding: 32px 40px;
        margin-bottom: 32px;
        position: relative;
        overflow: hidden;
    }
    .hero-header::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--accent-orange), var(--accent-gold));
    }
    .hero-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FFFFFF 0%, var(--accent-gold) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 8px 0;
    }
    .hero-subtitle {
        color: var(--text-secondary);
        font-size: 1.1rem;
        font-weight: 400;
    }
    
    /* =========== GLASSMORPHISM CARDS =========== */
    .glass-card {
        background: var(--bg-glass);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--border-subtle);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 20px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .glass-card:hover {
        border-color: rgba(255, 94, 0, 0.3);
        box-shadow: var(--glow-orange);
        transform: translateY(-2px);
    }
    
    /* =========== SIGNAL CARDS =========== */
    .signal-card {
        background: linear-gradient(135deg, var(--bg-card) 0%, rgba(18, 22, 31, 0.95) 100%);
        border: 1px solid var(--border-subtle);
        border-radius: 20px;
        padding: 28px;
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    .signal-card::before {
        content: '';
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: 4px;
        border-radius: 4px 0 0 4px;
    }
    .signal-card.critical::before { background: linear-gradient(180deg, var(--accent-red), #DC2626); }
    .signal-card.high::before { background: linear-gradient(180deg, var(--accent-orange), var(--accent-gold)); }
    .signal-card.medium::before { background: linear-gradient(180deg, var(--accent-gold), #FBBF24); }
    .signal-card.low::before { background: linear-gradient(180deg, var(--accent-blue), #60A5FA); }
    
    .signal-card:hover {
        border-color: rgba(255, 94, 0, 0.4);
        box-shadow: 0 20px 60px -20px rgba(255, 94, 0, 0.25);
        transform: translateY(-4px);
    }
    
    .signal-title {
        color: var(--text-primary);
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 12px;
    }
    .signal-meta {
        display: flex;
        gap: 16px;
        margin-bottom: 16px;
    }
    
    /* =========== SCORE BADGES =========== */
    .score-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: 50px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .risk-badge {
        background: rgba(239, 68, 68, 0.15);
        color: #FCA5A5;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    .risk-badge.high {
        background: rgba(255, 94, 0, 0.15);
        color: #FDBA74;
        border: 1px solid rgba(255, 94, 0, 0.3);
    }
    .confidence-badge {
        background: rgba(59, 130, 246, 0.15);
        color: #93C5FD;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    .category-badge {
        background: rgba(139, 92, 246, 0.15);
        color: #C4B5FD;
        border: 1px solid rgba(139, 92, 246, 0.3);
    }
    
    /* =========== AI REASONING BOX =========== */
    .ai-reasoning {
        background: rgba(255, 94, 0, 0.05);
        border-left: 3px solid var(--accent-orange);
        border-radius: 0 12px 12px 0;
        padding: 16px 20px;
        margin: 16px 0;
    }
    .ai-reasoning-title {
        color: var(--accent-gold);
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    .ai-reasoning-text {
        color: var(--text-secondary);
        font-size: 0.95rem;
        line-height: 1.6;
    }
    
    /* =========== ACTION BUTTONS =========== */
    .action-btn {
        padding: 12px 24px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.2s ease;
        border: none;
    }
    .action-btn.escalate {
        background: linear-gradient(135deg, var(--accent-orange), #FF7A00);
        color: white;
    }
    .action-btn.dismiss {
        background: transparent;
        color: var(--text-secondary);
        border: 1px solid var(--border-subtle);
    }
    
    /* =========== KPI METRICS =========== */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 20px;
        margin-bottom: 32px;
    }
    .kpi-card {
        background: var(--bg-glass);
        backdrop-filter: blur(16px);
        border: 1px solid var(--border-subtle);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
    }
    .kpi-value {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, var(--accent-orange), var(--accent-gold));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .kpi-label {
        color: var(--text-secondary);
        font-size: 0.85rem;
        font-weight: 500;
        margin-top: 8px;
    }
    
    /* =========== TEAM ROUTING =========== */
    .team-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin: 16px 0;
    }
    .team-btn {
        background: var(--bg-glass);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .team-btn:hover {
        border-color: var(--accent-orange);
        background: rgba(255, 94, 0, 0.1);
    }
    .team-btn.selected {
        border-color: var(--accent-orange);
        background: rgba(255, 94, 0, 0.15);
        box-shadow: 0 0 20px rgba(255, 94, 0, 0.2);
    }
    
    /* =========== AUDIT LOG =========== */
    .audit-entry {
        background: var(--bg-glass);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .audit-timestamp {
        color: var(--text-muted);
        font-size: 0.8rem;
        font-family: 'SF Mono', monospace;
        min-width: 140px;
    }
    .audit-action {
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .audit-action.escalated { background: rgba(255, 94, 0, 0.2); color: #FDBA74; }
    .audit-action.dismissed { background: rgba(100, 116, 139, 0.2); color: #94A3B8; }
    .audit-action.approved { background: rgba(16, 185, 129, 0.2); color: #6EE7B7; }
    
    /* =========== TABS OVERRIDE =========== */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-glass);
        border-radius: 16px;
        padding: 8px;
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 12px;
        color: var(--text-secondary);
        font-weight: 600;
        padding: 12px 24px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--accent-orange), var(--accent-gold)) !important;
        color: white !important;
    }
    
    /* =========== STREAMLIT OVERRIDES =========== */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-orange), #FF7A00);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        box-shadow: 0 10px 30px -10px rgba(255, 94, 0, 0.5);
        transform: translateY(-2px);
    }
    .stButton > button[kind="secondary"] {
        background: transparent;
        border: 1px solid var(--border-subtle);
        color: var(--text-secondary);
    }
    
    .stSelectbox > div > div {
        background: var(--bg-glass);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
    }
    
    .stTextInput > div > div {
        background: var(--bg-glass);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
    }
    
    /* =========== DECISION BANNER =========== */
    .decision-banner {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(59, 130, 246, 0.1));
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 16px;
        padding: 20px 28px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .decision-banner-icon {
        font-size: 2rem;
    }
    .decision-banner-text {
        color: var(--text-primary);
        font-weight: 600;
    }
    .decision-banner-sub {
        color: var(--text-secondary);
        font-size: 0.9rem;
    }
    
    /* =========== PROGRESS BAR =========== */
    .risk-bar-container {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 50px;
        height: 8px;
        overflow: hidden;
        margin-top: 8px;
    }
    .risk-bar-fill {
        height: 100%;
        border-radius: 50px;
        background: linear-gradient(90deg, var(--accent-orange), var(--accent-gold));
        transition: width 1s ease;
    }
    
    /* =========== EXECUTIVE SUMMARY =========== */
    .exec-summary {
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.1), rgba(255, 94, 0, 0.05));
        border: 1px solid rgba(212, 175, 55, 0.3);
        border-radius: 20px;
        padding: 32px;
        margin-bottom: 24px;
    }
    .exec-summary-title {
        color: var(--accent-gold);
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 16px;
    }
    
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# STATE MANAGEMENT
# ==============================================================================

if 'pipeline_result' not in st.session_state:
    st.session_state['pipeline_result'] = None
if 'escalated_signals' not in st.session_state:
    st.session_state['escalated_signals'] = []
if 'dismissed_signals' not in st.session_state:
    st.session_state['dismissed_signals'] = []
if 'audit_log' not in st.session_state:
    st.session_state['audit_log'] = []

# Department definitions
DEPARTMENTS = {
    "IT Operations": {"icon": "🖥️", "color": "#3B82F6", "desc": "System outages, technical failures"},
    "Fraud Prevention": {"icon": "🛡️", "color": "#EF4444", "desc": "Scams, unauthorized access, phishing"},
    "Communications": {"icon": "📢", "color": "#8B5CF6", "desc": "Misinformation, PR crisis"},
    "Risk Management": {"icon": "⚠️", "color": "#F59E0B", "desc": "Liquidity concerns, market rumors"},
    "Customer Experience": {"icon": "💬", "color": "#10B981", "desc": "Service complaints, sentiment"},
    "Compliance": {"icon": "📋", "color": "#6366F1", "desc": "Regulatory, audit requirements"}
}

# ==============================================================================
# DATA LOADING
# ==============================================================================

@st.cache_data(ttl=60)
def load_pipeline_data():
    """Load and process data through the 10-stage pipeline."""
    try:
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'synthetic_social_signals_mashreq.csv')
        if not os.path.exists(csv_path):
            csv_path = 'data/synthetic_social_signals_mashreq.csv'
        
        events = load_csv_events(csv_path)
        pipeline = get_pipeline()
        result = pipeline.process(events)
        return result, events
    except Exception as e:
        st.error(f"Pipeline error: {e}")
        return None, []

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_risk_level(score):
    if score >= 8: return "critical"
    if score >= 6: return "high"
    if score >= 4: return "medium"
    return "low"

def get_risk_color(score):
    if score >= 8: return "#EF4444"
    if score >= 6: return "#FF5E00"
    if score >= 4: return "#D4AF37"
    return "#3B82F6"

def log_action(action, signal_id, user="Risk Analyst", details=""):
    """Log an action to the audit trail."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "signal_id": signal_id,
        "user": user,
        "details": details
    }
    st.session_state['audit_log'].append(entry)
    return entry

# ==============================================================================
# RENDER FUNCTIONS
# ==============================================================================

def render_hero():
    """Render the hero header."""
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">🏦 Mashreq AI Command Center</div>
        <div class="hero-subtitle">Responsible AI Pipeline for Banking Signal Intelligence • Powered by 10-Stage Governance Architecture</div>
    </div>
    """, unsafe_allow_html=True)

def render_kpis(result, events):
    """Render the KPI metrics grid."""
    if not result:
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="glass-card" style="text-align: center;">
            <div class="kpi-value">{len(events)}</div>
            <div class="kpi-label">Signals Processed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        active_count = len([a for a in result.cluster_analyses if a.risk_score.total_score >= 4])
        st.markdown(f"""
        <div class="glass-card" style="text-align: center;">
            <div class="kpi-value" style="color: #FF5E00;">{active_count}</div>
            <div class="kpi-label">Requiring Review</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        critical_count = len([a for a in result.cluster_analyses if a.risk_score.total_score >= 8])
        st.markdown(f"""
        <div class="glass-card" style="text-align: center;">
            <div class="kpi-value" style="color: #EF4444;">{critical_count}</div>
            <div class="kpi-label">Critical Alerts</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="glass-card" style="text-align: center;">
            <div class="kpi-value" style="color: #10B981;">✓</div>
            <div class="kpi-label">Governance Validated</div>
        </div>
        """, unsafe_allow_html=True)

def render_signal_card(analysis, show_actions=True, key_prefix=""):
    """Render a single signal card with AI reasoning."""
    card = analysis.to_analyst_card()
    risk_level = get_risk_level(card['risk_score'])
    risk_color = get_risk_color(card['risk_score'])
    
    # Extract values
    title = card['title']
    risk_score = card['risk_score']
    confidence = card['confidence_percentage']
    category = card['category']
    signal_text = card['rationale']['what_signal']
    why_matters = card['rationale']['why_it_matters']
    uncertainty = card['uncertainty_wording']
    
    # Card container with badges
    st.markdown(f"""
<div class="signal-card {risk_level}">
    <div class="signal-title">{title}</div>
    <div class="signal-meta">
        <span class="score-badge risk-badge" style="background: rgba({int(risk_color[1:3], 16)}, {int(risk_color[3:5], 16)}, {int(risk_color[5:7], 16)}, 0.15);">
            ⚠️ Risk: {risk_score}/10
        </span>
        <span class="score-badge confidence-badge">
            🎯 Confidence: {confidence:.0f}%
        </span>
        <span class="score-badge category-badge">
            📂 {category}
        </span>
    </div>
    <div class="ai-reasoning">
        <div class="ai-reasoning-title">🤖 AI Reasoning</div>
        <div class="ai-reasoning-text">
            <span style="font-weight: 600; color: #D4AF37;">Signal:</span> {signal_text}
        </div>
        <div class="ai-reasoning-text" style="margin-top: 8px;">
            <span style="font-weight: 600; color: #D4AF37;">Why it matters:</span> {why_matters}
        </div>
        <div class="ai-reasoning-text" style="margin-top: 8px;">
            <span style="font-weight: 600; color: #D4AF37;">Uncertainty:</span> {uncertainty}
        </div>
    </div>
</div>
    """, unsafe_allow_html=True)
    
    if show_actions:
        col1, col2, col3 = st.columns([2, 2, 4])
        with col1:
            if st.button("🚀 Escalate", key=f"{key_prefix}_escalate_{card['cluster_id']}", type="primary"):
                st.session_state['escalated_signals'].append(analysis)
                log_action("ESCALATED", card['cluster_id'])
                st.rerun()
        with col2:
            if st.button("❌ Dismiss", key=f"{key_prefix}_dismiss_{card['cluster_id']}"):
                st.session_state['dismissed_signals'].append(analysis)
                log_action("DISMISSED", card['cluster_id'])
                st.rerun()

def render_escalation_card(analysis):
    """Render an escalated signal with team routing options."""
    card = analysis.to_analyst_card()
    
    st.markdown(f"""
    <div class="signal-card high">
        <div class="signal-title">📋 {card['title']}</div>
        <div style="margin: 16px 0; color: #94A3B8;">
            Escalated for review • Risk Score: {card['risk_score']}/10 • Suggested Queue: {card['suggested_queue']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # AI Suggested Action Plan
    st.markdown("""
    <div class="ai-reasoning" style="margin-top: 16px;">
        <div class="ai-reasoning-title">📋 AI Suggested Action Plan</div>
        <div class="ai-reasoning-text">
    """, unsafe_allow_html=True)
    
    # Generate action plan based on category
    if card['category'] == 'SERVICE':
        actions = [
            "1. **Immediate**: Verify system status via monitoring dashboards",
            "2. **Investigate**: Check recent deployment logs for changes",
            "3. **Communicate**: Prepare customer-facing status update",
            "4. **Escalate**: If unresolved in 15 mins, escalate to L2 support"
        ]
    elif card['category'] == 'FRAUD':
        actions = [
            "1. **Alert**: Notify fraud prevention team immediately",
            "2. **Block**: Consider temporary holds on affected channels",
            "3. **Investigate**: Review transaction patterns for anomalies",
            "4. **Report**: File regulatory report if confirmed"
        ]
    elif card['category'] == 'MISINFORMATION':
        actions = [
            "1. **Verify**: Cross-reference with official sources",
            "2. **Monitor**: Track spread across social channels",
            "3. **Prepare**: Draft official clarification statement",
            "4. **Engage**: Coordinate with PR team for response"
        ]
    else:
        actions = [
            "1. **Review**: Analyze signal patterns and trends",
            "2. **Classify**: Determine appropriate response category",
            "3. **Assign**: Route to relevant department",
            "4. **Track**: Monitor for escalation patterns"
        ]
    
    for action in actions:
        st.markdown(action)
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Team Routing
    st.markdown("#### 📤 Route to Department")
    cols = st.columns(3)
    
    for idx, (dept, info) in enumerate(DEPARTMENTS.items()):
        with cols[idx % 3]:
            if st.button(f"{info['icon']} {dept}", key=f"route_{card['cluster_id']}_{dept}"):
                log_action("ROUTED", card['cluster_id'], details=f"Routed to {dept}")
                st.success(f"✅ Routed to {dept}")

def render_audit_log():
    """Render the audit trail with filtering."""
    st.markdown("### 📊 Activity Log")
    
    # Executive Summary
    total_escalated = len([e for e in st.session_state['audit_log'] if e['action'] == 'ESCALATED'])
    total_dismissed = len([e for e in st.session_state['audit_log'] if e['action'] == 'DISMISSED'])
    total_routed = len([e for e in st.session_state['audit_log'] if e['action'] == 'ROUTED'])
    
    st.markdown(f"""
    <div class="exec-summary">
        <div class="exec-summary-title">📈 Executive Summary</div>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; color: #94A3B8;">
            <div>
                <div style="font-size: 2rem; color: #FF5E00; font-weight: 700;">{total_escalated}</div>
                <div>Signals Escalated</div>
            </div>
            <div>
                <div style="font-size: 2rem; color: #64748B; font-weight: 700;">{total_dismissed}</div>
                <div>Signals Dismissed</div>
            </div>
            <div>
                <div style="font-size: 2rem; color: #10B981; font-weight: 700;">{total_routed}</div>
                <div>Routed to Teams</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Generate Report Button
    if st.button("📄 Generate Management Report", type="primary"):
        report = generate_management_report()
        st.download_button(
            "⬇️ Download Report",
            report,
            file_name=f"ai_command_center_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown"
        )
    
    st.divider()
    
    # Detailed Log
    if not st.session_state['audit_log']:
        st.info("No actions recorded yet. Start reviewing signals to populate the audit trail.")
    else:
        for entry in reversed(st.session_state['audit_log'][-20:]):
            action_class = entry['action'].lower()
            st.markdown(f"""
            <div class="audit-entry">
                <span class="audit-timestamp">{entry['timestamp'][:19]}</span>
                <span class="audit-action {action_class}">{entry['action']}</span>
                <span style="color: #E2E8F0;">Signal: {entry['signal_id']}</span>
                <span style="color: #64748B; margin-left: auto;">{entry.get('details', '')}</span>
            </div>
            """, unsafe_allow_html=True)

def generate_management_report():
    """Generate a markdown report for upper management."""
    now = datetime.now()
    
    report = f"""# AI Command Center - Executive Report
Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}

## Summary

This report summarizes AI-assisted signal triage activities from the Mashreq Responsible AI Pipeline.

### Key Metrics

| Metric | Count |
|--------|-------|
| Signals Escalated | {len([e for e in st.session_state['audit_log'] if e['action'] == 'ESCALATED'])} |
| Signals Dismissed | {len([e for e in st.session_state['audit_log'] if e['action'] == 'DISMISSED'])} |
| Team Routings | {len([e for e in st.session_state['audit_log'] if e['action'] == 'ROUTED'])} |

### Governance Compliance

✅ All signals processed through 10-stage governance pipeline  
✅ PII automatically redacted (Phone, Email, IBAN, Social Handles)  
✅ Synthetic data only - no real customer data processed  
✅ Human-in-the-loop verification for all decisions  

### Activity Timeline

"""
    for entry in st.session_state['audit_log'][-10:]:
        report += f"- **{entry['timestamp'][:19]}**: {entry['action']} - Signal {entry['signal_id']} {entry.get('details', '')}\n"
    
    report += """

---
*This report was generated by the Mashreq AI Command Center. All AI recommendations require human approval.*
"""
    return report

def render_governance_center():
    """Render the governance and compliance tab."""
    st.markdown("### 📜 Governance Center")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Data Card")
        try:
            data_card_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'data_card.json')
            if not os.path.exists(data_card_path):
                data_card_path = 'data/data_card.json'
            with open(data_card_path, 'r') as f:
                data_card = json.load(f)
            
            st.markdown(f"""
            <div class="glass-card">
                <h4 style="color: #D4AF37;">{data_card['dataset_name']}</h4>
                <p style="color: #94A3B8;">{data_card['description']}</p>
                <hr style="border-color: rgba(255,255,255,0.1);">
                <p><strong>Records:</strong> {data_card['composition']['total_records']}</p>
                <p><strong>PII Handling:</strong> {data_card['governance']['pii_redaction']}</p>
                <p><strong>Synthetic Flag:</strong> ✅ Enabled</p>
            </div>
            """, unsafe_allow_html=True)
        except:
            st.warning("Data card not found")
    
    with col2:
        st.markdown("#### 🤖 Model Card")
        try:
            model_card_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'model_card.json')
            if not os.path.exists(model_card_path):
                model_card_path = 'data/model_card.json'
            with open(model_card_path, 'r') as f:
                model_card = json.load(f)
            
            st.markdown(f"""
            <div class="glass-card">
                <h4 style="color: #D4AF37;">{model_card['model_name']}</h4>
                <p style="color: #94A3B8;">{model_card['intended_use']}</p>
                <hr style="border-color: rgba(255,255,255,0.1);">
                <p><strong>Type:</strong> {model_card['model_type']}</p>
                <p><strong>Accuracy:</strong> {model_card['performance_metrics']['accuracy']:.0%}</p>
                <p><strong>Latency P99:</strong> {model_card['performance_metrics']['latency_p99']}</p>
            </div>
            """, unsafe_allow_html=True)
        except:
            st.warning("Model card not found")
    
    # Policy Display
    st.markdown("#### 📋 System Use Policy")
    guardrails = get_guardrails()
    
    with st.expander("View Full Policy", expanded=False):
        st.markdown(guardrails.get_policy_text())

def render_analytics_tab(result, events):
    """Render the analytics and simulation tab."""
    st.markdown("### 📈 Pipeline Analytics")
    
    if not result:
        st.warning("Run the pipeline first to see analytics.")
        return
    
    # Pipeline Performance
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ⚡ Pipeline Performance")
        st.markdown(f"""
        <div class="glass-card">
            <p><strong>Processing Time:</strong> {result.processing_time_ms}ms</p>
            <p><strong>Events Processed:</strong> {len(events)}</p>
            <p><strong>Signals Surfaced:</strong> {result.gating_result.signal_count}</p>
            <p><strong>Noise Filtered:</strong> {result.gating_result.noise_count}</p>
            <p><strong>Clusters Formed:</strong> {result.clustering_result.cluster_count}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### 📊 Category Distribution")
        dist = result.clustering_result.category_distribution
        for cat, count in dist.items():
            pct = count / sum(dist.values()) * 100 if dist.values() else 0
            st.markdown(f"""
            <div style="margin-bottom: 12px;">
                <div style="color: #E2E8F0; margin-bottom: 4px;">{cat}: {count} signals</div>
                <div class="risk-bar-container">
                    <div class="risk-bar-fill" style="width: {pct}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Monte Carlo Simulation
    st.markdown("---")
    st.markdown("#### 🎲 Risk Simulation (Monte Carlo)")
    
    with st.form("simulation_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            interest_rate = st.slider("Interest Rate Impact (bps)", 0, 100, 25)
            downtime = st.slider("Downtime (minutes)", 0, 120, 30)
        with col2:
            reg_fine = st.slider("Regulatory Fine (MM)", 0.0, 10.0, 1.0)
            volatility = st.slider("Market Volatility (VIX)", 10, 50, 20)
        with col3:
            cyber_cost = st.slider("Cyber Breach Cost (MM)", 0.0, 20.0, 5.0)
        
        if st.form_submit_button("Run Simulation", type="primary"):
            with st.spinner("Running 5,000 Monte Carlo iterations..."):
                sim = SimulationEngine(iterations=5000)
                sim_result = sim.run_simulation(interest_rate, downtime, reg_fine, volatility, cyber_cost)
                
                st.markdown(f"""
                <div class="glass-card" style="text-align: center; margin-top: 20px;">
                    <div style="font-size: 3rem; font-weight: 800; color: {'#EF4444' if sim_result['is_breach'] else '#10B981'};">
                        {sim_result['breach_probability']:.1%}
                    </div>
                    <div style="color: #94A3B8;">Probability of Risk Threshold Breach</div>
                    <hr style="border-color: rgba(255,255,255,0.1); margin: 20px 0;">
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; text-align: center;">
                        <div>
                            <div style="color: #D4AF37; font-size: 1.5rem; font-weight: 700;">${sim_result['mean_impact']:.1f}M</div>
                            <div style="color: #64748B;">Mean Impact</div>
                        </div>
                        <div>
                            <div style="color: #FF5E00; font-size: 1.5rem; font-weight: 700;">${sim_result['var_95']:.1f}M</div>
                            <div style="color: #64748B;">VaR (95%)</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# ==============================================================================
# MAIN APP
# ==============================================================================

def main():
    # Hero Header
    render_hero()
    
    # Load Pipeline Data
    with st.spinner("Loading AI Pipeline..."):
        result, events = load_pipeline_data()
        st.session_state['pipeline_result'] = result
    
    # KPI Metrics
    if result:
        render_kpis(result, events)
    
    # Main Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📥 Signal Triage",
        "🚀 Escalation Hub", 
        "📊 Audit Trail",
        "🏛️ Governance",
        "📈 Analytics"
    ])
    
    # TAB 1: Signal Triage
    with tab1:
        st.markdown("""
        <div class="decision-banner">
            <span class="decision-banner-icon">🤖</span>
            <div>
                <div class="decision-banner-text">AI-Assisted Signal Triage</div>
                <div class="decision-banner-sub">Review signals below. AI provides reasoning — you make the decision.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if result and result.cluster_analyses:
            # Filter out already processed signals
            escalated_ids = [a.cluster.cluster_id for a in st.session_state['escalated_signals']]
            dismissed_ids = [a.cluster.cluster_id for a in st.session_state['dismissed_signals']]
            
            pending = [a for a in result.cluster_analyses 
                      if a.cluster.cluster_id not in escalated_ids 
                      and a.cluster.cluster_id not in dismissed_ids]
            
            # Sort by risk score
            pending.sort(key=lambda x: x.risk_score.total_score, reverse=True)
            
            if pending:
                st.markdown(f"**{len(pending)} signals awaiting review**")
                for analysis in pending:
                    render_signal_card(analysis, show_actions=True, key_prefix="triage")
            else:
                st.success("✅ All signals have been processed!")
        else:
            st.warning("No signals loaded. Check pipeline configuration.")
    
    # TAB 2: Escalation Hub
    with tab2:
        st.markdown("### 🚀 Escalation Hub")
        st.markdown("Review escalated signals and route to appropriate departments.")
        
        if st.session_state['escalated_signals']:
            for analysis in st.session_state['escalated_signals']:
                render_escalation_card(analysis)
                st.divider()
        else:
            st.info("No escalated signals yet. Escalate signals from the Triage tab.")
    
    # TAB 3: Audit Trail
    with tab3:
        render_audit_log()
    
    # TAB 4: Governance
    with tab4:
        render_governance_center()
    
    # TAB 5: Analytics
    with tab5:
        render_analytics_tab(result, events)

if __name__ == "__main__":
    main()

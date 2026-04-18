import streamlit as st
import os
import re
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go

# Backend imports
from app.services import parser, hf_client, ats_scorer, matcher
from app.utils import helpers
from app.services.experience_extractor import extract_work_experience, extract_education

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Resume Analyzer V2",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with dark theme and modern design
custom_css = """
<style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    body {
        background: linear-gradient(180deg, #0a0a0a 0%, #1a0a2e 100%);
        color: #ffffff;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .stApp {
        background: linear-gradient(180deg, #0a0a0a 0%, #1a0a2e 100%);
    }
    
    /* Gradient Header */
    .header-banner {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 25%, #0f3460 50%, #0a2540 75%, #16213e 100%);
        padding: 50px 40px;
        border-radius: 20px;
        margin-bottom: 35px;
        border: 2px solid #00d4aa;
        box-shadow: 0 0 50px rgba(0, 212, 170, 0.4), inset 0 0 20px rgba(0, 212, 170, 0.1);
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    .header-banner::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(0, 212, 170, 0.1) 0%, transparent 70%);
        animation: pulse 4s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 0.5; }
        50% { opacity: 1; }
    }
    
    .header-banner h1 {
        font-size: 3.2em;
        background: linear-gradient(135deg, #00d4aa 0%, #00f5ff 50%, #00d4aa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0 0 12px 0;
        font-weight: 800;
        letter-spacing: -1px;
        position: relative;
        z-index: 1;
    }
    
    .header-banner p {
        font-size: 1.15em;
        color: #a8d4ff;
        margin-top: 8px;
        letter-spacing: 2px;
        font-weight: 500;
        position: relative;
        z-index: 1;
    }
    
    .underline-glow {
        height: 4px;
        background: linear-gradient(90deg, transparent, #00d4aa, #00f5ff, #00d4aa, transparent);
        margin-top: 18px;
        border-radius: 2px;
        box-shadow: 0 0 20px rgba(0, 212, 170, 1), 0 0 40px rgba(0, 245, 255, 0.5);
        position: relative;
        z-index: 1;
    }
    
    /* Upload Card */
    .upload-card {
        background: transparent;
        border: none;
        border-radius: 0;
        padding: 0;
        text-align: left;
        transition: none;
        box-shadow: none;
        backdrop-filter: none;
    }
    
    .upload-card:hover {
        transform: none;
    }
    
    .file-preview {
        background: linear-gradient(135deg, #0f1419 0%, #1a1830 100%);
        border-left: 5px solid #00d4aa;
        padding: 18px;
        margin-top: 15px;
        border-radius: 10px;
        font-size: 0.95em;
        color: #b0ffff;
        box-shadow: 0 4px 15px rgba(0, 212, 170, 0.15);
    }
    
    /* Score Circle */
    .score-circle {
        width: 200px;
        height: 200px;
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 0 auto 20px;
        background: linear-gradient(135deg, #1a2f4f 0%, #0f1a2e 100%);
        border: 3px solid #00d4aa;
        box-shadow: 0 0 50px rgba(0, 212, 170, 0.5), inset 0 0 30px rgba(0, 212, 170, 0.15);
        position: relative;
        transition: all 0.3s ease;
    }
    
    .score-circle:hover {
        box-shadow: 0 0 70px rgba(0, 212, 170, 0.7), inset 0 0 40px rgba(0, 212, 170, 0.25);
        transform: scale(1.05);
    }
    
    .score-circle-number {
        font-size: 58px;
        font-weight: 900;
        color: #00f5ff;
        line-height: 1;
        text-shadow: 0 0 30px rgba(0, 245, 255, 0.5);
    }
    
    .score-circle-suffix {
        font-size: 16px;
        color: #00d4aa;
        margin-top: 5px;
        font-weight: 600;
    }
    
    .score-circle-label {
        font-size: 15px;
        font-weight: bold;
        margin-top: 12px;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .score-circle.excellent .score-circle-label {
        color: #4ade80;
        text-shadow: 0 0 10px rgba(74, 222, 128, 0.6);
    }
    
    .score-circle.good .score-circle-label {
        color: #f59e0b;
        text-shadow: 0 0 10px rgba(245, 158, 11, 0.6);
    }
    
    .score-circle.poor .score-circle-label {
        color: #ef4444;
        text-shadow: 0 0 10px rgba(239, 68, 68, 0.6);
    }
    
    /* Score Breakdown Cards */
    .breakdown-card {
        background: linear-gradient(135deg, #1a2f4f 0%, #0f1a2e 100%);
        border-radius: 14px;
        padding: 22px 18px;
        border: 1px solid #00d4aa;
        box-shadow: 0 8px 32px rgba(0, 212, 170, 0.15), inset 0 0 15px rgba(0, 212, 170, 0.05);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
    }
    
    .breakdown-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 15px 40px rgba(0, 212, 170, 0.25), inset 0 0 20px rgba(0, 212, 170, 0.1);
        border-color: #00f5ff;
    }
    
    .breakdown-card-category {
        font-size: 12px;
        color: #a8d4ff;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 10px;
        font-weight: 700;
    }
    
    .breakdown-card-score {
        font-size: 32px;
        background: linear-gradient(135deg, #00d4aa 0%, #00f5ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 900;
        margin-bottom: 14px;
    }
    
    .breakdown-card-icon {
        font-size: 28px;
        margin-bottom: 8px;
        display: block;
    }
    
    .progress-bar {
        width: 100%;
        height: 8px;
        background: rgba(0, 212, 170, 0.1);
        border-radius: 4px;
        overflow: hidden;
        margin-top: 14px;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    .progress-bar-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 0 15px currentColor;
    }
    
    .progress-bar-fill.excellent {
        background: linear-gradient(90deg, #4ade80 0%, #86efac 100%);
    }
    
    .progress-bar-fill.good {
        background: linear-gradient(90deg, #f59e0b 0%, #fbbf24 100%);
    }
    
    .progress-bar-fill.poor {
        background: linear-gradient(90deg, #ef4444 0%, #f87171 100%);
    }
    
    /* Chart Container */
    .chart-container {
        background: linear-gradient(135deg, #1a2f4f 0%, #0f1a2e 100%);
        border-radius: 14px;
        padding: 10px;
        border: 1px solid #00d4aa;
        margin-bottom: 12px;
        box-shadow: 0 8px 32px rgba(0, 212, 170, 0.15);
        transition: all 0.3s ease;
    }
    
    .chart-container:hover {
        box-shadow: 0 12px 40px rgba(0, 212, 170, 0.25);
        border-color: #00f5ff;
    }
    
    .section-header {
        font-size: 24px;
        font-weight: 800;
        color: #00f5ff;
        border-left: 5px solid #00d4aa;
        padding-left: 16px;
        margin-bottom: 15px;
        margin-top: 15px;
        text-shadow: 0 0 20px rgba(0, 245, 255, 0.3);
        letter-spacing: 0.5px;
    }
    
    /* Keyword Pills */
    .keyword-pills-container {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 16px;
    }
    
    .keyword-pill {
        background: linear-gradient(135deg, #0d2137 0%, #1a3f5c 100%);
        border: 1.5px solid #00d4aa;
        color: #00f5ff;
        border-radius: 24px;
        padding: 8px 16px;
        font-size: 13px;
        display: inline-block;
        white-space: nowrap;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(0, 212, 170, 0.2);
        transition: all 0.3s ease;
    }
    
    .keyword-pill:hover {
        background: linear-gradient(135deg, #1a3f5c 0%, #2a5f7f 100%);
        box-shadow: 0 6px 16px rgba(0, 212, 170, 0.35);
        transform: translateY(-2px);
    }

    /* Job Match UI */
    .job-match-card {
        background: linear-gradient(135deg, #1a2f4f 0%, #0f1a2e 100%);
        border: 1px solid #00d4aa;
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 8px 24px rgba(0, 212, 170, 0.15);
        height: 100%;
    }

    .job-match-card.compact-center {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 190px;
    }

    .job-match-title {
        color: #00f5ff;
        font-size: 13px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 12px;
    }

    .job-match-stats {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
    }

    .job-coverage-wrap {
        margin-top: 14px;
    }

    .job-coverage-label {
        color: #a8d4ff;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
        font-weight: 700;
    }

    .job-coverage-bar {
        width: 100%;
        height: 10px;
        border-radius: 999px;
        background: rgba(0, 212, 170, 0.12);
        border: 1px solid rgba(0, 212, 170, 0.28);
        overflow: hidden;
    }

    .job-coverage-fill {
        height: 100%;
        background: linear-gradient(90deg, #00d4aa 0%, #00f5ff 100%);
        box-shadow: 0 0 14px rgba(0, 245, 255, 0.45);
    }

    .job-stat-tile {
        background: rgba(0, 0, 0, 0.25);
        border: 1px solid rgba(0, 212, 170, 0.35);
        border-radius: 10px;
        padding: 12px;
    }

    .job-stat-label {
        color: #a8d4ff;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
        font-weight: 700;
    }

    .job-stat-value {
        color: #e6fffb;
        font-size: 28px;
        font-weight: 900;
        line-height: 1;
    }

    .job-stat-value.matched {
        color: #4ade80;
    }

    .job-stat-value.missing {
        color: #ef4444;
    }

    .job-score-circle {
        width: 150px;
        height: 150px;
        border-width: 2px;
        margin: 0 auto;
        box-shadow: 0 0 25px rgba(0, 212, 170, 0.35), inset 0 0 16px rgba(0, 212, 170, 0.1);
    }

    .job-score-circle .score-circle-number {
        font-size: 48px;
    }

    .job-score-circle .score-circle-suffix {
        font-size: 18px;
        margin-top: 2px;
    }

    .job-score-circle .score-circle-label {
        font-size: 13px;
        margin-top: 10px;
    }

    .job-subsection-title {
        color: #00f5ff;
        font-size: 28px;
        font-weight: 800;
        margin: 4px 0 14px;
        text-shadow: 0 0 14px rgba(0, 245, 255, 0.25);
    }

    .job-keyword-block {
        background: linear-gradient(135deg, #142a45 0%, #0f1a2e 100%);
        border: 1px solid rgba(0, 212, 170, 0.35);
        border-radius: 14px;
        padding: 14px 14px 10px;
        margin-bottom: 14px;
        box-shadow: inset 0 0 14px rgba(0, 212, 170, 0.06);
    }

    .job-keyword-pill {
        border-radius: 24px;
        padding: 7px 12px;
        font-size: 11px;
        font-weight: 700;
        display: inline-block;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.25);
        border: 1px solid transparent;
    }

    .job-keyword-pill.matched {
        background: linear-gradient(135deg, #1f7f5f 0%, #22c55e 100%);
        color: #ecfff5;
        border-color: rgba(134, 239, 172, 0.4);
    }

    .job-keyword-pill.missing {
        background: linear-gradient(135deg, #8f2430 0%, #ef4444 100%);
        color: #fff1f2;
        border-color: rgba(252, 165, 165, 0.35);
    }
    
    /* Suggestion Card - Styled */
    .suggestion-card-styled {
        border-left: 5px solid;
        border-radius: 12px;
        padding: 18px;
        margin: 12px 0;
        background: rgba(0, 0, 0, 0.15);
        color: #ffffff;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .suggestion-card-styled:hover {
        transform: translateX(5px);
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
    }
    
    .suggestion-card-styled.success {
        border-left-color: #4ade80;
        background: linear-gradient(135deg, rgba(74, 222, 128, 0.15) 0%, rgba(34, 197, 94, 0.1) 100%);
    }
    
    .suggestion-card-styled.warning {
        border-left-color: #f59e0b;
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(217, 119, 6, 0.1) 100%);
    }
    
    .suggestion-card-styled.critical {
        border-left-color: #ef4444;
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.1) 100%);
    }
    
    .suggestion-icon {
        font-size: 18px;
        margin-right: 10px;
        display: inline-block;
    }
    
    .suggestion-text {
        font-weight: 700;
        display: block;
        margin-bottom: 6px;
        font-size: 1.05em;
    }
    
    .suggestion-subtext {
        font-size: 13px;
        color: #a8d4ff;
        font-style: italic;
        margin-top: 6px;
    }
    
    /* Old styles kept for compatibility */
    .score-badge {
        width: 180px;
        height: 180px;
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        font-size: 3em;
        font-weight: bold;
        margin: 0 auto;
        box-shadow: 0 0 30px rgba(0, 0, 0, 0.5);
    }
    
    .score-excellent {
        background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
        color: white;
        box-shadow: 0 0 30px rgba(34, 197, 94, 0.5);
    }
    
    .score-good {
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        color: #000;
        box-shadow: 0 0 30px rgba(245, 158, 11, 0.5);
    }
    
    .score-poor {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        box-shadow: 0 0 30px rgba(220, 38, 38, 0.5);
    }
    
    .score-label {
        font-size: 0.7em;
        margin-top: 5px;
        font-weight: bold;
    }
    
    /* Breakdown Scores - Old style kept for compatibility */
    .score-breakdown {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 15px;
        margin-top: 20px;
    }
    
    .breakdown-item {
        background: #1a1a2e;
        border: 1px solid #00d4aa;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }
    
    .breakdown-item .label {
        font-size: 0.85em;
        color: #b0b0b0;
        margin-bottom: 5px;
    }
    
    .breakdown-item .score {
        font-size: 1.8em;
        color: #00d4aa;
        font-weight: bold;
    }

    
    /* Entity Cards */
    .entity-card {
        background: linear-gradient(135deg, #1a2f4f 0%, #0f1a2e 100%);
        border-left: 5px solid #00d4aa;
        border-radius: 12px;
        padding: 22px;
        margin: 16px 0;
        box-shadow: 0 8px 24px rgba(0, 212, 170, 0.15);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border-top: 1px solid rgba(0, 212, 170, 0.2);
    }
    
    .entity-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 32px rgba(0, 212, 170, 0.25);
        border-color: #00f5ff;
    }
    
    .entity-card .title {
        color: #00f5ff;
        font-size: 12px;
        font-weight: 800;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    
    .entity-card .content {
        color: #d4f1ff;
        font-size: 1em;
        line-height: 1.6;
    }
    
    /* Skill Pills */
    .skill-pills {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 12px;
    }
    
    .skill-pill {
        background: linear-gradient(135deg, #00d4aa 0%, #00f5ff 100%);
        color: #000;
        padding: 9px 18px;
        border-radius: 24px;
        font-size: 0.9em;
        font-weight: 700;
        display: inline-block;
        box-shadow: 0 6px 16px rgba(0, 212, 170, 0.3);
        transition: all 0.3s ease;
    }
    
    .skill-pill:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 24px rgba(0, 212, 170, 0.4);
    }
    
    /* Suggestion Cards - Old */
    .suggestion-card {
        border-left: 5px solid #00d4aa;
        border-radius: 8px;
        padding: 15px;
        margin: 12px 0;
        background: #1a1a2e;
        color: #ffffff;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
    
    .suggestion-card.success {
        border-left-color: #4ade80;
        background: rgba(74, 222, 128, 0.1);
    }
    
    .suggestion-card.warning {
        border-left-color: #fbbf24;
        background: rgba(251, 191, 36, 0.1);
    }
    
    .suggestion-card.critical {
        border-left-color: #ef4444;
        background: rgba(239, 68, 68, 0.1);
    }
    
    /* Sidebar Styling */
    .sidebar-box {
        background: linear-gradient(135deg, #1a2f4f 0%, #0f1a2e 100%);
        border: 1.5px solid #00d4aa;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 8px 24px rgba(0, 212, 170, 0.15);
        transition: all 0.3s ease;
    }
    
    .sidebar-box:hover {
        box-shadow: 0 10px 32px rgba(0, 212, 170, 0.25);
        border-color: #00f5ff;
    }
    
    .sidebar-box .title {
        color: #00f5ff;
        font-weight: 800;
        margin-bottom: 12px;
        font-size: 0.95em;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .pro-tip {
        background: linear-gradient(135deg, #0d2137 0%, #0f1a2e 100%);
        border-left: 4px solid #00d4aa;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
        font-size: 0.9em;
        color: #a8d4ff;
        line-height: 1.6;
        box-shadow: 0 4px 12px rgba(0, 212, 170, 0.1);
        transition: all 0.3s ease;
    }
    
    .pro-tip:hover {
        box-shadow: 0 6px 16px rgba(0, 212, 170, 0.2);
        border-left-color: #00f5ff;
    }
    
    /* Streamlit Button Override */
    .stButton > button {
        background: linear-gradient(135deg, #00d4aa 0%, #00f5ff 100%) !important;
        color: #000000 !important;
        font-weight: 700 !important;
        font-size: 1.05em !important;
        padding: 12px 24px !important;
        border-radius: 10px !important;
        border: none !important;
        box-shadow: 0 8px 20px rgba(0, 212, 170, 0.3) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }
    
    .stButton > button:hover {
        box-shadow: 0 12px 32px rgba(0, 212, 170, 0.5) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Tabs Styling */
    .stTabs [role="tab"] {
        color: #b0b0b0;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [role="tab"][aria-selected="true"] {
        color: #00f5ff;
        font-weight: 800;
        border-bottom: 3px solid #00d4aa;
    }

    /* Upload widget styling */
    [data-testid="stFileUploader"] {
        width: 100%;
    }

    [data-testid="stFileUploader"] section {
        border: 2px dashed rgba(0, 212, 170, 0.5) !important;
        border-radius: 12px !important;
        background: #0d2137 !important;
        padding: 0 16px !important;
        min-height: 80px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        transition: all 0.3s ease !important;
    }

    [data-testid="stFileUploader"] section:hover {
        border-color: #00d4aa !important;
        background: #0d2a40 !important;
    }

    /* Keep uploader instructions visible before upload */
    [data-testid="stFileUploaderDropzoneInstructions"] {
        display: block !important;
    }

    [data-testid="stFileUploaderDropzoneInstructions"] > div {
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 14px !important;
    }

    /* When a file exists, hide the empty drop zone and style the file row as the upload box */
    [data-testid="stFileUploader"]:has([data-testid="stFileUploaderFile"]) section {
        display: none !important;
    }

    [data-testid="stFileUploader"]:has([data-testid="stFileUploaderFile"]) section + div {
        margin-top: 0 !important;
        border: 2px dashed rgba(0, 212, 170, 0.5) !important;
        border-radius: 12px !important;
        background: #0d2137 !important;
        padding: 12px 16px !important;
        min-height: 80px !important;
        display: flex !important;
        align-items: center !important;
    }

    [data-testid="stFileUploaderFile"] {
        background: transparent !important;
        border: none !important;
        padding: 4px 0 !important;
    }

    [data-testid="stFileUploaderFileName"] {
        color: #00d4aa !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }

    [data-testid="stFileUploaderFileSize"] {
        color: #718096 !important;
        font-size: 12px !important;
    }

    [data-testid="stFileUploader"] section button {
        background: transparent !important;
        border: 1px solid rgba(0, 212, 170, 0.6) !important;
        color: #00d4aa !important;
        border-radius: 6px !important;
        padding: 6px 16px !important;
        font-size: 13px !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        margin: 0 !important;
        align-self: center !important;
        display: inline-flex !important;
        align-items: center !important;
    }

    [data-testid="stFileUploader"] section button:hover {
        background: rgba(0, 212, 170, 0.1) !important;
        border-color: #00d4aa !important;
    }

    [data-testid="stFileUploaderDropzoneInstructions"] small,
    [data-testid="stFileUploader"] small {
        color: #718096 !important;
        font-size: 12px !important;
    }

    /* Light mode overrides for upload widget */
    [data-theme="light"] [data-testid="stFileUploader"] section {
        background: #f0fff4 !important;
        border-color: rgba(0, 180, 140, 0.5) !important;
    }

    [data-theme="light"] [data-testid="stFileUploader"]:has([data-testid="stFileUploaderFile"]) section + div {
        background: #f0fff4 !important;
        border-color: rgba(0, 180, 140, 0.5) !important;
    }

    [data-theme="light"] [data-testid="stFileUploaderFileName"] {
        color: #00a884 !important;
    }

    [data-theme="light"] [data-testid="stFileUploader"] section button {
        border-color: rgba(0, 180, 140, 0.6) !important;
        color: #00a884 !important;
    }
    
    /* Divider */
    .stDivider {
        background: linear-gradient(90deg, transparent, #00d4aa, transparent) !important;
        height: 2px !important;
    }
    
    @media (max-width: 768px) {
        .score-breakdown {
            grid-template-columns: 1fr;
        }
        .header-banner h1 {
            font-size: 2.2em;
        }
    }
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

# Initialize session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = None
if 'job_description' not in st.session_state:
    st.session_state.job_description = None
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_score_color(score):
    """Return color class based on score"""
    if score >= 70:
        return "score-excellent", "✅ Excellent"
    elif score >= 40:
        return "score-good", "🟡 Good"
    else:
        return "score-poor", "🔴 Needs Improvement"

def create_gauge_chart(score):
    """Create gauge/speedometer chart for ATS score"""
    fig = go.Figure(data=[
        go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "ATS Score"},
            delta={'reference': 80},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "#00d4aa"},
                'steps': [
                    {'range': [0, 40], 'color': "rgba(239, 68, 68, 0.3)"},
                    {'range': [40, 70], 'color': "rgba(251, 191, 36, 0.3)"},
                    {'range': [70, 100], 'color': "rgba(74, 222, 128, 0.3)"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 80
                }
            },
            number={'font': {'size': 40}, 'suffix': ' / 100'}
        )
    ])
    
    fig.update_layout(
        font={'color': '#ffffff', 'family': 'Arial'},
        paper_bgcolor='#1a1a2e',
        plot_bgcolor='#1a1a2e',
        margin={'l': 10, 'r': 10, 't': 30, 'b': 10},
        height=350
    )
    
    return fig

def create_radar_chart(breakdown):
    """Create radar chart for score breakdown - only show categories with scores > 0"""
    all_categories = [
        'Contact Info',
        'Skills',
        'Education',
        'Experience',
        'Keywords',
        'Length'
    ]
    all_values = [
        breakdown.get('contact_info', 0),
        breakdown.get('skills_section', 0),
        breakdown.get('education_section', 0),
        breakdown.get('experience_section', 0),
        breakdown.get('action_verbs_keywords', 0),
        breakdown.get('resume_length', 0)
    ]
    max_values_all = [20, 20, 15, 15, 20, 10]
    
    # Filter out categories with 0 value to avoid clutter
    categories = []
    values = []
    max_values = []
    
    for i, (cat, val, max_val) in enumerate(zip(all_categories, all_values, max_values_all)):
        if val > 0:  # Only include categories with score > 0
            categories.append(cat)
            values.append(val)
            max_values.append(max_val)
    
    # Fallback: if all categories are 0, show all (shouldn't happen, but be safe)
    if not categories:
        categories = all_categories
        values = all_values
        max_values = max_values_all
    
    # Normalize to 0-100 for radar
    normalized_values = [int((v / max_values[i]) * 100) if max_values[i] > 0 else 0 
                        for i, v in enumerate(values)]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=normalized_values,
        theta=categories,
        fill='toself',
        name='Score',
        line_color='#00d4aa',
        fillcolor='rgba(0, 212, 170, 0.3)',
        marker_color='#00f5ff'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(color='#b0b0b0', size=9),
                gridcolor='#16213e'
            ),
            angularaxis=dict(
                tickfont=dict(color='#00d4aa', size=10),
                gridcolor='#16213e'
            ),
            bgcolor='rgba(0, 0, 0, 0.2)'
        ),
        font={'color': '#ffffff', 'family': 'Arial'},
        paper_bgcolor='#1a1a2e',
        showlegend=False,
        height=350,
        margin={'l': 30, 'r': 30, 't': 30, 'b': 30}
    )
    
    return fig

def create_bar_chart(breakdown):
    """Create bar chart comparing scores to max"""
    categories = [
        'Contact\nInfo',
        'Skills',
        'Education',
        'Experience',
        'Keywords',
        'Length'
    ]
    current = [
        breakdown.get('contact_info', 0),
        breakdown.get('skills_section', 0),
        breakdown.get('education_section', 0),
        breakdown.get('experience_section', 0),
        breakdown.get('action_verbs_keywords', 0),
        breakdown.get('resume_length', 0)
    ]
    maximum = [20, 20, 15, 15, 20, 10]
    
    fig = go.Figure(data=[
        go.Bar(
            name='Current Score',
            x=categories,
            y=current,
            marker_color='#00d4aa',
            marker_line_color='#00f5ff',
            marker_line_width=2
        ),
        go.Bar(
            name='Maximum Score',
            x=categories,
            y=maximum,
            marker_color='rgba(0, 212, 170, 0.2)',
            marker_line_color='#00d4aa',
            marker_line_width=1
        )
    ])
    
    fig.update_layout(
        barmode='group',
        font={'color': '#ffffff', 'family': 'Arial'},
        paper_bgcolor='#1a1a2e',
        plot_bgcolor='#16213e',
        xaxis=dict(tickfont=dict(size=10), gridcolor='#16213e'),
        yaxis=dict(tickfont=dict(size=9), gridcolor='#16213e'),
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(0, 0, 0, 0.5)',
            bordercolor='#00d4aa',
            borderwidth=1
        ),
        hovermode='x unified',
        height=350,
        margin={'l': 40, 'r': 15, 't': 20, 'b': 50}
    )
    
    return fig

def perform_analysis(resume_text, job_description=None):
    """Perform complete resume analysis"""

    def extract_education_entries(text):
        """Extract structured education entries using dynamic service logic."""
        return extract_education(text)

    # Extract entities
    entities = hf_client.extract_entities(resume_text)
    
    # Add experience extraction
    try:
        experience_list = extract_work_experience(resume_text)
        entities['experience'] = experience_list
    except Exception as e:
        print(f"[DEBUG] Experience extraction error: {e}")
        entities['experience'] = []

    # Add structured education extraction for UI display (similar to experience cards)
    try:
        education_entries = extract_education_entries(resume_text)
        entities['education_details'] = education_entries
    except Exception as e:
        print(f"[DEBUG] Education extraction error: {e}")
        entities['education_details'] = []
    
    # Calculate ATS score
    ats_result = ats_scorer.calculate_ats_score(resume_text, entities=entities)
    
    # Get job match if job description provided
    job_match = None
    if job_description:
        job_match = matcher.get_job_match(resume_text, job_description)
    
    return {
        'entities': entities,
        'ats_score': ats_result,
        'job_match': job_match,
        'resume_text': resume_text,
        'job_description': job_description
    }

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

# ============================================================================
# MAIN APP
# ============================================================================

# Header Banner
st.markdown("""
<div class="header-banner">
    <h1>📄 Resume Analyzer</h1>
    <p>ATS-Optimized · AI-Powered · Instant Feedback</p>
    <div class="underline-glow"></div>
</div>
""", unsafe_allow_html=True)

# File Upload Section
st.markdown("### 📤 Upload Your Resume")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="upload-card">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Choose a PDF, DOCX, or TXT file (max 5MB)",
        type=['pdf', 'docx', 'txt'],
        key="file_uploader"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Persist uploaded file in session state
    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file

with col2:
    st.markdown("### ⚙️ Options")
    analyze_job_match = st.checkbox("Match with Job Description?", value=False)

# Parse the file and extract text
if uploaded_file is not None:
    try:
        if uploaded_file.type == "application/pdf":
            resume_text = parser.parse_pdf(uploaded_file)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            resume_text = parser.parse_docx(uploaded_file)
        else:
            resume_text = parser.parse_txt(uploaded_file)
        
        st.session_state.resume_text = resume_text
        
        # Job description input
        if analyze_job_match:
            st.markdown("### 💼 Paste Job Description (Optional)")
            job_description = st.text_area(
                "Enter the job description you're applying for:",
                height=150,
                key="job_desc_input"
            )
            st.session_state.job_description = job_description if job_description else None
    
    except Exception as e:
        st.error(f"❌ Error parsing file: {str(e)}")

# Analyze Button
if st.session_state.resume_text:
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🔍 Analyze Resume", use_container_width=True, type="primary"):
            with st.spinner("🤖 Analyzing your resume..."):
                try:
                    st.session_state.analysis_results = perform_analysis(
                        st.session_state.resume_text,
                        st.session_state.job_description
                    )
                    st.success("✅ Analysis complete!")
                except Exception as e:
                    st.error(f"❌ Analysis error: {str(e)}")
                    print(f"[ERROR] {str(e)}")

# ============================================================================
# RESULTS SECTION
# ============================================================================

if st.session_state.analysis_results:
    results = st.session_state.analysis_results
    entities = results['entities']
    ats_data = results['ats_score']
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 ATS Score", "👤 Entity Extraction", "💼 Job Match", "💡 Suggestions"])
    
    # ========== TAB 1: ATS SCORE ==========
    with tab1:
        score = ats_data['score']
        breakdown = ats_data['breakdown']
        
        # Determine score class
        if score >= 70:
            score_class = "excellent"
            score_label = "Excellent"
        elif score >= 40:
            score_class = "good"
            score_label = "Good"
        else:
            score_class = "poor"
            score_label = "Needs Work"
        
        # Score circle
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            st.markdown(f"""
            <div class="score-circle {score_class}">
                <div class="score-circle-number">{score}</div>
                <div class="score-circle-suffix">/100</div>
                <div class="score-circle-label">{score_label}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Score Breakdown Cards
        st.markdown('<div class="section-header">Score Breakdown</div>', unsafe_allow_html=True)
        
        breakdown_data = [
            ("📇", "Contact Info", breakdown.get('contact_info', 0), 20),
            ("🛠️", "Skills", breakdown.get('skills_section', 0), 20),
            ("🎓", "Education", breakdown.get('education_section', 0), 15),
            ("💼", "Experience", breakdown.get('experience_section', 0), 15),
            ("🔑", "Keywords", breakdown.get('action_verbs_keywords', 0), 20),
            ("📏", "Length", breakdown.get('resume_length', 0), 10),
        ]
        
        cols = st.columns(3)
        
        for idx, (icon, category, current, max_score) in enumerate(breakdown_data):
            with cols[idx % 3]:
                percentage = (current / max_score * 100) if max_score > 0 else 0
                
                if percentage >= 80:
                    bar_class = "excellent"
                elif percentage >= 50:
                    bar_class = "good"
                else:
                    bar_class = "poor"
                
                st.markdown(f"""
                <div class="breakdown-card">
                    <div class="breakdown-card-category">{icon} {category}</div>
                    <div class="breakdown-card-score">{current}/{max_score}</div>
                    <div class="progress-bar">
                        <div class="progress-bar-fill {bar_class}" style="width: {percentage}%"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.divider()
        
        # Charts Section
        st.markdown('<div class="section-header">Visual Analysis</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            gauge_fig = create_gauge_chart(score)
            gauge_fig.update_layout(height=350, margin={'l': 20, 'r': 20, 't': 40, 'b': 20})
            st.plotly_chart(gauge_fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            radar_fig = create_radar_chart(breakdown)
            radar_fig.update_layout(height=350, margin={'l': 20, 'r': 20, 't': 40, 'b': 20})
            st.plotly_chart(radar_fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        bar_fig = create_bar_chart(breakdown)
        bar_fig.update_layout(height=350, margin={'l': 50, 'r': 20, 't': 30, 'b': 60})
        st.plotly_chart(bar_fig, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ========== TAB 2: ENTITY EXTRACTION ==========
    with tab2:
        st.markdown("#### 👤 Contact Information")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="entity-card">
                <div class="title">👤 Name</div>
                <div class="content">{entities.get('name') or 'Not detected'}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="entity-card">
                <div class="title">📧 Email</div>
                <div class="content">{entities.get('email') or 'Not detected'}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="entity-card">
                <div class="title">📱 Phone</div>
                <div class="content">{entities.get('phone') or 'Not detected'}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Skills
        st.markdown("#### 💻 Technical Skills")
        skills = entities.get('skills', [])
        if skills:
            skills_html = '<div class="skill-pills">'
            for skill in skills[:15]:  # Limit to 15 skills
                skills_html += f'<div class="skill-pill">{skill}</div>'
            skills_html += '</div>'
            st.markdown(skills_html, unsafe_allow_html=True)
        else:
            st.info("No skills detected. Consider adding a dedicated skills section.")
        
        # Education
        st.markdown("#### 🎓 Education")
        education_entries = entities.get('education_details', [])

        if education_entries:
            for entry in education_entries[:8]:
                if isinstance(entry, dict):
                    institution = str(entry.get('institution', '')).strip()
                    degree = str(entry.get('degree', '')).strip()
                    year = str(entry.get('year', '')).strip()
                    location = str(entry.get('location', '')).strip()

                    parts = [p for p in [institution, degree, year, location] if p]
                    safe_entry = " | ".join(parts)
                else:
                    safe_entry = str(entry).strip()

                if not safe_entry:
                    continue
                st.markdown(f"""
                <div style="background:#0d2137; border-left:3px solid #00d4aa;
                            border-radius:8px; padding:12px 16px; margin-bottom:8px;">
                    <span style="color:#00d4aa; font-size:13px;">🎓</span>
                    <span style="color:#e2e8f0; font-size:14px; margin-left:8px;">{safe_entry}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No education entries detected")
        
        # Experience
        st.markdown("#### 💼 Work Experience")
        experience = entities.get('experience', [])
        experience_found = False
        if experience and len(experience) > 0:
            for exp in experience[:5]:
                if isinstance(exp, dict):
                    experience_found = True
                    title = exp.get('title', 'Unknown')
                    company = exp.get('company', '')
                    duration = exp.get('duration', '')
                    description = exp.get('description', '')
                    
                    st.markdown(f"""
                    <div class="entity-card">
                        <div class="title">{title}</div>
                        <div class="content">
                            <strong>{company}</strong><br>
                            <em>{duration}</em><br>
                            {description}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        if not experience_found:
            st.info("No experience detected")
    
    # ========== TAB 3: JOB MATCH ==========
    with tab3:
        if results['job_match']:
            job_match = results['job_match']
            match_score = job_match.get('match_score', 0)
            matched_keywords = job_match.get('matched_keywords', [])
            missing_keywords = job_match.get('missing_keywords', [])
            total_keywords = len(matched_keywords) + len(missing_keywords)
            coverage = int((len(matched_keywords) / total_keywords) * 100) if total_keywords > 0 else 0
            
            # Match overview
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if match_score >= 70:
                    match_class = "excellent"
                    match_label = "Strong Match"
                    score_color = "#4ade80"
                elif match_score >= 40:
                    match_class = "good"
                    match_label = "Partial Match"
                    score_color = "#f59e0b"
                else:
                    match_class = "poor"
                    match_label = "Needs Improvement"
                    score_color = "#ef4444"

                feedback = job_match.get("feedback", "")

                st.markdown(f"""
                <div class="job-match-card" style="display:flex; align-items:center; justify-content:space-between; gap:2rem; flex-wrap:wrap; padding:1.8rem 2.5rem;">
                    <div style="display:flex; flex-direction:row; align-items:baseline; justify-content:center; min-width:110px; gap:0.3rem;">
                        <div style="font-size:3.5rem; font-weight:900; color:{score_color}; line-height:1; letter-spacing:-0.02em;">{match_score}</div>
                        <div style="font-size:0.9rem; color:#718096; font-weight:500;">/ 100</div>
                    </div>
                    <div style="flex:1; min-width:160px; display:flex; flex-direction:column; gap:0.5rem;">
                        <div style="font-size:0.75rem; font-weight:700; color:#718096; text-transform:uppercase; letter-spacing:0.12em;">Job Match Score</div>
                        <div style="font-size:1.15rem; font-weight:800; color:{score_color}; text-transform:uppercase; letter-spacing:0.06em;">{match_label}</div>
                        <div style="font-size:0.88rem; color:#a0aec0; line-height:1.55; margin-top:0.2rem;">{feedback}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="job-match-card">
                    <div class="job-match-title">📊 Match Details</div>
                    <div class="job-match-stats">
                        <div class="job-stat-tile">
                            <div class="job-stat-label">Matched Keywords</div>
                            <div class="job-stat-value matched">{len(matched_keywords)}</div>
                        </div>
                        <div class="job-stat-tile">
                            <div class="job-stat-label">Missing Keywords</div>
                            <div class="job-stat-value missing">{len(missing_keywords)}</div>
                        </div>
                        <div class="job-stat-tile">
                            <div class="job-stat-label">Coverage</div>
                            <div class="job-stat-value">{coverage}%</div>
                        </div>
                        <div class="job-stat-tile">
                            <div class="job-stat-label">Total Keywords</div>
                            <div class="job-stat-value">{total_keywords}</div>
                        </div>
                    </div>
                    <div class="job-coverage-wrap">
                        <div class="job-coverage-label">Keyword Match Progress</div>
                        <div class="job-coverage-bar">
                            <div class="job-coverage-fill" style="width: {coverage}%;"></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.divider()
            
            # Matched keywords
            st.markdown('<div class="job-subsection-title">✅ Matched Keywords</div>', unsafe_allow_html=True)
            if matched_keywords:
                matched_html = '<div class="job-keyword-block"><div class="skill-pills">'
                for keyword in matched_keywords[:20]:
                    matched_html += f'<div class="job-keyword-pill matched">{keyword}</div>'
                matched_html += '</div></div>'
                st.markdown(matched_html, unsafe_allow_html=True)
            else:
                st.info("No keywords matched.")
            
            # Missing keywords
            st.markdown('<div class="job-subsection-title">❌ Missing Keywords (To Add)</div>', unsafe_allow_html=True)
            if missing_keywords:
                missing_html = '<div class="job-keyword-block"><div class="skill-pills">'
                for keyword in missing_keywords[:20]:
                    missing_html += f'<div class="job-keyword-pill missing">{keyword}</div>'
                missing_html += '</div></div>'
                st.markdown(missing_html, unsafe_allow_html=True)
            else:
                st.success("You have all the keywords!")
        else:
            st.info("💡 Upload a job description to see match analysis.")
    
    # ========== TAB 4: SUGGESTIONS ==========
    with tab4:
        suggestions = ats_data['suggestions']
        extracted_keywords = ats_data['extracted_keywords']
        
        # Summary header
        issues_count = len([s for s in suggestions[1:] if s])  # Count non-summary suggestions
        st.markdown(f'<div class="section-header">Found {issues_count} issue(s) · Score: {ats_data["score"]}/100</div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Display suggestions with styled cards
        for i, suggestion in enumerate(suggestions):
            if i == 0:  # Summary line
                if "well-optimized" in suggestion.lower():
                    card_class = "success"
                    icon = "✅"
                    subtext = "Your resume meets ATS standards and is ready for submission."
                elif "good" in suggestion.lower():
                    card_class = "warning"
                    icon = "⚠️"
                    subtext = "Review the suggestions below to improve further."
                else:
                    card_class = "critical"
                    icon = "🔴"
                    subtext = "Follow the critical suggestions below to improve your ATS score significantly."
                
                st.markdown(f"""
                <div class="suggestion-card-styled {card_class}">
                    <span class="suggestion-icon">{icon}</span>
                    <span class="suggestion-text">{suggestion}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Determine suggestion type and styling
                suggestion_lower = suggestion.lower()
                
                if "missing" in suggestion_lower or "add your full name" in suggestion_lower or "add your phone" in suggestion_lower or "include a professional email" in suggestion_lower:
                    card_class = "critical"
                    icon = "🔴"
                    if "full name" in suggestion_lower:
                        subtext = "A name is essential for ATS parsing and recruiter contact."
                    elif "email" in suggestion_lower:
                        subtext = "Email is critical for recruiters to reach you."
                    elif "phone" in suggestion_lower:
                        subtext = "Phone number provides backup contact information."
                    else:
                        subtext = "This is a critical missing element."
                elif "add an experience" in suggestion_lower or "add an education" in suggestion_lower or "list 5+" in suggestion_lower:
                    card_class = "warning"
                    icon = "⚠️"
                    if "experience" in suggestion_lower:
                        subtext = "Work experience is important for ATS matching."
                    elif "education" in suggestion_lower:
                        subtext = "Education helps establish credentials."
                    else:
                        subtext = "More skills increase keyword matching chances."
                elif "action verb" in suggestion_lower or "keyword" in suggestion_lower:
                    card_class = "warning"
                    icon = "⚠️"
                    subtext = "Using specific action verbs improves ATS scoring."
                elif "keep resume" in suggestion_lower or "length" in suggestion_lower:
                    card_class = "warning"
                    icon = "⚠️"
                    subtext = "Optimal length ensures all content is parsed by ATS."
                else:
                    card_class = "warning"
                    icon = "ℹ️"
                    subtext = "Review this suggestion to optimize your resume."
                
                st.markdown(f"""
                <div class="suggestion-card-styled {card_class}">
                    <span class="suggestion-icon">{icon}</span>
                    <span class="suggestion-text">{suggestion}</span>
                    <span class="suggestion-subtext">{subtext}</span>
                </div>
                """, unsafe_allow_html=True)
        
        st.divider()
        
        # Extracted keywords section
        st.markdown('<div class="section-header">🔑 Extracted Keywords</div>', unsafe_allow_html=True)
        
        if extracted_keywords:
            keywords_html = '<div class="keyword-pills-container">'
            for keyword in extracted_keywords[:20]:
                keywords_html += f'<div class="keyword-pill">{keyword}</div>'
            keywords_html += '</div>'
            st.markdown(keywords_html, unsafe_allow_html=True)
        else:
            st.info("No technical keywords detected")


# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("### 📚 How It Works")
    
    with st.expander("Process Overview", expanded=False):
          st.markdown(
                """
1. Upload Your Resume  
    Submit a PDF, DOCX, or TXT file

2. AI Analysis  
    Our AI extracts entities and calculates scores

3. Get Insights  
    Receive actionable recommendations

4. Improve & Resubmit  
    Make adjustments and re-analyze
                """
          )
    
    st.markdown("---")
    
    st.markdown("### 🎯 Score Legend")
    
    st.markdown("""
    <div class="sidebar-box">
        <div class="title">Score Ranges</div>
        <div style="font-size: 0.9em; color: #b0b0b0;">
            <strong style="color: #4ade80;">70-100:</strong> Excellent<br>
            <strong style="color: #fbbf24;">40-69:</strong> Good<br>
            <strong style="color: #ef4444;">0-39:</strong> Needs Work
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 💡 Pro Tips")
    
    st.markdown("""
    <div class="sidebar-box">
        <div class="pro-tip">
            <strong style="color: #00d4aa;">✅ Format Matters</strong><br>
            Use clear section headers and consistent formatting
        </div>
        <div class="pro-tip">
            <strong style="color: #00d4aa;">✅ Keywords First</strong><br>
            Mirror job description keywords naturally
        </div>
        <div class="pro-tip">
            <strong style="color: #00d4aa;">✅ Quantify Results</strong><br>
            Use numbers: "Increased sales by 30%"
        </div>
        <div class="pro-tip">
            <strong style="color: #00d4aa;">✅ Action Verbs</strong><br>
            Start bullets with: managed, developed, led
        </div>
        <div class="pro-tip">
            <strong style="color: #00d4aa;">✅ Optimal Length</strong><br>
            Keep it between 300-800 words
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### ℹ️ About")
    st.info(
        "Resume Analyzer V2 uses AI to optimize your resume for ATS systems. "
        "All analysis is performed locally and securely."
    )

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.markdown("""
<div style="text-align: center; color: #b0b0b0; font-size: 12px; padding: 20px 0;">
    <p>Resume Analyzer v2.0 | Powered by AI & Streamlit</p>
    <p>Made with ❤️ | Premium Resume Analysis</p>
</div>
""", unsafe_allow_html=True)
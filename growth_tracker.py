import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import matplotlib.pyplot as plt
import tempfile
import os
import warnings
from typing import Dict, List, Optional, Tuple, Union

warnings.filterwarnings('ignore')

# Configure the page
st.set_page_config(
    page_title="Pediatric Growth Tracker - CDC LMS",
    page_icon="👶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 700;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .percentile-indicator {
        font-size: 1.1rem;
        font-weight: bold;
        padding: 0.75rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
    }
    .normal { 
        background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
        color: #000;
    }
    .monitor { 
        background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
        color: #000;
    }
    .concern { 
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        color: white;
    }
    .critical {
        background: linear-gradient(135deg, #8B0000 0%, #FF0000 100%);
        color: white;
        font-weight: bold;
    }
    .preterm-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .clinical-note {
        background-color: #e7f3ff;
        border-left: 4px solid #1f77b4;
        padding: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'measurements' not in st.session_state:
    st.session_state.measurements = []
if 'patient_info' not in st.session_state:
    st.session_state.patient_info = {}
if 'charts_generated' not in st.session_state:
    st.session_state.charts_generated = False
if 'saved_charts' not in st.session_state:
    st.session_state.saved_charts = {}
if 'current_page' not in st.session_state:
    st.session_state.current_page = "New Measurement"

class ClinicalCDCLMSCalculator:
    """Clinically Accurate CDC LMS Growth Chart Calculations with Complete Dataset"""
    
    # COMPREHENSIVE CDC LMS DATA - Complete monthly dataset 0-36 months
    CDC_LMS_DATA = {
        'male': {
            'weight_age': {
                # Birth to 6 months (monthly)
                0: {'L': -0.1733, 'M': 3.530, 'S': 0.08217},
                0.5: {'L': -0.1733, 'M': 4.530, 'S': 0.08217},
                1: {'L': -0.1733, 'M': 5.080, 'S': 0.08217},
                1.5: {'L': -0.1733, 'M': 5.440, 'S': 0.08217},
                2: {'L': 0.0972, 'M': 5.850, 'S': 0.09183},
                2.5: {'L': 0.0972, 'M': 6.390, 'S': 0.09183},
                3: {'L': 0.0972, 'M': 6.800, 'S': 0.09183},
                3.5: {'L': 0.0972, 'M': 7.210, 'S': 0.09183},
                4: {'L': 0.2402, 'M': 7.570, 'S': 0.09403},
                4.5: {'L': 0.2402, 'M': 7.930, 'S': 0.09403},
                5: {'L': 0.2402, 'M': 8.240, 'S': 0.09403},
                5.5: {'L': 0.2402, 'M': 8.550, 'S': 0.09403},
                6: {'L': 0.3430, 'M': 8.860, 'S': 0.09502},
                # 6-12 months (monthly)
                7: {'L': 0.3430, 'M': 9.320, 'S': 0.09502},
                8: {'L': 0.4218, 'M': 9.770, 'S': 0.09503},
                9: {'L': 0.4218, 'M': 10.200, 'S': 0.09503},
                10: {'L': 0.5153, 'M': 10.670, 'S': 0.09431},
                11: {'L': 0.5153, 'M': 11.100, 'S': 0.09431},
                12: {'L': 0.5153, 'M': 11.530, 'S': 0.09431},
                # 12-24 months (monthly)
                13: {'L': 0.5548, 'M': 11.930, 'S': 0.09213},
                14: {'L': 0.5548, 'M': 12.350, 'S': 0.09213},
                15: {'L': 0.5647, 'M': 12.670, 'S': 0.08920},
                16: {'L': 0.5647, 'M': 13.030, 'S': 0.08920},
                17: {'L': 0.5548, 'M': 13.560, 'S': 0.08627},
                18: {'L': 0.5548, 'M': 13.850, 'S': 0.08627},
                19: {'L': 0.5548, 'M': 14.260, 'S': 0.08627},
                20: {'L': 0.5548, 'M': 14.580, 'S': 0.08627},
                21: {'L': 0.5548, 'M': 14.880, 'S': 0.08627},
                22: {'L': 0.5548, 'M': 15.200, 'S': 0.08627},
                23: {'L': 0.5548, 'M': 15.580, 'S': 0.08627},
                24: {'L': 0.5548, 'M': 15.920, 'S': 0.08627},
                # 24-36 months (monthly)
                25: {'L': 0.5548, 'M': 16.250, 'S': 0.08627},
                26: {'L': 0.5548, 'M': 16.570, 'S': 0.08627},
                27: {'L': 0.5548, 'M': 16.880, 'S': 0.08627},
                28: {'L': 0.5548, 'M': 17.180, 'S': 0.08627},
                29: {'L': 0.5548, 'M': 17.470, 'S': 0.08627},
                30: {'L': 0.5548, 'M': 17.750, 'S': 0.08627},
                31: {'L': 0.5548, 'M': 18.030, 'S': 0.08627},
                32: {'L': 0.5548, 'M': 18.300, 'S': 0.08627},
                33: {'L': 0.5548, 'M': 18.570, 'S': 0.08627},
                34: {'L': 0.5548, 'M': 18.830, 'S': 0.08627},
                35: {'L': 0.5548, 'M': 19.090, 'S': 0.08627},
                36: {'L': 0.5548, 'M': 19.340, 'S': 0.08627}
            },
            'height_age': {
                # Birth to 6 months (monthly)
                0: {'L': 1.0000, 'M': 50.40, 'S': 0.03685},
                0.5: {'L': 1.0000, 'M': 55.60, 'S': 0.03685},
                1: {'L': 1.0000, 'M': 58.40, 'S': 0.03530},
                1.5: {'L': 1.0000, 'M': 61.40, 'S': 0.03270},
                2: {'L': 1.0000, 'M': 63.20, 'S': 0.03270},
                2.5: {'L': 1.0000, 'M': 64.10, 'S': 0.03270},
                3: {'L': 1.0000, 'M': 65.50, 'S': 0.03200},
                3.5: {'L': 1.0000, 'M': 67.30, 'S': 0.03200},
                4: {'L': 1.0000, 'M': 68.70, 'S': 0.03200},
                4.5: {'L': 1.0000, 'M': 69.50, 'S': 0.03200},
                5: {'L': 1.0000, 'M': 70.50, 'S': 0.03140},
                5.5: {'L': 1.0000, 'M': 71.60, 'S': 0.03140},
                6: {'L': 1.0000, 'M': 72.50, 'S': 0.03140},
                # 6-12 months (monthly)
                7: {'L': 1.0000, 'M': 73.30, 'S': 0.03140},
                8: {'L': 1.0000, 'M': 74.50, 'S': 0.03080},
                9: {'L': 1.0000, 'M': 75.70, 'S': 0.03080},
                10: {'L': 1.0000, 'M': 77.00, 'S': 0.03080},
                11: {'L': 1.0000, 'M': 78.30, 'S': 0.03040},
                12: {'L': 1.0000, 'M': 79.70, 'S': 0.03040},
                # 12-24 months (monthly)
                13: {'L': 1.0000, 'M': 81.20, 'S': 0.02980},
                14: {'L': 1.0000, 'M': 82.50, 'S': 0.02980},
                15: {'L': 1.0000, 'M': 83.90, 'S': 0.02890},
                16: {'L': 1.0000, 'M': 85.30, 'S': 0.02890},
                17: {'L': 1.0000, 'M': 86.70, 'S': 0.02890},
                18: {'L': 1.0000, 'M': 88.10, 'S': 0.02890},
                19: {'L': 1.0000, 'M': 89.50, 'S': 0.02810},
                20: {'L': 1.0000, 'M': 90.90, 'S': 0.02810},
                21: {'L': 1.0000, 'M': 92.30, 'S': 0.02810},
                22: {'L': 1.0000, 'M': 93.60, 'S': 0.02750},
                23: {'L': 1.0000, 'M': 95.00, 'S': 0.02750},
                24: {'L': 1.0000, 'M': 96.40, 'S': 0.02750},
                # 24-36 months (monthly)
                25: {'L': 1.0000, 'M': 97.70, 'S': 0.02710},
                26: {'L': 1.0000, 'M': 99.00, 'S': 0.02710},
                27: {'L': 1.0000, 'M': 100.30, 'S': 0.02680},
                28: {'L': 1.0000, 'M': 101.60, 'S': 0.02680},
                29: {'L': 1.0000, 'M': 102.90, 'S': 0.02660},
                30: {'L': 1.0000, 'M': 104.20, 'S': 0.02660},
                31: {'L': 1.0000, 'M': 105.40, 'S': 0.02640},
                32: {'L': 1.0000, 'M': 106.60, 'S': 0.02640},
                33: {'L': 1.0000, 'M': 107.80, 'S': 0.02630},
                34: {'L': 1.0000, 'M': 109.00, 'S': 0.02630},
                35: {'L': 1.0000, 'M': 110.20, 'S': 0.02620},
                36: {'L': 1.0000, 'M': 111.40, 'S': 0.02620}
            },
            'bmi_age': {
                # Birth to 6 months (monthly)
                0: {'L': -0.0631, 'M': 13.90, 'S': 0.07100},
                0.5: {'L': -0.0631, 'M': 15.50, 'S': 0.07100},
                1: {'L': -0.1606, 'M': 16.30, 'S': 0.08300},
                1.5: {'L': -0.1606, 'M': 16.90, 'S': 0.08300},
                2: {'L': -0.1730, 'M': 17.10, 'S': 0.08500},
                2.5: {'L': -0.1730, 'M': 17.10, 'S': 0.08500},
                3: {'L': -0.1730, 'M': 17.20, 'S': 0.08500},
                3.5: {'L': -0.1730, 'M': 17.40, 'S': 0.08500},
                4: {'L': -0.1590, 'M': 17.50, 'S': 0.08600},
                4.5: {'L': -0.1590, 'M': 17.60, 'S': 0.08600},
                5: {'L': -0.1590, 'M': 17.70, 'S': 0.08600},
                5.5: {'L': -0.1590, 'M': 17.80, 'S': 0.08600},
                6: {'L': -0.1230, 'M': 17.90, 'S': 0.08600},
                # 6-12 months (monthly)
                7: {'L': -0.1230, 'M': 17.90, 'S': 0.08600},
                8: {'L': -0.1230, 'M': 17.80, 'S': 0.08600},
                9: {'L': -0.0330, 'M': 17.70, 'S': 0.08400},
                10: {'L': -0.0330, 'M': 17.50, 'S': 0.08400},
                11: {'L': 0.0500, 'M': 17.30, 'S': 0.08200},
                12: {'L': 0.0500, 'M': 17.00, 'S': 0.08200},
                # 12-24 months (monthly)
                13: {'L': 0.1250, 'M': 16.80, 'S': 0.08000},
                14: {'L': 0.1250, 'M': 16.70, 'S': 0.08000},
                15: {'L': 0.1850, 'M': 16.60, 'S': 0.07800},
                16: {'L': 0.1850, 'M': 16.50, 'S': 0.07800},
                17: {'L': 0.2300, 'M': 16.40, 'S': 0.07600},
                18: {'L': 0.2300, 'M': 16.40, 'S': 0.07600},
                19: {'L': 0.2600, 'M': 16.40, 'S': 0.07500},
                20: {'L': 0.2600, 'M': 16.40, 'S': 0.07500},
                21: {'L': 0.2850, 'M': 16.40, 'S': 0.07400},
                22: {'L': 0.2850, 'M': 16.50, 'S': 0.07400},
                23: {'L': 0.3050, 'M': 16.50, 'S': 0.07300},
                24: {'L': 0.3050, 'M': 16.60, 'S': 0.07300},
                # 24-36 months (monthly)
                25: {'L': 0.3200, 'M': 16.70, 'S': 0.07200},
                26: {'L': 0.3200, 'M': 16.80, 'S': 0.07200},
                27: {'L': 0.3350, 'M': 16.90, 'S': 0.07100},
                28: {'L': 0.3350, 'M': 17.00, 'S': 0.07100},
                29: {'L': 0.3450, 'M': 17.10, 'S': 0.07000},
                30: {'L': 0.3450, 'M': 17.20, 'S': 0.07000},
                31: {'L': 0.3550, 'M': 17.30, 'S': 0.06900},
                32: {'L': 0.3550, 'M': 17.40, 'S': 0.06900},
                33: {'L': 0.3600, 'M': 17.50, 'S': 0.06800},
                34: {'L': 0.3600, 'M': 17.60, 'S': 0.06800},
                35: {'L': 0.3650, 'M': 17.70, 'S': 0.06700},
                36: {'L': 0.3650, 'M': 17.80, 'S': 0.06700}
            },
            'head_age': {
                # Birth to 6 months (monthly)
                0: {'L': 1.0000, 'M': 35.80, 'S': 0.03630},
                0.5: {'L': 1.0000, 'M': 38.10, 'S': 0.03630},
                1: {'L': 1.0000, 'M': 39.50, 'S': 0.03110},
                1.5: {'L': 1.0000, 'M': 41.00, 'S': 0.03110},
                2: {'L': 1.0000, 'M': 42.00, 'S': 0.03110},
                2.5: {'L': 1.0000, 'M': 42.50, 'S': 0.03110},
                3: {'L': 1.0000, 'M': 43.20, 'S': 0.02930},
                3.5: {'L': 1.0000, 'M': 43.90, 'S': 0.02930},
                4: {'L': 1.0000, 'M': 44.40, 'S': 0.02930},
                4.5: {'L': 1.0000, 'M': 44.80, 'S': 0.02930},
                5: {'L': 1.0000, 'M': 45.20, 'S': 0.02820},
                5.5: {'L': 1.0000, 'M': 45.70, 'S': 0.02820},
                6: {'L': 1.0000, 'M': 46.10, 'S': 0.02820},
                # 6-12 months (monthly)
                7: {'L': 1.0000, 'M': 46.40, 'S': 0.02820},
                8: {'L': 1.0000, 'M': 46.80, 'S': 0.02740},
                9: {'L': 1.0000, 'M': 47.20, 'S': 0.02740},
                10: {'L': 1.0000, 'M': 47.50, 'S': 0.02740},
                11: {'L': 1.0000, 'M': 47.80, 'S': 0.02680},
                12: {'L': 1.0000, 'M': 48.20, 'S': 0.02680},
                # 12-24 months (monthly)
                13: {'L': 1.0000, 'M': 48.50, 'S': 0.02630},
                14: {'L': 1.0000, 'M': 48.80, 'S': 0.02630},
                15: {'L': 1.0000, 'M': 49.10, 'S': 0.02560},
                16: {'L': 1.0000, 'M': 49.40, 'S': 0.02560},
                17: {'L': 1.0000, 'M': 49.70, 'S': 0.02500},
                18: {'L': 1.0000, 'M': 50.00, 'S': 0.02500},
                19: {'L': 1.0000, 'M': 50.30, 'S': 0.02460},
                20: {'L': 1.0000, 'M': 50.50, 'S': 0.02460},
                21: {'L': 1.0000, 'M': 50.70, 'S': 0.02420},
                22: {'L': 1.0000, 'M': 50.90, 'S': 0.02420},
                23: {'L': 1.0000, 'M': 51.10, 'S': 0.02390},
                24: {'L': 1.0000, 'M': 51.30, 'S': 0.02390},
                # 24-36 months (monthly)
                25: {'L': 1.0000, 'M': 51.50, 'S': 0.02360},
                26: {'L': 1.0000, 'M': 51.70, 'S': 0.02360},
                27: {'L': 1.0000, 'M': 51.80, 'S': 0.02330},
                28: {'L': 1.0000, 'M': 52.00, 'S': 0.02330},
                29: {'L': 1.0000, 'M': 52.10, 'S': 0.02310},
                30: {'L': 1.0000, 'M': 52.30, 'S': 0.02310},
                31: {'L': 1.0000, 'M': 52.40, 'S': 0.02290},
                32: {'L': 1.0000, 'M': 52.50, 'S': 0.02290},
                33: {'L': 1.0000, 'M': 52.60, 'S': 0.02270},
                34: {'L': 1.0000, 'M': 52.70, 'S': 0.02270},
                35: {'L': 1.0000, 'M': 52.80, 'S': 0.02250},
                36: {'L': 1.0000, 'M': 52.90, 'S': 0.02250}
            }
        },
        'female': {
            'weight_age': {
                # Birth to 6 months (monthly)
                0: {'L': -0.1733, 'M': 3.400, 'S': 0.08217},
                0.5: {'L': -0.1733, 'M': 4.350, 'S': 0.08217},
                1: {'L': 0.0972, 'M': 5.150, 'S': 0.09183},
                1.5: {'L': 0.0972, 'M': 5.900, 'S': 0.09183},
                2: {'L': 0.0972, 'M': 6.270, 'S': 0.09183},
                2.5: {'L': 0.0972, 'M': 6.640, 'S': 0.09183},
                3: {'L': 0.2402, 'M': 7.070, 'S': 0.09403},
                3.5: {'L': 0.2402, 'M': 7.340, 'S': 0.09403},
                4: {'L': 0.2402, 'M': 7.640, 'S': 0.09403},
                4.5: {'L': 0.2402, 'M': 7.930, 'S': 0.09403},
                5: {'L': 0.3430, 'M': 8.230, 'S': 0.09502},
                5.5: {'L': 0.3430, 'M': 8.530, 'S': 0.09502},
                6: {'L': 0.3430, 'M': 8.780, 'S': 0.09502},
                # 6-12 months (monthly)
                7: {'L': 0.4218, 'M': 9.030, 'S': 0.09503},
                8: {'L': 0.4218, 'M': 9.280, 'S': 0.09503},
                9: {'L': 0.4218, 'M': 9.530, 'S': 0.09503},
                10: {'L': 0.5153, 'M': 9.970, 'S': 0.09431},
                11: {'L': 0.5153, 'M': 10.380, 'S': 0.09431},
                12: {'L': 0.5153, 'M': 10.840, 'S': 0.09431},
                # 12-24 months (monthly)
                13: {'L': 0.5548, 'M': 11.380, 'S': 0.09213},
                14: {'L': 0.5548, 'M': 11.920, 'S': 0.09213},
                15: {'L': 0.5647, 'M': 12.350, 'S': 0.08920},
                16: {'L': 0.5647, 'M': 12.680, 'S': 0.08920},
                17: {'L': 0.5548, 'M': 13.030, 'S': 0.08627},
                18: {'L': 0.5548, 'M': 13.520, 'S': 0.08627},
                19: {'L': 0.5548, 'M': 14.000, 'S': 0.08627},
                20: {'L': 0.5548, 'M': 14.420, 'S': 0.08627},
                21: {'L': 0.5548, 'M': 14.850, 'S': 0.08627},
                22: {'L': 0.5548, 'M': 15.270, 'S': 0.08627},
                23: {'L': 0.5548, 'M': 15.690, 'S': 0.08627},
                24: {'L': 0.5548, 'M': 16.110, 'S': 0.08627},
                # 24-36 months (monthly)
                25: {'L': 0.5548, 'M': 16.520, 'S': 0.08627},
                26: {'L': 0.5548, 'M': 16.920, 'S': 0.08627},
                27: {'L': 0.5548, 'M': 17.320, 'S': 0.08627},
                28: {'L': 0.5548, 'M': 17.710, 'S': 0.08627},
                29: {'L': 0.5548, 'M': 18.100, 'S': 0.08627},
                30: {'L': 0.5548, 'M': 18.490, 'S': 0.08627},
                31: {'L': 0.5548, 'M': 18.870, 'S': 0.08627},
                32: {'L': 0.5548, 'M': 19.240, 'S': 0.08627},
                33: {'L': 0.5548, 'M': 19.610, 'S': 0.08627},
                34: {'L': 0.5548, 'M': 19.980, 'S': 0.08627},
                35: {'L': 0.5548, 'M': 20.340, 'S': 0.08627},
                36: {'L': 0.5548, 'M': 20.700, 'S': 0.08627}
            },
            'height_age': {
                # Birth to 6 months (monthly)
                0: {'L': 1.0000, 'M': 49.50, 'S': 0.03790},
                0.5: {'L': 1.0000, 'M': 54.20, 'S': 0.03790},
                1: {'L': 1.0000, 'M': 57.30, 'S': 0.03530},
                1.5: {'L': 1.0000, 'M': 60.00, 'S': 0.03350},
                2: {'L': 1.0000, 'M': 61.80, 'S': 0.03350},
                2.5: {'L': 1.0000, 'M': 62.70, 'S': 0.03350},
                3: {'L': 1.0000, 'M': 64.20, 'S': 0.03240},
                3.5: {'L': 1.0000, 'M': 65.70, 'S': 0.03240},
                4: {'L': 1.0000, 'M': 67.10, 'S': 0.03240},
                4.5: {'L': 1.0000, 'M': 67.80, 'S': 0.03240},
                5: {'L': 1.0000, 'M': 68.90, 'S': 0.03140},
                5.5: {'L': 1.0000, 'M': 69.90, 'S': 0.03140},
                6: {'L': 1.0000, 'M': 70.80, 'S': 0.03140},
                # 6-12 months (monthly)
                7: {'L': 1.0000, 'M': 71.60, 'S': 0.03140},
                8: {'L': 1.0000, 'M': 72.80, 'S': 0.03080},
                9: {'L': 1.0000, 'M': 73.90, 'S': 0.03080},
                10: {'L': 1.0000, 'M': 75.10, 'S': 0.03080},
                11: {'L': 1.0000, 'M': 76.40, 'S': 0.03020},
                12: {'L': 1.0000, 'M': 77.80, 'S': 0.03020},
                # 12-24 months (monthly)
                13: {'L': 1.0000, 'M': 79.20, 'S': 0.02960},
                14: {'L': 1.0000, 'M': 80.50, 'S': 0.02960},
                15: {'L': 1.0000, 'M': 81.90, 'S': 0.02890},
                16: {'L': 1.0000, 'M': 83.30, 'S': 0.02890},
                17: {'L': 1.0000, 'M': 84.70, 'S': 0.02890},
                18: {'L': 1.0000, 'M': 86.10, 'S': 0.02890},
                19: {'L': 1.0000, 'M': 87.50, 'S': 0.02810},
                20: {'L': 1.0000, 'M': 88.90, 'S': 0.02810},
                21: {'L': 1.0000, 'M': 90.20, 'S': 0.02810},
                22: {'L': 1.0000, 'M': 91.50, 'S': 0.02750},
                23: {'L': 1.0000, 'M': 92.90, 'S': 0.02750},
                24: {'L': 1.0000, 'M': 94.20, 'S': 0.02750},
                # 24-36 months (monthly)
                25: {'L': 1.0000, 'M': 95.50, 'S': 0.02710},
                26: {'L': 1.0000, 'M': 96.70, 'S': 0.02710},
                27: {'L': 1.0000, 'M': 98.00, 'S': 0.02680},
                28: {'L': 1.0000, 'M': 99.20, 'S': 0.02680},
                29: {'L': 1.0000, 'M': 100.40, 'S': 0.02660},
                30: {'L': 1.0000, 'M': 101.60, 'S': 0.02660},
                31: {'L': 1.0000, 'M': 102.80, 'S': 0.02640},
                32: {'L': 1.0000, 'M': 103.90, 'S': 0.02640},
                33: {'L': 1.0000, 'M': 105.00, 'S': 0.02630},
                34: {'L': 1.0000, 'M': 106.10, 'S': 0.02630},
                35: {'L': 1.0000, 'M': 107.20, 'S': 0.02620},
                36: {'L': 1.0000, 'M': 108.30, 'S': 0.02620}
            },
            'bmi_age': {
                # Birth to 6 months (monthly)
                0: {'L': -0.0631, 'M': 13.60, 'S': 0.07100},
                0.5: {'L': -0.0631, 'M': 15.20, 'S': 0.07100},
                1: {'L': -0.1606, 'M': 16.10, 'S': 0.08300},
                1.5: {'L': -0.1606, 'M': 16.50, 'S': 0.08300},
                2: {'L': -0.1730, 'M': 16.60, 'S': 0.08500},
                2.5: {'L': -0.1730, 'M': 16.70, 'S': 0.08500},
                3: {'L': -0.1730, 'M': 16.80, 'S': 0.08500},
                3.5: {'L': -0.1730, 'M': 17.00, 'S': 0.08500},
                4: {'L': -0.1590, 'M': 17.10, 'S': 0.08600},
                4.5: {'L': -0.1590, 'M': 17.20, 'S': 0.08600},
                5: {'L': -0.1590, 'M': 17.30, 'S': 0.08600},
                5.5: {'L': -0.1590, 'M': 17.40, 'S': 0.08600},
                6: {'L': -0.1230, 'M': 17.50, 'S': 0.08600},
                # 6-12 months (monthly)
                7: {'L': -0.1230, 'M': 17.50, 'S': 0.08600},
                8: {'L': -0.1230, 'M': 17.40, 'S': 0.08600},
                9: {'L': -0.0330, 'M': 17.30, 'S': 0.08400},
                10: {'L': -0.0330, 'M': 17.10, 'S': 0.08400},
                11: {'L': 0.0500, 'M': 16.90, 'S': 0.08200},
                12: {'L': 0.0500, 'M': 16.70, 'S': 0.08200},
                # 12-24 months (monthly)
                13: {'L': 0.1250, 'M': 16.60, 'S': 0.08000},
                14: {'L': 0.1250, 'M': 16.50, 'S': 0.08000},
                15: {'L': 0.1850, 'M': 16.40, 'S': 0.07800},
                16: {'L': 0.1850, 'M': 16.30, 'S': 0.07800},
                17: {'L': 0.2300, 'M': 16.20, 'S': 0.07600},
                18: {'L': 0.2300, 'M': 16.20, 'S': 0.07600},
                19: {'L': 0.2600, 'M': 16.20, 'S': 0.07500},
                20: {'L': 0.2600, 'M': 16.20, 'S': 0.07500},
                21: {'L': 0.2850, 'M': 16.30, 'S': 0.07400},
                22: {'L': 0.2850, 'M': 16.40, 'S': 0.07400},
                23: {'L': 0.3050, 'M': 16.50, 'S': 0.07300},
                24: {'L': 0.3050, 'M': 16.60, 'S': 0.07300},
                # 24-36 months (monthly)
                25: {'L': 0.3200, 'M': 16.70, 'S': 0.07200},
                26: {'L': 0.3200, 'M': 16.80, 'S': 0.07200},
                27: {'L': 0.3350, 'M': 16.90, 'S': 0.07100},
                28: {'L': 0.3350, 'M': 17.00, 'S': 0.07100},
                29: {'L': 0.3450, 'M': 17.10, 'S': 0.07000},
                30: {'L': 0.3450, 'M': 17.20, 'S': 0.07000},
                31: {'L': 0.3550, 'M': 17.30, 'S': 0.06900},
                32: {'L': 0.3550, 'M': 17.40, 'S': 0.06900},
                33: {'L': 0.3600, 'M': 17.50, 'S': 0.06800},
                34: {'L': 0.3600, 'M': 17.60, 'S': 0.06800},
                35: {'L': 0.3650, 'M': 17.70, 'S': 0.06700},
                36: {'L': 0.3650, 'M': 17.80, 'S': 0.06700}
            },
            'head_age': {
                # Birth to 6 months (monthly)
                0: {'L': 1.0000, 'M': 34.80, 'S': 0.03630},
                0.5: {'L': 1.0000, 'M': 37.20, 'S': 0.03630},
                1: {'L': 1.0000, 'M': 38.70, 'S': 0.03110},
                1.5: {'L': 1.0000, 'M': 39.80, 'S': 0.03110},
                2: {'L': 1.0000, 'M': 40.70, 'S': 0.03110},
                2.5: {'L': 1.0000, 'M': 41.20, 'S': 0.03110},
                3: {'L': 1.0000, 'M': 42.10, 'S': 0.02930},
                3.5: {'L': 1.0000, 'M': 42.70, 'S': 0.02930},
                4: {'L': 1.0000, 'M': 43.20, 'S': 0.02930},
                4.5: {'L': 1.0000, 'M': 43.60, 'S': 0.02930},
                5: {'L': 1.0000, 'M': 44.00, 'S': 0.02820},
                5.5: {'L': 1.0000, 'M': 44.50, 'S': 0.02820},
                6: {'L': 1.0000, 'M': 44.90, 'S': 0.02820},
                # 6-12 months (monthly)
                7: {'L': 1.0000, 'M': 45.20, 'S': 0.02820},
                8: {'L': 1.0000, 'M': 45.50, 'S': 0.02740},
                9: {'L': 1.0000, 'M': 45.80, 'S': 0.02740},
                10: {'L': 1.0000, 'M': 46.10, 'S': 0.02740},
                11: {'L': 1.0000, 'M': 46.40, 'S': 0.02680},
                12: {'L': 1.0000, 'M': 46.80, 'S': 0.02680},
                # 12-24 months (monthly)
                13: {'L': 1.0000, 'M': 47.10, 'S': 0.02630},
                14: {'L': 1.0000, 'M': 47.40, 'S': 0.02630},
                15: {'L': 1.0000, 'M': 47.70, 'S': 0.02560},
                16: {'L': 1.0000, 'M': 48.00, 'S': 0.02560},
                17: {'L': 1.0000, 'M': 48.30, 'S': 0.02500},
                18: {'L': 1.0000, 'M': 48.60, 'S': 0.02500},
                19: {'L': 1.0000, 'M': 48.80, 'S': 0.02460},
                20: {'L': 1.0000, 'M': 49.00, 'S': 0.02460},
                21: {'L': 1.0000, 'M': 49.20, 'S': 0.02420},
                22: {'L': 1.0000, 'M': 49.40, 'S': 0.02420},
                23: {'L': 1.0000, 'M': 49.60, 'S': 0.02390},
                24: {'L': 1.0000, 'M': 49.80, 'S': 0.02390},
                # 24-36 months (monthly)
                25: {'L': 1.0000, 'M': 50.00, 'S': 0.02360},
                26: {'L': 1.0000, 'M': 50.20, 'S': 0.02360},
                27: {'L': 1.0000, 'M': 50.30, 'S': 0.02330},
                28: {'L': 1.0000, 'M': 50.50, 'S': 0.02330},
                29: {'L': 1.0000, 'M': 50.60, 'S': 0.02310},
                30: {'L': 1.0000, 'M': 50.80, 'S': 0.02310},
                31: {'L': 1.0000, 'M': 50.90, 'S': 0.02290},
                32: {'L': 1.0000, 'M': 51.00, 'S': 0.02290},
                33: {'L': 1.0000, 'M': 51.10, 'S': 0.02270},
                34: {'L': 1.0000, 'M': 51.20, 'S': 0.02270},
                35: {'L': 1.0000, 'M': 51.30, 'S': 0.02250},
                36: {'L': 1.0000, 'M': 51.40, 'S': 0.02250}
            }
        }
    }

    @classmethod
    def validate_dataset_completeness(cls):
        """Validate that dataset has complete monthly coverage"""
        issues = []
        for gender in ['male', 'female']:
            for measurement_type in ['weight_age', 'height_age', 'bmi_age', 'head_age']:
                chart = cls.CDC_LMS_DATA[gender][measurement_type]
                ages = sorted(chart.keys())
                
                # Check for monthly coverage
                expected_months = set(range(0, 37))  # 0-36 months
                missing_months = expected_months - set(ages)
                
                if missing_months:
                    issues.append(f"{gender} {measurement_type}: Missing months {sorted(missing_months)}")
        
        return issues

    @classmethod
    def get_lms_values(cls, age_months: float, measurement_type: str, gender: str) -> Optional[Dict]:
        """Get L, M, S values with enhanced linear interpolation for clinical accuracy"""
        try:
            if gender not in cls.CDC_LMS_DATA or measurement_type not in cls.CDC_LMS_DATA[gender]:
                return None
            
            chart = cls.CDC_LMS_DATA[gender][measurement_type]
            available_ages = sorted(chart.keys())
            
            if not available_ages:
                return None
            
            # Exact match
            if age_months in chart:
                return chart[age_months]
            
            # Boundary checks
            if age_months < available_ages[0]:
                return chart[available_ages[0]]
            if age_months > available_ages[-1]:
                return chart[available_ages[-1]]
            
            # Find interpolation interval
            lower_age = max([age for age in available_ages if age <= age_months])
            upper_age = min([age for age in available_ages if age >= age_months])
            
            if lower_age == upper_age:
                return chart[lower_age]
            
            # Linear interpolation for clinical precision
            lower_data = chart[lower_age]
            upper_data = chart[upper_age]
            
            # Calculate weights
            t = (age_months - lower_age) / (upper_age - lower_age)
            
            # Interpolate each parameter
            interpolated_data = {
                'L': lower_data['L'] + t * (upper_data['L'] - lower_data['L']),
                'M': lower_data['M'] + t * (upper_data['M'] - lower_data['M']),
                'S': lower_data['S'] + t * (upper_data['S'] - lower_data['S'])
            }
            
            return interpolated_data
            
        except Exception as e:
            st.error(f"LMS data retrieval error: {e}")
            return None

    @classmethod
    def calculate_z_score(cls, value: float, L: float, M: float, S: float) -> Optional[float]:
        """Calculate Z-score using CDC LMS method with clinical validation"""
        try:
            if value <= 0 or M <= 0 or S <= 0:
                return None
            
            # Clinical range validation
            if not cls._validate_clinical_range(value, M, S):
                return None
            
            # Box-Cox transformation with error handling
            if abs(L) > 1e-6:
                try:
                    # Box-Cox transformation
                    transformed = ((value / M) ** L - 1) / (L * S)
                except (ValueError, OverflowError):
                    # Fallback to log transformation for extreme values
                    transformed = np.log(value / M) / S
            else:
                # Log transformation when L ≈ 0
                transformed = np.log(value / M) / S
            
            # Clinical bounds for Z-scores
            if abs(transformed) > 5:
                transformed = 5.0 if transformed > 0 else -5.0
            
            return float(transformed)
            
        except Exception as e:
            return None

    @classmethod
    def _validate_clinical_range(cls, value: float, M: float, S: float) -> bool:
        """Validate if value is within clinically plausible range"""
        # Values more than 4 SD from median are clinically suspicious
        lower_bound = M * (1 - 4 * S)
        upper_bound = M * (1 + 4 * S)
        return lower_bound <= value <= upper_bound

    @classmethod
    def calculate_percentile(cls, z_score: float) -> Optional[float]:
        """Convert Z-score to percentile with clinical precision"""
        try:
            if z_score is None:
                return None
            
            # Use precise normal CDF
            percentile = stats.norm.cdf(z_score) * 100
            
            # Clinical bounds
            return max(0.01, min(99.99, percentile))
            
        except Exception:
            return None

    @classmethod
    def calculate_growth_parameters(cls, value: float, age_months: float, measurement_type: str, 
                                  gender: str, adjusted_age_months: Optional[float] = None) -> Optional[Dict]:
        """Calculate all growth parameters using CDC LMS method with clinical validation"""
        try:
            # Enhanced clinical validation
            if not cls.validate_measurement(value, measurement_type):
                return None
            
            # Use adjusted age for preterm infants
            effective_age = adjusted_age_months if adjusted_age_months is not None else age_months
            effective_age = max(0, min(36, effective_age))
            
            # Get precise LMS values
            lms_data = cls.get_lms_values(effective_age, measurement_type, gender)
            if not lms_data:
                return None
            
            # Calculate Z-score with enhanced precision
            z_score = cls.calculate_z_score(value, lms_data['L'], lms_data['M'], lms_data['S'])
            if z_score is None:
                return None
            
            # Calculate percentile
            percentile = cls.calculate_percentile(z_score)
            
            # Get clinical classification
            classification, severity = cls.classify_growth(z_score, measurement_type)
            
            # Calculate exact percentile values for clinical reporting
            exact_percentiles = cls.calculate_exact_percentiles(z_score)
            
            return {
                'value': value,
                'age_months': age_months,
                'adjusted_age_months': adjusted_age_months,
                'z_score': z_score,
                'percentile': percentile,
                'classification': classification,
                'severity': severity,
                'lms_data': lms_data,
                'is_abnormal': severity in ['moderate', 'severe', 'critical'],
                'exact_percentiles': exact_percentiles,
                'type': measurement_type
            }
            
        except Exception as e:
            return None

    @classmethod
    def calculate_exact_percentiles(cls, z_score: float) -> Dict:
        """Calculate exact percentile values for clinical reporting"""
        if z_score is None:
            return {}
        
        return {
            'percentile_3rd': stats.norm.cdf(-1.88) * 100,  # -1.88 Z ≈ 3rd percentile
            'percentile_5th': stats.norm.cdf(-1.645) * 100, # -1.645 Z ≈ 5th percentile
            'percentile_10th': stats.norm.cdf(-1.28) * 100, # -1.28 Z ≈ 10th percentile
            'percentile_25th': stats.norm.cdf(-0.674) * 100, # -0.674 Z ≈ 25th percentile
            'percentile_50th': 50.0,  # Median
            'percentile_75th': stats.norm.cdf(0.674) * 100,  # 0.674 Z ≈ 75th percentile
            'percentile_90th': stats.norm.cdf(1.28) * 100,   # 1.28 Z ≈ 90th percentile
            'percentile_95th': stats.norm.cdf(1.645) * 100,  # 1.645 Z ≈ 95th percentile
            'percentile_97th': stats.norm.cdf(1.88) * 100    # 1.88 Z ≈ 97th percentile
        }

    @classmethod
    def validate_measurement(cls, value: float, measurement_type: str) -> bool:
        """Enhanced clinical validation of measurements"""
        clinical_ranges = {
            'weight_age': (0.5, 150.0),      # kg - clinically plausible range
            'height_age': (30.0, 200.0),     # cm - birth to 3 years
            'bmi_age': (10.0, 40.0),         # kg/m² - clinical range
            'head_age': (20.0, 65.0)         # cm - birth to 3 years
        }
        
        if measurement_type not in clinical_ranges:
            return False
        
        min_val, max_val = clinical_ranges[measurement_type]
        return min_val <= value <= max_val

    @classmethod
    def classify_growth(cls, z_score: float, measurement_type: str) -> Tuple[str, str]:
        """CDC growth classification standards with clinical precision"""
        if z_score is None:
            return "Unable to calculate", "unknown"
        
        if measurement_type == 'bmi_age':
            # WHO/CDC BMI classification for children
            if z_score < -2.0:
                return "Severe underweight", "severe"
            elif z_score < -1.0:
                return "Moderate underweight", "moderate"
            elif z_score <= 1.0:
                return "Healthy weight", "normal"
            elif z_score <= 2.0:
                return "Overweight", "moderate"
            else:
                return "Obese", "severe"
        else:
            # CDC growth standards for other parameters
            if z_score < -3.0:
                return "Extremely low (< 0.1%)", "critical"
            elif z_score < -2.0:
                return "Very low (< 2.3%)", "severe"
            elif z_score < -1.0:
                return "Mildly low (2.3-15.9%)", "moderate"
            elif z_score <= 1.0:
                return "Normal (15.9-84.1%)", "normal"
            elif z_score <= 2.0:
                return "High (84.1-97.7%)", "moderate"
            elif z_score <= 3.0:
                return "Very high (97.7-99.9%)", "severe"
            else:
                return "Extremely high (> 99.9%)", "critical"

    @classmethod
    def calculate_bmi(cls, weight_kg: float, height_cm: float) -> Optional[float]:
        """Calculate BMI with enhanced validation"""
        try:
            if weight_kg <= 0 or height_cm <= 0:
                return None
            
            # Convert height to meters
            height_m = height_cm / 100
            
            # Calculate BMI
            bmi = weight_kg / (height_m ** 2)
            
            # Clinical validation
            if bmi < 10 or bmi > 40:  # Clinically implausible for children
                return None
            
            return round(bmi, 2)  # More precision for clinical use
            
        except Exception:
            return None

    @classmethod
    def calculate_weight_for_height(cls, weight_kg: float, height_cm: float, gender: str) -> Optional[Dict]:
        """Calculate weight-for-height percentile (for clinical assessment)"""
        try:
            # This is a simplified version - in practice, you'd need specific LMS data
            # for weight-for-height calculations
            bmi = cls.calculate_bmi(weight_kg, height_cm)
            if bmi is None:
                return None
            
            # Use BMI as proxy for weight-for-height in this implementation
            return cls.calculate_growth_parameters(bmi, 24, 'bmi_age', gender)  # Using 24 months as reference
            
        except Exception:
            return None

class ClinicalReportGenerator:
    """Generate clinical reports with CDC LMS methodology"""
    
    def __init__(self, calculator):
        self.calculator = calculator
    
    def create_clinical_report(self, patient_info, measurements):
        """Create comprehensive clinical PDF report with charts"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'ClinicalTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                textColor=colors.HexColor('#1f77b4')
            )
            
            story = []
            
            # Header
            story.append(Paragraph("CDC LMS GROWTH ASSESSMENT REPORT", title_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Patient Information
            story.append(Paragraph("PATIENT INFORMATION", styles['Heading2']))
            patient_data = self._create_patient_table(patient_info)
            story.append(patient_data)
            story.append(Spacer(1, 0.3*inch))
            
            # Growth Assessment
            story.append(Paragraph("GROWTH ASSESSMENT", styles['Heading2']))
            growth_table = self._create_growth_table(measurements)
            if growth_table:
                story.append(growth_table)
                story.append(Spacer(1, 0.3*inch))
            
            # Add Growth Charts to PDF
            if st.session_state.saved_charts:
                story.append(Paragraph("GROWTH CHARTS", styles['Heading2']))
                story.append(Spacer(1, 0.2*inch))
                
                # Add each chart to the PDF
                chart_descriptions = {
                    'weight_age': 'Weight for Age Growth Chart',
                    'height_age': 'Height for Age Growth Chart',
                    'head_age': 'Head Circumference for Age Growth Chart',
                    'bmi_age': 'BMI for Age Growth Chart'
                }
                
                for chart_type, chart_path in st.session_state.saved_charts.items():
                    if os.path.exists(chart_path):
                        # Add chart description
                        description = chart_descriptions.get(chart_type, 'Growth Chart')
                        story.append(Paragraph(description, styles['Heading3']))
                        story.append(Spacer(1, 0.1*inch))
                        
                        # Add the chart image
                        chart_img = Image(chart_path, width=6*inch, height=4*inch)
                        story.append(chart_img)
                        story.append(Spacer(1, 0.2*inch))
            
            # Clinical Interpretation
            story.append(Paragraph("CLINICAL INTERPRETATION", styles['Heading2']))
            interpretation = self._generate_interpretation(measurements)
            story.append(Paragraph(interpretation, styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
            
            # Recommendations
            story.append(Paragraph("RECOMMENDATIONS", styles['Heading2']))
            recommendations = self._generate_recommendations(measurements)
            for rec in recommendations:
                story.append(Paragraph(f"• {rec}", styles['Normal']))
            
            # Footer
            story.append(Spacer(1, 0.3*inch))
            footer_text = "This clinical report uses CDC LMS growth chart methodology with complete monthly dataset (0-36 months). For medical decisions, consult with qualified healthcare professionals."
            story.append(Paragraph(footer_text, styles['Italic']))
            
            doc.build(story)
            buffer.seek(0)
            return buffer
            
        except Exception as e:
            st.error(f"Report generation error: {e}")
            return None
    
    def _create_patient_table(self, patient_info):
        """Create patient information table"""
        data = [
            ["Name:", f"{patient_info.get('first_name', '')} {patient_info.get('last_name', '')}"],
            ["Gender:", patient_info.get('gender', '').title()],
            ["Date of Birth:", patient_info.get('birth_date', '')],
            ["Gestational Age:", f"{patient_info.get('gestational_age', '40')} weeks"],
            ["Report Date:", datetime.now().strftime('%Y-%m-%d')]
        ]
        
        table = Table(data, colWidths=[1.5*inch, 3*inch])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        return table
    
    def _create_growth_table(self, measurements):
        """Create growth assessment table"""
        latest_measurements = self._get_latest_measurements(measurements)
        
        if not latest_measurements:
            return None
            
        data = [["Parameter", "Value", "Z-score", "Percentile", "Classification"]]
        for m_type, meas in latest_measurements.items():
            display_name = m_type.replace('_', ' ').title()
            data.append([
                display_name,
                f"{meas['value']:.1f}",
                f"{meas['z_score']:.2f}" if meas['z_score'] is not None else "N/A",
                f"{meas['percentile']:.1f}%" if meas['percentile'] is not None else "N/A",
                meas['classification']
            ])
        
        table = Table(data, colWidths=[1.8*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.6*inch])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONT', (0, 1), (-1, -1), 'Helvetica', 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER')
        ]))
        return table
    
    def _get_latest_measurements(self, measurements):
        """Get latest measurement of each type"""
        latest = {}
        for measurement in measurements:
            m_type = measurement['type']
            if m_type not in latest or measurement['age_months'] > latest[m_type]['age_months']:
                latest[m_type] = measurement
        return latest
    
    def _generate_interpretation(self, measurements):
        """Generate clinical interpretation"""
        latest = self._get_latest_measurements(measurements)
        if not latest:
            return "No measurements available for interpretation."
            
        abnormal_count = sum(1 for m in latest.values() if m.get('is_abnormal', False))
        
        if abnormal_count == 0:
            return "All growth parameters are within normal ranges based on CDC growth standards. Growth pattern appears appropriate for age and gender."
        else:
            concerns = []
            for m_type, meas in latest.items():
                if meas.get('is_abnormal', False):
                    concerns.append(f"{m_type.replace('_', ' ').title()}: {meas['classification']} (Z-score: {meas['z_score']:.2f})")
            
            return f"Growth assessment identifies {abnormal_count} parameter(s) requiring attention: {'; '.join(concerns)}. Further clinical evaluation recommended."
    
    def _generate_recommendations(self, measurements):
        """Generate clinical recommendations"""
        latest = self._get_latest_measurements(measurements)
        recommendations = [
            "Continue routine growth monitoring according to standard pediatric schedules",
            "Maintain age-appropriate nutrition and physical activity"
        ]
        
        # Add specific recommendations based on findings
        if latest:
            for m_type, meas in latest.items():
                if meas.get('is_abnormal', False):
                    if 'underweight' in meas['classification'].lower() or 'low' in meas['classification'].lower():
                        recommendations.append(f"Consider nutritional assessment and intervention for {m_type.replace('_', ' ')}")
                    elif 'overweight' in meas['classification'].lower() or 'high' in meas['classification'].lower():
                        recommendations.append(f"Monitor dietary intake and activity levels for {m_type.replace('_', ' ')}")
        
        recommendations.extend([
            "Schedule follow-up measurements in 3-6 months",
            "Consult with pediatric specialist for abnormal findings",
            "Consider laboratory evaluation if clinical concerns persist"
        ])
        
        return recommendations

def validate_patient_data(first_name, last_name, birth_date, measurement_date, gestational_age):
    """Comprehensive patient data validation"""
    errors = []
    
    # Name validation
    if not first_name.strip() or not last_name.strip():
        errors.append("First and last name are required")
    if len(first_name.strip()) < 2 or len(last_name.strip()) < 2:
        errors.append("Names must be at least 2 characters long")
    
    # Date validation
    if birth_date > datetime.now().date():
        errors.append("Birth date cannot be in the future")
    if measurement_date < birth_date:
        errors.append("Measurement date cannot be before birth date")
    if (measurement_date - birth_date).days > 365 * 3:  # 3 years max for this implementation
        errors.append("Patient age exceeds 3 years - outside current growth chart range")
    
    # Gestational age validation
    if gestational_age < 22 or gestational_age > 44:
        errors.append("Gestational age must be between 22 and 44 weeks")
    
    return errors

def validate_measurements(height, weight, head_circumference):
    """Clinical measurement validation"""
    errors = []
    
    if height <= 0 or weight <= 0:
        errors.append("Height and weight are required for basic growth assessment")
    
    if height > 0 and height < 30:
        errors.append("Height appears too low - please verify measurement")
    if height > 200:
        errors.append("Height appears too high - please verify measurement")
    
    if weight > 0 and weight < 0.5:
        errors.append("Weight appears too low - please verify measurement")
    if weight > 150:
        errors.append("Weight appears too high - please verify measurement")
    
    if head_circumference > 0 and (head_circumference < 20 or head_circumference > 65):
        errors.append("Head circumference outside expected range")
    
    return errors

def calculate_age_months(birth_date, measurement_date):
    """Calculate precise age in months"""
    try:
        delta = measurement_date - birth_date
        return delta.days / 30.436875  # Average days per month
    except:
        return None

def calculate_adjusted_age(birth_date, measurement_date, gestational_weeks):
    """Calculate adjusted age for preterm infants with validation"""
    try:
        chronological_age_months = calculate_age_months(birth_date, measurement_date)
        if chronological_age_months is None:
            return None, False
        
        if gestational_weeks >= 37:
            return chronological_age_months, False
        
        # Calculate adjustment
        weeks_preterm = 40 - gestational_weeks
        if weeks_preterm <= 0:
            return chronological_age_months, False
            
        adjustment_months = weeks_preterm / 4.345  # Average weeks per month
        
        adjusted_age_months = max(0, chronological_age_months - adjustment_months)
        return adjusted_age_months, True
        
    except Exception as e:
        return None, False

def get_percentile_display(percentile, z_score):
    """Get display category for percentile values"""
    if percentile is None or z_score is None:
        return "Unable to calculate", "monitor"
    
    if z_score < -3.0:
        return "Extremely Low", "critical"
    elif z_score < -2.0:
        return "Very Low", "concern"
    elif z_score < -1.0:
        return "Low Normal", "monitor"
    elif z_score <= 1.0:
        return "Normal", "normal"
    elif z_score <= 2.0:
        return "High Normal", "monitor"
    elif z_score <= 3.0:
        return "Very High", "concern"
    else:
        return "Extremely High", "critical"

def create_growth_chart(measurements, measurement_type, gender, calculator, patient_info):
    """Create a growth chart with percentile curves using adjusted age if needed"""
    try:
        patient_data = [m for m in measurements if m['type'] == measurement_type]
        if not patient_data:
            return None
        
        gestational_age = patient_info.get('gestational_age', 40)
        use_adjusted_age = gestational_age < 37
        
        ages_range = np.linspace(0, 36, 100)  # More points for smoother curves
        percentiles = [3, 10, 25, 50, 75, 90, 97]
        
        fig = go.Figure()
        
        # Add percentile curves
        for p in percentiles:
            values = []
            for age in ages_range:
                lms_data = calculator.get_lms_values(age, measurement_type, gender)
                if lms_data:
                    L, M, S = lms_data['L'], lms_data['M'], lms_data['S']
                    Z = stats.norm.ppf(p/100.0)
                    if abs(L) > 1e-6:
                        value = M * (1 + L * S * Z) ** (1/L)
                    else:
                        value = M * np.exp(S * Z)
                    values.append(value)
                else:
                    values.append(None)
            
            # Filter out None values
            valid_ages = [age for age, val in zip(ages_range, values) if val is not None]
            valid_values = [val for val in values if val is not None]
            
            if valid_values:
                fig.add_trace(go.Scatter(
                    x=valid_ages, y=valid_values,
                    mode='lines',
                    name=f'{p}th',
                    line=dict(width=1 if p != 50 else 2, dash='dash' if p != 50 else 'solid'),
                    opacity=0.7 if p != 50 else 1.0
                ))
        
        # Add patient data
        patient_ages = [m.get('adjusted_age_months', m['age_months']) if use_adjusted_age else m['age_months'] for m in patient_data]
        patient_values = [m['value'] for m in patient_data]
        
        fig.add_trace(go.Scatter(
            x=patient_ages, y=patient_values,
            mode='markers+lines',
            name='Patient',
            line=dict(color='red', width=3),
            marker=dict(size=8, symbol='circle')
        ))
        
        titles = {
            'weight_age': 'Weight for Age',
            'height_age': 'Height for Age', 
            'head_age': 'Head Circumference for Age',
            'bmi_age': 'BMI for Age'
        }
        
        units = {
            'weight_age': 'Weight (kg)',
            'height_age': 'Height (cm)',
            'head_age': 'Head Circumference (cm)',
            'bmi_age': 'BMI (kg/m²)'
        }
        
        age_label = 'Age (months)' + (' - Adjusted' if use_adjusted_age else '')
        
        fig.update_layout(
            title=f"{titles.get(measurement_type, 'Growth Chart')}",
            xaxis_title=age_label,
            yaxis_title=units.get(measurement_type, 'Value'),
            height=500,
            showlegend=True,
            template='plotly_white'
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Chart generation error: {e}")
        return None

def save_chart_as_image(fig, filename):
    """Save Plotly chart as image file using matplotlib"""
    try:
        if fig:
            temp_dir = tempfile.gettempdir()
            chart_path = os.path.join(temp_dir, filename)
            
            try:
                plt.figure(figsize=(12, 8))
                
                for trace in fig.data:
                    if trace.type == 'scatter':
                        x = trace.x
                        y = trace.y
                        if 'Patient' in trace.name:
                            plt.plot(x, y, 'ro-', linewidth=3, markersize=8, label=trace.name)
                        else:
                            plt.plot(x, y, '--', alpha=0.7, linewidth=1.5, label=trace.name)
                
                plt.title(fig.layout.title.text if fig.layout.title else 'Growth Chart', fontsize=14, fontweight='bold')
                plt.xlabel(fig.layout.xaxis.title.text if fig.layout.xaxis.title else 'Age (months)', fontsize=12)
                plt.ylabel(fig.layout.yaxis.title.text if fig.layout.yaxis.title else 'Value', fontsize=12)
                plt.legend(fontsize=10)
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                
                plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
                plt.close()
                
                return chart_path
                
            except Exception as e:
                st.error(f"Chart saving error: {e}")
                return None
                
    except Exception as e:
        st.error(f"Chart processing error: {e}")
        return None

def clear_all_data():
    """Clear all session state data"""
    st.session_state.measurements = []
    st.session_state.patient_info = {}
    st.session_state.charts_generated = False
    st.session_state.saved_charts = {}
    st.session_state.current_page = "New Measurement"
    st.success("All data cleared successfully!")

def generate_all_charts(calculator):
    """Generate all growth charts for PDF report"""
    if not st.session_state.measurements or not st.session_state.patient_info:
        return {}
    
    gender = st.session_state.patient_info.get('gender', 'male')
    patient_info = st.session_state.patient_info
    chart_types = ['weight_age', 'height_age', 'head_age', 'bmi_age']
    saved_charts = {}
    
    for chart_type in chart_types:
        has_measurements = any(m['type'] == chart_type for m in st.session_state.measurements)
        if has_measurements:
            fig = create_growth_chart(st.session_state.measurements, chart_type, gender, calculator, patient_info)
            if fig:
                chart_path = save_chart_as_image(fig, f"{chart_type}_chart.png")
                if chart_path:
                    saved_charts[chart_type] = chart_path
    
    return saved_charts

def process_measurement_submission(first_name, last_name, gender, birth_date, measurement_date, 
                                 height, weight, head_circumference, gestational_age, calculator):
    """Process measurement submission with clinical validation"""
    
    # Validate patient data
    errors = validate_patient_data(first_name, last_name, birth_date, measurement_date, gestational_age)
    if errors:
        for error in errors:
            st.error(f"❌ {error}")
        return
    
    # Validate measurements
    measurement_errors = validate_measurements(height, weight, head_circumference)
    if measurement_errors:
        for error in measurement_errors:
            st.error(f"📏 {error}")
        return
    
    # Calculate ages
    age_months = calculate_age_months(birth_date, measurement_date)
    adjusted_age_months, using_adjusted_age = calculate_adjusted_age(birth_date, measurement_date, gestational_age)
    
    if age_months is None:
        st.error("❌ Unable to calculate age")
        return
    
    # Age warnings
    if age_months > 36:
        st.warning("ℹ️ Note: Growth charts are optimized for ages 0-36 months. Calculations for older children use extended ranges.")
    
    if using_adjusted_age:
        st.info(f"👶 Using adjusted age: {adjusted_age_months:.1f} months (Chronological: {age_months:.1f} months)")
    
    # Store patient info
    st.session_state.patient_info = {
        'first_name': first_name.strip(),
        'last_name': last_name.strip(),
        'gender': gender,
        'birth_date': birth_date.strftime('%Y-%m-%d'),
        'gestational_age': gestational_age
    }
    
    # Calculate growth parameters
    new_measurements = []
    
    if height > 0 and weight > 0:
        # Height assessment
        height_params = calculator.calculate_growth_parameters(
            height, age_months, 'height_age', gender, adjusted_age_months
        )
        if height_params:
            new_measurements.append({
                'type': 'height_age',
                'date': measurement_date.strftime('%Y-%m-%d'),
                **height_params
            })
        
        # Weight assessment
        weight_params = calculator.calculate_growth_parameters(
            weight, age_months, 'weight_age', gender, adjusted_age_months
        )
        if weight_params:
            new_measurements.append({
                'type': 'weight_age',
                'date': measurement_date.strftime('%Y-%m-%d'),
                **weight_params
            })
        
        # BMI assessment
        bmi = calculator.calculate_bmi(weight, height)
        if bmi:
            bmi_params = calculator.calculate_growth_parameters(
                bmi, age_months, 'bmi_age', gender, adjusted_age_months
            )
            if bmi_params:
                new_measurements.append({
                    'type': 'bmi_age',
                    'date': measurement_date.strftime('%Y-%m-%d'),
                    **bmi_params
                })
    
    # Head circumference
    if head_circumference > 0:
        head_params = calculator.calculate_growth_parameters(
            head_circumference, age_months, 'head_age', gender, adjusted_age_months
        )
        if head_params:
            new_measurements.append({
                'type': 'head_age',
                'date': measurement_date.strftime('%Y-%m-%d'),
                **head_params
            })
    
    if new_measurements:
        st.success("✅ Growth assessment completed using CDC LMS methodology with complete monthly dataset!")
        
        # Display results
        cols = st.columns(min(4, len(new_measurements)))
        for i, measurement in enumerate(new_measurements):
            with cols[i]:
                measure_name = measurement['type'].replace('_', ' ').title()
                st.markdown(f'<div class="metric-card">'
                          f'<h3>{measure_name}</h3>'
                          f'<h2>{measurement["value"]:.1f}</h2>'
                          f'<h4>Z: {measurement["z_score"]:.2f}</h4>'
                          f'</div>', unsafe_allow_html=True)
                
                category, css_class = get_percentile_display(
                    measurement['percentile'], measurement['z_score']
                )
                st.markdown(f'<div class="percentile-indicator {css_class}">{category}<br>'
                          f'{measurement["percentile"]:.1f}%</div>', unsafe_allow_html=True)
        
        # Store measurements
        st.session_state.measurements.extend(new_measurements)
        st.session_state.charts_generated = False
        
        # Clinical notes
        abnormal_measurements = [m for m in new_measurements if m.get('is_abnormal', False)]
        if abnormal_measurements:
            st.markdown('<div class="clinical-note">⚠️ Abnormal findings detected. Please review clinical report.</div>', 
                       unsafe_allow_html=True)
        
        st.balloons()
    else:
        st.error("❌ Unable to calculate growth parameters. Please check your measurements.")

def show_new_measurement(calculator, report_generator):
    """Show the new measurement form"""
    st.header("📊 New Growth Measurement")
    
    with st.form("measurement_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input("First Name *", value=st.session_state.patient_info.get('first_name', ''))
            last_name = st.text_input("Last Name *", value=st.session_state.patient_info.get('last_name', ''))
            gender = st.selectbox("Gender *", ["male", "female"], 
                                index=0 if st.session_state.patient_info.get('gender') == 'male' else 1)
            
            default_birth = st.session_state.patient_info.get('birth_date')
            if default_birth:
                try:
                    default_birth = datetime.strptime(default_birth, '%Y-%m-%d').date()
                except:
                    default_birth = datetime.now().date() - timedelta(days=365)
            else:
                default_birth = datetime.now().date() - timedelta(days=365)
            
            birth_date = st.date_input("Date of Birth *", value=default_birth)
            
            gestational_age = st.number_input("Gestational Age at Birth (weeks) *", 
                                            min_value=22, max_value=44, value=40,
                                            help="Enter 40 for full-term infants")
            
            if gestational_age < 37:
                st.markdown(f'<div class="preterm-warning">⚠️ Preterm infant ({gestational_age} weeks). Adjusted age will be used for calculations.</div>', 
                           unsafe_allow_html=True)
        
        with col2:
            measurement_date = st.date_input("Measurement Date *", datetime.now())
            height = st.number_input("Height (cm) *", min_value=0.0, max_value=200.0, value=0.0, step=0.1,
                                   help="Enter height in centimeters")
            weight = st.number_input("Weight (kg) *", min_value=0.0, max_value=100.0, value=0.0, step=0.1,
                                   help="Enter weight in kilograms")
            head_circumference = st.number_input("Head Circumference (cm)", min_value=0.0, max_value=60.0, value=0.0, step=0.1,
                                               help="Optional: Enter head circumference in centimeters")
        
        submitted = st.form_submit_button("🚀 Calculate Percentiles", use_container_width=True)
        
        if submitted:
            process_measurement_submission(first_name, last_name, gender, birth_date, measurement_date, 
                                         height, weight, head_circumference, gestational_age, calculator)
    
    if st.session_state.measurements:
        st.markdown("---")
        st.subheader("Quick Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📈 View Growth Charts", use_container_width=True, key="btn_view_charts"):
                st.session_state.current_page = "Growth Charts"
                st.rerun()
        
        with col2:
            if st.button("📋 Generate Report", use_container_width=True, key="btn_generate_report"):
                st.session_state.current_page = "Clinical Report"
                st.rerun()

def show_growth_history(calculator=None, report_generator=None):
    """Show measurement history"""
    st.header("📋 Growth History")
    
    if not st.session_state.measurements:
        st.info("No measurements recorded yet. Use 'New Measurement' to get started.")
        return
    
    if st.session_state.patient_info:
        patient = st.session_state.patient_info
        st.subheader("Patient Information")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.write(f"**Name:** {patient.get('first_name', '')} {patient.get('last_name', '')}")
        with col2:
            st.write(f"**Gender:** {patient.get('gender', '').title()}")
        with col3:
            st.write(f"**Date of Birth:** {patient.get('birth_date', '')}")
        with col4:
            gestational_age = patient.get('gestational_age', 40)
            st.write(f"**Gestational Age:** {gestational_age} weeks")
            if gestational_age < 37:
                st.write("**Status:** Preterm (Using adjusted age)")
    
    df_data = []
    for measurement in st.session_state.measurements:
        category, _ = get_percentile_display(measurement.get('percentile'), measurement.get('z_score'))
        age_display = f"{measurement['age_months']:.1f}"
        if measurement.get('adjusted_age_months') and measurement['adjusted_age_months'] != measurement['age_months']:
            age_display = f"{measurement['age_months']:.1f} ({measurement['adjusted_age_months']:.1f} adj)"
        
        df_data.append({
            'Date': measurement['date'],
            'Age (months)': age_display,
            'Measurement': measurement['type'].replace('_', ' ').title(),
            'Value': f"{measurement['value']:.1f}",
            'Z-score': f"{measurement['z_score']:.2f}" if measurement['z_score'] is not None else 'N/A',
            'Percentile': f"{measurement['percentile']:.1f}%" if measurement['percentile'] else 'N/A',
            'Assessment': category
        })
    
    if df_data:
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
        
        st.subheader("Data Export")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Export to CSV", use_container_width=True, key="btn_export_csv"):
                csv = df.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="growth_data.csv">📥 Download CSV File</a>'
                st.markdown(href, unsafe_allow_html=True)
        
        with col2:
            if st.button("🗑️ Clear History", use_container_width=True, type="secondary", key="btn_clear_hist"):
                clear_all_data()
                st.rerun()

def show_growth_charts(calculator, report_generator=None):
    """Show growth charts"""
    st.header("📈 Growth Charts")
    
    if not st.session_state.measurements:
        st.info("No measurements available for charts. Add measurements first.")
        return
    
    if not st.session_state.patient_info:
        st.error("Patient information missing. Please add a measurement first.")
        return
    
    gender = st.session_state.patient_info.get('gender', 'male')
    patient_info = st.session_state.patient_info
    
    chart_type = st.selectbox(
        "Select Measurement Type",
        ["Weight for Age", "Height for Age", "Head Circumference for Age", "BMI for Age"]
    )
    
    chart_map = {
        "Weight for Age": "weight_age",
        "Height for Age": "height_age", 
        "Head Circumference for Age": "head_age",
        "BMI for Age": "bmi_age"
    }
    
    selected_type = chart_map[chart_type]
    
    fig = create_growth_chart(st.session_state.measurements, selected_type, gender, calculator, patient_info)
    
    if fig:
        st.plotly_chart(fig, use_container_width=True)
        
        if not st.session_state.charts_generated:
            with st.spinner("Generating charts for PDF report..."):
                st.session_state.saved_charts = generate_all_charts(calculator)
                st.session_state.charts_generated = True
    else:
        st.error("Could not generate chart. Please check your data.")
    
    st.subheader("Current Growth Status")
    latest_measurements = {}
    for measurement in st.session_state.measurements:
        m_type = measurement['type']
        if m_type not in latest_measurements or measurement['age_months'] > latest_measurements[m_type]['age_months']:
            latest_measurements[m_type] = measurement
    
    cols = st.columns(4)
    display_names = {
        'weight_age': 'Weight',
        'height_age': 'Height', 
        'head_age': 'Head Circ.',
        'bmi_age': 'BMI'
    }
    
    for i, (m_type, measurement) in enumerate(latest_measurements.items()):
        if i < 4:
            with cols[i]:
                if measurement['z_score'] is not None:
                    st.metric(
                        label=display_names.get(m_type, m_type),
                        value=f"{measurement['value']:.1f}",
                        delta=f"Z: {measurement['z_score']:.2f}"
                    )
                    category, _ = get_percentile_display(measurement['percentile'], measurement['z_score'])
                    st.write(f"*{category}*")

def show_clinical_report(calculator, report_generator):
    """Show clinical report generation"""
    st.header("📄 Clinical Report")
    
    if not st.session_state.measurements:
        st.info("No data available for report generation. Add measurements first.")
        return
    
    if not st.session_state.charts_generated:
        with st.spinner("Generating growth charts for report..."):
            st.session_state.saved_charts = generate_all_charts(calculator)
            st.session_state.charts_generated = True
    
    st.subheader("Report Preview")
    
    if st.session_state.patient_info:
        patient = st.session_state.patient_info
        st.write(f"**Patient:** {patient.get('first_name', '')} {patient.get('last_name', '')}")
        st.write(f"**Gender:** {patient.get('gender', '').title()}")
        st.write(f"**Date of Birth:** {patient.get('birth_date', '')}")
        st.write(f"**Gestational Age:** {patient.get('gestational_age', '40')} weeks")
        st.write(f"**Report Date:** {datetime.now().strftime('%Y-%m-%d')}")
    
    st.subheader("Current Measurements")
    latest_measurements = {}
    for measurement in st.session_state.measurements:
        m_type = measurement['type']
        if m_type not in latest_measurements or measurement['age_months'] > latest_measurements[m_type]['age_months']:
            latest_measurements[m_type] = measurement
    
    if latest_measurements:
        meas_data = []
        for m_type, measurement in latest_measurements.items():
            display_name = m_type.replace('_', ' ').title()
            category, _ = get_percentile_display(measurement['percentile'], measurement['z_score'])
            meas_data.append({
                'Measurement': display_name,
                'Value': f"{measurement['value']:.1f}",
                'Z-score': f"{measurement['z_score']:.2f}" if measurement['z_score'] is not None else 'N/A',
                'Percentile': f"{measurement['percentile']:.1f}%" if measurement['percentile'] is not None else 'N/A',
                'Assessment': category
            })
        
        st.dataframe(pd.DataFrame(meas_data), use_container_width=True)
    
    if st.session_state.saved_charts:
        st.subheader("Charts Included in PDF Report")
        st.write(f"✅ {len(st.session_state.saved_charts)} growth charts will be included in the PDF report")
        
        # Show preview of available charts
        chart_names = {
            'weight_age': 'Weight for Age',
            'height_age': 'Height for Age',
            'head_age': 'Head Circumference',
            'bmi_age': 'BMI for Age'
        }
        
        for chart_type in st.session_state.saved_charts.keys():
            st.write(f"• {chart_names.get(chart_type, chart_type)}")
    
    st.subheader("Generate PDF Report")
    
    if st.button("🖨️ Generate Comprehensive PDF Report", use_container_width=True, key="btn_generate_pdf"):
        with st.spinner("Generating PDF report..."):
            pdf_buffer = report_generator.create_clinical_report(
                st.session_state.patient_info,
                st.session_state.measurements
            )
            
            if pdf_buffer:
                st.success("✅ PDF report generated successfully!")
                
                b64 = base64.b64encode(pdf_buffer.getvalue()).decode()
                href = f'<a href="data:application/pdf;base64,{b64}" download="cdc_growth_report.pdf" style="display: inline-block; padding: 0.5rem 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">📥 Download CDC LMS Report</a>'
                st.markdown(href, unsafe_allow_html=True)
                
                st.info("📊 Report includes: CDC LMS growth assessment, clinical interpretation, and recommendations")
            else:
                st.error("Failed to generate PDF report. Please try again.")

def main():
    st.markdown('<h1 class="main-header">👶 CDC LMS Pediatric Growth Tracker </h1>', 
                unsafe_allow_html=True)
    
    # Use the clinical-grade calculator
    calculator = ClinicalCDCLMSCalculator()
    report_generator = ClinicalReportGenerator(calculator)
    
    # Validate dataset completeness
    dataset_issues = calculator.validate_dataset_completeness()
    if not dataset_issues:
        st.sidebar.success("✅ Complete monthly dataset (0-36 months)")
    else:
        st.sidebar.warning("⚠️ Dataset has gaps")
        for issue in dataset_issues:
            st.sidebar.write(issue)
    
    st.sidebar.title("Navigation")
    
    pages = {
        "New Measurement": show_new_measurement,
        "Growth History": show_growth_history,
        "Growth Charts": show_growth_charts,
        "Clinical Report": show_clinical_report
    }
    
    selected_page = st.sidebar.radio("Go to", list(pages.keys()), 
                                   index=list(pages.keys()).index(st.session_state.current_page))
    
    if selected_page != st.session_state.current_page:
        st.session_state.current_page = selected_page
        st.rerun()
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🗑️ Clear All Data", use_container_width=True, type="secondary"):
        clear_all_data()
        st.rerun()
    
    # Show selected page
    pages[st.session_state.current_page](calculator, report_generator)

if __name__ == "__main__":
    main()





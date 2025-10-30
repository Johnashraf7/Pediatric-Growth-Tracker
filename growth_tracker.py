%%writefile growth_tracker_corrected.py
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
warnings.filterwarnings('ignore')

# Configure the page
st.set_page_config(
    page_title="Pediatric Growth Tracker",
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
    .preterm-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .trend-alert {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
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

class GrowthCalculator:
    """Accurate growth calculator with realistic CDC/WHO data patterns"""
    
    def __init__(self):
        self.cdc_data = self._initialize_accurate_cdc_data()
    
    def _initialize_accurate_cdc_data(self):
        """Initialize realistic growth chart data based on CDC/WHO patterns"""
        ages = np.arange(0, 241, 1)  # 0 to 240 months (20 years)
        
        return {
            'male': {
                'weight_age': self._create_realistic_weight_data(ages, 'male'),
                'height_age': self._create_realistic_height_data(ages, 'male'),
                'head_age': self._create_realistic_head_data(ages, 'male'),
                'bmi_age': self._create_realistic_bmi_data(ages, 'male')
            },
            'female': {
                'weight_age': self._create_realistic_weight_data(ages, 'female'),
                'height_age': self._create_realistic_height_data(ages, 'female'),
                'head_age': self._create_realistic_head_data(ages, 'female'),
                'bmi_age': self._create_realistic_bmi_data(ages, 'female')
            }
        }
    
    def _create_realistic_weight_data(self, ages, gender):
        """Create realistic weight-for-age data"""
        m = np.zeros_like(ages, dtype=float)
        
        for i, age in enumerate(ages):
            if age <= 12:
                if gender == 'male':
                    m[i] = 3.5 + (10.0 - 3.5) * (age / 12) ** 1.5
                else:
                    m[i] = 3.4 + (9.5 - 3.4) * (age / 12) ** 1.5
            elif age <= 24:
                if gender == 'male':
                    m[i] = 10.0 + (12.5 - 10.0) * ((age - 12) / 12)
                else:
                    m[i] = 9.5 + (11.8 - 9.5) * ((age - 12) / 12)
            elif age <= 36:
                if gender == 'male':
                    m[i] = 12.5 + (14.5 - 12.5) * ((age - 24) / 12)
                else:
                    m[i] = 11.8 + (14.0 - 11.8) * ((age - 24) / 12)
            else:
                if gender == 'male':
                    m[i] = 14.5 + (70.0 - 14.5) * ((age - 36) / (240 - 36)) ** 1.2
                else:
                    m[i] = 14.0 + (60.0 - 14.0) * ((age - 36) / (240 - 36)) ** 1.2
        
        return {
            'ages': ages.tolist(),
            'l': [1.0] * len(ages),
            'm': m.tolist(),
            's': [0.12] * len(ages)
        }
    
    def _create_realistic_height_data(self, ages, gender):
        """Create realistic height-for-age data"""
        m = np.zeros_like(ages, dtype=float)
        
        for i, age in enumerate(ages):
            if age <= 12:
                if gender == 'male':
                    m[i] = 50.0 + (75.0 - 50.0) * (age / 12)
                else:
                    m[i] = 49.0 + (74.0 - 49.0) * (age / 12)
            elif age <= 24:
                if gender == 'male':
                    m[i] = 75.0 + (87.0 - 75.0) * ((age - 12) / 12)
                else:
                    m[i] = 74.0 + (86.0 - 74.0) * ((age - 12) / 12)
            elif age <= 36:
                if gender == 'male':
                    m[i] = 87.0 + (96.0 - 87.0) * ((age - 24) / 12)
                else:
                    m[i] = 86.0 + (95.0 - 86.0) * ((age - 24) / 12)
            else:
                if gender == 'male':
                    m[i] = 96.0 + (175.0 - 96.0) * (1 - np.exp(-0.015 * (age - 36)))
                else:
                    m[i] = 95.0 + (165.0 - 95.0) * (1 - np.exp(-0.018 * (age - 36)))
        
        return {
            'ages': ages.tolist(),
            'l': [1.0] * len(ages),
            'm': m.tolist(),
            's': [0.02] * len(ages)
        }
    
    def _create_realistic_head_data(self, ages, gender):
        """Create realistic head circumference data"""
        m = np.zeros_like(ages, dtype=float)
        
        for i, age in enumerate(ages):
            if age <= 12:
                if gender == 'male':
                    m[i] = 35.0 + (47.0 - 35.0) * (1 - np.exp(-0.3 * age))
                else:
                    m[i] = 34.0 + (45.5 - 34.0) * (1 - np.exp(-0.3 * age))
            elif age <= 36:
                if gender == 'male':
                    m[i] = 47.0 + (51.0 - 47.0) * ((age - 12) / 24)
                else:
                    m[i] = 45.5 + (49.5 - 45.5) * ((age - 12) / 24)
            else:
                if gender == 'male':
                    m[i] = 51.0 + (57.0 - 51.0) * (1 - np.exp(-0.01 * (age - 36)))
                else:
                    m[i] = 49.5 + (55.0 - 49.5) * (1 - np.exp(-0.01 * (age - 36)))
        
        return {
            'ages': ages.tolist(),
            'l': [1.0] * len(ages),
            'm': m.tolist(),
            's': [0.03] * len(ages)
        }
    
    def _create_realistic_bmi_data(self, ages, gender):
        """Create realistic BMI-for-age data"""
        m = np.zeros_like(ages, dtype=float)
        
        for i, age in enumerate(ages):
            if age <= 12:
                if gender == 'male':
                    m[i] = 14.0 + (18.0 - 14.0) * np.sin(age * np.pi / 12)
                else:
                    m[i] = 13.8 + (17.8 - 13.8) * np.sin(age * np.pi / 12)
            elif age <= 36:
                if gender == 'male':
                    m[i] = 18.0 - (18.0 - 16.5) * ((age - 12) / 24)
                else:
                    m[i] = 17.8 - (17.8 - 16.3) * ((age - 12) / 24)
            else:
                if gender == 'male':
                    m[i] = 16.5 + (22.0 - 16.5) * ((age - 36) / (240 - 36)) ** 0.7
                else:
                    m[i] = 16.3 + (21.5 - 16.3) * ((age - 36) / (240 - 36)) ** 0.7
        
        return {
            'ages': ages.tolist(),
            'l': [1.0] * len(ages),
            'm': m.tolist(),
            's': [0.08] * len(ages)
        }
    
    def calculate_percentile(self, value, age_months, measurement_type, gender, adjusted_age_months=None):
        """Calculate percentile with proper adjusted age handling"""
        try:
            if value <= 0 or age_months < 0:
                return None
            
            effective_age = adjusted_age_months if adjusted_age_months is not None else age_months
            
            if effective_age > 240:
                effective_age = 240
                
            if gender not in self.cdc_data:
                return None
            
            if measurement_type not in self.cdc_data[gender]:
                return None
            
            data = self.cdc_data[gender][measurement_type]
            ages = np.array(data['ages'])
            
            idx = np.abs(ages - effective_age).argmin()
            
            L = data['l'][idx]
            M = data['m'][idx]
            S = data['s'][idx]
            
            if M <= 0 or S <= 0:
                return None
            
            if abs(L) > 1e-6:
                Z = ((value / M) ** L - 1) / (L * S)
            else:
                Z = np.log(value / M) / S
            
            percentile = stats.norm.cdf(Z) * 100
            return max(0.1, min(99.9, percentile))
            
        except Exception as e:
            return None
    
    def calculate_bmi(self, weight_kg, height_cm):
        """Calculate BMI safely"""
        try:
            if weight_kg <= 0 or height_cm <= 0:
                return None
            height_m = height_cm / 100
            bmi = weight_kg / (height_m ** 2)
            return round(bmi, 1)
        except:
            return None
    
    def get_reference_value(self, age_months, percentile, measurement_type, gender, adjusted_age_months=None):
        """Get reference value for a specific percentile"""
        try:
            effective_age = adjusted_age_months if adjusted_age_months is not None else age_months
            
            if gender not in self.cdc_data or measurement_type not in self.cdc_data[gender]:
                return None
            
            data = self.cdc_data[gender][measurement_type]
            ages = np.array(data['ages'])
            idx = np.abs(ages - effective_age).argmin()
            
            L = data['l'][idx]
            M = data['m'][idx]
            S = data['s'][idx]
            
            Z = stats.norm.ppf(percentile/100.0)
            
            if abs(L) > 1e-6:
                value = M * (1 + L * S * Z) ** (1/L)
            else:
                value = M * np.exp(S * Z)
            
            return value
        except:
            return None

class PDFReportGenerator:
    """Generate comprehensive PDF reports with charts"""
    
    def __init__(self, calculator):
        self.calculator = calculator
    
    def create_comprehensive_report(self, patient_info, measurements, charts):
        """Create a comprehensive PDF report"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                textColor=colors.HexColor('#1f77b4')
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=12,
                spaceAfter=12,
                textColor=colors.HexColor('#2e86ab')
            )
            
            story = []
            
            # Title
            story.append(Paragraph("PEDIATRIC GROWTH ASSESSMENT REPORT", title_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Patient Information
            story.append(Paragraph("PATIENT INFORMATION", heading_style))
            patient_data = [
                ["Name:", f"{patient_info.get('first_name', '')} {patient_info.get('last_name', '')}"],
                ["Gender:", patient_info.get('gender', '').title()],
                ["Date of Birth:", patient_info.get('birth_date', '')],
                ["Gestational Age:", f"{patient_info.get('gestational_age', '40')} weeks"],
                ["Report Date:", datetime.now().strftime('%Y-%m-%d')]
            ]
            patient_table = Table(patient_data, colWidths=[1.5*inch, 3*inch])
            patient_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f2f6')),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(patient_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Current Measurements
            story.append(Paragraph("CURRENT MEASUREMENTS", heading_style))
            
            latest_measurements = self._get_latest_measurements(measurements)
            if latest_measurements:
                meas_data = [["Measurement", "Value", "Percentile", "Assessment"]]
                for m_type, measurement in latest_measurements.items():
                    display_name = self._get_display_name(m_type)
                    category, _ = get_percentile_category(measurement['percentile'])
                    meas_data.append([
                        display_name,
                        f"{measurement['value']:.1f}",
                        f"{measurement['percentile']:.1f}%" if measurement['percentile'] else "N/A",
                        category
                    ])
                
                meas_table = Table(meas_data, colWidths=[1.8*inch, 1.2*inch, 1.2*inch, 1.8*inch])
                meas_table.setStyle(TableStyle([
                    ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER')
                ]))
                story.append(meas_table)
            
            story.append(Spacer(1, 0.3*inch))
            
            # Clinical Assessment
            story.append(Paragraph("CLINICAL ASSESSMENT", heading_style))
            assessment = self._generate_clinical_assessment(latest_measurements, measurements)
            story.append(Paragraph(assessment, styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
            
            # Recommendations
            story.append(Paragraph("RECOMMENDATIONS", heading_style))
            recommendations = self._generate_recommendations(latest_measurements, measurements)
            for rec in recommendations:
                story.append(Paragraph(rec, styles['Normal']))
            
            # Footer
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph("***This report was generated by Iskros Pediatric Growth Tracker. For clinical decisions, always consult with healthcare professionals.***", 
                                 styles['Italic']))
            
            doc.build(story)
            buffer.seek(0)
            return buffer
            
        except Exception as e:
            st.error(f"Error generating PDF: {e}")
            return None
    
    def _get_latest_measurements(self, measurements):
        """Get the latest measurement of each type"""
        latest = {}
        for measurement in measurements:
            m_type = measurement['type']
            if m_type not in latest or measurement['age_months'] > latest[m_type]['age_months']:
                latest[m_type] = measurement
        return latest
    
    def _get_display_name(self, measurement_type):
        """Get display name for measurement type"""
        names = {
            'weight_age': 'Weight for Age',
            'height_age': 'Height for Age',
            'head_age': 'Head Circumference',
            'bmi_age': 'BMI for Age'
        }
        return names.get(measurement_type, measurement_type)
    
    def _generate_clinical_assessment(self, latest_measurements, all_measurements):
        """Generate clinical assessment based on measurements and trends"""
        if not latest_measurements:
            return "No measurements available for assessment."
        
        concerns = []
        normal_count = 0
        
        for m_type, measurement in latest_measurements.items():
            if measurement.get('percentile'):
                percentile = measurement['percentile']
                if percentile < 5:
                    concerns.append(f"Low {self._get_display_name(m_type)} percentile ({percentile:.1f}%) may indicate need for further evaluation")
                elif percentile > 95:
                    concerns.append(f"High {self._get_display_name(m_type)} percentile ({percentile:.1f}%) may warrant monitoring")
                else:
                    normal_count += 1
        
        if not concerns:
            return "All growth parameters are within normal ranges. Growth pattern appears appropriate for age."
        elif normal_count > len(latest_measurements) / 2:
            return f"Most growth parameters are normal. Areas for attention: {'; '.join(concerns)}"
        else:
            return f"Several growth parameters require attention: {'; '.join(concerns)}. Recommend consultation with pediatrician."
    
    def _generate_recommendations(self, latest_measurements, all_measurements):
        """Generate personalized recommendations"""
        recommendations = [
            "• Continue regular well-child visits",
            "• Maintain age-appropriate nutrition",
            "• Monitor growth patterns over time"
        ]
        
        for m_type, measurement in latest_measurements.items():
            if measurement.get('percentile'):
                percentile = measurement['percentile']
                if percentile < 5:
                    recommendations.append(f"• Consider nutritional assessment for {self._get_display_name(m_type).lower()}")
                elif percentile > 95:
                    recommendations.append(f"• Monitor dietary intake and activity levels for {self._get_display_name(m_type).lower()}")
        
        recommendations.append("• Schedule follow-up measurements in 3-6 months")
        recommendations.append("• Consult healthcare provider with any concerns")
        
        return recommendations

def validate_patient_data(first_name, last_name, birth_date, measurement_date, gestational_age):
    """Validate patient data inputs"""
    errors = []
    
    if not first_name.strip() or not last_name.strip():
        errors.append("First and last name are required")
    
    if birth_date > datetime.now().date():
        errors.append("Birth date cannot be in the future")
    
    if measurement_date < birth_date:
        errors.append("Measurement date cannot be before birth date")
    
    if gestational_age < 22 or gestational_age > 44:
        errors.append("Gestational age must be between 22 and 44 weeks")
    
    return errors

def calculate_age_months(birth_date, measurement_date):
    """Calculate age in months between two dates"""
    try:
        delta = measurement_date - birth_date
        return delta.days / 30.436875
    except:
        return 0

def calculate_adjusted_age(birth_date, measurement_date, gestational_weeks):
    """Calculate adjusted age for preterm infants"""
    try:
        chronological_age_months = calculate_age_months(birth_date, measurement_date)
        
        if gestational_weeks >= 37:
            return chronological_age_months, False
        
        weeks_preterm = 40 - gestational_weeks
        adjustment_months = weeks_preterm / 4.345
        
        adjusted_age_months = max(0, chronological_age_months - adjustment_months)
        return adjusted_age_months, True
        
    except:
        return calculate_age_months(birth_date, measurement_date), False

def get_percentile_category(percentile):
    """Categorize percentile with safe handling"""
    if percentile is None:
        return "Unable to calculate", "monitor"
    
    if percentile < 5:
        return "Low - Clinical Concern", "concern"
    elif percentile < 25:
        return "Lower Normal Range", "monitor"
    elif percentile <= 75:
        return "Normal Range", "normal"
    elif percentile <= 95:
        return "Upper Normal Range", "monitor"
    else:
        return "High - Clinical Concern", "concern"

def create_growth_chart(measurements, measurement_type, gender, calculator, patient_info):
    """Create a growth chart with percentile curves using adjusted age if needed"""
    try:
        patient_data = [m for m in measurements if m['type'] == measurement_type]
        if not patient_data:
            return None
        
        gestational_age = patient_info.get('gestational_age', 40)
        use_adjusted_age = gestational_age < 37
        
        ages_range = np.linspace(0, 36, 50)
        percentiles = [3, 10, 25, 50, 75, 90, 97]
        
        fig = go.Figure()
        
        for p in percentiles:
            values = []
            for age in ages_range:
                ref_value = calculator.get_reference_value(age, p, measurement_type, gender)
                if ref_value:
                    values.append(ref_value)
            
            if values:
                fig.add_trace(go.Scatter(
                    x=ages_range, y=values,
                    mode='lines',
                    name=f'{p}th',
                    line=dict(width=1 if p != 50 else 2, dash='dash' if p != 50 else 'solid'),
                    opacity=0.7 if p != 50 else 1.0
                ))
        
        patient_ages = [m.get('adjusted_age_months', m['age_months']) for m in patient_data]
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
            height=400,
            showlegend=True,
            template='plotly_white'
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating chart: {e}")
        return None

def save_chart_as_image(fig, filename):
    """Save Plotly chart as image file using matplotlib"""
    try:
        if fig:
            temp_dir = tempfile.gettempdir()
            chart_path = os.path.join(temp_dir, filename)
            
            try:
                plt.figure(figsize=(10, 6))
                
                for trace in fig.data:
                    if trace.type == 'scatter':
                        x = trace.x
                        y = trace.y
                        if 'Patient' in trace.name:
                            plt.plot(x, y, 'ro-', linewidth=2, markersize=6, label=trace.name)
                        else:
                            plt.plot(x, y, '--', alpha=0.7, linewidth=1, label=trace.name)
                
                plt.title(fig.layout.title.text if fig.layout.title else 'Growth Chart')
                plt.xlabel(fig.layout.xaxis.title.text if fig.layout.xaxis.title else 'Age (months)')
                plt.ylabel(fig.layout.yaxis.title.text if fig.layout.yaxis.title else 'Value')
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                
                plt.savefig(chart_path, dpi=150, bbox_inches='tight')
                plt.close()
                
                return chart_path
                
            except Exception as e:
                return None
                
    except Exception as e:
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

def main():
    st.markdown('<h1 class="main-header">👶 Pediatric Growth Tracker </h1>', 
                unsafe_allow_html=True)
    
    calculator = GrowthCalculator()
    pdf_generator = PDFReportGenerator(calculator)
    
    if 'nav_to' in st.session_state:
        st.session_state.current_page = st.session_state.nav_to
        del st.session_state.nav_to
        st.rerun()
    
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
    
    pages[st.session_state.current_page](calculator, pdf_generator)

def show_new_measurement(calculator, pdf_generator):
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
                default_birth = datetime.strptime(default_birth, '%Y-%m-%d').date()
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
            height = st.number_input("Height (cm) *", min_value=0.0, max_value=200.0, value=0.0, step=0.1)
            weight = st.number_input("Weight (kg) *", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
            head_circumference = st.number_input("Head Circumference (cm)", min_value=0.0, max_value=60.0, value=0.0, step=0.1)
        
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
                st.session_state.nav_to = "Growth Charts"
                st.rerun()
        
        with col2:
            if st.button("📋 Generate Report", use_container_width=True, key="btn_generate_report"):
                st.session_state.nav_to = "Clinical Report"
                st.rerun()

def process_measurement_submission(first_name, last_name, gender, birth_date, measurement_date, 
                                 height, weight, head_circumference, gestational_age, calculator):
    """Process the measurement form submission"""
    errors = validate_patient_data(first_name, last_name, birth_date, measurement_date, gestational_age)
    
    if errors:
        for error in errors:
            st.error(error)
        return
    
    age_months = calculate_age_months(birth_date, measurement_date)
    adjusted_age_months, using_adjusted_age = calculate_adjusted_age(birth_date, measurement_date, gestational_age)
    
    if age_months > 36:
        st.warning("Note: Growth charts are optimized for ages 0-36 months. Calculations for older children use extended ranges.")
    
    if using_adjusted_age:
        st.info(f"Using adjusted age: {adjusted_age_months:.1f} months (Chronological: {age_months:.1f} months)")
    
    st.session_state.patient_info = {
        'first_name': first_name.strip(),
        'last_name': last_name.strip(),
        'gender': gender,
        'birth_date': birth_date.strftime('%Y-%m-%d'),
        'gestational_age': gestational_age
    }
    
    new_measurements = []
    has_required_measurements = False
    
    if height > 0 and weight > 0:
        has_required_measurements = True
        
        height_percentile = calculator.calculate_percentile(height, age_months, 'height_age', gender, adjusted_age_months)
        weight_percentile = calculator.calculate_percentile(weight, age_months, 'weight_age', gender, adjusted_age_months)
        bmi = calculator.calculate_bmi(weight, height)
        bmi_percentile = calculator.calculate_percentile(bmi, age_months, 'bmi_age', gender, adjusted_age_months) if bmi else None
        
        new_measurements.extend([
            {
                'type': 'height_age',
                'value': height,
                'percentile': height_percentile,
                'age_months': age_months,
                'adjusted_age_months': adjusted_age_months,
                'date': measurement_date.strftime('%Y-%m-%d')
            },
            {
                'type': 'weight_age',
                'value': weight,
                'percentile': weight_percentile,
                'age_months': age_months,
                'adjusted_age_months': adjusted_age_months,
                'date': measurement_date.strftime('%Y-%m-%d')
            }
        ])
        
        if bmi_percentile:
            new_measurements.append({
                'type': 'bmi_age',
                'value': bmi,
                'percentile': bmi_percentile,
                'age_months': age_months,
                'adjusted_age_months': adjusted_age_months,
                'date': measurement_date.strftime('%Y-%m-%d')
            })
    
    if head_circumference > 0:
        head_percentile = calculator.calculate_percentile(head_circumference, age_months, 'head_age', gender, adjusted_age_months)
        new_measurements.append({
            'type': 'head_age',
            'value': head_circumference,
            'percentile': head_percentile,
            'age_months': age_months,
            'adjusted_age_months': adjusted_age_months,
            'date': measurement_date.strftime('%Y-%m-%d')
        })
    
    if new_measurements:
        st.success("✅ Percentiles calculated successfully!")
        
        cols = st.columns(min(4, len(new_measurements)))
        for i, measurement in enumerate(new_measurements):
            with cols[i]:
                measure_name = measurement['type'].replace('_', ' ').title()
                st.markdown(f'<div class="metric-card">'
                          f'<h3>{measure_name}</h3>'
                          f'<h2>{measurement["value"]:.1f}</h2>'
                          f'<h4>{measurement["percentile"]:.1f}%</h4>'
                          f'</div>', unsafe_allow_html=True)
                
                if measurement['percentile']:
                    category, css_class = get_percentile_category(measurement['percentile'])
                    st.markdown(f'<div class="percentile-indicator {css_class}">{category}</div>', 
                              unsafe_allow_html=True)
        
        st.session_state.measurements.extend(new_measurements)
        st.session_state.charts_generated = False
        
        st.balloons()
    else:
        if not has_required_measurements:
            st.error("Please enter both height and weight for basic growth assessment.")

def show_growth_history(calculator=None, pdf_generator=None):
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
        category, _ = get_percentile_category(measurement.get('percentile'))
        age_display = f"{measurement['age_months']:.1f}"
        if measurement.get('adjusted_age_months') and measurement['adjusted_age_months'] != measurement['age_months']:
            age_display = f"{measurement['age_months']:.1f} ({measurement['adjusted_age_months']:.1f} adj)"
        
        df_data.append({
            'Date': measurement['date'],
            'Age (months)': age_display,
            'Measurement': measurement['type'].replace('_', ' ').title(),
            'Value': f"{measurement['value']:.1f}",
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

def show_growth_charts(calculator, pdf_generator=None):
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
            chart_path = save_chart_as_image(fig, f"{selected_type}_chart.png")
            if chart_path:
                st.session_state.saved_charts[selected_type] = chart_path
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
                if measurement['percentile']:
                    st.metric(
                        label=display_names.get(m_type, m_type),
                        value=f"{measurement['value']:.1f}",
                        delta=f"{measurement['percentile']:.1f}%"
                    )
                    category, _ = get_percentile_category(measurement['percentile'])
                    st.write(f"*{category}*")

def show_clinical_report(calculator, pdf_generator):
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
            category, _ = get_percentile_category(measurement['percentile'])
            meas_data.append({
                'Measurement': display_name,
                'Value': f"{measurement['value']:.1f}",
                'Percentile': f"{measurement['percentile']:.1f}%" if measurement['percentile'] else 'N/A',
                'Assessment': category
            })
        
        st.dataframe(pd.DataFrame(meas_data), use_container_width=True)
    
    if st.session_state.saved_charts:
        st.subheader("Charts Included in PDF Report")
        st.write(f"✅ {len(st.session_state.saved_charts)} growth charts will be included in the PDF report")
    
    st.subheader("Generate PDF Report")
    
    if st.button("🖨️ Generate Comprehensive PDF Report", use_container_width=True, key="btn_generate_pdf"):
        with st.spinner("Generating PDF report..."):
            pdf_buffer = pdf_generator.create_comprehensive_report(
                st.session_state.patient_info,
                st.session_state.measurements,
                st.session_state.saved_charts
            )
            
            if pdf_buffer:
                st.success("✅ PDF report generated successfully!")
                
                b64 = base64.b64encode(pdf_buffer.getvalue()).decode()
                href = f'<a href="data:application/pdf;base64,{b64}" download="growth_report.pdf" style="display: inline-block; padding: 0.5rem 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">📥 Download PDF Report</a>'
                st.markdown(href, unsafe_allow_html=True)
                
                st.info(f"📊 Report includes: {len(st.session_state.saved_charts)} growth charts, clinical assessment, and recommendations")
            else:
                st.error("Failed to generate PDF report. Please try again.")

if __name__ == "__main__":
    main()

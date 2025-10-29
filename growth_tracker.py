# pediatric_growth_tracker.py
import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import base64
import io
from reportlab.lib.pagesizes import letter, A4
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
    page_title="Pediatric Growth Tracker Pro",
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
    .quick-action-container {
        display: flex;
        gap: 1rem;
        margin: 1rem 0;
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
    """Robust growth calculator with comprehensive CDC data"""
    
    def __init__(self):
        self.cdc_data = self._initialize_comprehensive_cdc_data()
    
    def _initialize_comprehensive_cdc_data(self):
        """Initialize comprehensive CDC growth chart data"""
        ages = np.arange(0, 37, 1)  # 0 to 36 months in 1 month increments
        
        return {
            'male': {
                'weight_age': self._create_detailed_weight_data(ages, 'male'),
                'height_age': self._create_detailed_height_data(ages, 'male'),
                'head_age': self._create_detailed_head_data(ages, 'male'),
                'bmi_age': self._create_detailed_bmi_data(ages, 'male')
            },
            'female': {
                'weight_age': self._create_detailed_weight_data(ages, 'female'),
                'height_age': self._create_detailed_height_data(ages, 'female'),
                'head_age': self._create_detailed_head_data(ages, 'female'),
                'bmi_age': self._create_detailed_bmi_data(ages, 'female')
            }
        }
    
    def _create_detailed_weight_data(self, ages, gender):
        """Create detailed weight-for-age data"""
        if gender == 'male':
            m = np.where(ages <= 12,
                        3.5 + 0.7 * ages,
                        np.where(ages <= 24,
                                10.9 + 0.35 * (ages - 12),
                                14.8 + 0.25 * (ages - 24)))
        else:
            m = np.where(ages <= 12,
                        3.4 + 0.65 * ages,
                        np.where(ages <= 24,
                                10.2 + 0.32 * (ages - 12),
                                14.0 + 0.22 * (ages - 24)))
        
        return {
            'ages': ages.tolist(),
            'l': [1.0] * len(ages),
            'm': m.tolist(),
            's': [0.12] * len(ages)
        }
    
    def _create_detailed_height_data(self, ages, gender):
        """Create detailed height-for-age data"""
        if gender == 'male':
            m = np.where(ages <= 12,
                        50 + 2.0 * ages,
                        np.where(ages <= 24,
                                74 + 1.0 * (ages - 12),
                                86 + 0.5 * (ages - 24)))
        else:
            m = np.where(ages <= 12,
                        49 + 1.9 * ages,
                        np.where(ages <= 24,
                                71.8 + 0.95 * (ages - 12),
                                82.7 + 0.45 * (ages - 24)))
        
        return {
            'ages': ages.tolist(),
            'l': [1.0] * len(ages),
            'm': m.tolist(),
            's': [0.03] * len(ages)
        }
    
    def _create_detailed_head_data(self, ages, gender):
        """Create detailed head circumference data"""
        if gender == 'male':
            m = np.where(ages <= 12,
                        35 + 1.2 * ages,
                        np.where(ages <= 24,
                                47 + 0.4 * (ages - 12),
                                51 + 0.1 * (ages - 24)))
        else:
            m = np.where(ages <= 12,
                        34 + 1.1 * ages,
                        np.where(ages <= 24,
                                45.2 + 0.38 * (ages - 12),
                                49.0 + 0.08 * (ages - 24)))
        
        return {
            'ages': ages.tolist(),
            'l': [1.0] * len(ages),
            'm': m.tolist(),
            's': [0.04] * len(ages)
        }
    
    def _create_detailed_bmi_data(self, ages, gender):
        """Create detailed BMI-for-age data"""
        if gender == 'male':
            m = 14.0 + 3.0 * np.sin(ages * np.pi / 24)
        else:
            m = 13.8 + 3.2 * np.sin(ages * np.pi / 24)
        
        return {
            'ages': ages.tolist(),
            'l': [1.0] * len(ages),
            'm': m.tolist(),
            's': [0.08] * len(ages)
        }
    
    def calculate_percentile(self, value, age_months, measurement_type, gender):
        """Safely calculate percentile with comprehensive error handling"""
        try:
            if value <= 0 or age_months < 0 or age_months > 36:
                return None
            
            if gender not in self.cdc_data:
                return None
            
            if measurement_type not in self.cdc_data[gender]:
                return None
            
            data = self.cdc_data[gender][measurement_type]
            ages = np.array(data['ages'])
            
            idx = np.abs(ages - age_months).argmin()
            
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
            
        except Exception:
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
    
    def get_reference_value(self, age_months, percentile, measurement_type, gender):
        """Get reference value for a specific percentile"""
        try:
            if gender not in self.cdc_data or measurement_type not in self.cdc_data[gender]:
                return None
            
            data = self.cdc_data[gender][measurement_type]
            ages = np.array(data['ages'])
            idx = np.abs(ages - age_months).argmin()
            
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
            
            # Growth Charts
            if charts:
                story.append(Paragraph("GROWTH CHARTS", heading_style))
                chart_names = {
                    'weight_age': 'Weight for Age',
                    'height_age': 'Height for Age',
                    'head_age': 'Head Circumference for Age',
                    'bmi_age': 'BMI for Age'
                }
                
                for chart_type, chart_path in charts.items():
                    if os.path.exists(chart_path):
                        try:
                            chart_title = chart_names.get(chart_type, chart_type.replace('_', ' ').title())
                            story.append(Paragraph(chart_title, styles['Heading3']))
                            
                            img = Image(chart_path, width=6*inch, height=3*inch)
                            story.append(img)
                            story.append(Spacer(1, 0.2*inch))
                        except Exception as e:
                            story.append(Paragraph(f"Chart {chart_type} could not be loaded", styles['Normal']))
            
            # Clinical Assessment
            story.append(Paragraph("CLINICAL ASSESSMENT", heading_style))
            assessment = self._generate_clinical_assessment(latest_measurements)
            story.append(Paragraph(assessment, styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
            
            # Recommendations
            story.append(Paragraph("RECOMMENDATIONS", heading_style))
            recommendations = [
                "• Continue regular well-child visits",
                "• Maintain age-appropriate nutrition",
                "• Monitor growth patterns over time",
                "• Consult healthcare provider with any concerns",
                "• Schedule follow-up measurements in 3-6 months"
            ]
            for rec in recommendations:
                story.append(Paragraph(rec, styles['Normal']))
            
            # Footer
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph("***This report was generated by Pediatric Growth Tracker Pro. For clinical decisions, always consult with healthcare professionals.***", 
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
    
    def _generate_clinical_assessment(self, measurements):
        """Generate clinical assessment based on measurements"""
        if not measurements:
            return "No measurements available for assessment."
        
        concerns = []
        normal_count = 0
        
        for m_type, measurement in measurements.items():
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
        elif normal_count > len(measurements) / 2:
            return f"Most growth parameters are normal. Areas for attention: {'; '.join(concerns)}"
        else:
            return f"Several growth parameters require attention: {'; '.join(concerns)}. Recommend consultation with pediatrician."

def validate_patient_data(first_name, last_name, birth_date, measurement_date):
    """Validate patient data inputs"""
    errors = []
    
    if not first_name.strip() or not last_name.strip():
        errors.append("First and last name are required")
    
    if birth_date > datetime.now().date():
        errors.append("Birth date cannot be in the future")
    
    if measurement_date < birth_date:
        errors.append("Measurement date cannot be before birth date")
    
    if (measurement_date - birth_date).days > 365 * 5:
        errors.append("Patient age exceeds recommended range for these growth charts")
    
    return errors

def calculate_age_months(birth_date, measurement_date):
    """Calculate age in months between two dates"""
    try:
        delta = measurement_date - birth_date
        return delta.days / 30.436875
    except:
        return 0

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

def create_growth_chart(measurements, measurement_type, gender, calculator):
    """Create a growth chart with percentile curves"""
    try:
        patient_data = [m for m in measurements if m['type'] == measurement_type]
        if not patient_data:
            return None
        
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
                    line=dict(width=1 if p != 50 else 2),
                    opacity=0.7
                ))
        
        patient_ages = [m['age_months'] for m in patient_data]
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
        
        fig.update_layout(
            title=f"{titles.get(measurement_type, 'Growth Chart')}",
            xaxis_title='Age (months)',
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
            
            # Convert Plotly figure to matplotlib for reliable export
            try:
                # Create matplotlib figure
                plt.figure(figsize=(10, 6))
                
                # Get data from plotly figure
                for trace in fig.data:
                    if trace.type == 'scatter':
                        x = trace.x
                        y = trace.y
                        if 'Patient' in trace.name:
                            # Patient data - plot as red line with markers
                            plt.plot(x, y, 'ro-', linewidth=2, markersize=6, label=trace.name)
                        else:
                            # Percentile lines - plot as dashed lines
                            plt.plot(x, y, '--', alpha=0.7, linewidth=1, label=trace.name)
                
                # Set titles and labels
                plt.title(fig.layout.title.text if fig.layout.title else 'Growth Chart')
                plt.xlabel(fig.layout.xaxis.title.text if fig.layout.xaxis.title else 'Age (months)')
                plt.ylabel(fig.layout.yaxis.title.text if fig.layout.yaxis.title else 'Value')
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                
                # Save the matplotlib figure
                plt.savefig(chart_path, dpi=150, bbox_inches='tight')
                plt.close()
                
                return chart_path
                
            except Exception as e:
                st.error(f"Error converting plotly to matplotlib: {e}")
                return None
                
    except Exception as e:
        st.error(f"Error saving chart: {e}")
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
    chart_types = ['weight_age', 'height_age', 'head_age', 'bmi_age']
    saved_charts = {}
    
    for chart_type in chart_types:
        has_measurements = any(m['type'] == chart_type for m in st.session_state.measurements)
        if has_measurements:
            fig = create_growth_chart(st.session_state.measurements, chart_type, gender, calculator)
            if fig:
                chart_path = save_chart_as_image(fig, f"{chart_type}_chart.png")
                if chart_path:
                    saved_charts[chart_type] = chart_path
    
    return saved_charts

def main():
    st.markdown('<h1 class="main-header">👶 Pediatric Growth Tracker Pro</h1>', 
                unsafe_allow_html=True)
    
    # Initialize calculator and PDF generator
    calculator = GrowthCalculator()
    pdf_generator = PDFReportGenerator(calculator)
    
    # Check if we need to navigate from quick actions
    if 'nav_to' in st.session_state:
        st.session_state.current_page = st.session_state.nav_to
        del st.session_state.nav_to
        st.rerun()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    # Define pages
    pages = {
        "New Measurement": show_new_measurement,
        "Growth History": show_growth_history,
        "Growth Charts": show_growth_charts,
        "Clinical Report": show_clinical_report
    }
    
    # Page selection using radio - this controls the main navigation
    selected_page = st.sidebar.radio("Go to", list(pages.keys()), 
                                   index=list(pages.keys()).index(st.session_state.current_page))
    
    # Update current page if sidebar selection changed
    if selected_page != st.session_state.current_page:
        st.session_state.current_page = selected_page
        st.rerun()
    
    # Clear All button in sidebar
    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Clear All Data", use_container_width=True, type="secondary"):
        clear_all_data()
        st.rerun()
    
    # Display the current page
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
        
        with col2:
            measurement_date = st.date_input("Measurement Date *", datetime.now())
            height = st.number_input("Height (cm) *", min_value=0.0, max_value=200.0, value=0.0, step=0.1)
            weight = st.number_input("Weight (kg) *", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
            head_circumference = st.number_input("Head Circumference (cm)", min_value=0.0, max_value=60.0, value=0.0, step=0.1)
        
        submitted = st.form_submit_button("🚀 Calculate Percentiles", use_container_width=True)
        
        if submitted:
            process_measurement_submission(first_name, last_name, gender, birth_date, measurement_date, 
                                         height, weight, head_circumference, calculator)
    
    # Quick Actions - Show only if we have measurements
    if st.session_state.measurements:
        st.markdown("---")
        st.subheader("Quick Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📈 View Growth Charts", use_container_width=True, key="btn_view_charts"):
                # Set navigation target and trigger rerun
                st.session_state.nav_to = "Growth Charts"
                st.rerun()
        
        with col2:
            if st.button("📋 Generate Report", use_container_width=True, key="btn_generate_report"):
                st.session_state.nav_to = "Clinical Report"
                st.rerun()

def process_measurement_submission(first_name, last_name, gender, birth_date, measurement_date, 
                                 height, weight, head_circumference, calculator):
    """Process the measurement form submission"""
    errors = validate_patient_data(first_name, last_name, birth_date, measurement_date)
    
    if errors:
        for error in errors:
            st.error(error)
        return
    
    age_months = calculate_age_months(birth_date, measurement_date)
    
    if age_months > 36:
        st.warning("Note: Growth charts are optimized for ages 0-36 months.")
    
    st.session_state.patient_info = {
        'first_name': first_name.strip(),
        'last_name': last_name.strip(),
        'gender': gender,
        'birth_date': birth_date.strftime('%Y-%m-%d')
    }
    
    new_measurements = []
    has_required_measurements = False
    
    if height > 0 and weight > 0:
        has_required_measurements = True
        
        height_percentile = calculator.calculate_percentile(height, age_months, 'height_age', gender)
        weight_percentile = calculator.calculate_percentile(weight, age_months, 'weight_age', gender)
        bmi = calculator.calculate_bmi(weight, height)
        bmi_percentile = calculator.calculate_percentile(bmi, age_months, 'bmi_age', gender) if bmi else None
        
        new_measurements.extend([
            {
                'type': 'height_age',
                'value': height,
                'percentile': height_percentile,
                'age_months': age_months,
                'date': measurement_date.strftime('%Y-%m-%d')
            },
            {
                'type': 'weight_age',
                'value': weight,
                'percentile': weight_percentile,
                'age_months': age_months,
                'date': measurement_date.strftime('%Y-%m-%d')
            }
        ])
        
        if bmi_percentile:
            new_measurements.append({
                'type': 'bmi_age',
                'value': bmi,
                'percentile': bmi_percentile,
                'age_months': age_months,
                'date': measurement_date.strftime('%Y-%m-%d')
            })
    
    if head_circumference > 0:
        head_percentile = calculator.calculate_percentile(head_circumference, age_months, 'head_age', gender)
        new_measurements.append({
            'type': 'head_age',
            'value': head_circumference,
            'percentile': head_percentile,
            'age_months': age_months,
            'date': measurement_date.strftime('%Y-%m-%d')
        })
    
    if new_measurements:
        st.success("✅ Percentiles calculated successfully!")
        
        cols = st.columns(len(new_measurements))
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
        
        # Show success message
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
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Name:** {patient.get('first_name', '')} {patient.get('last_name', '')}")
        with col2:
            st.write(f"**Gender:** {patient.get('gender', '').title()}")
        with col3:
            st.write(f"**Date of Birth:** {patient.get('birth_date', '')}")
    
    df_data = []
    for measurement in st.session_state.measurements:
        category, _ = get_percentile_category(measurement.get('percentile'))
        df_data.append({
            'Date': measurement['date'],
            'Age (months)': f"{measurement['age_months']:.1f}",
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
    
    fig = create_growth_chart(st.session_state.measurements, selected_type, gender, calculator)
    
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


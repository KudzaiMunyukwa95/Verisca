from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from typing import Dict, Any, List
import os

class ReportService:
    @staticmethod
    def generate_assessment_report(claim_data: Dict[str, Any], sessions: List[Dict[str, Any]]) -> BytesIO:
        """
        Generates a PDF report for a claim and its assessments.
        Returns a BytesIO buffer containing the PDF.
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # --- Title ---
        title_style = styles['Heading1']
        elements.append(Paragraph(f"Loss Assessment Report: {claim_data.get('claim_number')}", title_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # --- Claim Details ---
        elements.append(Paragraph("Claim Details", styles['Heading2']))
        claim_info = [
            ["Status", claim_data.get('status')],
            ["Date of Loss", str(claim_data.get('date_of_loss'))],
            ["Peril", claim_data.get('peril_type')],
            ["Farm/Field", f"{claim_data.get('farm_id')} / {claim_data.get('field_id')}"], # Simplify for MVP
        ]
        t = Table(claim_info, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.2 * inch))
        
        # --- Assessment Sessions ---
        for session in sessions:
            elements.append(Paragraph(f"Assessment Session: {session.get('date_started')}", styles['Heading2']))
            
            # Method & Result
            elements.append(Paragraph(f"Method: {session.get('assessment_method')}", styles['Normal']))
            
            result = session.get('calculated_result') or {}
            res_text = f"<b>Final Appraisal:</b> {result.get('average_potential_yield_pct', 'N/A')}% Potential Yield"
            if result.get('loss_percentage'):
                 res_text += f" (Loss: {result.get('loss_percentage')}%)"
            
            elements.append(Paragraph(res_text, styles['Normal']))
            elements.append(Spacer(1, 0.1 * inch))
            
            # Samples Table
            samples = session.get('samples', [])
            if samples:
                elements.append(Paragraph("Field Samples:", styles['Heading3']))
                sample_data = [["#", "Location", "Measurements", "Notes"]]
                for s in samples:
                    loc = "GPS Checked" if s.get('sample_location') else "N/A"
                    meas = str(s.get('measurements'))[:50] + "..." # Truncate
                    sample_data.append([
                        str(s.get('sample_number')),
                        loc,
                        meas,
                        s.get('notes') or ""
                    ])
                
                st = Table(sample_data, colWidths=[0.5*inch, 1.5*inch, 3*inch, 2*inch])
                st.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                ]))
                elements.append(st)
                elements.append(Spacer(1, 0.1 * inch))
                
            # Evidence Photos
            # For MVP: Iterate verify if file exists locally and embed
            # To be robust, need absolute paths
            # Skipping actual image embedding for this step to avoid path errors, 
            # but usually: elements.append(Image(path))
            
        doc.build(elements)
        buffer.seek(0)
        return buffer

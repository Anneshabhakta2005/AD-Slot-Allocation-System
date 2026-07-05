import io
import os
import tempfile
import pandas as pd
import numpy as np
from typing import Dict, Any

# Matplotlib for generating chart images for the PDF report
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from .parser import SLOT_CONFIGS

def calculate_statistics(ads_list, original_df, allocation_metrics) -> Dict[str, Any]:
    """
    Calculates detailed statistics for dashboard and reporting.
    """
    # Original dataset stats
    total_ads = len(original_df)
    avg_budget = float(original_df['Budget'].mean()) if total_ads > 0 else 0.0
    avg_duration = float(original_df['Duration'].mean()) if total_ads > 0 else 0.0
    highest_budget = float(original_df['Budget'].max()) if total_ads > 0 else 0.0
    lowest_budget = float(original_df['Budget'].min()) if total_ads > 0 else 0.0
    
    # Most requested slot
    slot_counts = original_df['PreferredSlot'].value_counts()
    most_requested_slot = str(slot_counts.index[0]) if not slot_counts.empty else 'N/A'
    
    # Allocation stats
    allocated_df = pd.DataFrame([ad for ad in ads_list if ad['Status'] == 'Allocated'])
    rejected_df = pd.DataFrame([ad for ad in ads_list if ad['Status'] == 'Rejected'])
    
    allocated_count = len(allocated_df)
    rejected_count = len(rejected_df)
    
    # Most profitable slot
    if not allocated_df.empty:
        slot_revenue = allocated_df.groupby('AllocatedSlot')['Budget'].sum()
        most_profitable_slot = str(slot_revenue.idxmax()) if not slot_revenue.empty else 'N/A'
    else:
        most_profitable_slot = 'N/A'
        
    # Priority distribution (Original dataset)
    priority_counts = original_df['Priority'].value_counts().sort_index()
    priority_dist = {int(k): int(v) for k, v in priority_counts.items()}
    
    # Slot utilization percentages
    utilization_pct = {}
    for slot, config in SLOT_CONFIGS.items():
        used_time = allocation_metrics['slot_utilization'].get(slot, 0)
        pct = (used_time / config['capacity']) * 100.0
        utilization_pct[slot] = round(pct, 2)
        
    return {
        'total_ads': total_ads,
        'allocated_count': allocated_count,
        'rejected_count': rejected_count,
        'avg_budget': avg_budget,
        'avg_duration': avg_duration,
        'highest_budget': highest_budget,
        'lowest_budget': lowest_budget,
        'most_requested_slot': most_requested_slot,
        'most_profitable_slot': most_profitable_slot,
        'priority_dist': priority_dist,
        'slot_utilization_pct': utilization_pct
    }

def generate_pdf_report_buffer(allocation_result: Dict[str, Any], stats: Dict[str, Any]) -> io.BytesIO:
    """
    Generates a PDF report containing charts, statistics, and tables,
    and returns it as an in-memory BytesIO buffer.
    """
    ads = allocation_result['ads']
    metrics = allocation_result['metrics']
    comparisons = allocation_result.get('comparisons', {})
    algorithm = metrics['algorithm_name']
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1e1b4b'), # Indigo
        spaceAfter=15,
        alignment=1 # Center
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=10,
        textColor=colors.HexColor('#475569'),
        spaceAfter=25,
        alignment=1
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#4338ca'),
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )
    
    normal_text = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155')
    )
    
    table_cell = ParagraphStyle(
        'TableCellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1e293b')
    )
    
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=table_cell,
        fontName='Helvetica-Bold'
    )
    
    elements = []
    
    # 1. Header Section
    elements.append(Paragraph("Smart Advertisement Slot Allocation Report", title_style))
    elements.append(Paragraph(f"Algorithm Applied: <b>{algorithm} Scheduling</b> | Dataset Summary Report", subtitle_style))
    elements.append(Spacer(1, 10))
    
    # 2. Key Metrics Summary Cards (Table representation)
    summary_data = [
        [
            Paragraph("<b>Total Revenue</b>", table_cell_bold),
            Paragraph("<b>Allocated Ads</b>", table_cell_bold),
            Paragraph("<b>Rejected Ads</b>", table_cell_bold),
            Paragraph("<b>Execution Time</b>", table_cell_bold)
        ],
        [
            Paragraph(f"${metrics['total_revenue']:,.2f}", table_cell),
            Paragraph(f"{metrics['allocated_count']} / {stats['total_ads']}", table_cell),
            Paragraph(f"{metrics['rejected_count']}", table_cell),
            Paragraph(f"{metrics['execution_time_ms']:.4f} ms", table_cell)
        ]
    ]
    
    t_summary = Table(summary_data, colWidths=[130, 130, 130, 130])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e0e7ff')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#f8fafc')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
    ]))
    
    elements.append(Paragraph("Key Performance Metrics", section_heading))
    elements.append(t_summary)
    elements.append(Spacer(1, 15))
    
    # 3. Statistics Grid
    stats_data = [
        [Paragraph("<b>Stat Metric</b>", table_cell_bold), Paragraph("<b>Value</b>", table_cell_bold), Paragraph("<b>Stat Metric</b>", table_cell_bold), Paragraph("<b>Value</b>", table_cell_bold)],
        [Paragraph("Average Budget", table_cell), Paragraph(f"${stats['avg_budget']:,.2f}", table_cell), Paragraph("Average Duration", table_cell), Paragraph(f"{stats['avg_duration']:.2f} mins", table_cell)],
        [Paragraph("Highest Budget", table_cell), Paragraph(f"${stats['highest_budget']:,.2f}", table_cell), Paragraph("Lowest Budget", table_cell), Paragraph(f"${stats['lowest_budget']:,.2f}", table_cell)],
        [Paragraph("Most Requested Slot", table_cell), Paragraph(stats['most_requested_slot'], table_cell), Paragraph("Most Profitable Slot", table_cell), Paragraph(stats['most_profitable_slot'], table_cell)],
    ]
    t_stats = Table(stats_data, colWidths=[150, 110, 150, 110])
    t_stats.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(Paragraph("Dataset Statistics", section_heading))
    elements.append(t_stats)
    elements.append(Spacer(1, 20))
    
    # Generate Charts via Matplotlib and insert into PDF
    # We will construct a double chart row
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    
    # Chart 1: Revenue by Slot
    slots_list = list(SLOT_CONFIGS.keys())
    # Calculate revenue per slot in result
    rev_per_slot = {s: 0.0 for s in slots_list}
    for ad in ads:
        if ad['Status'] == 'Allocated':
            rev_per_slot[ad['AllocatedSlot']] += float(ad['Budget'])
            
    ax1.bar(rev_per_slot.keys(), rev_per_slot.values(), color=['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e'])
    ax1.set_title("Revenue by Slot ($)", fontsize=10, fontweight='bold', color='#1e1b4b')
    ax1.set_ylabel("Revenue")
    ax1.tick_params(axis='both', labelsize=8)
    
    # Chart 2: Allocation Ratio
    ax2.pie(
        [metrics['allocated_count'], metrics['rejected_count']],
        labels=['Allocated', 'Rejected'],
        autopct='%1.1f%%',
        colors=['#10b981', '#ef4444'],
        startangle=90,
        textprops={'fontsize': 8}
    )
    ax2.set_title("Allocated vs Rejected Count", fontsize=10, fontweight='bold', color='#1e1b4b')
    
    plt.tight_layout()
    
    # Save plot to temp file and load as flowable
    temp_img = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    temp_img_path = temp_img.name
    temp_img.close()
    
    plt.savefig(temp_img_path, dpi=200)
    plt.close(fig)
    
    img_flowable = Image(temp_img_path, width=7.2*inch, height=2.88*inch)
    elements.append(Paragraph("Allocation Visualizations", section_heading))
    elements.append(img_flowable)
    elements.append(Spacer(1, 10))
    
    # Page Break for the Table
    elements.append(PageBreak())
    
    # 4. Allocation Details Table
    elements.append(Paragraph("Detailed Allocation Schedule", section_heading))
    
    table_headers = [
        Paragraph("<b>Ad ID</b>", table_cell_bold),
        Paragraph("<b>Duration</b>", table_cell_bold),
        Paragraph("<b>Budget</b>", table_cell_bold),
        Paragraph("<b>Priority</b>", table_cell_bold),
        Paragraph("<b>Slot Pref</b>", table_cell_bold),
        Paragraph("<b>Allocated Slot</b>", table_cell_bold),
        Paragraph("<b>Schedule</b>", table_cell_bold),
        Paragraph("<b>Status</b>", table_cell_bold)
    ]
    
    table_rows = [table_headers]
    for ad in ads[:100]: # Cap table at 100 rows in PDF to keep document size reasonable
        sched = f"{ad.get('AllocatedStartTime', 'N/A')} - {ad.get('AllocatedEndTime', 'N/A')}" if ad['Status'] == 'Allocated' else 'N/A'
        
        status_color = '#10b981' if ad['Status'] == 'Allocated' else '#ef4444'
        status_para = Paragraph(f"<font color='{status_color}'><b>{ad['Status']}</b></font>", table_cell)
        
        row = [
            Paragraph(ad['AdvertisementID'], table_cell),
            Paragraph(f"{ad['Duration']}m", table_cell),
            Paragraph(f"${ad['Budget']:,.0f}", table_cell),
            Paragraph(str(ad['Priority']), table_cell),
            Paragraph(ad['PreferredSlot'], table_cell),
            Paragraph(ad['AllocatedSlot'], table_cell),
            Paragraph(sched, table_cell),
            status_para
        ]
        table_rows.append(row)
        
    # Table layout: width margins total 520
    t_details = Table(table_rows, colWidths=[65, 55, 60, 45, 65, 80, 85, 65])
    t_details_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e1b4b')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ])
    
    # Textcolor white for header paragraph hack
    for col_idx in range(len(table_headers)):
        table_headers[col_idx].style.textColor = colors.white
        
    t_details.setStyle(t_details_style)
    elements.append(t_details)
    
    if len(ads) > 100:
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"<i>* Showing first 100 of {len(ads)} advertisements. Export CSV to download the complete set.</i>", normal_text))
        
    # 5. Algorithm Comparison Table
    if comparisons:
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Algorithm Performance Benchmarks", section_heading))
        comp_headers = [
            Paragraph("<b>Algorithm</b>", table_cell_bold),
            Paragraph("<b>Revenue ($)</b>", table_cell_bold),
            Paragraph("<b>Allocated Ads</b>", table_cell_bold),
            Paragraph("<b>Rejected Ads</b>", table_cell_bold),
            Paragraph("<b>Unused Mins</b>", table_cell_bold),
            Paragraph("<b>Execution (ms)</b>", table_cell_bold)
        ]
        comp_rows = [comp_headers]
        for alg_name, data in comparisons.items():
            comp_rows.append([
                Paragraph(alg_name.capitalize(), table_cell_bold),
                Paragraph(f"${data['revenue']:,.2f}", table_cell),
                Paragraph(str(data['allocated']), table_cell),
                Paragraph(str(data['rejected']), table_cell),
                Paragraph(str(data['unused_mins']), table_cell),
                Paragraph(f"{data['time_ms']:.4f} ms", table_cell)
            ])
        t_comp = Table(comp_rows, colWidths=[100, 90, 80, 80, 80, 90])
        t_comp.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f8fafc')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(t_comp)
        
    # Build Document
    try:
        doc.build(elements)
    finally:
        # Cleanup temporary image file
        if os.path.exists(temp_img_path):
            try:
                os.unlink(temp_img_path)
            except OSError:
                pass
                
    buffer.seek(0)
    return buffer

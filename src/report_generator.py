"""PDF Report Generator for VMware Inventory."""

from datetime import datetime
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from sqlalchemy import create_engine, func, case
from sqlalchemy.orm import sessionmaker
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from .models import VirtualMachine
import pandas as pd


class VMwareInventoryReport:
    """Generate comprehensive PDF reports for VMware inventory.
    
    Modes:
    - Standard: Key charts and tables (default)
    - Extended: Includes all charts from the web interface where feasible
    - Summary: Tables only
    """
    
    def __init__(self, db_url: str, *, include_charts: bool = True, extended: bool = False, chart_dpi: int = 150):
        """Initialize report generator.
        
        Args:
            db_url: SQLAlchemy database URL
        """
        self.db_url = db_url
        self.engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=self.engine)
        self.session = SessionLocal()
        self.include_charts = include_charts
        self.extended = extended
        self.chart_dpi = max(100, min(int(chart_dpi), 300))  # clamp 100-300
        
        # Setup styles
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2e8b57'),
            spaceAfter=12,
            spaceBefore=12
        )
        
    def generate_report(self) -> BytesIO:
        """Generate complete PDF report.
        
        Returns:
            BytesIO: PDF file content
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
        
        # Build story
        story = []
        
        # Title page
        story.extend(self._create_title_page())
        story.append(PageBreak())
        
        # Executive Summary
        story.extend(self._create_executive_summary())
        story.append(PageBreak())
        
        # Infrastructure Overview
        story.extend(self._create_infrastructure_section())
        story.append(PageBreak())
        
        # Resource Analysis
        story.extend(self._create_resource_section())
        story.append(PageBreak())
        
        # Storage Analysis
        story.extend(self._create_storage_section())
        story.append(PageBreak())
        
        # Folder Analysis
        story.extend(self._create_folder_section())
        story.append(PageBreak())
        
        # Extended Analytics (only in extended mode)
        if self.extended:
            story.extend(self._create_extended_analytics_section())
            story.append(PageBreak())
            
            story.extend(self._create_extended_comparison_section())
            story.append(PageBreak())
            
            story.extend(self._create_extended_folder_analytics_section())
            story.append(PageBreak())
        
        # Data Quality
        story.extend(self._create_data_quality_section())
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer
    
    def _create_title_page(self) -> list:
        """Create title page."""
        elements = []
        
        # Title
        title = Paragraph("VMware vSphere<br/>Inventory Report", self.title_style)
        elements.append(Spacer(1, 2*inch))
        elements.append(title)
        elements.append(Spacer(1, 0.5*inch))
        
        # Date
        date_style = ParagraphStyle(
            'DateStyle',
            parent=self.styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER
        )
        date_text = Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %H:%M')}", date_style)
        elements.append(date_text)
        elements.append(Spacer(1, 0.3*inch))
        
        # Database info
        db_info = Paragraph(f"Database: {self.db_url.split('/')[-1]}", date_style)
        elements.append(db_info)
        
        return elements
    
    def _create_chart(self, fig, width=5*inch, height=3*inch) -> Image:
        """Convert matplotlib figure to reportlab Image.
        
        Args:
            fig: matplotlib figure
            width: desired width in reportlab units
            height: desired height in reportlab units
            
        Returns:
            Image: reportlab Image object
        """
        img_buffer = BytesIO()
        fig.savefig(img_buffer, format='png', dpi=self.chart_dpi, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close(fig)
        
        img = Image(img_buffer, width=width, height=height)
        return img
    
    def _create_executive_summary(self) -> list:
        """Create executive summary section."""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Get key metrics
        total_vms = self.session.query(func.count(VirtualMachine.id)).scalar() or 0
        powered_on = self.session.query(func.count(VirtualMachine.id)).filter(
            VirtualMachine.powerstate == "poweredOn"
        ).scalar() or 0
        powered_off = total_vms - powered_on
        
        total_cpus = self.session.query(func.sum(VirtualMachine.cpus)).scalar() or 0
        total_memory_gb = (self.session.query(func.sum(VirtualMachine.memory)).scalar() or 0) / 1024
        
        datacenters = self.session.query(func.count(func.distinct(VirtualMachine.datacenter))).scalar() or 0
        clusters = self.session.query(func.count(func.distinct(VirtualMachine.cluster))).scalar() or 0
        hosts = self.session.query(func.count(func.distinct(VirtualMachine.host))).scalar() or 0
        
        # Create summary table
        data = [
            ['Metric', 'Value'],
            ['Total Virtual Machines', f'{total_vms:,}'],
            ['Powered On', f'{powered_on:,} ({powered_on/total_vms*100:.1f}%)' if total_vms > 0 else '0'],
            ['Powered Off', f'{powered_off:,} ({powered_off/total_vms*100:.1f}%)' if total_vms > 0 else '0'],
            ['Total vCPUs', f'{int(total_cpus):,}'],
            ['Total Memory', f'{total_memory_gb:,.0f} GB'],
            ['Datacenters', f'{datacenters}'],
            ['Clusters', f'{clusters}'],
            ['ESXi Hosts', f'{hosts}'],
        ]
        
        table = Table(data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Add summary text
        summary_text = f"""
        This VMware vSphere environment consists of <b>{total_vms:,} virtual machines</b> distributed 
        across <b>{datacenters} datacenter(s)</b>, <b>{clusters} cluster(s)</b>, and <b>{hosts} ESXi host(s)</b>.
        Currently, <b>{powered_on:,} VMs ({powered_on/total_vms*100:.1f}%)</b> are powered on, 
        consuming a total of <b>{int(total_cpus):,} vCPUs</b> and <b>{total_memory_gb:,.0f} GB</b> of memory.
        """
        elements.append(Paragraph(summary_text, self.styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Add power state pie chart
        elements.append(Paragraph("Power State Distribution", self.styles['Heading3']))
        elements.append(Spacer(1, 0.1*inch))
        
        fig, ax = plt.subplots(figsize=(6, 4))
        power_data = [powered_on, powered_off]
        power_labels = [f'Powered On\n{powered_on:,}', f'Powered Off\n{powered_off:,}']
        colors_pie = ['#2ecc71', '#e74c3c']
        
        ax.pie(power_data, labels=power_labels, autopct='%1.1f%%', 
               colors=colors_pie, startangle=90)
        ax.set_title('VM Power State Distribution', fontsize=12, fontweight='bold')
        
        if self.include_charts:
            elements.append(self._create_chart(fig, width=4.5*inch, height=3*inch))
        
        return elements
    
    def _create_infrastructure_section(self) -> list:
        """Create infrastructure overview section."""
        elements = []
        
        elements.append(Paragraph("Infrastructure Overview", self.heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Datacenter breakdown
        dc_stats = self.session.query(
            VirtualMachine.datacenter,
            func.count(VirtualMachine.id).label('vm_count')
        ).group_by(VirtualMachine.datacenter).order_by(func.count(VirtualMachine.id).desc()).limit(10).all()
        
        if dc_stats:
            elements.append(Paragraph("Top 10 Datacenters by VM Count", self.styles['Heading3']))
            elements.append(Spacer(1, 0.1*inch))
            
            data = [['Datacenter', 'VM Count']]
            for dc, count in dc_stats:
                data.append([str(dc or 'Unknown'), f'{count:,}'])
            
            table = Table(data, colWidths=[3.5*inch, 1.5*inch])
            table.setStyle(self._get_table_style())
            elements.append(table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Add datacenter bar chart
            if self.include_charts and len(dc_stats) > 1:
                fig, ax = plt.subplots(figsize=(6, 4))
                dc_names = [str(dc or 'Unknown')[:20] for dc, _ in dc_stats[:10]]
                dc_counts = [count for _, count in dc_stats[:10]]
                
                bars = ax.barh(dc_names, dc_counts, color='#3498db')
                ax.set_xlabel('VM Count', fontsize=10)
                ax.set_title('VMs per Datacenter', fontsize=12, fontweight='bold')
                ax.invert_yaxis()
                
                # Add value labels
                for bar in bars:
                    width = bar.get_width()
                    ax.text(width, bar.get_y() + bar.get_height()/2, 
                           f'{int(width):,}', ha='left', va='center', fontsize=8)
                
                plt.tight_layout()
                elements.append(self._create_chart(fig, width=5*inch, height=3*inch))
                elements.append(Spacer(1, 0.3*inch))
        
        # Cluster breakdown
        cluster_stats = self.session.query(
            VirtualMachine.cluster,
            func.count(VirtualMachine.id).label('vm_count'),
            func.sum(VirtualMachine.cpus).label('total_cpus'),
            func.sum(VirtualMachine.memory).label('total_memory')
        ).group_by(VirtualMachine.cluster).order_by(func.count(VirtualMachine.id).desc()).limit(10).all()
        
        if cluster_stats:
            elements.append(Paragraph("Top 10 Clusters by VM Count", self.styles['Heading3']))
            elements.append(Spacer(1, 0.1*inch))
            
            data = [['Cluster', 'VMs', 'vCPUs', 'Memory (GB)']]
            for cluster, count, cpus, memory in cluster_stats:
                memory_gb = (memory or 0) / 1024
                data.append([
                    str(cluster or 'Unknown'),
                    f'{count:,}',
                    f'{int(cpus or 0):,}',
                    f'{memory_gb:,.0f}'
                ])
            
            table = Table(data, colWidths=[2*inch, 1*inch, 1*inch, 1.5*inch])
            table.setStyle(self._get_table_style())
            elements.append(table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Add cluster resource chart
            if self.include_charts and len(cluster_stats) > 1:
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
                
                # Top 10 clusters by VM count
                cluster_names = [str(c or 'Unknown')[:15] for c, _, _, _ in cluster_stats[:10]]
                vm_counts = [count for _, count, _, _ in cluster_stats[:10]]
                
                ax1.barh(cluster_names, vm_counts, color='#9b59b6')
                ax1.set_xlabel('VM Count', fontsize=10)
                ax1.set_title('Top 10 Clusters by VM Count', fontsize=11, fontweight='bold')
                ax1.invert_yaxis()
                
                # vCPU allocation
                cpu_counts = [int(cpus or 0) for _, _, cpus, _ in cluster_stats[:10]]
                ax2.barh(cluster_names, cpu_counts, color='#e67e22')
                ax2.set_xlabel('Total vCPUs', fontsize=10)
                ax2.set_title('vCPU Allocation by Cluster', fontsize=11, fontweight='bold')
                ax2.invert_yaxis()
                
                plt.tight_layout()
                elements.append(self._create_chart(fig, width=6.5*inch, height=3*inch))
        
        return elements
    
    def _create_resource_section(self) -> list:
        """Create resource analysis section."""
        elements = []
        
        elements.append(Paragraph("Resource Analysis", self.heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # CPU distribution
        elements.append(Paragraph("vCPU Allocation", self.styles['Heading3']))
        elements.append(Spacer(1, 0.1*inch))
        
        cpu_stats = self.session.query(
            VirtualMachine.cpus,
            func.count(VirtualMachine.id).label('count')
        ).filter(VirtualMachine.cpus.isnot(None)).group_by(
            VirtualMachine.cpus
        ).order_by(VirtualMachine.cpus).all()
        
        if cpu_stats:
            data = [['vCPUs', 'VM Count', 'Percentage']]
            total_vms = sum(count for _, count in cpu_stats)
            for cpus, count in cpu_stats[:10]:  # Top 10
                pct = (count / total_vms * 100) if total_vms > 0 else 0
                data.append([f'{cpus}', f'{count:,}', f'{pct:.1f}%'])
            
            table = Table(data, colWidths=[1.5*inch, 2*inch, 2*inch])
            table.setStyle(self._get_table_style())
            elements.append(table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Add CPU distribution chart
            if self.include_charts and len(cpu_stats) > 1:
                fig, ax = plt.subplots(figsize=(6, 3.5))
                cpus_list = [cpus for cpus, _ in cpu_stats[:15]]
                counts_list = [count for _, count in cpu_stats[:15]]
                
                bars = ax.bar(range(len(cpus_list)), counts_list, color='#3498db')
                ax.set_xlabel('vCPU Configuration', fontsize=10)
                ax.set_ylabel('VM Count', fontsize=10)
                ax.set_title('vCPU Distribution', fontsize=12, fontweight='bold')
                ax.set_xticks(range(len(cpus_list)))
                ax.set_xticklabels([f'{c}' for c in cpus_list], fontsize=8)
                
                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(height):,}', ha='center', va='bottom', fontsize=7)
                
                plt.tight_layout()
                elements.append(self._create_chart(fig, width=5.5*inch, height=3*inch))
                elements.append(Spacer(1, 0.3*inch))
        
        # Memory distribution
        elements.append(Paragraph("Memory Allocation Distribution", self.styles['Heading3']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Define memory ranges
        memory_ranges = [
            (0, 2048, "< 2 GB"),
            (2048, 4096, "2-4 GB"),
            (4096, 8192, "4-8 GB"),
            (8192, 16384, "8-16 GB"),
            (16384, 32768, "16-32 GB"),
            (32768, 999999, "> 32 GB")
        ]
        
        data = [['Memory Range', 'VM Count', 'Percentage']]
        total_vms = self.session.query(func.count(VirtualMachine.id)).filter(
            VirtualMachine.memory.isnot(None)
        ).scalar() or 0
        
        for min_mem, max_mem, label in memory_ranges:
            count = self.session.query(func.count(VirtualMachine.id)).filter(
                VirtualMachine.memory >= min_mem,
                VirtualMachine.memory < max_mem
            ).scalar() or 0
            
            pct = (count / total_vms * 100) if total_vms > 0 else 0
            data.append([label, f'{count:,}', f'{pct:.1f}%'])
        
        table = Table(data, colWidths=[2*inch, 1.5*inch, 2*inch])
        table.setStyle(self._get_table_style())
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Add memory distribution chart
        mem_labels = [label for _, _, label in memory_ranges]
        mem_counts = []
        for min_mem, max_mem, _ in memory_ranges:
            count = self.session.query(func.count(VirtualMachine.id)).filter(
                VirtualMachine.memory >= min_mem,
                VirtualMachine.memory < max_mem
            ).scalar() or 0
            mem_counts.append(count)
        
        if self.include_charts and sum(mem_counts) > 0:
            fig, ax = plt.subplots(figsize=(6, 3.5))
            bars = ax.bar(mem_labels, mem_counts, color='#e74c3c')
            ax.set_xlabel('Memory Range', fontsize=10)
            ax.set_ylabel('VM Count', fontsize=10)
            ax.set_title('Memory Distribution', fontsize=12, fontweight='bold')
            plt.xticks(rotation=45, ha='right', fontsize=8)
            
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(height):,}', ha='center', va='bottom', fontsize=7)
            
            plt.tight_layout()
            elements.append(self._create_chart(fig, width=5.5*inch, height=3*inch))
        
        return elements
    
    def _create_storage_section(self) -> list:
        """Create storage analysis section."""
        elements = []
        
        elements.append(Paragraph("Storage Analysis", self.heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Storage summary
        total_provisioned = (self.session.query(func.sum(VirtualMachine.provisioned_mib)).scalar() or 0) / 1024
        total_in_use = (self.session.query(func.sum(VirtualMachine.in_use_mib)).scalar() or 0) / 1024
        total_unshared = (self.session.query(func.sum(VirtualMachine.unshared_mib)).scalar() or 0) / 1024
        
        efficiency = (total_in_use / total_provisioned * 100) if total_provisioned > 0 else 0
        
        data = [
            ['Storage Metric', 'Value'],
            ['Total Provisioned', f'{total_provisioned:,.0f} GB'],
            ['Total In Use', f'{total_in_use:,.0f} GB'],
            ['Total Unshared', f'{total_unshared:,.0f} GB'],
            ['Storage Efficiency', f'{efficiency:.1f}%'],
            ['Thin Provisioning Savings', f'{total_provisioned - total_in_use:,.0f} GB'],
        ]
        
        table = Table(data, colWidths=[3*inch, 2*inch])
        table.setStyle(self._get_table_style())
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Add storage visualization
        if self.include_charts and total_provisioned > 0:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.5))
            
            # Storage breakdown bar chart
            storage_types = ['Provisioned', 'In Use', 'Unshared']
            storage_values = [total_provisioned, total_in_use, total_unshared]
            colors_bar = ['#3498db', '#2ecc71', '#f39c12']
            
            bars = ax1.bar(storage_types, storage_values, color=colors_bar)
            ax1.set_ylabel('Storage (GB)', fontsize=10)
            ax1.set_title('Storage Breakdown', fontsize=11, fontweight='bold')
            
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height):,}', ha='center', va='bottom', fontsize=8)
            
            # Storage efficiency gauge/comparison
            categories = ['Provisioned', 'Actually Used']
            values = [total_provisioned, total_in_use]
            colors_gauge = ['#95a5a6', '#27ae60']
            
            ax2.barh(categories, values, color=colors_gauge)
            ax2.set_xlabel('Storage (GB)', fontsize=10)
            ax2.set_title(f'Storage Efficiency: {efficiency:.1f}%', fontsize=11, fontweight='bold')
            ax2.invert_yaxis()
            
            # Add value labels
            for i, (cat, val) in enumerate(zip(categories, values)):
                ax2.text(val, i, f' {int(val):,} GB', va='center', fontsize=8)
            
            plt.tight_layout()
            elements.append(self._create_chart(fig, width=6.5*inch, height=2.8*inch))
        
        return elements
    
    def _create_folder_section(self) -> list:
        """Create folder analysis section."""
        elements = []
        
        elements.append(Paragraph("Folder Analysis", self.heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Top folders by VM count
        folder_stats = self.session.query(
            VirtualMachine.folder,
            func.count(VirtualMachine.id).label('vm_count'),
            func.sum(VirtualMachine.cpus).label('total_cpus'),
            func.sum(VirtualMachine.memory).label('total_memory')
        ).filter(VirtualMachine.folder.isnot(None)).group_by(
            VirtualMachine.folder
        ).order_by(func.count(VirtualMachine.id).desc()).limit(15).all()
        
        if folder_stats:
            elements.append(Paragraph("Top 15 Folders by VM Count", self.styles['Heading3']))
            elements.append(Spacer(1, 0.1*inch))
            
            data = [['Folder', 'VMs', 'vCPUs', 'Memory (GB)']]
            for folder, count, cpus, memory in folder_stats:
                memory_gb = (memory or 0) / 1024
                folder_name = str(folder)[:40] if folder else 'Unknown'  # Truncate long names
                data.append([
                    folder_name,
                    f'{count:,}',
                    f'{int(cpus or 0):,}',
                    f'{memory_gb:,.0f}'
                ])
            
            table = Table(data, colWidths=[2.5*inch, 0.8*inch, 1*inch, 1.2*inch])
            table.setStyle(self._get_table_style())
            elements.append(table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Add folder chart
            if self.include_charts and len(folder_stats) > 1:
                fig, ax = plt.subplots(figsize=(7, 4))
                
                folder_names = [str(f)[:25] + '...' if len(str(f)) > 25 else str(f) 
                               for f, _, _, _ in folder_stats[:12]]
                vm_counts = [count for _, count, _, _ in folder_stats[:12]]
                
                bars = ax.barh(folder_names, vm_counts, color='#9b59b6')
                ax.set_xlabel('VM Count', fontsize=10)
                ax.set_title('Top 12 Folders by VM Count', fontsize=12, fontweight='bold')
                ax.invert_yaxis()
                
                # Add value labels
                for bar in bars:
                    width = bar.get_width()
                    ax.text(width, bar.get_y() + bar.get_height()/2,
                           f' {int(width):,}', va='center', fontsize=8)
                
                plt.tight_layout()
                elements.append(self._create_chart(fig, width=6*inch, height=3.5*inch))
        
        return elements
    
    def _create_data_quality_section(self) -> list:
        """Create data quality section."""
        elements = []
        
        elements.append(Paragraph("Data Quality Report", self.heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        total_vms = self.session.query(func.count(VirtualMachine.id)).scalar() or 0
        
        # Check key fields for completeness
        fields_to_check = [
            ('dns_name', 'DNS Name'),
            ('primary_ip_address', 'IP Address'),
            ('os_config', 'OS Configuration'),
            ('folder', 'Folder'),
            ('datacenter', 'Datacenter'),
            ('cluster', 'Cluster'),
            ('host', 'Host'),
        ]
        
        data = [['Field', 'Populated', 'Missing', 'Completeness']]
        
        for field_name, display_name in fields_to_check:
            col_attr = getattr(VirtualMachine, field_name)
            populated = self.session.query(func.count(VirtualMachine.id)).filter(
                col_attr.isnot(None)
            ).scalar() or 0
            missing = total_vms - populated
            completeness = (populated / total_vms * 100) if total_vms > 0 else 0
            
            data.append([
                display_name,
                f'{populated:,}',
                f'{missing:,}',
                f'{completeness:.1f}%'
            ])
        
        table = Table(data, colWidths=[2*inch, 1.2*inch, 1.2*inch, 1.1*inch])
        table.setStyle(self._get_table_style())
        elements.append(table)
        
        # Add interpretation
        elements.append(Spacer(1, 0.2*inch))
        quality_text = """
        <b>Data Quality Summary:</b> This table shows the completeness of key fields in the inventory.
        High completeness (>90%) indicates good data quality, while low completeness may indicate
        missing VMware Tools, network issues, or incomplete vCenter configuration.
        """
        elements.append(Paragraph(quality_text, self.styles['Normal']))
        
        return elements
    
    def _get_table_style(self) -> TableStyle:
        """Get standard table style."""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e8b57')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ])
    
    def _create_extended_analytics_section(self) -> list:
        """Create extended analytics section with all charts from analytics page."""
        elements = []
        
        elements.append(Paragraph("Extended Analytics", self.heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Get VM data with resources
        vms = self.session.query(VirtualMachine).filter(
            VirtualMachine.cpus.isnot(None),
            VirtualMachine.memory.isnot(None)
        ).all()
        
        if vms:
            # CPU vs Memory Scatter
            elements.append(Paragraph("Resource Allocation Patterns", self.styles['Heading3']))
            elements.append(Spacer(1, 0.1*inch))
            
            df_vms = pd.DataFrame([{
                'CPUs': vm.cpus,
                'Memory_GB': vm.memory / 1024,
                'PowerState': vm.powerstate or 'Unknown'
            } for vm in vms if vm.cpus and vm.memory])
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
            
            # CPU vs Memory scatter
            powered_on = df_vms[df_vms['PowerState'] == 'poweredOn']
            powered_off = df_vms[df_vms['PowerState'] != 'poweredOn']
            
            ax1.scatter(powered_on['CPUs'], powered_on['Memory_GB'], 
                       alpha=0.6, s=50, c='#2ecc71', label='Powered On')
            ax1.scatter(powered_off['CPUs'], powered_off['Memory_GB'], 
                       alpha=0.6, s=50, c='#e74c3c', label='Powered Off')
            ax1.set_xlabel('vCPUs', fontsize=10)
            ax1.set_ylabel('Memory (GB)', fontsize=10)
            ax1.set_title('CPU vs Memory Allocation', fontsize=11, fontweight='bold')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Top 10 Resource Configurations
            df_vms['Config'] = df_vms['CPUs'].astype(str) + ' CPU / ' + df_vms['Memory_GB'].round(0).astype(int).astype(str) + ' GB'
            config_counts = df_vms['Config'].value_counts().head(10)
            
            bars = ax2.barh(range(len(config_counts)), config_counts.values, color='#17a2b8')
            ax2.set_yticks(range(len(config_counts)))
            ax2.set_yticklabels(config_counts.index, fontsize=8)
            ax2.set_xlabel('Count', fontsize=10)
            ax2.set_title('Top 10 Resource Configurations', fontsize=11, fontweight='bold')
            ax2.invert_yaxis()
            
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax2.text(width, bar.get_y() + bar.get_height()/2,
                        f' {int(width)}', va='center', fontsize=8)
            
            plt.tight_layout()
            elements.append(self._create_chart(fig, width=6.5*inch, height=3*inch))
            elements.append(Spacer(1, 0.3*inch))
        
        # OS Distribution Analysis
        elements.append(Paragraph("Operating System Distribution", self.styles['Heading3']))
        elements.append(Spacer(1, 0.1*inch))
        
        os_data = self.session.query(
            VirtualMachine.os_config,
            func.count(VirtualMachine.id).label('count'),
            func.sum(VirtualMachine.cpus).label('total_cpus')
        ).filter(
            VirtualMachine.os_config.isnot(None)
        ).group_by(VirtualMachine.os_config).order_by(
            func.count(VirtualMachine.id).desc()
        ).limit(10).all()
        
        if os_data:
            os_names = [str(os)[:30] for os, _, _ in os_data]
            os_counts = [count for _, count, _ in os_data]
            os_cpus = [int(cpus or 0) for _, _, cpus in os_data]
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
            
            # OS Distribution bar
            bars = ax1.barh(range(len(os_names)), os_counts, color='#6f42c1')
            ax1.set_yticks(range(len(os_names)))
            ax1.set_yticklabels(os_names, fontsize=7)
            ax1.set_xlabel('VM Count', fontsize=10)
            ax1.set_title('Top 10 Operating Systems', fontsize=11, fontweight='bold')
            ax1.invert_yaxis()
            
            for bar in bars:
                width = bar.get_width()
                ax1.text(width, bar.get_y() + bar.get_height()/2,
                        f' {int(width)}', va='center', fontsize=7)
            
            # CPU allocation by OS (pie chart)
            colors_pie = plt.cm.Spectral(np.linspace(0, 1, len(os_names)))
            wedges, texts, autotexts = ax2.pie(os_cpus, labels=None, autopct='%1.1f%%',
                                                colors=colors_pie, startangle=90)
            ax2.set_title('CPU Allocation by OS', fontsize=11, fontweight='bold')
            
            # Make percentage text smaller
            for autotext in autotexts:
                autotext.set_fontsize(7)
            
            plt.tight_layout()
            elements.append(self._create_chart(fig, width=6.5*inch, height=3*inch))
            elements.append(Spacer(1, 0.3*inch))
        
        # Cluster Efficiency Metrics
        elements.append(Paragraph("Cluster Efficiency Analysis", self.styles['Heading3']))
        elements.append(Spacer(1, 0.1*inch))
        
        cluster_data = self.session.query(
            VirtualMachine.cluster,
            func.count(VirtualMachine.id).label('vm_count'),
            func.count(func.distinct(VirtualMachine.host)).label('host_count'),
            func.sum(VirtualMachine.cpus).label('total_cpus'),
            func.sum(VirtualMachine.memory).label('total_memory')
        ).filter(
            VirtualMachine.cluster.isnot(None)
        ).group_by(VirtualMachine.cluster).all()
        
        if cluster_data:
            cluster_names = [str(c)[:20] for c, _, _, _, _ in cluster_data[:10]]
            vms_per_host = [(vm_count / host_count) if host_count > 0 else 0 
                           for _, vm_count, host_count, _, _ in cluster_data[:10]]
            cluster_cpus = [int(cpus or 0) for _, _, _, cpus, _ in cluster_data[:10]]
            cluster_mem = [(mem or 0) / 1024 for _, _, _, _, mem in cluster_data[:10]]
            cluster_vms = [vm_count for _, vm_count, _, _, _ in cluster_data[:10]]
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
            
            # VMs per Host by Cluster
            bars = ax1.bar(range(len(cluster_names)), vms_per_host, color='#fd7e14')
            ax1.set_xticks(range(len(cluster_names)))
            ax1.set_xticklabels(cluster_names, rotation=45, ha='right', fontsize=7)
            ax1.set_ylabel('VMs per Host', fontsize=10)
            ax1.set_title('Avg VMs per Host by Cluster', fontsize=11, fontweight='bold')
            
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2, height,
                        f'{height:.1f}', ha='center', va='bottom', fontsize=7)
            
            # Cluster Resource Bubble Chart
            scatter = ax2.scatter(cluster_cpus, cluster_mem, s=[v*5 for v in cluster_vms],
                                 alpha=0.6, c=range(len(cluster_names)), cmap='rainbow')
            ax2.set_xlabel('Total vCPUs', fontsize=10)
            ax2.set_ylabel('Total Memory (GB)', fontsize=10)
            ax2.set_title('Cluster Resource Distribution', fontsize=11, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            elements.append(self._create_chart(fig, width=6.5*inch, height=3*inch))
            elements.append(Spacer(1, 0.3*inch))
        
        # Environment Distribution
        env_data = self.session.query(
            VirtualMachine.env,
            func.count(VirtualMachine.id).label('count')
        ).filter(
            VirtualMachine.env.isnot(None)
        ).group_by(VirtualMachine.env).all()
        
        if env_data:
            elements.append(Paragraph("Environment Distribution", self.styles['Heading3']))
            elements.append(Spacer(1, 0.1*inch))
            
            env_names = [str(env) for env, _ in env_data]
            env_counts = [count for _, count in env_data]
            
            fig, ax = plt.subplots(figsize=(6, 4))
            colors_env = plt.cm.Pastel1(np.linspace(0, 1, len(env_names)))
            wedges, texts, autotexts = ax.pie(env_counts, labels=env_names, autopct='%1.1f%%',
                                               colors=colors_env, startangle=90)
            ax.set_title('VMs by Environment', fontsize=12, fontweight='bold')
            
            for text in texts:
                text.set_fontsize(9)
            for autotext in autotexts:
                autotext.set_fontsize(8)
                autotext.set_color('black')
            
            plt.tight_layout()
            elements.append(self._create_chart(fig, width=5*inch, height=3.5*inch))
        
        return elements
    
    def _create_extended_comparison_section(self) -> list:
        """Create extended comparison section with comparison charts."""
        elements = []
        
        elements.append(Paragraph("Infrastructure Comparison", self.heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Datacenter Comparison
        dc_data = self.session.query(
            VirtualMachine.datacenter,
            func.count(VirtualMachine.id).label('total_vms'),
            func.sum(case((VirtualMachine.powerstate == 'poweredOn', 1), else_=0)).label('powered_on'),
            func.sum(VirtualMachine.cpus).label('total_cpus'),
            func.sum(VirtualMachine.memory).label('total_memory')
        ).filter(
            VirtualMachine.datacenter.isnot(None)
        ).group_by(VirtualMachine.datacenter).all()
        
        if dc_data and len(dc_data) > 1:
            elements.append(Paragraph("Datacenter Comparison", self.styles['Heading3']))
            elements.append(Spacer(1, 0.1*inch))
            
            dc_names = [str(dc)[:20] for dc, _, _, _, _ in dc_data[:5]]
            total_vms = [vm_count for _, vm_count, _, _, _ in dc_data[:5]]
            powered_on = [po for _, _, po, _, _ in dc_data[:5]]
            dc_cpus = [int(cpus or 0) for _, _, _, cpus, _ in dc_data[:5]]
            dc_mem = [(mem or 0) / 1024 for _, _, _, _, mem in dc_data[:5]]
            
            fig = plt.figure(figsize=(10, 6))
            gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
            
            # VM Count Comparison
            ax1 = fig.add_subplot(gs[0, 0])
            bars = ax1.bar(dc_names, total_vms, color='#3498db')
            ax1.set_ylabel('VM Count', fontsize=9)
            ax1.set_title('VM Count by Datacenter', fontsize=10, fontweight='bold')
            ax1.tick_params(axis='x', rotation=45, labelsize=7)
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2, height,
                        f'{int(height)}', ha='center', va='bottom', fontsize=7)
            
            # Power State Comparison
            ax2 = fig.add_subplot(gs[0, 1])
            x = np.arange(len(dc_names))
            width = 0.35
            ax2.bar(x - width/2, total_vms, width, label='Total', color='lightblue')
            ax2.bar(x + width/2, powered_on, width, label='Powered On', color='lightgreen')
            ax2.set_ylabel('VM Count', fontsize=9)
            ax2.set_title('Power State Distribution', fontsize=10, fontweight='bold')
            ax2.set_xticks(x)
            ax2.set_xticklabels(dc_names, rotation=45, ha='right', fontsize=7)
            ax2.legend(fontsize=8)
            
            # Resource Comparison (grouped bar)
            ax3 = fig.add_subplot(gs[1, :])
            x = np.arange(len(dc_names))
            width = 0.25
            ax3.bar(x - width, total_vms, width, label='VMs', color='#3498db')
            # Normalize CPUs and Memory for visibility
            max_resource = max(max(dc_cpus), max(dc_mem))
            norm_cpus = [c / max_resource * max(total_vms) for c in dc_cpus]
            norm_mem = [m / max_resource * max(total_vms) for m in dc_mem]
            ax3.bar(x, norm_cpus, width, label='vCPUs (norm)', color='#e67e22')
            ax3.bar(x + width, norm_mem, width, label='Memory (norm)', color='#9b59b6')
            ax3.set_ylabel('Normalized Values', fontsize=9)
            ax3.set_title('Resource Comparison (Normalized)', fontsize=10, fontweight='bold')
            ax3.set_xticks(x)
            ax3.set_xticklabels(dc_names, rotation=45, ha='right', fontsize=7)
            ax3.legend(fontsize=8)
            
            elements.append(self._create_chart(fig, width=6.5*inch, height=4.5*inch))
            elements.append(Spacer(1, 0.3*inch))
        
        # Cluster Comparison
        cluster_data = self.session.query(
            VirtualMachine.cluster,
            func.count(VirtualMachine.id).label('total_vms'),
            func.sum(case((VirtualMachine.powerstate == 'poweredOn', 1), else_=0)).label('powered_on'),
            func.sum(VirtualMachine.cpus).label('total_cpus'),
            func.sum(VirtualMachine.memory).label('total_memory')
        ).filter(
            VirtualMachine.cluster.isnot(None)
        ).group_by(VirtualMachine.cluster).all()
        
        if cluster_data and len(cluster_data) > 1:
            elements.append(Paragraph("Top Clusters Comparison", self.styles['Heading3']))
            elements.append(Spacer(1, 0.1*inch))
            
            # Sort and take top 6
            sorted_clusters = sorted(cluster_data, key=lambda x: x[1], reverse=True)[:6]
            
            cluster_names = [str(c)[:15] for c, _, _, _, _ in sorted_clusters]
            cluster_vms = [vm_count for _, vm_count, _, _, _ in sorted_clusters]
            cluster_po = [po for _, _, po, _, _ in sorted_clusters]
            cluster_cpus = [int(cpus or 0) for _, _, _, cpus, _ in sorted_clusters]
            cluster_mem = [(mem or 0) / 1024 for _, _, _, _, mem in sorted_clusters]
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
            
            # VM Distribution
            x = np.arange(len(cluster_names))
            width = 0.35
            ax1.bar(x - width/2, cluster_vms, width, label='Total VMs', color='#3498db')
            ax1.bar(x + width/2, cluster_po, width, label='Powered On', color='#2ecc71')
            ax1.set_ylabel('VM Count', fontsize=9)
            ax1.set_title('Cluster VM Distribution', fontsize=10, fontweight='bold')
            ax1.set_xticks(x)
            ax1.set_xticklabels(cluster_names, rotation=45, ha='right', fontsize=7)
            ax1.legend(fontsize=8)
            
            # Resource Allocation Scatter
            scatter = ax2.scatter(cluster_cpus, cluster_mem, s=[v*10 for v in cluster_vms],
                                 alpha=0.6, c=range(len(cluster_names)), cmap='viridis')
            ax2.set_xlabel('Total vCPUs', fontsize=9)
            ax2.set_ylabel('Total Memory (GB)', fontsize=9)
            ax2.set_title('Resource Allocation Profile', fontsize=10, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            elements.append(self._create_chart(fig, width=6.5*inch, height=3*inch))
        
        return elements
    
    def _create_extended_folder_analytics_section(self) -> list:
        """Create extended folder analytics with all folder charts."""
        elements = []
        
        elements.append(Paragraph("Extended Folder Analytics", self.heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Get comprehensive folder stats
        folder_stats = self.session.query(
            VirtualMachine.folder,
            func.count(VirtualMachine.id).label('vm_count'),
            func.sum(VirtualMachine.cpus).label('total_cpus'),
            func.sum(VirtualMachine.memory).label('total_memory'),
            func.sum(VirtualMachine.provisioned_mib).label('total_provisioned'),
            func.sum(VirtualMachine.in_use_mib).label('total_in_use')
        ).filter(
            VirtualMachine.folder.isnot(None)
        ).group_by(VirtualMachine.folder).all()
        
        if folder_stats and len(folder_stats) > 1:
            # Create dataframe
            df_folders = pd.DataFrame(folder_stats, columns=[
                'Folder', 'VMs', 'Total_CPUs', 'Total_Memory_MB',
                'Total_Provisioned_MiB', 'Total_In_Use_MiB'
            ])
            df_folders['Total_Memory_GB'] = (df_folders['Total_Memory_MB'] / 1024).round(1)
            df_folders['Total_Provisioned_GB'] = (df_folders['Total_Provisioned_MiB'] / 1024).round(1)
            df_folders['Total_In_Use_GB'] = (df_folders['Total_In_Use_MiB'] / 1024).round(1)
            df_folders['Avg_CPUs'] = (df_folders['Total_CPUs'] / df_folders['VMs']).round(1)
            df_folders['Avg_Memory_GB'] = (df_folders['Total_Memory_GB'] / df_folders['VMs']).round(1)
            df_folders['Avg_Provisioned_GB'] = (df_folders['Total_Provisioned_GB'] / df_folders['VMs']).round(1)
            df_folders = df_folders.fillna(0)
            df_folders = df_folders.sort_values('VMs', ascending=False)
            
            # Folder Size Distribution (histogram)
            elements.append(Paragraph("Folder Distribution Patterns", self.styles['Heading3']))
            elements.append(Spacer(1, 0.1*inch))
            
            fig, ax = plt.subplots(figsize=(7, 3.5))
            ax.hist(df_folders['VMs'], bins=min(20, len(df_folders)//2), color='#3498db', edgecolor='black')
            ax.set_xlabel('Number of VMs', fontsize=10)
            ax.set_ylabel('Number of Folders', fontsize=10)
            ax.set_title('Folder Size Distribution', fontsize=11, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            plt.tight_layout()
            elements.append(self._create_chart(fig, width=6*inch, height=3*inch))
            elements.append(Spacer(1, 0.3*inch))
            
            # Resource Allocation by Top Folders
            elements.append(Paragraph("Top Folders - Resource Allocation", self.styles['Heading3']))
            elements.append(Spacer(1, 0.1*inch))
            
            df_top = df_folders.head(10)
            folder_names = [str(f)[:20] for f in df_top['Folder']]
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
            
            # Grouped bar for resources
            x = np.arange(len(folder_names))
            width = 0.35
            ax1.bar(x - width/2, df_top['Total_CPUs'], width, label='vCPUs', color='lightblue')
            ax1.bar(x + width/2, df_top['Total_Memory_GB'], width, label='Memory (GB)', color='lightcoral')
            ax1.set_ylabel('Resources', fontsize=9)
            ax1.set_title('Resource Allocation', fontsize=10, fontweight='bold')
            ax1.set_xticks(x)
            ax1.set_xticklabels(folder_names, rotation=45, ha='right', fontsize=6)
            ax1.legend(fontsize=8)
            
            # Avg Resource Profile Scatter
            scatter = ax2.scatter(df_top['Avg_CPUs'], df_top['Avg_Memory_GB'],
                                 s=df_top['VMs']*5, alpha=0.6,
                                 c=range(len(df_top)), cmap='viridis')
            ax2.set_xlabel('Avg vCPUs per VM', fontsize=9)
            ax2.set_ylabel('Avg Memory (GB) per VM', fontsize=9)
            ax2.set_title('Avg Resource Profile', fontsize=10, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            elements.append(self._create_chart(fig, width=6.5*inch, height=3*inch))
            elements.append(Spacer(1, 0.3*inch))
            
            # Storage Analysis
            elements.append(Paragraph("Folder Storage Analysis", self.styles['Heading3']))
            elements.append(Spacer(1, 0.1*inch))
            
            df_top_storage = df_folders.head(10)
            folder_names_storage = [str(f)[:20] for f in df_top_storage['Folder']]
            
            fig = plt.figure(figsize=(10, 7))
            gs = fig.add_gridspec(3, 2, hspace=0.4, wspace=0.3)
            
            # Provisioned Storage (horizontal bar)
            ax1 = fig.add_subplot(gs[0, :])
            bars = ax1.barh(range(len(folder_names_storage)), df_top_storage['Total_Provisioned_GB'],
                           color='#fd7e14')
            ax1.set_yticks(range(len(folder_names_storage)))
            ax1.set_yticklabels(folder_names_storage, fontsize=7)
            ax1.set_xlabel('Provisioned Storage (GB)', fontsize=9)
            ax1.set_title('Top 10 Folders by Provisioned Storage', fontsize=10, fontweight='bold')
            ax1.invert_yaxis()
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax1.text(width, bar.get_y() + bar.get_height()/2,
                        f' {width:.0f} GB', va='center', fontsize=6)
            
            # Storage Utilization (grouped bar)
            ax2 = fig.add_subplot(gs[1, :])
            x = np.arange(len(folder_names_storage))
            width = 0.35
            ax2.bar(x - width/2, df_top_storage['Total_Provisioned_GB'], width,
                   label='Provisioned', color='lightsalmon')
            ax2.bar(x + width/2, df_top_storage['Total_In_Use_GB'], width,
                   label='In Use', color='lightseagreen')
            ax2.set_ylabel('Storage (GB)', fontsize=9)
            ax2.set_title('Storage Utilization Comparison', fontsize=10, fontweight='bold')
            ax2.set_xticks(x)
            ax2.set_xticklabels(folder_names_storage, rotation=45, ha='right', fontsize=6)
            ax2.legend(fontsize=8)
            
            # Storage Efficiency Scatter
            ax3 = fig.add_subplot(gs[2, 0])
            df_eff = df_top_storage.copy()
            df_eff['Efficiency'] = (df_eff['Total_In_Use_GB'] / df_eff['Total_Provisioned_GB'] * 100).fillna(0)
            scatter = ax3.scatter(df_eff['Total_Provisioned_GB'], df_eff['Efficiency'],
                                 s=df_eff['VMs']*5, alpha=0.6,
                                 c=range(len(df_eff)), cmap='viridis')
            ax3.axhline(y=100, linestyle='--', color='red', alpha=0.5, linewidth=1)
            ax3.set_xlabel('Provisioned Storage (GB)', fontsize=8)
            ax3.set_ylabel('Efficiency (%)', fontsize=8)
            ax3.set_title('Storage Efficiency', fontsize=9, fontweight='bold')
            ax3.grid(True, alpha=0.3)
            
            # Avg Provisioned per VM
            ax4 = fig.add_subplot(gs[2, 1])
            bars = ax4.barh(range(len(folder_names_storage)), df_top_storage['Avg_Provisioned_GB'],
                           color='#6f42c1')
            ax4.set_yticks(range(len(folder_names_storage)))
            ax4.set_yticklabels(folder_names_storage, fontsize=7)
            ax4.set_xlabel('Avg Storage per VM (GB)', fontsize=8)
            ax4.set_title('Avg Provisioned per VM', fontsize=9, fontweight='bold')
            ax4.invert_yaxis()
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax4.text(width, bar.get_y() + bar.get_height()/2,
                        f' {width:.1f}', va='center', fontsize=6)
            
            elements.append(self._create_chart(fig, width=6.5*inch, height=5*inch))
        
        return elements
    
    def close(self):
        """Close database session."""
        self.session.close()

"""
Document Generation Agent

This agent handles generation of various documents including:
- PDF invoices and receipts
- Shipping labels (PDF, PNG, ZPL formats)
- Packing slips
- Return labels
- Custom reports
- Product catalogs
- Marketing materials

The agent integrates with:
- Workflow system for automated document generation
- Order management for invoices and packing slips
- Shipping system for labels
- Return/RMA system for return labels
- Notification system for document delivery

Technologies:
- ReportLab for PDF generation
- Pillow for image manipulation
- Jinja2 for template rendering
- Kafka for inter-agent communication
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from io import BytesIO

from shared.db_helpers import DatabaseHelper
import base64

# PDF generation
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

# Image processing
from PIL import Image, ImageDraw, ImageFont

# Template engine
from jinja2 import Template

# Database
import psycopg2
from psycopg2.extras import RealDictCursor

# Kafka for inter-agent communication
from kafka import KafkaProducer, KafkaConsumer

# Configuration
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'ecommerce'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

KAFKA_CONFIG = {
    'bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
    'document_topic': 'document_generation_requests',
    'response_topic': 'document_generation_responses'
}

STORAGE_PATH = os.getenv('DOCUMENT_STORAGE_PATH', '/app/storage/documents')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocumentGenerationAgent:
    """Main agent class for document generation"""
    
    def __init__(self):
        self.db_conn = None
        self.kafka_producer = None
        self.kafka_consumer = None
        self.templates = {}
        self.initialize()
    
    def initialize(self):
        """Initialize database and Kafka connections"""
        try:
            # Database connection
            self.db_conn = psycopg2.connect(**DATABASE_CONFIG)
            logger.info("Connected to database")
            
            # Kafka producer
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=KAFKA_CONFIG['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logger.info("Kafka producer initialized")
            
            # Kafka consumer
            self.kafka_consumer = KafkaConsumer(
                KAFKA_CONFIG['document_topic'],
                bootstrap_servers=KAFKA_CONFIG['bootstrap_servers'],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id='document_generation_agent',
                auto_offset_reset='latest'
            )
            logger.info("Kafka consumer initialized")
            
            # Ensure storage directory exists
            os.makedirs(STORAGE_PATH, exist_ok=True)
            
            # Load document templates
            self.load_templates()
            
        except Exception as e:
            logger.error(f"Initialization error: {str(e)}")
            raise
    
    def load_templates(self):
        """Load document templates from database"""
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, name, type, template_content, metadata
                    FROM document_templates
                    WHERE enabled = true
                """)
                templates = cursor.fetchall()
                
                for template in templates:
                    self.templates[template['name']] = template
                
                logger.info(f"Loaded {len(self.templates)} document templates")
        except Exception as e:
            logger.error(f"Error loading templates: {str(e)}")
    
    def generate_invoice(self, order_id: int, format: str = 'PDF') -> Dict[str, Any]:
        """Generate invoice for an order"""
        try:
            # Fetch order data
            order_data = self.fetch_order_data(order_id)
            
            if not order_data:
                raise ValueError(f"Order {order_id} not found")
            
            # Generate PDF
            if format.upper() == 'PDF':
                file_path = self.generate_invoice_pdf(order_data)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # Save to database
            doc_id = self.save_document_record(
                document_type='invoice',
                related_id=order_id,
                related_type='order',
                file_path=file_path,
                format=format
            )
            
            logger.info(f"Generated invoice for order {order_id}: {file_path}")
            
            return {
                'success': True,
                'document_id': doc_id,
                'file_path': file_path,
                'order_id': order_id
            }
            
        except Exception as e:
            logger.error(f"Error generating invoice: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_invoice_pdf(self, order_data: Dict) -> str:
        """Generate invoice PDF using ReportLab"""
        filename = f"invoice_{order_data['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        file_path = os.path.join(STORAGE_PATH, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        story.append(Paragraph("INVOICE", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Company info and invoice details
        company_info = [
            ['Company Name', f"Invoice #: {order_data['id']}"],
            ['123 Business Street', f"Date: {order_data['created_at']}"],
            ['City, State 12345', f"Order #: {order_data['order_number']}"],
            ['contact@company.com', '']
        ]
        
        info_table = Table(company_info, colWidths=[3*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Customer info
        story.append(Paragraph("<b>Bill To:</b>", styles['Normal']))
        customer_info = [
            [order_data.get('customer_name', 'N/A')],
            [order_data.get('billing_address', 'N/A')],
            [order_data.get('customer_email', 'N/A')]
        ]
        customer_table = Table(customer_info, colWidths=[6*inch])
        customer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(customer_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Items table
        items_data = [['Item', 'Quantity', 'Unit Price', 'Total']]
        for item in order_data.get('items', []):
            items_data.append([
                item.get('product_name', 'N/A'),
                str(item.get('quantity', 0)),
                f"${item.get('unit_price', 0):.2f}",
                f"${item.get('total_price', 0):.2f}"
            ])
        
        items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Totals
        totals_data = [
            ['Subtotal:', f"${order_data.get('subtotal', 0):.2f}"],
            ['Tax:', f"${order_data.get('tax', 0):.2f}"],
            ['Shipping:', f"${order_data.get('shipping', 0):.2f}"],
            ['Total:', f"${order_data.get('total', 0):.2f}"]
        ]
        
        totals_table = Table(totals_data, colWidths=[5*inch, 1.5*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ]))
        story.append(totals_table)
        
        # Build PDF
        doc.build(story)
        
        return file_path
    
    def generate_shipping_label(self, shipment_id: int, format: str = 'PDF') -> Dict[str, Any]:
        """Generate shipping label"""
        try:
            # Fetch shipment data
            shipment_data = self.fetch_shipment_data(shipment_id)
            
            if not shipment_data:
                raise ValueError(f"Shipment {shipment_id} not found")
            
            # Generate label based on format
            if format.upper() == 'PDF':
                file_path = self.generate_shipping_label_pdf(shipment_data)
            elif format.upper() == 'PNG':
                file_path = self.generate_shipping_label_image(shipment_data)
            elif format.upper() == 'ZPL':
                file_path = self.generate_shipping_label_zpl(shipment_data)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # Save to database
            doc_id = self.save_document_record(
                document_type='shipping_label',
                related_id=shipment_id,
                related_type='shipment',
                file_path=file_path,
                format=format
            )
            
            logger.info(f"Generated shipping label for shipment {shipment_id}: {file_path}")
            
            return {
                'success': True,
                'document_id': doc_id,
                'file_path': file_path,
                'shipment_id': shipment_id
            }
            
        except Exception as e:
            logger.error(f"Error generating shipping label: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_shipping_label_pdf(self, shipment_data: Dict) -> str:
        """Generate shipping label PDF"""
        filename = f"label_{shipment_data['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        file_path = os.path.join(STORAGE_PATH, filename)
        
        # Create PDF (4x6 label size)
        doc = SimpleDocTemplate(file_path, pagesize=(4*inch, 6*inch))
        story = []
        styles = getSampleStyleSheet()
        
        # Carrier logo placeholder
        story.append(Paragraph(f"<b>{shipment_data.get('carrier', 'CARRIER')}</b>", styles['Title']))
        story.append(Spacer(1, 0.2*inch))
        
        # Tracking number
        tracking_style = ParagraphStyle(
            'Tracking',
            parent=styles['Normal'],
            fontSize=14,
            alignment=TA_CENTER
        )
        story.append(Paragraph(f"Tracking: <b>{shipment_data.get('tracking_number', 'N/A')}</b>", tracking_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Ship To
        story.append(Paragraph("<b>SHIP TO:</b>", styles['Heading2']))
        ship_to = [
            [shipment_data.get('recipient_name', 'N/A')],
            [shipment_data.get('address_line1', 'N/A')],
            [f"{shipment_data.get('city', 'N/A')}, {shipment_data.get('state', 'N/A')} {shipment_data.get('zip', 'N/A')}"],
            [shipment_data.get('country', 'N/A')]
        ]
        ship_to_table = Table(ship_to, colWidths=[3.5*inch])
        story.append(ship_to_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Ship From
        story.append(Paragraph("<b>SHIP FROM:</b>", styles['Heading2']))
        ship_from = [
            [shipment_data.get('sender_name', 'Warehouse')],
            [shipment_data.get('sender_address', 'N/A')]
        ]
        ship_from_table = Table(ship_from, colWidths=[3.5*inch])
        story.append(ship_from_table)
        
        doc.build(story)
        return file_path
    
    def generate_shipping_label_image(self, shipment_data: Dict) -> str:
        """Generate shipping label as PNG image"""
        filename = f"label_{shipment_data['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        file_path = os.path.join(STORAGE_PATH, filename)
        
        # Create image (4x6 inches at 300 DPI)
        img = Image.new('RGB', (1200, 1800), color='white')
        draw = ImageDraw.Draw(img)
        
        # Use default font (in production, load custom fonts)
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Draw carrier name
        draw.text((50, 50), shipment_data.get('carrier', 'CARRIER'), fill='black', font=font_large)
        
        # Draw tracking number
        draw.text((50, 150), f"Tracking: {shipment_data.get('tracking_number', 'N/A')}", fill='black', font=font_medium)
        
        # Draw ship to address
        y_pos = 300
        draw.text((50, y_pos), "SHIP TO:", fill='black', font=font_medium)
        y_pos += 50
        draw.text((50, y_pos), shipment_data.get('recipient_name', 'N/A'), fill='black', font=font_small)
        y_pos += 40
        draw.text((50, y_pos), shipment_data.get('address_line1', 'N/A'), fill='black', font=font_small)
        y_pos += 40
        draw.text((50, y_pos), f"{shipment_data.get('city', 'N/A')}, {shipment_data.get('state', 'N/A')} {shipment_data.get('zip', 'N/A')}", fill='black', font=font_small)
        
        img.save(file_path)
        return file_path
    
    def generate_shipping_label_zpl(self, shipment_data: Dict) -> str:
        """Generate shipping label in ZPL format (for Zebra printers)"""
        filename = f"label_{shipment_data['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.zpl"
        file_path = os.path.join(STORAGE_PATH, filename)
        
        # Generate ZPL code
        zpl_code = f"""^XA
^FO50,50^A0N,50,50^FD{shipment_data.get('carrier', 'CARRIER')}^FS
^FO50,150^A0N,30,30^FDTracking: {shipment_data.get('tracking_number', 'N/A')}^FS
^FO50,250^A0N,40,40^FDSHIP TO:^FS
^FO50,300^A0N,30,30^FD{shipment_data.get('recipient_name', 'N/A')}^FS
^FO50,340^A0N,25,25^FD{shipment_data.get('address_line1', 'N/A')}^FS
^FO50,380^A0N,25,25^FD{shipment_data.get('city', 'N/A')}, {shipment_data.get('state', 'N/A')} {shipment_data.get('zip', 'N/A')}^FS
^XZ"""
        
        with open(file_path, 'w') as f:
            f.write(zpl_code)
        
        return file_path
    
    def generate_packing_slip(self, order_id: int) -> Dict[str, Any]:
        """Generate packing slip for an order"""
        try:
            order_data = self.fetch_order_data(order_id)
            
            if not order_data:
                raise ValueError(f"Order {order_id} not found")
            
            file_path = self.generate_packing_slip_pdf(order_data)
            
            doc_id = self.save_document_record(
                document_type='packing_slip',
                related_id=order_id,
                related_type='order',
                file_path=file_path,
                format='PDF'
            )
            
            logger.info(f"Generated packing slip for order {order_id}: {file_path}")
            
            return {
                'success': True,
                'document_id': doc_id,
                'file_path': file_path,
                'order_id': order_id
            }
            
        except Exception as e:
            logger.error(f"Error generating packing slip: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_packing_slip_pdf(self, order_data: Dict) -> str:
        """Generate packing slip PDF"""
        filename = f"packing_slip_{order_data['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        file_path = os.path.join(STORAGE_PATH, filename)
        
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        story.append(Paragraph("PACKING SLIP", styles['Title']))
        story.append(Spacer(1, 0.3*inch))
        
        # Order info
        order_info = [
            [f"Order #: {order_data.get('order_number', 'N/A')}"],
            [f"Date: {order_data.get('created_at', 'N/A')}"]
        ]
        order_table = Table(order_info)
        story.append(order_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Ship to
        story.append(Paragraph("<b>Ship To:</b>", styles['Heading2']))
        ship_to = [
            [order_data.get('customer_name', 'N/A')],
            [order_data.get('shipping_address', 'N/A')]
        ]
        ship_to_table = Table(ship_to)
        story.append(ship_to_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Items
        items_data = [['SKU', 'Product', 'Quantity']]
        for item in order_data.get('items', []):
            items_data.append([
                item.get('sku', 'N/A'),
                item.get('product_name', 'N/A'),
                str(item.get('quantity', 0))
            ])
        
        items_table = Table(items_data, colWidths=[1.5*inch, 4*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(items_table)
        
        doc.build(story)
        return file_path
    
    def fetch_order_data(self, order_id: int) -> Optional[Dict]:
        """Fetch order data from database"""
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT o.*, c.name as customer_name, c.email as customer_email
                    FROM orders o
                    LEFT JOIN customers c ON o.customer_id = c.id
                    WHERE o.id = %s
                """, (order_id,))
                order = cursor.fetchone()
                
                if order:
                    # Fetch order items
                    cursor.execute("""
                        SELECT * FROM order_items WHERE order_id = %s
                    """, (order_id,))
                    order['items'] = cursor.fetchall()
                
                return dict(order) if order else None
        except Exception as e:
            logger.error(f"Error fetching order data: {str(e)}")
            return None
    
    def fetch_shipment_data(self, shipment_id: int) -> Optional[Dict]:
        """Fetch shipment data from database"""
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM shipments WHERE id = %s
                """, (shipment_id,))
                shipment = cursor.fetchone()
                return dict(shipment) if shipment else None
        except Exception as e:
            logger.error(f"Error fetching shipment data: {str(e)}")
            return None
    
    def save_document_record(self, document_type: str, related_id: int, 
                           related_type: str, file_path: str, format: str) -> int:
        """Save document record to database"""
        try:
            with self.db_conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO generated_documents 
                    (document_type, related_id, related_type, file_path, format, generated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (document_type, related_id, related_type, file_path, format, datetime.now()))
                doc_id = cursor.fetchone()[0]
                self.db_conn.commit()
                return doc_id
        except Exception as e:
            logger.error(f"Error saving document record: {str(e)}")
            self.db_conn.rollback()
            return None
    
    def process_kafka_message(self, message: Dict):
        """Process incoming Kafka message"""
        try:
            request_type = message.get('type')
            request_id = message.get('request_id')
            
            logger.info(f"Processing request {request_id}: {request_type}")
            
            result = None
            
            if request_type == 'generate_invoice':
                result = self.generate_invoice(message.get('order_id'), message.get('format', 'PDF'))
            elif request_type == 'generate_shipping_label':
                result = self.generate_shipping_label(message.get('shipment_id'), message.get('format', 'PDF'))
            elif request_type == 'generate_packing_slip':
                result = self.generate_packing_slip(message.get('order_id'))
            else:
                result = {'success': False, 'error': f'Unknown request type: {request_type}'}
            
            # Send response
            response = {
                'request_id': request_id,
                'type': request_type,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
            self.kafka_producer.send(KAFKA_CONFIG['response_topic'], response)
            logger.info(f"Sent response for request {request_id}")
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
    
    def run(self):
        """Main agent loop"""
        logger.info("Document Generation Agent started")
        
        try:
            for message in self.kafka_consumer:
                self.process_kafka_message(message.value)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        if self.db_conn:
            self.db_conn.close()
        if self.kafka_producer:
            self.kafka_producer.close()
        if self.kafka_consumer:
            self.kafka_consumer.close()
        logger.info("Document Generation Agent stopped")


if __name__ == '__main__':
    agent = DocumentGenerationAgent()
    agent.run()


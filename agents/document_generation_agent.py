
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
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio

from shared.db_helpers import DatabaseHelper
from shared.base_agent_v2 import BaseAgentV2
from shared.models import AgentMessage, MessageType
from shared.cors_middleware import add_cors_middleware
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

# Configuration
# Use environment variables for configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@localhost:5432/ecommerce')
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_DOCUMENT_TOPIC = os.getenv('KAFKA_DOCUMENT_TOPIC', 'document_generation_requests')
KAFKA_RESPONSE_TOPIC = os.getenv('KAFKA_RESPONSE_TOPIC', 'document_generation_responses')
STORAGE_PATH = os.getenv('DOCUMENT_STORAGE_PATH', '/app/storage/documents')
AGENT_ID = os.getenv('AGENT_ID', 'document_generation_agent_001')
AGENT_TYPE = os.getenv('AGENT_TYPE', 'document_generation')
API_PORT = int(os.getenv('API_PORT', 8013))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocumentGenerationAgent(BaseAgentV2):
    """
    Main agent class for document generation.

    This agent is responsible for generating various types of documents such as invoices, 
    shipping labels, packing slips, and custom reports. It integrates with a database 
    for data retrieval and Kafka for inter-agent communication.
    """
    
    def __init__(self):
        """
        Initializes the DocumentGenerationAgent.
        """
        super().__init__(agent_id="document_generation_agent")
        
        # FastAPI app for REST API
        self.app = FastAPI(title="Document Generation Agent API")
        
        # Add CORS middleware for dashboard integration
        add_cors_middleware(self.app)
        self.db_helper = DatabaseHelper(self.db_manager)
        self.templates = {}
        self._db_initialized = False

    async def initialize_agent(self):
        """
        Initializes database and Kafka connections, and loads document templates.
        This method is called during agent instantiation.
        """
        try:
            self._db_initialized = True
            logger.info("Database connection initialized.")
            
            # Ensure storage directory exists
            os.makedirs(STORAGE_PATH, exist_ok=True)
            
            # Load document templates
            await self.load_templates()
            logger.info("DocumentGenerationAgent initialized successfully.")
            
        except Exception as e:
            logger.error(f"Initialization error: {e}", exc_info=True)
            raise

    async def load_templates(self):
        """
        Loads document templates from the database into memory.
        Templates are stored in the `document_templates` table.
        """
        if not self._db_initialized: return []
        try:
            async with self.db_manager.get_async_session() as session:
                # Query document templates from database
                from sqlalchemy import select, text
                result = await session.execute(text("SELECT * FROM document_templates WHERE enabled = true"))
                templates_data = [dict(row._mapping) for row in result.fetchall()]
                for template in templates_data:
                    if template.get('enabled'):
                        self.templates[template['name']] = template
                logger.info(f"Loaded {len(self.templates)} document templates.")
        except Exception as e:
            logger.error(f"Error loading templates: {e}", exc_info=True)

    async def generate_invoice(self, order_id: int, format: str = 'PDF') -> Dict[str, Any]:
        """
        Generates an invoice for a given order.

        Args:
            order_id (int): The ID of the order for which to generate the invoice.
            format (str): The desired output format (e.g., 'PDF'). Defaults to 'PDF'.

        Returns:
            Dict[str, Any]: A dictionary containing the generation result, including success status, 
                           document ID, file path, and order ID, or an error message.
        """
        if not self._db_initialized: return {'success': False, 'error': 'Database not initialized'}
        try:
            order_data = await self.fetch_order_data(order_id)
            
            if not order_data:
                raise ValueError(f"Order {order_id} not found.")
            
            file_path = None
            if format.upper() == 'PDF':
                file_path = await self.generate_invoice_pdf(order_data)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            doc_id = await self.save_document_record(
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
            logger.error(f"Error generating invoice for order {order_id}: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    async def generate_invoice_pdf(self, order_data: Dict) -> str:
        """
        Generates an invoice in PDF format using ReportLab.

        Args:
            order_data (Dict): A dictionary containing all necessary order details.

        Returns:
            str: The file path to the generated PDF invoice.
        """
        try:
            filename = f"invoice_{order_data['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            file_path = os.path.join(STORAGE_PATH, filename)
            
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
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
            
            company_info = [
                ['Company Name', f"Invoice #: {order_data['id']}"],
                ['123 Business Street', f"Date: {order_data.get('created_at', datetime.now()).strftime('%Y-%m-%d')}"],
                ['City, State 12345', f"Order #: {order_data.get('order_number', 'N/A')}"],
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
            
            doc.build(story)
            return file_path
        except Exception as e:
            logger.error(f"Error generating invoice PDF for order {order_data.get('id', 'N/A')}: {e}", exc_info=True)
            raise

    async def generate_shipping_label(self, shipment_id: int, format: str = 'PDF') -> Dict[str, Any]:
        """
        Generates a shipping label for a given shipment.

        Args:
            shipment_id (int): The ID of the shipment for which to generate the label.
            format (str): The desired output format (e.g., 'PDF', 'PNG', 'ZPL'). Defaults to 'PDF'.

        Returns:
            Dict[str, Any]: A dictionary containing the generation result, including success status, 
                           document ID, file path, and shipment ID, or an error message.
        """
        if not self._db_initialized: return {'success': False, 'error': 'Database not initialized'}
        try:
            shipment_data = await self.fetch_shipment_data(shipment_id)
            
            if not shipment_data:
                raise ValueError(f"Shipment {shipment_id} not found.")
            
            file_path = None
            if format.upper() == 'PDF':
                file_path = await self.generate_shipping_label_pdf(shipment_data)
            elif format.upper() == 'PNG':
                file_path = await self.generate_shipping_label_image(shipment_data, 'PNG')
            elif format.upper() == 'ZPL':
                file_path = await self.generate_shipping_label_zpl(shipment_data)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            doc_id = await self.save_document_record(
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
            logger.error(f"Error generating shipping label for shipment {shipment_id}: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    async def generate_shipping_label_pdf(self, shipment_data: Dict) -> str:
        """
        Generates a shipping label in PDF format using ReportLab.

        Args:
            shipment_data (Dict): A dictionary containing all necessary shipment details.

        Returns:
            str: The file path to the generated PDF shipping label.
        """
        try:
            filename = f"shipping_label_{shipment_data['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            file_path = os.path.join(STORAGE_PATH, filename)

            doc = SimpleDocTemplate(file_path, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()

            story.append(Paragraph("<b>Shipping Label</b>", styles['h2']))
            story.append(Spacer(1, 0.2*inch))

            # Barcode (placeholder)
            story.append(Paragraph(f"Tracking Number: <b>{shipment_data.get('tracking_number', 'N/A')}</b>", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph("<i>[BARCODE IMAGE HERE]</i>", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))

            # From/To Addresses
            story.append(Paragraph("<b>From:</b>", styles['Normal']))
            from_address = [
                [shipment_data.get('sender_name', 'N/A')],
                [shipment_data.get('sender_address', 'N/A')]
            ]
            from_table = Table(from_address)
            story.append(from_table)
            story.append(Spacer(1, 0.2*inch))

            story.append(Paragraph("<b>To:</b>", styles['Normal']))
            to_address = [
                [shipment_data.get('recipient_name', 'N/A')],
                [shipment_data.get('recipient_address', 'N/A')]
            ]
            to_table = Table(to_address)
            story.append(to_table)
            story.append(Spacer(1, 0.3*inch))

            doc.build(story)
            return file_path
        except Exception as e:
            logger.error(f"Error generating shipping label PDF for shipment {shipment_data.get('id', 'N/A')}: {e}", exc_info=True)
            raise

    async def generate_shipping_label_image(self, shipment_data: Dict, image_format: str = 'PNG') -> str:
        """
        Generates a shipping label as an image (PNG) using Pillow.

        Args:
            shipment_data (Dict): A dictionary containing all necessary shipment details.
            image_format (str): The desired image format (e.g., 'PNG').

        Returns:
            str: The file path to the generated image shipping label.
        """
        try:
            filename = f"shipping_label_{shipment_data['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{image_format.lower()}"
            file_path = os.path.join(STORAGE_PATH, filename)

            img_width, img_height = 600, 400
            img = Image.new('RGB', (img_width, img_height), color = (255, 255, 255))
            d = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 20) # Requires font to be available
            except IOError:
                font = ImageFont.load_default()

            d.text((50, 50), "Shipping Label", fill=(0,0,0), font=font)
            d.text((50, 100), f"Tracking: {shipment_data.get('tracking_number', 'N/A')}", fill=(0,0,0), font=font)
            d.text((50, 150), f"From: {shipment_data.get('sender_name', 'N/A')}", fill=(0,0,0), font=font)
            d.text((50, 180), f"      {shipment_data.get('sender_address', 'N/A')}", fill=(0,0,0), font=font)
            d.text((50, 230), f"To: {shipment_data.get('recipient_name', 'N/A')}", fill=(0,0,0), font=font)
            d.text((50, 260), f"    {shipment_data.get('recipient_address', 'N/A')}", fill=(0,0,0), font=font)

            img.save(file_path)
            return file_path
        except Exception as e:
            logger.error(f"Error generating shipping label image for shipment {shipment_data.get('id', 'N/A')}: {e}", exc_info=True)
            raise

    async def generate_shipping_label_zpl(self, shipment_data: Dict) -> str:
        """
        Generates a shipping label in ZPL (Zebra Programming Language) format.

        Args:
            shipment_data (Dict): A dictionary containing all necessary shipment details.

        Returns:
            str: The file path to the generated ZPL shipping label.
        """
        try:
            filename = f"shipping_label_{shipment_data['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.zpl"
            file_path = os.path.join(STORAGE_PATH, filename)

            zpl_commands = [
                "^XA",
                "^FO50,50^A0N,30,30^FDShipping Label^FS",
                f"^FO50,100^A0N,20,20^FDTracking: {shipment_data.get('tracking_number', 'N/A')}^FS",
                f"^FO50,150^A0N,20,20^FDFrom: {shipment_data.get('sender_name', 'N/A')}^FS",
                f"^FO50,170^A0N,20,20^FD      {shipment_data.get('sender_address', 'N/A')}^FS",
                f"^FO50,220^A0N,20,20^FDTo: {shipment_data.get('recipient_name', 'N/A')}^FS",
                f"^FO50,240^A0N,20,20^FD    {shipment_data.get('recipient_address', 'N/A')}^FS",
                "^XZ"
            ]
            zpl_content = "\n".join(zpl_commands)

            with open(file_path, 'w') as f:
                f.write(zpl_content)
            return file_path
        except Exception as e:
            logger.error(f"Error generating ZPL shipping label for shipment {shipment_data.get('id', 'N/A')}: {e}", exc_info=True)
            raise

    async def generate_packing_slip(self, order_id: int) -> Dict[str, Any]:
        """
        Generates a packing slip for a given order.

        Args:
            order_id (int): The ID of the order for which to generate the packing slip.

        Returns:
            Dict[str, Any]: A dictionary containing the generation result, including success status, 
                           document ID, file path, and order ID, or an error message.
        """
        if not self._db_initialized: return {'success': False, 'error': 'Database not initialized'}
        try:
            order_data = await self.fetch_order_data(order_id)
            
            if not order_data:
                raise ValueError(f"Order {order_id} not found.")
            
            file_path = await self.generate_packing_slip_pdf(order_data)
            
            doc_id = await self.save_document_record(
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
            logger.error(f"Error generating packing slip for order {order_id}: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    async def generate_packing_slip_pdf(self, order_data: Dict) -> str:
        """
        Generates a packing slip in PDF format using ReportLab.

        Args:
            order_data (Dict): A dictionary containing all necessary order details.

        Returns:
            str: The file path to the generated PDF packing slip.
        """
        try:
            filename = f"packing_slip_{order_data['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            file_path = os.path.join(STORAGE_PATH, filename)
            
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            story.append(Paragraph("<b>PACKING SLIP</b>", styles['h1']))
            story.append(Spacer(1, 0.2*inch))
            
            story.append(Paragraph(f"Order #: <b>{order_data.get('order_number', 'N/A')}</b>", styles['Normal']))
            story.append(Paragraph(f"Order Date: {order_data.get('created_at', datetime.now()).strftime('%Y-%m-%d')}", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            story.append(Paragraph("<b>Ship To:</b>", styles['Heading2']))
            ship_to = [
                [order_data.get('customer_name', 'N/A')],
                [order_data.get('shipping_address', 'N/A')]
            ]
            ship_to_table = Table(ship_to)
            story.append(ship_to_table)
            story.append(Spacer(1, 0.3*inch))
            
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
        except Exception as e:
            logger.error(f"Error generating packing slip PDF for order {order_data.get('id', 'N/A')}: {e}", exc_info=True)
            raise

    async def fetch_order_data(self, order_id: int) -> Optional[Dict]:
        """
        Fetches order data, including customer information and order items, from the database.

        Args:
            order_id (int): The ID of the order to fetch.

        Returns:
            Optional[Dict]: A dictionary containing the order data if found, otherwise None.
        """
        if not self._db_initialized: return None
        try:
            async with self.db_helper.get_session() as session:
                order = await self.db_helper.get_by_id(session, "orders", order_id)
                if order:
                    customer = await self.db_helper.get_by_id(session, "customers", order['customer_id'])
                    if customer:
                        order['customer_name'] = customer.get('name')
                        order['customer_email'] = customer.get('email')
                    order_items = await self.db_helper.get_all_where(session, "order_items", "order_id", order_id)
                    order['items'] = order_items
                return order
        except Exception as e:
            logger.error(f"Error fetching order data for order {order_id}: {e}", exc_info=True)
            return None

    async def fetch_shipment_data(self, shipment_id: int) -> Optional[Dict]:
        """
        Fetches shipment data from the database.

        Args:
            shipment_id (int): The ID of the shipment to fetch.

        Returns:
            Optional[Dict]: A dictionary containing the shipment data if found, otherwise None.
        """
        if not self._db_initialized: return None
        try:
            async with self.db_helper.get_session() as session:
                shipment = await self.db_helper.get_by_id(session, "shipments", shipment_id)
                return shipment
        except Exception as e:
            logger.error(f"Error fetching shipment data for shipment {shipment_id}: {e}", exc_info=True)
            return None

    async def save_document_record(self, document_type: str, related_id: int,
                                   related_type: str, file_path: str, format: str) -> Optional[int]:
        """
        Saves a record of a generated document to the database.

        Args:
            document_type (str): The type of document (e.g., 'invoice', 'shipping_label').
            related_id (int): The ID of the entity related to the document (e.g., order_id, shipment_id).
            related_type (str): The type of the related entity (e.g., 'order', 'shipment').
            file_path (str): The file path where the document is stored.
            format (str): The format of the document (e.g., 'PDF', 'PNG').

        Returns:
            Optional[int]: The ID of the newly created document record, or None if an error occurred.
        """
        if not self._db_initialized: return None
        try:
            async with self.db_helper.get_session() as session:
                document_data = {
                    'document_type': document_type,
                    'related_id': related_id,
                    'related_type': related_type,
                    'file_path': file_path,
                    'format': format,
                    'generated_at': datetime.now()
                }
                new_doc = await self.db_helper.create(session, "generated_documents", document_data)
                return new_doc.get('id')
        except Exception as e:
            logger.error(f"Error saving document record: {e}", exc_info=True)
            return None

    async def process_message(self, message: AgentMessage):
        """
        Processes incoming messages from Kafka.

        Args:
            message (AgentMessage): The message object received from Kafka.
        """
        logger.info(f"Processing message with type: {message.message_type} and payload: {message.payload}")
        
        response_payload = {"success": False, "message": "Unknown error"}
        try:
            if message.message_type == MessageType.GENERATE_INVOICE:
                order_id = message.payload.get("order_id")
                doc_format = message.payload.get("format", "PDF")
                if order_id:
                    response_payload = await self.generate_invoice(order_id, doc_format)
                else:
                    response_payload = {"success": False, "message": "order_id missing in payload"}
            
            elif message.message_type == MessageType.GENERATE_SHIPPING_LABEL:
                shipment_id = message.payload.get("shipment_id")
                doc_format = message.payload.get("format", "PDF")
                if shipment_id:
                    response_payload = await self.generate_shipping_label(shipment_id, doc_format)
                else:
                    response_payload = {"success": False, "message": "shipment_id missing in payload"}

            elif message.message_type == MessageType.GENERATE_PACKING_SLIP:
                order_id = message.payload.get("order_id")
                if order_id:
                    response_payload = await self.generate_packing_slip(order_id)
                else:
                    response_payload = {"success": False, "message": "order_id missing in payload"}
            
            else:
                response_payload = {"success": False, "message": f"Unsupported message type: {message.message_type}"}
            
            await self.send_message(KAFKA_RESPONSE_TOPIC, 
                                    MessageType.DOCUMENT_GENERATION_RESPONSE, 
                                    response_payload)
            
        except Exception as e:
            logger.error(f"Error processing Kafka message: {e}", exc_info=True)
            await self.send_message(KAFKA_RESPONSE_TOPIC, 
                                    MessageType.ERROR_NOTIFICATION, 
                                    {"original_message_type": message.message_type, "error": str(e)})

    async def initialize(self):
        """Initialize agent-specific components"""
        await super().initialize()
        logger.info(f"{self.agent_name} initialized successfully")
    
    async def cleanup(self):
        """Cleanup agent resources"""
        try:
            if hasattr(self, 'db_manager') and self.db_manager:
                await self.db_manager.close()
            await super().cleanup()
            logger.info(f"{self.agent_name} cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process agent-specific business logic
        
        Args:
            data: Dictionary containing operation type and parameters
            
        Returns:
            Dictionary with processing results
        """
        try:
            operation = data.get("operation", "process")
            # Implement specific business logic here
            return {"status": "success", "operation": operation, "data": data}
        except Exception as e:
            logger.error(f"Error in process_business_logic: {e}")
            return {"status": "error", "message": str(e)}



# FastAPI Server Setup
# FastAPI app moved to __init__ method as self.app

# Agent instance (global for FastAPI to access)
agent_instance: Optional[DocumentGenerationAgent] = None

async def startup_event():
    """
    FastAPI startup event to initialize the DocumentGenerationAgent.
    """
    global agent_instance
    logger.info("FastAPI startup event triggered. Initializing agent...")
    try:
        agent_instance = DocumentGenerationAgent()
        await agent_instance.initialize_agent() # Ensure async initialization is awaited
        # BaseAgent handles Kafka consumer initialization in its start() method
        # No need to manually start Kafka consumer - it's handled by the base class
        logger.info("DocumentGenerationAgent initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize DocumentGenerationAgent during startup: {e}", exc_info=True)
        # Depending on criticality, you might want to exit or disable endpoints
        raise HTTPException(status_code=500, detail=f"Agent initialization failed: {e}")

async def shutdown_event():
    """
    FastAPI shutdown event to clean up agent resources.
    """
    global agent_instance
    logger.info("FastAPI shutdown event triggered. Cleaning up agent...")
    if agent_instance:
        await agent_instance.cleanup()
        logger.info("DocumentGenerationAgent resources cleaned up.")

@agent_instance.app.get("/health", summary="Health Check", response_description="Agent health status")
async def health_check():
    """
    Checks the health status of the Document Generation Agent.

    Returns:
        Dict[str, str]: A dictionary indicating the agent's status.
    """
    if agent_instance and agent_instance._db_initialized:
        return {"status": "healthy", "agent": AGENT_TYPE, "agent_id": AGENT_ID}
    raise HTTPException(status_code=503, detail="Agent not fully initialized or unhealthy")

@agent_instance.app.get("/", summary="Root Endpoint", response_description="Agent information")
async def root():
    """
    Provides basic information about the Document Generation Agent.

    Returns:
        Dict[str, str]: A dictionary with agent details.
    """
    return {
        "agent": AGENT_TYPE,
        "status": "running",
        "version": "1.0.0",
        "agent_id": AGENT_ID
    }

@agent_instance.app.post("/generate/invoice", summary="Generate Invoice", response_description="Result of invoice generation")
async def generate_invoice_api(order_id: int, format: str = 'PDF'):
    """
    API endpoint to trigger invoice generation.

    Args:
        order_id (int): The ID of the order.
        format (str): The desired document format (e.g., 'PDF').

    Returns:
        Dict[str, Any]: The result of the invoice generation.
    """
    if not agent_instance: raise HTTPException(status_code=503, detail="Agent not initialized")
    result = await agent_instance.generate_invoice(order_id, format)
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to generate invoice'))
    return result

@agent_instance.app.post("/generate/shipping_label", summary="Generate Shipping Label", response_description="Result of shipping label generation")
async def generate_shipping_label_api(shipment_id: int, format: str = 'PDF'):
    """
    API endpoint to trigger shipping label generation.

    Args:
        shipment_id (int): The ID of the shipment.
        format (str): The desired document format (e.g., 'PDF', 'PNG', 'ZPL').

    Returns:
        Dict[str, Any]: The result of the shipping label generation.
    """
    if not agent_instance: raise HTTPException(status_code=503, detail="Agent not initialized")
    result = await agent_instance.generate_shipping_label(shipment_id, format)
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to generate shipping label'))
    return result

@agent_instance.app.post("/generate/packing_slip", summary="Generate Packing Slip", response_description="Result of packing slip generation")
async def generate_packing_slip_api(order_id: int):
    """
    API endpoint to trigger packing slip generation.

    Args:
        order_id (int): The ID of the order.

    Returns:
        Dict[str, Any]: The result of the packing slip generation.
    """
    if not agent_instance: raise HTTPException(status_code=503, detail="Agent not initialized")
    result = await agent_instance.generate_packing_slip(order_id)
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to generate packing slip'))
    return result


if __name__ == '__main__':
    # The main entry point for running the FastAPI application with Uvicorn.
    # This block ensures that the Uvicorn server is started when the script is executed directly.
    # Initialize agent first
    import asyncio
    agent_instance = DocumentGenerationAgent()
    asyncio.run(agent_instance.initialize_agent())
    
    # Register event handlers
    agent_instance.app.add_event_handler("startup", startup_event)
    agent_instance.app.add_event_handler("shutdown", shutdown_event)
    
    uvicorn.run(agent_instance.app, host="0.0.0.0", port=API_PORT)


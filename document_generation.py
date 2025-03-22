"""
Document Generation System Module

This module implements the document generation system for the XGBoost home valuation system.
It includes functionality to generate Nevada-specific real estate disclosure forms,
electronic signature collection, and PDF generation of all signed documents.
"""

import os
import json
import base64
import io
from datetime import datetime
import uuid
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import PyPDF2
import reportlab
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import qrcode
from PIL import Image

class DocumentGenerator:
    """
    Document Generator class for generating Nevada-specific real estate disclosure forms.
    """
    
    def __init__(self, base_dir="/home/ubuntu/xgboost-valuation"):
        """
        Initialize the DocumentGenerator.
        
        Args:
            base_dir: Base directory for the application.
        """
        self.base_dir = base_dir
        self.templates_dir = os.path.join(base_dir, "legal", "templates")
        self.output_dir = os.path.join(base_dir, "legal", "generated")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize styles
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'Title',
            parent=self.styles['Heading1'],
            fontSize=16,
            alignment=1,
            spaceAfter=12
        )
        self.heading_style = ParagraphStyle(
            'Heading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=10
        )
        self.subheading_style = ParagraphStyle(
            'Subheading',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=8
        )
        self.normal_style = ParagraphStyle(
            'Normal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        self.bold_style = ParagraphStyle(
            'Bold',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            spaceAfter=6
        )
        self.signature_style = ParagraphStyle(
            'Signature',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            spaceAfter=0
        )
    
    def generate_all_documents(self, user_data, verification_data, property_data=None):
        """
        Generate all required documents based on user type.
        
        Args:
            user_data: User registration data.
            verification_data: Identity verification data.
            property_data: Property data (optional).
            
        Returns:
            dict: Dictionary containing information about all generated documents.
        """
        documents = []
        
        # Generate common documents
        registration_confirmation = self.generate_registration_confirmation(user_data, verification_data)
        documents.append(registration_confirmation)
        
        duties_owed = self.generate_duties_owed(user_data, verification_data)
        documents.append(duties_owed)
        
        lead_paint = self.generate_lead_paint_disclosure(user_data, verification_data, property_data)
        documents.append(lead_paint)
        
        # Generate user type specific documents
        if user_data["user_type"] == "seller":
            residential_disclosure = self.generate_residential_disclosure(user_data, verification_data, property_data)
            documents.append(residential_disclosure)
            
            listing_agreement = self.generate_listing_agreement(user_data, verification_data, property_data)
            documents.append(listing_agreement)
        else:  # buyer
            buyer_agreement = self.generate_buyer_agreement(user_data, verification_data)
            documents.append(buyer_agreement)
        
        # Create documents data
        documents_data = {
            "documents": documents,
            "zip_filename": f"all_documents_{user_data['registration_id']}.zip",
            "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return documents_data
    
    def generate_registration_confirmation(self, user_data, verification_data):
        """
        Generate a registration confirmation document.
        
        Args:
            user_data: User registration data.
            verification_data: Identity verification data.
            
        Returns:
            dict: Document information.
        """
        filename = f"registration_confirmation_{user_data['registration_id']}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create PDF
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        elements = []
        
        # Title
        elements.append(Paragraph("Registration Confirmation", self.title_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # User Information
        elements.append(Paragraph("User Information", self.heading_style))
        elements.append(Paragraph(f"Name: {user_data['full_name']}", self.normal_style))
        elements.append(Paragraph(f"Email: {user_data['email']}", self.normal_style))
        elements.append(Paragraph(f"Phone: {user_data['phone']}", self.normal_style))
        elements.append(Paragraph(f"Marital Status: {user_data['marital_status'].capitalize()}", self.normal_style))
        
        address = user_data['address']
        address_str = f"{address['line1']}"
        if address['line2']:
            address_str += f", {address['line2']}"
        address_str += f", {address['city']}, {address['state']} {address['zip']}"
        elements.append(Paragraph(f"Address: {address_str}", self.normal_style))
        
        elements.append(Paragraph(f"User Type: {'Seller' if user_data['user_type'] == 'seller' else 'Buyer'}", self.normal_style))
        elements.append(Paragraph(f"Registration ID: {user_data['registration_id']}", self.normal_style))
        elements.append(Paragraph(f"Registration Date: {user_data['registration_date']}", self.normal_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Verification Information
        elements.append(Paragraph("Verification Information", self.heading_style))
        
        if user_data["user_type"] == "seller":
            ownership_status = {
                "owner": "I am the legal owner of the property I am selling",
                "authorized": "I am authorized to act on behalf of the property owner",
                "buyer": "I am a potential buyer"
            }.get(verification_data['ownership'], "Unknown")
            elements.append(Paragraph(f"Ownership Status: {ownership_status}", self.normal_style))
        
        legal_acknowledgments = ", ".join([ack.capitalize() for ack in verification_data['legal_acknowledgments']])
        elements.append(Paragraph(f"Legal Acknowledgments: {legal_acknowledgments}", self.normal_style))
        
        disclosures = verification_data['disclosures_acknowledged']
        elements.append(Paragraph("Disclosures Acknowledged:", self.normal_style))
        for key, value in disclosures.items():
            elements.append(Paragraph(f"- {key.replace('_', ' ').title()}: {'Yes' if value else 'No'}", self.normal_style))
        
        elements.append(Paragraph(f"Signature: {verification_data['signature']}", self.normal_style))
        elements.append(Paragraph(f"Signature Date: {verification_data['signature_date']}", self.normal_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Legal Disclaimer
        elements.append(Paragraph("Legal Disclaimer", self.heading_style))
        elements.append(Paragraph(
            "This document serves as confirmation of your registration with the XGBoost Home Valuation System. "
            "The information provided during registration will be used in accordance with our Privacy Policy. "
            "By signing this document, you acknowledge that all information provided is accurate and complete "
            "to the best of your knowledge, and you understand that providing false information may be subject "
            "to penalty of perjury under Nevada law.",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.5 * inch))
        
        # Signature Line
        elements.append(Paragraph("Signature: " + "_" * 40, self.signature_style))
        elements.append(Paragraph("Date: " + "_" * 20, self.signature_style))
        
        # Build PDF
        doc.build(elements)
        
        # Create document information
        document_info = {
            "title": "Registration Confirmation",
            "filename": filename,
            "filepath": filepath,
            "type": "confirmation",
            "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "content": self._get_base64_pdf(filepath)
        }
        
        return document_info
    
    def generate_duties_owed(self, user_data, verification_data):
        """
        Generate a Duties Owed by a Nevada Real Estate Licensee document.
        
        Args:
            user_data: User registration data.
            verification_data: Identity verification data.
            
        Returns:
            dict: Document information.
        """
        filename = f"duties_owed_{user_data['registration_id']}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create PDF
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        elements = []
        
        # Title
        elements.append(Paragraph("DUTIES OWED BY A NEVADA REAL ESTATE LICENSEE", self.title_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Introduction
        elements.append(Paragraph(
            "This form does not constitute a contract for services nor an agreement to pay compensation.",
            self.bold_style
        ))
        elements.append(Spacer(1, 0.1 * inch))
        
        elements.append(Paragraph(
            "In Nevada, a real estate licensee is required to provide a form setting forth the duties owed by the "
            "licensee to: a) Each party for whom the licensee is acting as an agent in the real estate transaction, and "
            "b) Each unrepresented party to the real estate transaction, if any.",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Licensee's Duties
        elements.append(Paragraph("LICENSEE'S DUTIES AND RESPONSIBILITIES:", self.heading_style))
        
        duties = [
            "A Nevada real estate licensee shall:",
            "1. Not deal with any party to a real estate transaction in a manner which is deceitful, fraudulent, or dishonest.",
            "2. Exercise reasonable skill and care with respect to all parties to the real estate transaction.",
            "3. Disclose to each party to the real estate transaction as soon as practicable:",
            "   a. Any material and relevant facts, data or information which licensee knows, or with reasonable care and diligence the licensee should know, about the property.",
            "   b. Each source from which licensee will receive compensation.",
            "4. Abide by all other duties, responsibilities and obligations required of the licensee in law or regulations.",
        ]
        
        for duty in duties:
            elements.append(Paragraph(duty, self.normal_style))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # Additional Duties
        elements.append(Paragraph("ADDITIONAL DUTIES OWED TO CLIENT:", self.heading_style))
        
        additional_duties = [
            "A Nevada real estate licensee who acts as an agent in a real estate transaction owes the following duties to his/her client:",
            "1. Exercise reasonable skill and care to carry out the terms of the brokerage agreement and the licensee's duties in the brokerage agreement;",
            "2. Not disclose, except to the licensee's broker, confidential information relating to a client for 1 year after the revocation or termination of the brokerage agreement, unless licensee is required to do so by court order or the client gives written permission;",
            "3. Seek a sale, purchase, option, rental or lease of real property at the price and terms stated in the brokerage agreement or at a price acceptable to the client;",
            "4. Present all offers made to, or by the client as soon as practicable, unless the client chooses to waive the duty of the licensee to present all offers and signs a waiver of the duty on a form prescribed by the Division;",
            "5. Disclose to the client material facts of which the licensee has knowledge concerning the real estate transaction;",
            "6. Advise the client to obtain advice from an expert relating to matters which are beyond the expertise of the licensee; and",
            "7. Account to the client for all money and property the licensee receives in which the client may have an interest."
        ]
        
        for duty in additional_duties:
            elements.append(Paragraph(duty, self.normal_style))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # Conflict of Interest
        elements.append(Paragraph("CONFLICT OF INTEREST:", self.heading_style))
        
        conflict = [
            "A Nevada real estate licensee who acts as an agent in a real estate transaction shall not act as an agent for more than one party in the same transaction except with the written consent of each party for whom the licensee acts.",
            "A licensee who acts as an agent for more than one party in the same real estate transaction shall disclose to each party for whom the licensee acts the duties owed to that party and the licensee's brokerage relationship."
        ]
        
        for item in conflict:
            elements.append(Paragraph(item, self.normal_style))
        
        elements.append(Spacer(1, 0.5 * inch))
        
        # Acknowledgment
        elements.append(Paragraph("ACKNOWLEDGMENT OF RECEIPT:", self.heading_style))
        elements.append(Paragraph(
            f"I/We acknowledge receipt of a copy of this form: {user_data['full_name']}",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Signature Lines
        elements.append(Paragraph("Client/Licensee Signature: " + "_" * 30 + " Date: " + "_" * 15, self.signature_style))
        elements.append(Spacer(1, 0.25 * inch))
        elements.append(Paragraph("Client/Licensee Signature: " + "_" * 30 + " Date: " + "_" * 15, self.signature_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Electronic Signature
        elements.append(Paragraph("ELECTRONIC SIGNATURE:", self.heading_style))
        elements.append(Paragraph(
            f"By typing my name below, I am signing this document electronically. "
            f"I agree my electronic signature is the legal equivalent of my manual signature.",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        elements.append(Paragraph(f"Signature: {verification_data['signature']}", self.bold_style))
        elements.append(Paragraph(f"Date: {verification_data['signature_date']}", self.normal_style))
        
        # Build PDF
        doc.build(elements)
        
        # Create document information
        document_info = {
            "title": "Duties Owed by a Nevada Real Estate Licensee",
            "filename": filename,
            "filepath": filepath,
            "type": "disclosure",
            "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "content": self._get_base64_pdf(filepath)
        }
        
        return document_info
    
    def generate_lead_paint_disclosure(self, user_data, verification_data, property_data=None):
        """
        Generate a Lead-Based Paint Disclosure document.
        
        Args:
            user_data: User registration data.
            verification_data: Identity verification data.
            property_data: Property data (optional).
            
        Returns:
            dict: Document information.
        """
        filename = f"lead_paint_disclosure_{user_data['registration_id']}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create PDF
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        elements = []
        
        # Title
        elements.append(Paragraph("DISCLOSURE OF INFORMATION ON LEAD-BASED PAINT AND/OR LEAD-BASED PAINT HAZARDS", self.title_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Property Address
        property_address = "Property Address: " + "_" * 60
        if property_data and "address" in property_data:
            property_address = f"Property Address: {property_data['address']}"
        elements.append(Paragraph(property_address, self.normal_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Lead Warning Statement
        elements.append(Paragraph("Lead Warning Statement", self.heading_style))
        elements.append(Paragraph(
            "Every purchaser of any interest in residential real property on which a residential dwelling was built prior to 1978 "
            "is notified that such property may present exposure to lead from lead-based paint that may place young children "
            "at risk of developing lead poisoning. Lead poisoning in young children may produce permanent neurological damage, "
            "including learning disabilities, reduced intelligence quotient, behavioral problems, and impaired memory. Lead "
            "poisoning also poses a particular risk to pregnant women. The seller of any interest in residential real property "
            "is required to provide the buyer with any information on lead-based paint hazards from risk assessments or inspections "
            "in the seller's possession and notify the buyer of any known lead-based paint hazards. A risk assessment or inspection "
            "for possible lead-based paint hazards is recommended prior to purchase.",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Seller's Disclosure
        elements.append(Paragraph("Seller's Disclosure", self.heading_style))
        elements.append(Paragraph("(a) Presence of lead-based paint and/or lead-based paint hazards (check one below):", self.normal_style))
        elements.append(Paragraph("[ ] Known lead-based paint and/or lead-based paint hazards are present in the housing (explain):", self.normal_style))
        elements.append(Paragraph("_" * 80, self.normal_style))
        elements.append(Paragraph("[ ] Seller has no knowledge of lead-based paint and/or lead-based paint hazards in the housing.", self.normal_style))
        elements.append(Spacer(1, 0.1 * inch))
        
        elements.append(Paragraph("(b) Records and reports available to the seller (check one below):", self.normal_style))
        elements.append(Paragraph("[ ] Seller has provided the purchaser with all available records and reports pertaining to lead-based paint and/or lead-based paint hazards in the housing (list documents below):", self.normal_style))
        elements.append(Paragraph("_" * 80, self.normal_style))
        elements.append(Paragraph("[ ] Seller has no reports or records pertaining to lead-based paint and/or lead-based paint hazards in the housing.", self.normal_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Purchaser's Acknowledgment
        elements.append(Paragraph("Purchaser's Acknowledgment", self.heading_style))
        elements.append(Paragraph("(c) Purchaser has received copies of all information listed above.", self.normal_style))
        elements.append(Paragraph("(d) Purchaser has received the pamphlet Protect Your Family from Lead in Your Home.", self.normal_style))
        elements.append(Paragraph("(e) Purchaser has (check one below):", self.normal_style))
        elements.append(Paragraph("[ ] Received a 10-day opportunity (or mutually agreed upon period) to conduct a risk assessment or inspection for the presence of lead-based paint and/or lead-based paint hazards; or", self.normal_style))
        elements.append(Paragraph("[ ] Waived the opportunity to conduct a risk assessment or inspection for the presence of lead-based paint and/or lead-based paint hazards.", self.normal_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Agent's Acknowledgment
        elements.append(Paragraph("Agent's Acknowledgment", self.heading_style))
        elements.append(Paragraph("(f) Agent has informed the seller of the seller's obligations under 42 U.S.C. 4852d and is aware of his/her responsibility to ensure compliance.", self.normal_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Certification of Accuracy
        elements.append(Paragraph("Certification of Accuracy", self.heading_style))
        elements.append(Paragraph(
            "The following parties have reviewed the information above and certify, to the best of their knowledge, "
            "that the information they have provided is true and accurate.",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Signature Lines
        elements.append(Paragraph("Seller: " + "_" * 30 + " Date: " + "_" * 15, self.signature_style))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("Seller: " + "_" * 30 + " Date: " + "_" * 15, self.signature_style))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("Purchaser: " + "_" * 30 + " Date: " + "_" * 15, self.signature_style))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("Purchaser: " + "_" * 30 + " Date: " + "_" * 15, self.signature_style))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("Agent: " + "_" * 30 + " Date: " + "_" * 15, self.signature_style))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("Agent: " + "_" * 30 + " Date: " + "_" * 15, self.signature_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Electronic Signature
        elements.append(Paragraph("ELECTRONIC SIGNATURE:", self.heading_style))
        elements.append(Paragraph(
            f"By typing my name below, I am signing this document electronically. "
            f"I agree my electronic signature is the legal equivalent of my manual signature.",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        elements.append(Paragraph(f"Signature: {verification_data['signature']}", self.bold_style))
        elements.append(Paragraph(f"Date: {verification_data['signature_date']}", self.normal_style))
        
        # Build PDF
        doc.build(elements)
        
        # Create document information
        document_info = {
            "title": "Disclosure of Lead-Based Paint",
            "filename": filename,
            "filepath": filepath,
            "type": "disclosure",
            "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "content": self._get_base64_pdf(filepath)
        }
        
        return document_info
    
    def generate_residential_disclosure(self, user_data, verification_data, property_data=None):
        """
        Generate a Residential Disclosure Guide document.
        
        Args:
            user_data: User registration data.
            verification_data: Identity verification data.
            property_data: Property data (optional).
            
        Returns:
            dict: Document information.
        """
        filename = f"residential_disclosure_{user_data['registration_id']}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create PDF
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        elements = []
        
        # Title
        elements.append(Paragraph("NEVADA RESIDENTIAL DISCLOSURE GUIDE", self.title_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Property Address
        property_address = "Property Address: " + "_" * 60
        if property_data and "address" in property_data:
            property_address = f"Property Address: {property_data['address']}"
        elements.append(Paragraph(property_address, self.normal_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Introduction
        elements.append(Paragraph("Introduction", self.heading_style))
        elements.append(Paragraph(
            "This disclosure guide is provided to inform you of your rights and obligations when selling residential "
            "property in Nevada. This guide is not a substitute for legal advice. You are encouraged to consult with "
            "a licensed attorney regarding your rights and obligations in selling residential property.",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Seller's Disclosures
        elements.append(Paragraph("Seller's Disclosures", self.heading_style))
        elements.append(Paragraph(
            "Nevada law requires a seller to disclose any and all known conditions and aspects of the property which "
            "materially affect the value or use of residential property in an adverse manner (NRS 113.130).",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.1 * inch))
        
        elements.append(Paragraph("Required Disclosures:", self.subheading_style))
        disclosures = [
            "1. Physical condition of the property",
            "2. Conditions affecting title",
            "3. Existence of any deed restrictions or CC&Rs",
            "4. Existence of any conservation easements",
            "5. Existence of any environmental hazards",
            "6. Whether property is located in a flood zone, wetlands, or other environmentally sensitive area",
            "7. Whether property has been the site of a crime involving the manufacturing of methamphetamine",
            "8. Whether property is subject to an HOA and related fees",
            "9. Whether property is subject to any pending legal action",
            "10. Whether property has any defects or features that affect health or safety"
        ]
        
        for disclosure in disclosures:
            elements.append(Paragraph(disclosure, self.normal_style))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # Seller's Real Property Disclosure Form
        elements.append(Paragraph("Seller's Real Property Disclosure Form (SRPD)", self.heading_style))
        elements.append(Paragraph(
            "Nevada law requires sellers to complete the Seller's Real Property Disclosure Form (SRPD). This form asks "
            "specific questions about various aspects of the property, including:",
            self.normal_style
        ))
        
        srpd_items = [
            "• Systems and appliances",
            "• Property conditions, improvements, and features",
            "• Environmental conditions",
            "• Sewer/septic systems",
            "• Water supply",
            "• Title conditions",
            "• Neighborhood conditions"
        ]
        
        for item in srpd_items:
            elements.append(Paragraph(item, self.normal_style))
        
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph(
            "The SRPD must be provided to the buyer before signing a binding agreement. Failure to provide the required "
            "disclosures can result in civil liability, including but not limited to actual damages, court costs, and attorney fees.",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Additional Required Disclosures
        elements.append(Paragraph("Additional Required Disclosures", self.heading_style))
        
        additional_disclosures = [
            "1. Lead-Based Paint Disclosure (for homes built before 1978)",
            "2. HOA Information Statement (if applicable)",
            "3. Open Range Disclosure (if applicable)",
            "4. Construction Defect Claims (if applicable)",
            "5. Impact Fee Disclosure (if applicable)",
            "6. Airport Noise Disclosure (if applicable)",
            "7. Gaming Corridor Disclosure (if applicable)"
        ]
        
        for disclosure in additional_disclosures:
            elements.append(Paragraph(disclosure, self.normal_style))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # Acknowledgment
        elements.append(Paragraph("Acknowledgment", self.heading_style))
        elements.append(Paragraph(
            "By signing below, I acknowledge that I have read and understand the Nevada Residential Disclosure Guide. "
            "I understand my obligations as a seller to disclose all known material facts and conditions affecting the property.",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Signature Lines
        elements.append(Paragraph("Seller: " + "_" * 30 + " Date: " + "_" * 15, self.signature_style))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("Seller: " + "_" * 30 + " Date: " + "_" * 15, self.signature_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Electronic Signature
        elements.append(Paragraph("ELECTRONIC SIGNATURE:", self.heading_style))
        elements.append(Paragraph(
            f"By typing my name below, I am signing this document electronically. "
            f"I agree my electronic signature is the legal equivalent of my manual signature.",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        elements.append(Paragraph(f"Signature: {verification_data['signature']}", self.bold_style))
        elements.append(Paragraph(f"Date: {verification_data['signature_date']}", self.normal_style))
        
        # Build PDF
        doc.build(elements)
        
        # Create document information
        document_info = {
            "title": "Residential Disclosure Guide",
            "filename": filename,
            "filepath": filepath,
            "type": "disclosure",
            "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "content": self._get_base64_pdf(filepath)
        }
        
        return document_info
    
    def generate_listing_agreement(self, user_data, verification_data, property_data=None):
        """
        Generate an Exclusive Authorization and Right to Sell document.
        
        Args:
            user_data: User registration data.
            verification_data: Identity verification data.
            property_data: Property data (optional).
            
        Returns:
            dict: Document information.
        """
        filename = f"listing_agreement_{user_data['registration_id']}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create PDF
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        elements = []
        
        # Title
        elements.append(Paragraph("EXCLUSIVE AUTHORIZATION AND RIGHT TO SELL, EXCHANGE, OR LEASE BROKERAGE LISTING AGREEMENT", self.title_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Property Address
        property_address = "Property Address: " + "_" * 60
        if property_data and "address" in property_data:
            property_address = f"Property Address: {property_data['address']}"
        elements.append(Paragraph(property_address, self.normal_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # 1. PARTIES
        elements.append(Paragraph("1. PARTIES", self.heading_style))
        elements.append(Paragraph(
            f"This Agreement is entered into between {user_data['full_name']} (\"Seller\") and "
            f"XGBoost Real Estate Brokerage (\"Broker\").",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # 2. EXCLUSIVE RIGHT
        elements.append(Paragraph("2. EXCLUSIVE RIGHT", self.heading_style))
        elements.append(Paragraph(
            "Seller grants to Broker the exclusive and irrevocable right to sell, exchange, or lease the real property "
            "described above, together with all improvements thereon, and such personal property as specified herein "
            "(collectively \"Property\").",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # 3. TERM
        elements.append(Paragraph("3. TERM", self.heading_style))
        elements.append(Paragraph(
            "This Agreement shall begin on the date of signature and shall expire at 11:59 p.m. on _______________ (date). "
            "If a sale, exchange, or lease of the Property is in progress at the time of expiration, this Agreement shall "
            "continue until the transaction is completed or terminated.",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # 4. PRICE
        elements.append(Paragraph("4. PRICE", self.heading_style))
        elements.append(Paragraph(
            "The listing price shall be $________________ or such other price as Seller may authorize. "
            "Seller acknowledges that Broker has provided a Comparative Market Analysis (CMA) and that the listing price "
            "has been determined by Seller.",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # 5. COMMISSION
        elements.append(Paragraph("5. COMMISSION", self.heading_style))
        elements.append(Paragraph(
            "Seller agrees to pay Broker a commission of ______% of the gross selling price or $________________, "
            "whichever is greater, if during the term of this Agreement:",
            self.normal_style
        ))
        
        commission_terms = [
            "a. The Property is sold, exchanged, or leased by Broker, Seller, or any other person;",
            "b. A buyer is procured who is ready, willing, and able to purchase, exchange, or lease the Property on the terms set forth herein, or on any other terms acceptable to Seller;",
            "c. Seller enters into a contract to sell, exchange, or lease the Property and subsequently defaults on the contract;",
            "d. Within ______ calendar days after the expiration of this Agreement, Seller enters into a contract to sell, exchange, or lease the Property to any person to whom the Property was shown by Broker or any licensee associated with Broker, unless Seller has entered into a valid listing agreement with another licensed real estate broker."
        ]
        
        for term in commission_terms:
            elements.append(Paragraph(term, self.normal_style))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # 6. BROKER'S OBLIGATIONS
        elements.append(Paragraph("6. BROKER'S OBLIGATIONS", self.heading_style))
        
        broker_obligations = [
            "a. Use reasonable efforts to attract buyers, exchangers, or lessees for the Property;",
            "b. Present all offers to Seller in a timely manner;",
            "c. Disclose to Seller all material facts of which Broker has knowledge concerning the Property;",
            "d. Advise Seller to obtain expert advice on matters beyond the expertise of Broker;",
            "e. Account to Seller for all money and property received by Broker in which Seller may have an interest;",
            "f. Comply with all applicable laws in the marketing and sale of the Property, including fair housing and anti-discrimination laws."
        ]
        
        for obligation in broker_obligations:
            elements.append(Paragraph(obligation, self.normal_style))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # 7. SELLER'S OBLIGATIONS
        elements.append(Paragraph("7. SELLER'S OBLIGATIONS", self.heading_style))
        
        seller_obligations = [
            "a. Provide Broker with all requested information concerning the Property;",
            "b. Allow Broker to advertise and market the Property;",
            "c. Allow Broker to place a sign on the Property, if permitted;",
            "d. Allow Broker to show the Property at reasonable times;",
            "e. Refer all inquiries concerning the Property to Broker;",
            "f. Disclose to Broker all material facts concerning the Property;",
            "g. Complete and provide to Broker the Seller's Real Property Disclosure Form as required by NRS 113.130;",
            "h. Provide Broker with copies of all relevant documents, including but not limited to, title information, surveys, and existing leases."
        ]
        
        for obligation in seller_obligations:
            elements.append(Paragraph(obligation, self.normal_style))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # 8. DISCLOSURES
        elements.append(Paragraph("8. DISCLOSURES", self.heading_style))
        elements.append(Paragraph(
            "Seller acknowledges receipt of the following disclosures:",
            self.normal_style
        ))
        
        disclosures = [
            "a. Duties Owed by a Nevada Real Estate Licensee",
            "b. Residential Disclosure Guide",
            "c. Lead-Based Paint Disclosure (if applicable)"
        ]
        
        for disclosure in disclosures:
            elements.append(Paragraph(disclosure, self.normal_style))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # 9. ADDITIONAL TERMS
        elements.append(Paragraph("9. ADDITIONAL TERMS", self.heading_style))
        elements.append(Paragraph(
            "Additional terms and conditions: _________________________________________________",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # 10. ENTIRE AGREEMENT
        elements.append(Paragraph("10. ENTIRE AGREEMENT", self.heading_style))
        elements.append(Paragraph(
            "This Agreement contains the entire agreement between the parties and supersedes any prior written or oral "
            "agreements between the parties concerning the Property. This Agreement can only be modified in writing signed "
            "by both parties.",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Signature Lines
        elements.append(Paragraph("Seller: " + "_" * 30 + " Date: " + "_" * 15, self.signature_style))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("Seller: " + "_" * 30 + " Date: " + "_" * 15, self.signature_style))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("Broker: " + "_" * 30 + " Date: " + "_" * 15, self.signature_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Electronic Signature
        elements.append(Paragraph("ELECTRONIC SIGNATURE:", self.heading_style))
        elements.append(Paragraph(
            f"By typing my name below, I am signing this document electronically. "
            f"I agree my electronic signature is the legal equivalent of my manual signature.",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        elements.append(Paragraph(f"Signature: {verification_data['signature']}", self.bold_style))
        elements.append(Paragraph(f"Date: {verification_data['signature_date']}", self.normal_style))
        
        # Build PDF
        doc.build(elements)
        
        # Create document information
        document_info = {
            "title": "Exclusive Authorization and Right to Sell",
            "filename": filename,
            "filepath": filepath,
            "type": "agreement",
            "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "content": self._get_base64_pdf(filepath)
        }
        
        return document_info
    
    def generate_buyer_agreement(self, user_data, verification_data):
        """
        Generate a Buyer Brokerage Representation Agreement document.
        
        Args:
            user_data: User registration data.
            verification_data: Identity verification data.
            
        Returns:
            dict: Document information.
        """
        filename = f"buyer_agreement_{user_data['registration_id']}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create PDF
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        elements = []
        
        # Title
        elements.append(Paragraph("BUYER BROKERAGE REPRESENTATION AGREEMENT", self.title_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # 1. PARTIES
        elements.append(Paragraph("1. PARTIES", self.heading_style))
        elements.append(Paragraph(
            f"This Agreement is entered into between {user_data['full_name']} (\"Buyer\") and "
            f"XGBoost Real Estate Brokerage (\"Broker\").",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # 2. APPOINTMENT
        elements.append(Paragraph("2. APPOINTMENT", self.heading_style))
        elements.append(Paragraph(
            "Buyer appoints Broker as Buyer's exclusive agent to assist Buyer in the acquisition of real property. "
            "Buyer agrees to conduct all negotiations for the types of property described below through Broker, and "
            "to refer to Broker all inquiries received from real estate brokers, salespersons, prospective sellers, "
            "or any other source during the time this Agreement is in effect.",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # 3. TERM
        elements.append(Paragraph("3. TERM", self.heading_style))
        elements.append(Paragraph(
            "This Agreement shall begin on the date of signature and shall expire at 11:59 p.m. on _______________ (date). "
            "If an acquisition of property is in progress at the time of expiration, this Agreement shall "
            "continue until the transaction is completed or terminated.",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # 4. PROPERTY DESCRIPTION
        elements.append(Paragraph("4. PROPERTY DESCRIPTION", self.heading_style))
        elements.append(Paragraph(
            "Buyer is interested in purchasing real property with the following characteristics:",
            self.normal_style
        ))
        
        property_characteristics = [
            "Type: _______________________________",
            "Location: ___________________________",
            "Price Range: ________________________",
            "Size: _______________________________",
            "Other: ______________________________"
        ]
        
        for characteristic in property_characteristics:
            elements.append(Paragraph(characteristic, self.normal_style))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # 5. BROKER'S OBLIGATIONS
        elements.append(Paragraph("5. BROKER'S OBLIGATIONS", self.heading_style))
        
        broker_obligations = [
            "a. Use reasonable efforts to locate property that meets Buyer's specifications;",
            "b. Present all offers and counteroffers in a timely manner;",
            "c. Disclose to Buyer all material facts of which Broker has knowledge concerning properties shown;",
            "d. Advise Buyer to obtain expert advice on matters beyond the expertise of Broker;",
            "e. Account to Buyer for all money and property received by Broker in which Buyer may have an interest;",
            "f. Comply with all applicable laws in assisting Buyer, including fair housing and anti-discrimination laws."
        ]
        
        for obligation in broker_obligations:
            elements.append(Paragraph(obligation, self.normal_style))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # 6. BUYER'S OBLIGATIONS
        elements.append(Paragraph("6. BUYER'S OBLIGATIONS", self.heading_style))
        
        buyer_obligations = [
            "a. Work exclusively with Broker during the term of this Agreement;",
            "b. Provide Broker with relevant personal and financial information to facilitate Buyer's acquisition of property;",
            "c. Cooperate with Broker in finding suitable property;",
            "d. Inform all real estate licensees Buyer comes in contact with about this Agreement;",
            "e. Be available to view properties, and respond to communications from Broker in a timely manner;",
            "f. Conduct all negotiations through Broker."
        ]
        
        for obligation in buyer_obligations:
            elements.append(Paragraph(obligation, self.normal_style))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # 7. COMPENSATION
        elements.append(Paragraph("7. COMPENSATION", self.heading_style))
        elements.append(Paragraph(
            "Broker will be compensated as follows (check all that apply):",
            self.normal_style
        ))
        
        compensation_options = [
            "[ ] Broker will be paid by the seller or seller's broker.",
            "[ ] If the property is not listed with a broker, or if the seller or seller's broker does not offer compensation, Buyer agrees to pay Broker a fee of ______% of the purchase price or $________________, whichever is greater.",
            "[ ] Buyer agrees to pay Broker a retainer fee of $________________, which [ ] will [ ] will not be credited against any other compensation Broker receives.",
            "[ ] Other: ______________________________"
        ]
        
        for option in compensation_options:
            elements.append(Paragraph(option, self.normal_style))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # 8. DISCLOSURES
        elements.append(Paragraph("8. DISCLOSURES", self.heading_style))
        elements.append(Paragraph(
            "Buyer acknowledges receipt of the following disclosures:",
            self.normal_style
        ))
        
        disclosures = [
            "a. Duties Owed by a Nevada Real Estate Licensee",
            "b. Lead-Based Paint Disclosure (if applicable)"
        ]
        
        for disclosure in disclosures:
            elements.append(Paragraph(disclosure, self.normal_style))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # 9. ADDITIONAL TERMS
        elements.append(Paragraph("9. ADDITIONAL TERMS", self.heading_style))
        elements.append(Paragraph(
            "Additional terms and conditions: _________________________________________________",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # 10. ENTIRE AGREEMENT
        elements.append(Paragraph("10. ENTIRE AGREEMENT", self.heading_style))
        elements.append(Paragraph(
            "This Agreement contains the entire agreement between the parties and supersedes any prior written or oral "
            "agreements between the parties. This Agreement can only be modified in writing signed by both parties.",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Signature Lines
        elements.append(Paragraph("Buyer: " + "_" * 30 + " Date: " + "_" * 15, self.signature_style))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("Buyer: " + "_" * 30 + " Date: " + "_" * 15, self.signature_style))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("Broker: " + "_" * 30 + " Date: " + "_" * 15, self.signature_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Electronic Signature
        elements.append(Paragraph("ELECTRONIC SIGNATURE:", self.heading_style))
        elements.append(Paragraph(
            f"By typing my name below, I am signing this document electronically. "
            f"I agree my electronic signature is the legal equivalent of my manual signature.",
            self.normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        elements.append(Paragraph(f"Signature: {verification_data['signature']}", self.bold_style))
        elements.append(Paragraph(f"Date: {verification_data['signature_date']}", self.normal_style))
        
        # Build PDF
        doc.build(elements)
        
        # Create document information
        document_info = {
            "title": "Buyer Brokerage Representation Agreement",
            "filename": filename,
            "filepath": filepath,
            "type": "agreement",
            "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "content": self._get_base64_pdf(filepath)
        }
        
        return document_info
    
    def _get_base64_pdf(self, filepath):
        """
        Convert a PDF file to base64 encoding.
        
        Args:
            filepath: Path to the PDF file.
            
        Returns:
            str: Base64 encoded PDF content.
        """
        with open(filepath, "rb") as pdf_file:
            encoded_string = base64.b64encode(pdf_file.read())
        
        return encoded_string.decode("utf-8")


class DocumentSender:
    """
    Document Sender class for sending documents via email.
    """
    
    def __init__(self, smtp_server="smtp.gmail.com", smtp_port=587):
        """
        Initialize the DocumentSender.
        
        Args:
            smtp_server: SMTP server address.
            smtp_port: SMTP server port.
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
    
    def send_documents(self, user_data, notification_data, documents_data, email_credentials):
        """
        Send documents via email.
        
        Args:
            user_data: User registration data.
            notification_data: Notification data.
            documents_data: Documents data.
            email_credentials: Email credentials (username and password).
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = email_credentials["username"]
            msg["To"] = notification_data["agent_email"]
            msg["Subject"] = f"XGBoost Home Valuation - Documents for {user_data['full_name']}"
            
            # Add CC recipients
            cc_recipients = []
            if "copy" in notification_data["notification_preferences"]:
                cc_recipients.append(user_data["email"])
            
            cc_recipients.extend(notification_data["additional_recipients"])
            
            if cc_recipients:
                msg["Cc"] = ", ".join(cc_recipients)
            
            # Add message body
            body = f"""
            <html>
            <body>
                <h2>XGBoost Home Valuation - Documents</h2>
                <p>Please find attached the documents for {user_data['full_name']}.</p>
                <p><strong>Registration ID:</strong> {user_data['registration_id']}</p>
                <p><strong>Registration Date:</strong> {user_data['registration_date']}</p>
                <p><strong>User Type:</strong> {'Seller' if user_data['user_type'] == 'seller' else 'Buyer'}</p>
                <p><strong>Contact Information:</strong><br>
                Email: {user_data['email']}<br>
                Phone: {user_data['phone']}</p>
                <p><strong>Additional Notes:</strong><br>
                {notification_data['notes']}</p>
                <p>The following documents are attached:</p>
                <ul>
            """
            
            for doc in documents_data["documents"]:
                body += f"<li>{doc['title']}</li>"
            
            body += """
                </ul>
                <p>Thank you for your attention to this matter.</p>
                <p>Best regards,<br>
                XGBoost Home Valuation System</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, "html"))
            
            # Add attachments
            for doc in documents_data["documents"]:
                attachment = MIMEApplication(base64.b64decode(doc["content"]))
                attachment["Content-Disposition"] = f'attachment; filename="{doc["filename"]}"'
                msg.attach(attachment)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(email_credentials["username"], email_credentials["password"])
                
                recipients = [notification_data["agent_email"]]
                recipients.extend(cc_recipients)
                
                server.sendmail(email_credentials["username"], recipients, msg.as_string())
            
            return True
        
        except Exception as e:
            print(f"Error sending documents: {str(e)}")
            return False


class ElectronicSignature:
    """
    Electronic Signature class for handling electronic signatures.
    """
    
    def __init__(self, base_dir="/home/ubuntu/xgboost-valuation"):
        """
        Initialize the ElectronicSignature.
        
        Args:
            base_dir: Base directory for the application.
        """
        self.base_dir = base_dir
        self.signatures_dir = os.path.join(base_dir, "legal", "signatures")
        
        # Create signatures directory if it doesn't exist
        os.makedirs(self.signatures_dir, exist_ok=True)
    
    def create_signature_image(self, name, signature_id):
        """
        Create a signature image.
        
        Args:
            name: Name to use for the signature.
            signature_id: Unique signature ID.
            
        Returns:
            str: Path to the signature image.
        """
        # Create a signature image using PIL
        img = Image.new("RGB", (600, 200), color="white")
        from PIL import ImageDraw, ImageFont
        
        try:
            # Try to use a font that looks like handwriting
            font = ImageFont.truetype("arial.ttf", 50)
        except IOError:
            # Fall back to default font
            font = ImageFont.load_default()
        
        draw = ImageDraw.Draw(img)
        draw.text((50, 50), name, fill="black", font=font)
        
        # Add a timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        draw.text((50, 120), f"Signed electronically on {timestamp}", fill="black", font=ImageFont.load_default())
        
        # Save the image
        signature_path = os.path.join(self.signatures_dir, f"signature_{signature_id}.png")
        img.save(signature_path)
        
        return signature_path
    
    def create_signature_qr_code(self, verification_url, signature_id):
        """
        Create a QR code for signature verification.
        
        Args:
            verification_url: URL for signature verification.
            signature_id: Unique signature ID.
            
        Returns:
            str: Path to the QR code image.
        """
        # Create a QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(verification_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save the QR code
        qr_path = os.path.join(self.signatures_dir, f"qr_{signature_id}.png")
        img.save(qr_path)
        
        return qr_path
    
    def apply_signature_to_pdf(self, pdf_path, signature_path, qr_path, output_path):
        """
        Apply a signature and QR code to a PDF.
        
        Args:
            pdf_path: Path to the PDF file.
            signature_path: Path to the signature image.
            qr_path: Path to the QR code image.
            output_path: Path to save the signed PDF.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Create a new PDF with signature and QR code
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            
            # Add signature image
            can.drawImage(signature_path, 100, 100, width=400, height=100)
            
            # Add QR code
            can.drawImage(qr_path, 500, 100, width=50, height=50)
            
            # Add verification text
            can.drawString(400, 80, "Scan QR code to verify signature")
            
            can.save()
            
            # Move to the beginning of the StringIO buffer
            packet.seek(0)
            new_pdf = PyPDF2.PdfFileReader(packet)
            
            # Read the existing PDF
            existing_pdf = PyPDF2.PdfFileReader(open(pdf_path, "rb"))
            output = PyPDF2.PdfFileWriter()
            
            # Add the signature to the last page
            page = existing_pdf.getPage(existing_pdf.getNumPages() - 1)
            page.mergePage(new_pdf.getPage(0))
            output.addPage(page)
            
            # Add all other pages
            for i in range(existing_pdf.getNumPages() - 1):
                output.addPage(existing_pdf.getPage(i))
            
            # Write the signed PDF to file
            with open(output_path, "wb") as outputStream:
                output.write(outputStream)
            
            return True
        
        except Exception as e:
            print(f"Error applying signature to PDF: {str(e)}")
            return False


class AuditTrail:
    """
    Audit Trail class for tracking document activities.
    """
    
    def __init__(self, base_dir="/home/ubuntu/xgboost-valuation"):
        """
        Initialize the AuditTrail.
        
        Args:
            base_dir: Base directory for the application.
        """
        self.base_dir = base_dir
        self.audit_dir = os.path.join(base_dir, "legal", "audit")
        self.audit_file = os.path.join(self.audit_dir, "audit_trail.json")
        
        # Create audit directory if it doesn't exist
        os.makedirs(self.audit_dir, exist_ok=True)
        
        # Create audit file if it doesn't exist
        if not os.path.exists(self.audit_file):
            with open(self.audit_file, "w") as f:
                json.dump([], f)
    
    def add_entry(self, entry_type, user_data, document_data=None, ip_address=None):
        """
        Add an entry to the audit trail.
        
        Args:
            entry_type: Type of entry (e.g., "document_generated", "document_signed", "document_viewed").
            user_data: User data.
            document_data: Document data (optional).
            ip_address: IP address (optional).
            
        Returns:
            dict: Audit entry.
        """
        # Create audit entry
        entry = {
            "entry_id": str(uuid.uuid4()),
            "entry_type": entry_type,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user_data["registration_id"],
            "user_name": user_data["full_name"],
            "user_email": user_data["email"],
            "ip_address": ip_address
        }
        
        if document_data:
            entry["document_id"] = document_data.get("filename", "")
            entry["document_title"] = document_data.get("title", "")
            entry["document_type"] = document_data.get("type", "")
        
        # Load existing audit trail
        with open(self.audit_file, "r") as f:
            audit_trail = json.load(f)
        
        # Add new entry
        audit_trail.append(entry)
        
        # Save audit trail
        with open(self.audit_file, "w") as f:
            json.dump(audit_trail, f, indent=2)
        
        return entry
    
    def get_entries_by_user(self, user_id):
        """
        Get all audit entries for a specific user.
        
        Args:
            user_id: User ID.
            
        Returns:
            list: List of audit entries.
        """
        # Load audit trail
        with open(self.audit_file, "r") as f:
            audit_trail = json.load(f)
        
        # Filter entries by user ID
        user_entries = [entry for entry in audit_trail if entry["user_id"] == user_id]
        
        return user_entries
    
    def get_entries_by_document(self, document_id):
        """
        Get all audit entries for a specific document.
        
        Args:
            document_id: Document ID.
            
        Returns:
            list: List of audit entries.
        """
        # Load audit trail
        with open(self.audit_file, "r") as f:
            audit_trail = json.load(f)
        
        # Filter entries by document ID
        document_entries = [entry for entry in audit_trail if entry.get("document_id") == document_id]
        
        return document_entries
    
    def generate_audit_report(self, user_id=None, document_id=None, start_date=None, end_date=None):
        """
        Generate an audit report.
        
        Args:
            user_id: User ID (optional).
            document_id: Document ID (optional).
            start_date: Start date (optional).
            end_date: End date (optional).
            
        Returns:
            dict: Audit report.
        """
        # Load audit trail
        with open(self.audit_file, "r") as f:
            audit_trail = json.load(f)
        
        # Filter entries
        filtered_entries = audit_trail
        
        if user_id:
            filtered_entries = [entry for entry in filtered_entries if entry["user_id"] == user_id]
        
        if document_id:
            filtered_entries = [entry for entry in filtered_entries if entry.get("document_id") == document_id]
        
        if start_date:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            filtered_entries = [entry for entry in filtered_entries if datetime.strptime(entry["timestamp"].split()[0], "%Y-%m-%d") >= start_datetime]
        
        if end_date:
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
            filtered_entries = [entry for entry in filtered_entries if datetime.strptime(entry["timestamp"].split()[0], "%Y-%m-%d") <= end_datetime]
        
        # Create report
        report = {
            "report_id": str(uuid.uuid4()),
            "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "filters": {
                "user_id": user_id,
                "document_id": document_id,
                "start_date": start_date,
                "end_date": end_date
            },
            "entries": filtered_entries,
            "total_entries": len(filtered_entries)
        }
        
        return report

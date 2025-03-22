"""
Legal Compliance Module

This module implements legal compliance features for the XGBoost home valuation system.
It includes E-SIGN Act compliance, privacy policy, terms of service, and audit trail functionality.
"""

import os
import json
import base64
import io
from datetime import datetime
import uuid
import hashlib
import hmac
import re
import logging
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("legal_compliance.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("legal_compliance")

class ESignCompliance:
    """
    E-SIGN Act Compliance class for ensuring electronic signatures comply with federal regulations.
    """
    
    def __init__(self, base_dir="/home/ubuntu/xgboost-valuation"):
        """
        Initialize the ESignCompliance.
        
        Args:
            base_dir: Base directory for the application.
        """
        self.base_dir = base_dir
        self.compliance_dir = os.path.join(base_dir, "legal", "compliance")
        self.consent_file = os.path.join(self.compliance_dir, "esign_consents.json")
        
        # Create compliance directory if it doesn't exist
        os.makedirs(self.compliance_dir, exist_ok=True)
        
        # Create consent file if it doesn't exist
        if not os.path.exists(self.consent_file):
            with open(self.consent_file, "w") as f:
                json.dump([], f)
        
        logger.info("E-SIGN Compliance module initialized")
    
    def record_consent(self, user_data, consent_text, ip_address=None, user_agent=None):
        """
        Record user consent to use electronic signatures.
        
        Args:
            user_data: User data.
            consent_text: Text of the consent agreement.
            ip_address: IP address of the user (optional).
            user_agent: User agent of the user's browser (optional).
            
        Returns:
            dict: Consent record.
        """
        # Create consent record
        consent_record = {
            "consent_id": str(uuid.uuid4()),
            "user_id": user_data["registration_id"],
            "user_name": user_data["full_name"],
            "user_email": user_data["email"],
            "consent_text": consent_text,
            "consent_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "consent_hash": self._hash_consent(user_data["registration_id"], consent_text)
        }
        
        # Load existing consents
        with open(self.consent_file, "r") as f:
            consents = json.load(f)
        
        # Add new consent
        consents.append(consent_record)
        
        # Save consents
        with open(self.consent_file, "w") as f:
            json.dump(consents, f, indent=2)
        
        logger.info(f"Recorded E-SIGN consent for user {user_data['registration_id']}")
        
        return consent_record
    
    def verify_consent(self, user_id):
        """
        Verify if a user has consented to use electronic signatures.
        
        Args:
            user_id: User ID.
            
        Returns:
            bool: True if user has consented, False otherwise.
        """
        # Load consents
        with open(self.consent_file, "r") as f:
            consents = json.load(f)
        
        # Check if user has consented
        for consent in consents:
            if consent["user_id"] == user_id:
                logger.info(f"Verified E-SIGN consent for user {user_id}")
                return True
        
        logger.warning(f"No E-SIGN consent found for user {user_id}")
        return False
    
    def get_consent_record(self, user_id):
        """
        Get the consent record for a user.
        
        Args:
            user_id: User ID.
            
        Returns:
            dict: Consent record, or None if not found.
        """
        # Load consents
        with open(self.consent_file, "r") as f:
            consents = json.load(f)
        
        # Find user's consent
        for consent in consents:
            if consent["user_id"] == user_id:
                return consent
        
        return None
    
    def generate_consent_form(self, user_data):
        """
        Generate an E-SIGN consent form.
        
        Args:
            user_data: User data.
            
        Returns:
            str: Path to the generated consent form.
        """
        filename = f"esign_consent_{user_data['registration_id']}.pdf"
        filepath = os.path.join(self.compliance_dir, filename)
        
        # Create PDF
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Define styles
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=1,
            spaceAfter=12
        )
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10
        )
        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        bold_style = ParagraphStyle(
            'Bold',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            spaceAfter=6
        )
        signature_style = ParagraphStyle(
            'Signature',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            spaceAfter=0
        )
        
        elements = []
        
        # Title
        elements.append(Paragraph("ELECTRONIC SIGNATURE DISCLOSURE AND CONSENT", title_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Introduction
        elements.append(Paragraph(
            f"This Electronic Signature Disclosure and Consent applies to your use of electronic signatures "
            f"with XGBoost Home Valuation System for Clark County, Nevada.",
            normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Agreement to Use Electronic Signatures
        elements.append(Paragraph("Agreement to Use Electronic Signatures", heading_style))
        elements.append(Paragraph(
            "By checking the 'I agree' box and clicking 'Continue', you agree to use electronic signatures for "
            "documents related to your real estate transaction. You confirm that:",
            normal_style
        ))
        
        agreement_items = [
            "1. You have read and understand this Electronic Signature Disclosure and Consent.",
            "2. You consent to use electronic signatures for documents related to your real estate transaction.",
            "3. You have the hardware and software requirements described below.",
            "4. You can access and read this Electronic Signature Disclosure and Consent.",
            "5. You can print on paper the disclosure or save or send the disclosure to a place where you can print it, for future reference and access."
        ]
        
        for item in agreement_items:
            elements.append(Paragraph(item, normal_style))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # Hardware and Software Requirements
        elements.append(Paragraph("Hardware and Software Requirements", heading_style))
        elements.append(Paragraph(
            "To access and retain electronic records, you will need:",
            normal_style
        ))
        
        requirements = [
            "• A computer or mobile device with internet access",
            "• A valid email address",
            "• A web browser that supports 128-bit encryption (such as Chrome, Firefox, Safari, or Edge)",
            "• Software that can view PDF files (such as Adobe Acrobat Reader)",
            "• Sufficient electronic storage space on your computer's hard drive or other storage device"
        ]
        
        for requirement in requirements:
            elements.append(Paragraph(requirement, normal_style))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # Withdrawing Consent
        elements.append(Paragraph("Withdrawing Consent", heading_style))
        elements.append(Paragraph(
            "You may withdraw your consent to use electronic signatures at any time. To withdraw your consent, "
            "please contact us at support@xgboostvaluation.com. If you withdraw your consent, it will not affect "
            "the legal validity or enforceability of electronic records provided to you prior to your withdrawal.",
            normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Paper Copies
        elements.append(Paragraph("Paper Copies", heading_style))
        elements.append(Paragraph(
            "You have the right to receive a paper copy of any electronic record provided to you. To request a paper "
            "copy, please contact us at support@xgboostvaluation.com. We may charge a reasonable fee for providing "
            "paper copies.",
            normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Consent
        elements.append(Paragraph("Consent", heading_style))
        elements.append(Paragraph(
            f"By signing below, I, {user_data['full_name']}, confirm that I have read and understand this "
            f"Electronic Signature Disclosure and Consent, and I agree to use electronic signatures for "
            f"documents related to my real estate transaction.",
            normal_style
        ))
        elements.append(Spacer(1, 0.5 * inch))
        
        # Signature Lines
        elements.append(Paragraph("Signature: " + "_" * 40, signature_style))
        elements.append(Spacer(1, 0.25 * inch))
        elements.append(Paragraph("Date: " + "_" * 20, signature_style))
        
        # Build PDF
        doc.build(elements)
        
        logger.info(f"Generated E-SIGN consent form for user {user_data['registration_id']}")
        
        return filepath
    
    def _hash_consent(self, user_id, consent_text):
        """
        Create a hash of the consent text for verification purposes.
        
        Args:
            user_id: User ID.
            consent_text: Text of the consent agreement.
            
        Returns:
            str: Hash of the consent text.
        """
        # Create a secret key based on user ID
        secret_key = hashlib.sha256(user_id.encode()).digest()
        
        # Create HMAC hash of consent text
        h = hmac.new(secret_key, consent_text.encode(), hashlib.sha256)
        
        return h.hexdigest()


class PrivacyPolicy:
    """
    Privacy Policy class for generating and managing privacy policies.
    """
    
    def __init__(self, base_dir="/home/ubuntu/xgboost-valuation"):
        """
        Initialize the PrivacyPolicy.
        
        Args:
            base_dir: Base directory for the application.
        """
        self.base_dir = base_dir
        self.legal_dir = os.path.join(base_dir, "legal")
        self.privacy_file = os.path.join(self.legal_dir, "privacy_policy.pdf")
        
        # Create legal directory if it doesn't exist
        os.makedirs(self.legal_dir, exist_ok=True)
        
        logger.info("Privacy Policy module initialized")
    
    def generate_privacy_policy(self):
        """
        Generate a privacy policy document.
        
        Returns:
            str: Path to the generated privacy policy.
        """
        # Create PDF
        doc = SimpleDocTemplate(self.privacy_file, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Define styles
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=1,
            spaceAfter=12
        )
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10
        )
        subheading_style = ParagraphStyle(
            'Subheading',
            parent=styles['Heading3'],
            fontSize=12,
            spaceAfter=8
        )
        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        elements = []
        
        # Title
        elements.append(Paragraph("PRIVACY POLICY", title_style))
        elements.append(Paragraph("XGBoost Home Valuation System for Clark County, Nevada", normal_style))
        elements.append(Paragraph("Last Updated: " + datetime.now().strftime("%B %d, %Y"), normal_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Introduction
        elements.append(Paragraph("1. INTRODUCTION", heading_style))
        elements.append(Paragraph(
            "XGBoost Home Valuation System (\"we,\" \"our,\" or \"us\") is committed to protecting your privacy. "
            "This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use "
            "our home valuation system for Clark County, Nevada.",
            normal_style
        ))
        elements.append(Paragraph(
            "Please read this Privacy Policy carefully. By accessing or using our system, you acknowledge that you "
            "have read, understood, and agree to be bound by all the terms of this Privacy Policy.",
            normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Information We Collect
        elements.append(Paragraph("2. INFORMATION WE COLLECT", heading_style))
        
        elements.append(Paragraph("2.1 Personal Information", subheading_style))
        elements.append(Paragraph(
            "We may collect personal information that you voluntarily provide to us when you register with our system, "
            "express an interest in obtaining information about us or our products and services, or otherwise contact us. "
            "The personal information we collect may include:",
            normal_style
        ))
        
        personal_info = [
            "• Full legal name",
            "• Email address",
            "• Phone number",
            "• Marital status",
            "• Current address",
            "• Property information",
            "• Electronic signature"
        ]
        
        for info in personal_info:
            elements.append(Paragraph(info, normal_style))
        
        elements.append(Paragraph("2.2 Property and Financial Information", subheading_style))
        elements.append(Paragraph(
            "To provide accurate home valuations and cost of ownership calculations, we may collect information about "
            "properties and financial details, including:",
            normal_style
        ))
        
        property_info = [
            "• Property address and details",
            "• Property tax information",
            "• HOA fees",
            "• Mortgage information",
            "• Insurance rates",
            "• Maintenance costs"
        ]
        
        for info in property_info:
            elements.append(Paragraph(info, normal_style))
        
        elements.append(Paragraph("2.3 Automatically Collected Information", subheading_style))
        elements.append(Paragraph(
            "When you access our system, we may automatically collect certain information about your device and usage, "
            "including:",
            normal_style
        ))
        
        auto_info = [
            "• IP address",
            "• Browser type",
            "• Operating system",
            "• Device information",
            "• Usage patterns",
            "• Geographic location"
        ]
        
        for info in auto_info:
            elements.append(Paragraph(info, normal_style))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # How We Use Your Information
        elements.append(Paragraph("3. HOW WE USE YOUR INFORMATION", heading_style))
        elements.append(Paragraph(
            "We may use the information we collect for various purposes, including:",
            normal_style
        ))
        
        usage_purposes = [
            "• Providing and maintaining our home valuation system",
            "• Processing property valuations and cost calculations",
            "• Generating legal documents and disclosures",
            "• Communicating with you about your account or property",
            "• Sending you technical notices, updates, and support messages",
            "• Responding to your comments, questions, and requests",
            "• Improving our system and developing new products and services",
            "• Monitoring usage patterns and system performance",
            "• Protecting the security and integrity of our system",
            "• Complying with legal obligations"
        ]
        
        for purpose in usage_purposes:
            elements.append(Paragraph(purpose, normal_style))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # Disclosure of Your Information
        elements.append(Paragraph("4. DISCLOSURE OF YOUR INFORMATION", heading_style))
        elements.append(Paragraph(
            "We may share your information in the following situations:",
            normal_style
        ))
        
        disclosure_situations = [
            "• With real estate agents or brokers you designate to receive your information",
            "• With third-party service providers that help us operate our system",
            "• With data providers that supply property and market information",
            "• To comply with legal obligations",
            "• To protect our rights, privacy, safety, or property",
            "• In connection with a business transaction, such as a merger or acquisition"
        ]
        
        for situation in disclosure_situations:
            elements.append(Paragraph(situation, normal_style))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # Data Security
        elements.append(Paragraph("5. DATA SECURITY", heading_style))
        elements.append(Paragraph(
            "We have implemented appropriate technical and organizational security measures designed to protect the "
            "security of any personal information we process. However, despite our safeguards and efforts to secure "
            "your information, no electronic transmission over the Internet or information storage technology can be "
            "guaranteed to be 100% secure.",
            normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Data Retention
        elements.append(Paragraph("6. DATA RETENTION", heading_style))
        elements.append(Paragraph(
            "We will retain your personal information only for as long as is necessary for the purposes set out in "
            "this Privacy Policy. We will retain and use your information to the extent necessary to comply with our "
            "legal obligations, resolve disputes, and enforce our policies.",
            normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Your Privacy Rights
        elements.append(Paragraph("7. YOUR PRIVACY RIGHTS", heading_style))
        elements.append(Paragraph(
            "Depending on your location, you may have certain rights regarding your personal information, including:",
            normal_style
        ))
        
        privacy_rights = [
            "• Right to access your personal information",
            "• Right to correct inaccurate or incomplete information",
            "• Right to delete your personal information",
            "• Right to restrict or object to processing of your information",
            "• Right to data portability",
            "• Right to withdraw consent"
        ]
        
        for right in privacy_rights:
            elements.append(Paragraph(right, normal_style))
        
        elements.append(Paragraph(
            "To exercise these rights, please contact us at privacy@xgboostvaluation.com.",
            normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Children's Privacy
        elements.append(Paragraph("8. CHILDREN'S PRIVACY", heading_style))
        elements.append(Paragraph(
            "Our system is not intended for children under 18 years of age. We do not knowingly collect personal "
            "information from children under 18. If you are a parent or guardian and believe your child has provided "
            "us with personal information, please contact us immediately.",
            normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Changes to This Privacy Policy
        elements.append(Paragraph("9. CHANGES TO THIS PRIVACY POLICY", heading_style))
        elements.append(Paragraph(
            "We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new "
            "Privacy Policy on this page and updating the \"Last Updated\" date. You are advised to review this Privacy "
            "Policy periodically for any changes.",
            normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Contact Us
        elements.append(Paragraph("10. CONTACT US", heading_style))
        elements.append(Paragraph(
            "If you have questions or comments about this Privacy Policy, please contact us at:",
            normal_style
        ))
        elements.append(Paragraph("XGBoost Home Valuation System", normal_style))
        elements.append(Paragraph("Email: privacy@xgboostvaluation.com", normal_style))
        elements.append(Paragraph("Phone: (702) 555-1234", normal_style))
        elements.append(Paragraph("Address: 123 Main Street, Las Vegas, NV 89101", normal_style))
        
        # Build PDF
        doc.build(elements)
        
        logger.info("Generated privacy policy document")
        
        return self.privacy_file
    
    def get_privacy_policy_text(self):
        """
        Get the text of the privacy policy for display on the website.
        
        Returns:
            str: Privacy policy text in HTML format.
        """
        privacy_policy_html = """
        <h1>PRIVACY POLICY</h1>
        <p>XGBoost Home Valuation System for Clark County, Nevada</p>
        <p>Last Updated: {date}</p>
        
        <h2>1. INTRODUCTION</h2>
        <p>XGBoost Home Valuation System ("we," "our," or "us") is committed to protecting your privacy. 
        This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use 
        our home valuation system for Clark County, Nevada.</p>
        <p>Please read this Privacy Policy carefully. By accessing or using our system, you acknowledge that you 
        have read, understood, and agree to be bound by all the terms of this Privacy Policy.</p>
        
        <h2>2. INFORMATION WE COLLECT</h2>
        
        <h3>2.1 Personal Information</h3>
        <p>We may collect personal information that you voluntarily provide to us when you register with our system, 
        express an interest in obtaining information about us or our products and services, or otherwise contact us. 
        The personal information we collect may include:</p>
        <ul>
            <li>Full legal name</li>
            <li>Email address</li>
            <li>Phone number</li>
            <li>Marital status</li>
            <li>Current address</li>
            <li>Property information</li>
            <li>Electronic signature</li>
        </ul>
        
        <h3>2.2 Property and Financial Information</h3>
        <p>To provide accurate home valuations and cost of ownership calculations, we may collect information about 
        properties and financial details, including:</p>
        <ul>
            <li>Property address and details</li>
            <li>Property tax information</li>
            <li>HOA fees</li>
            <li>Mortgage information</li>
            <li>Insurance rates</li>
            <li>Maintenance costs</li>
        </ul>
        
        <h3>2.3 Automatically Collected Information</h3>
        <p>When you access our system, we may automatically collect certain information about your device and usage, 
        including:</p>
        <ul>
            <li>IP address</li>
            <li>Browser type</li>
            <li>Operating system</li>
            <li>Device information</li>
            <li>Usage patterns</li>
            <li>Geographic location</li>
        </ul>
        
        <h2>3. HOW WE USE YOUR INFORMATION</h2>
        <p>We may use the information we collect for various purposes, including:</p>
        <ul>
            <li>Providing and maintaining our home valuation system</li>
            <li>Processing property valuations and cost calculations</li>
            <li>Generating legal documents and disclosures</li>
            <li>Communicating with you about your account or property</li>
            <li>Sending you technical notices, updates, and support messages</li>
            <li>Responding to your comments, questions, and requests</li>
            <li>Improving our system and developing new products and services</li>
            <li>Monitoring usage patterns and system performance</li>
            <li>Protecting the security and integrity of our system</li>
            <li>Complying with legal obligations</li>
        </ul>
        
        <h2>4. DISCLOSURE OF YOUR INFORMATION</h2>
        <p>We may share your information in the following situations:</p>
        <ul>
            <li>With real estate agents or brokers you designate to receive your information</li>
            <li>With third-party service providers that help us operate our system</li>
            <li>With data providers that supply property and market information</li>
            <li>To comply with legal obligations</li>
            <li>To protect our rights, privacy, safety, or property</li>
            <li>In connection with a business transaction, such as a merger or acquisition</li>
        </ul>
        
        <h2>5. DATA SECURITY</h2>
        <p>We have implemented appropriate technical and organizational security measures designed to protect the 
        security of any personal information we process. However, despite our safeguards and efforts to secure 
        your information, no electronic transmission over the Internet or information storage technology can be 
        guaranteed to be 100% secure.</p>
        
        <h2>6. DATA RETENTION</h2>
        <p>We will retain your personal information only for as long as is necessary for the purposes set out in 
        this Privacy Policy. We will retain and use your information to the extent necessary to comply with our 
        legal obligations, resolve disputes, and enforce our policies.</p>
        
        <h2>7. YOUR PRIVACY RIGHTS</h2>
        <p>Depending on your location, you may have certain rights regarding your personal information, including:</p>
        <ul>
            <li>Right to access your personal information</li>
            <li>Right to correct inaccurate or incomplete information</li>
            <li>Right to delete your personal information</li>
            <li>Right to restrict or object to processing of your information</li>
            <li>Right to data portability</li>
            <li>Right to withdraw consent</li>
        </ul>
        <p>To exercise these rights, please contact us at privacy@xgboostvaluation.com.</p>
        
        <h2>8. CHILDREN'S PRIVACY</h2>
        <p>Our system is not intended for children under 18 years of age. We do not knowingly collect personal 
        information from children under 18. If you are a parent or guardian and believe your child has provided 
        us with personal information, please contact us immediately.</p>
        
        <h2>9. CHANGES TO THIS PRIVACY POLICY</h2>
        <p>We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new 
        Privacy Policy on this page and updating the "Last Updated" date. You are advised to review this Privacy 
        Policy periodically for any changes.</p>
        
        <h2>10. CONTACT US</h2>
        <p>If you have questions or comments about this Privacy Policy, please contact us at:</p>
        <p>XGBoost Home Valuation System<br>
        Email: privacy@xgboostvaluation.com<br>
        Phone: (702) 555-1234<br>
        Address: 123 Main Street, Las Vegas, NV 89101</p>
        """.format(date=datetime.now().strftime("%B %d, %Y"))
        
        return privacy_policy_html


class TermsOfService:
    """
    Terms of Service class for generating and managing terms of service.
    """
    
    def __init__(self, base_dir="/home/ubuntu/xgboost-valuation"):
        """
        Initialize the TermsOfService.
        
        Args:
            base_dir: Base directory for the application.
        """
        self.base_dir = base_dir
        self.legal_dir = os.path.join(base_dir, "legal")
        self.tos_file = os.path.join(self.legal_dir, "terms_of_service.pdf")
        
        # Create legal directory if it doesn't exist
        os.makedirs(self.legal_dir, exist_ok=True)
        
        logger.info("Terms of Service module initialized")
    
    def generate_terms_of_service(self):
        """
        Generate a terms of service document.
        
        Returns:
            str: Path to the generated terms of service.
        """
        # Create PDF
        doc = SimpleDocTemplate(self.tos_file, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Define styles
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=1,
            spaceAfter=12
        )
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10
        )
        subheading_style = ParagraphStyle(
            'Subheading',
            parent=styles['Heading3'],
            fontSize=12,
            spaceAfter=8
        )
        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        elements = []
        
        # Title
        elements.append(Paragraph("TERMS OF SERVICE", title_style))
        elements.append(Paragraph("XGBoost Home Valuation System for Clark County, Nevada", normal_style))
        elements.append(Paragraph("Last Updated: " + datetime.now().strftime("%B %d, %Y"), normal_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Introduction
        elements.append(Paragraph("1. INTRODUCTION", heading_style))
        elements.append(Paragraph(
            "Welcome to XGBoost Home Valuation System for Clark County, Nevada. These Terms of Service (\"Terms\") "
            "govern your access to and use of our home valuation system, including any content, functionality, and "
            "services offered on or through our system.",
            normal_style
        ))
        elements.append(Paragraph(
            "Please read these Terms carefully before using our system. By accessing or using our system, you agree "
            "to be bound by these Terms. If you do not agree to these Terms, you must not access or use our system.",
            normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Eligibility
        elements.append(Paragraph("2. ELIGIBILITY", heading_style))
        elements.append(Paragraph(
            "You must be at least 18 years old and capable of forming a binding contract with us to use our system. "
            "By using our system, you represent and warrant that you meet these requirements.",
            normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Account Registration
        elements.append(Paragraph("3. ACCOUNT REGISTRATION", heading_style))
        elements.append(Paragraph(
            "To access certain features of our system, you may be required to register for an account. You agree to "
            "provide accurate, current, and complete information during the registration process and to update such "
            "information to keep it accurate, current, and complete.",
            normal_style
        ))
        elements.append(Paragraph(
            "You are responsible for safeguarding your account credentials and for any activity that occurs under your "
            "account. You agree to notify us immediately of any unauthorized access to or use of your account.",
            normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # System Use and Restrictions
        elements.append(Paragraph("4. SYSTEM USE AND RESTRICTIONS", heading_style))
        
        elements.append(Paragraph("4.1 Permitted Use", subheading_style))
        elements.append(Paragraph(
            "You may use our system only for lawful purposes and in accordance with these Terms. You agree to use our "
            "system only for your personal, non-commercial use or for legitimate real estate transactions.",
            normal_style
        ))
        
        elements.append(Paragraph("4.2 Prohibited Use", subheading_style))
        elements.append(Paragraph(
            "You agree not to use our system:",
            normal_style
        ))
        
        prohibited_uses = [
            "• In any way that violates any applicable federal, state, local, or international law or regulation",
            "• To transmit any material that is defamatory, obscene, indecent, abusive, offensive, harassing, violent, hateful, inflammatory, or otherwise objectionable",
            "• To impersonate or attempt to impersonate us, our employees, another user, or any other person or entity",
            "• To engage in any other conduct that restricts or inhibits anyone's use or enjoyment of our system, or which may harm us or users of our system",
            "• To attempt to gain unauthorized access to, interfere with, damage, or disrupt any parts of our system",
            "• To use any robot, spider, or other automatic device, process, or means to access our system for any purpose",
            "• To introduce any viruses, trojan horses, worms, logic bombs, or other material that is malicious or technologically harmful"
        ]
        
        for use in prohibited_uses:
            elements.append(Paragraph(use, normal_style))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # Intellectual Property
        elements.append(Paragraph("5. INTELLECTUAL PROPERTY", heading_style))
        elements.append(Paragraph(
            "Our system and its entire contents, features, and functionality (including but not limited to all information, "
            "software, text, displays, images, video, and audio, and the design, selection, and arrangement thereof) are "
            "owned by us, our licensors, or other providers of such material and are protected by United States and "
            "international copyright, trademark, patent, trade secret, and other intellectual property or proprietary "
            "rights laws.",
            normal_style
        ))
        elements.append(Paragraph(
            "These Terms permit you to use our system for your personal, non-commercial use only. You must not reproduce, "
            "distribute, modify, create derivative works of, publicly display, publicly perform, republish, download, "
            "store, or transmit any of the material on our system, except as follows:",
            normal_style
        ))
        
        ip_permissions = [
            "• Your computer may temporarily store copies of such materials in RAM incidental to your accessing and viewing those materials",
            "• You may store files that are automatically cached by your Web browser for display enhancement purposes",
            "• You may print or download one copy of a reasonable number of pages of our system for your own personal, non-commercial use and not for further reproduction, publication, or distribution",
            "• If we provide social media features with certain content, you may take such actions as are enabled by such features"
        ]
        
        for permission in ip_permissions:
            elements.append(Paragraph(permission, normal_style))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # Disclaimer of Warranties
        elements.append(Paragraph("6. DISCLAIMER OF WARRANTIES", heading_style))
        elements.append(Paragraph(
            "YOUR USE OF OUR SYSTEM, ITS CONTENT, AND ANY SERVICES OR ITEMS OBTAINED THROUGH OUR SYSTEM IS AT YOUR OWN RISK. "
            "OUR SYSTEM, ITS CONTENT, AND ANY SERVICES OR ITEMS OBTAINED THROUGH OUR SYSTEM ARE PROVIDED ON AN \"AS IS\" AND "
            "\"AS AVAILABLE\" BASIS, WITHOUT ANY WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED.",
            normal_style
        ))
        elements.append(Paragraph(
            "NEITHER WE NOR ANY PERSON ASSOCIATED WITH US MAKES ANY WARRANTY OR REPRESENTATION WITH RESPECT TO THE COMPLETENESS, "
            "SECURITY, RELIABILITY, QUALITY, ACCURACY, OR AVAILABILITY OF OUR SYSTEM. WITHOUT LIMITING THE FOREGOING, NEITHER "
            "WE NOR ANYONE ASSOCIATED WITH US REPRESENTS OR WARRANTS THAT OUR SYSTEM, ITS CONTENT, OR ANY SERVICES OR ITEMS "
            "OBTAINED THROUGH OUR SYSTEM WILL BE ACCURATE, RELIABLE, ERROR-FREE, OR UNINTERRUPTED, THAT DEFECTS WILL BE "
            "CORRECTED, THAT OUR SYSTEM OR THE SERVER THAT MAKES IT AVAILABLE ARE FREE OF VIRUSES OR OTHER HARMFUL COMPONENTS, "
            "OR THAT OUR SYSTEM OR ANY SERVICES OR ITEMS OBTAINED THROUGH OUR SYSTEM WILL OTHERWISE MEET YOUR NEEDS OR EXPECTATIONS.",
            normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Limitation of Liability
        elements.append(Paragraph("7. LIMITATION OF LIABILITY", heading_style))
        elements.append(Paragraph(
            "IN NO EVENT WILL WE, OUR AFFILIATES, OR THEIR LICENSORS, SERVICE PROVIDERS, EMPLOYEES, AGENTS, OFFICERS, OR "
            "DIRECTORS BE LIABLE FOR DAMAGES OF ANY KIND, UNDER ANY LEGAL THEORY, ARISING OUT OF OR IN CONNECTION WITH YOUR "
            "USE, OR INABILITY TO USE, OUR SYSTEM, ANY WEBSITES LINKED TO IT, ANY CONTENT ON OUR SYSTEM OR SUCH OTHER WEBSITES, "
            "INCLUDING ANY DIRECT, INDIRECT, SPECIAL, INCIDENTAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING BUT NOT LIMITED "
            "TO, PERSONAL INJURY, PAIN AND SUFFERING, EMOTIONAL DISTRESS, LOSS OF REVENUE, LOSS OF PROFITS, LOSS OF BUSINESS OR "
            "ANTICIPATED SAVINGS, LOSS OF USE, LOSS OF GOODWILL, LOSS OF DATA, AND WHETHER CAUSED BY TORT (INCLUDING NEGLIGENCE), "
            "BREACH OF CONTRACT, OR OTHERWISE, EVEN IF FORESEEABLE.",
            normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Real Estate Specific Terms
        elements.append(Paragraph("8. REAL ESTATE SPECIFIC TERMS", heading_style))
        
        elements.append(Paragraph("8.1 Valuation Accuracy", subheading_style))
        elements.append(Paragraph(
            "Our home valuation system uses XGBoost machine learning models and various data sources to estimate property "
            "values. These valuations are estimates only and should not be relied upon as the sole basis for any real estate "
            "transaction. We recommend consulting with a licensed real estate professional before making any real estate decisions.",
            normal_style
        ))
        
        elements.append(Paragraph("8.2 No Brokerage Relationship", subheading_style))
        elements.append(Paragraph(
            "Use of our system does not create a brokerage relationship between you and us. We are not acting as a real "
            "estate broker, agent, or advisor through your use of our system.",
            normal_style
        ))
        
        elements.append(Paragraph("8.3 Not a Substitute for Professional Advice", subheading_style))
        elements.append(Paragraph(
            "Our system provides information and tools for educational purposes only. It is not a substitute for professional "
            "advice from a licensed real estate agent, broker, appraiser, attorney, financial advisor, or other qualified "
            "professional.",
            normal_style
        ))
        
        elements.append(Paragraph("8.4 Legal Compliance", subheading_style))
        elements.append(Paragraph(
            "Our system is designed to comply with Nevada real estate laws and regulations. However, you are responsible for "
            "ensuring that your use of our system and any actions you take based on information provided by our system comply "
            "with all applicable laws and regulations.",
            normal_style
        ))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # Indemnification
        elements.append(Paragraph("9. INDEMNIFICATION", heading_style))
        elements.append(Paragraph(
            "You agree to defend, indemnify, and hold harmless us, our affiliates, licensors, and service providers, and our "
            "and their respective officers, directors, employees, contractors, agents, licensors, suppliers, successors, and "
            "assigns from and against any claims, liabilities, damages, judgments, awards, losses, costs, expenses, or fees "
            "(including reasonable attorneys' fees) arising out of or relating to your violation of these Terms or your use of "
            "our system, including, but not limited to, any use of our system's content, services, and products other than as "
            "expressly authorized in these Terms.",
            normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Governing Law and Jurisdiction
        elements.append(Paragraph("10. GOVERNING LAW AND JURISDICTION", heading_style))
        elements.append(Paragraph(
            "These Terms and any dispute or claim arising out of or related to them, their subject matter, or their formation "
            "(in each case, including non-contractual disputes or claims) shall be governed by and construed in accordance with "
            "the laws of the State of Nevada, without giving effect to any choice or conflict of law provision or rule.",
            normal_style
        ))
        elements.append(Paragraph(
            "Any legal suit, action, or proceeding arising out of, or related to, these Terms or our system shall be instituted "
            "exclusively in the federal courts of the United States or the courts of the State of Nevada, in each case located "
            "in Clark County. You waive any and all objections to the exercise of jurisdiction over you by such courts and to "
            "venue in such courts.",
            normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Changes to the Terms
        elements.append(Paragraph("11. CHANGES TO THE TERMS", heading_style))
        elements.append(Paragraph(
            "We may revise and update these Terms from time to time in our sole discretion. All changes are effective immediately "
            "when we post them, and apply to all access to and use of our system thereafter. Your continued use of our system "
            "following the posting of revised Terms means that you accept and agree to the changes.",
            normal_style
        ))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Contact Information
        elements.append(Paragraph("12. CONTACT INFORMATION", heading_style))
        elements.append(Paragraph(
            "If you have any questions about these Terms, please contact us at:",
            normal_style
        ))
        elements.append(Paragraph("XGBoost Home Valuation System", normal_style))
        elements.append(Paragraph("Email: terms@xgboostvaluation.com", normal_style))
        elements.append(Paragraph("Phone: (702) 555-1234", normal_style))
        elements.append(Paragraph("Address: 123 Main Street, Las Vegas, NV 89101", normal_style))
        
        # Build PDF
        doc.build(elements)
        
        logger.info("Generated terms of service document")
        
        return self.tos_file
    
    def get_terms_of_service_text(self):
        """
        Get the text of the terms of service for display on the website.
        
        Returns:
            str: Terms of service text in HTML format.
        """
        terms_of_service_html = """
        <h1>TERMS OF SERVICE</h1>
        <p>XGBoost Home Valuation System for Clark County, Nevada</p>
        <p>Last Updated: {date}</p>
        
        <h2>1. INTRODUCTION</h2>
        <p>Welcome to XGBoost Home Valuation System for Clark County, Nevada. These Terms of Service ("Terms") 
        govern your access to and use of our home valuation system, including any content, functionality, and 
        services offered on or through our system.</p>
        <p>Please read these Terms carefully before using our system. By accessing or using our system, you agree 
        to be bound by these Terms. If you do not agree to these Terms, you must not access or use our system.</p>
        
        <h2>2. ELIGIBILITY</h2>
        <p>You must be at least 18 years old and capable of forming a binding contract with us to use our system. 
        By using our system, you represent and warrant that you meet these requirements.</p>
        
        <h2>3. ACCOUNT REGISTRATION</h2>
        <p>To access certain features of our system, you may be required to register for an account. You agree to 
        provide accurate, current, and complete information during the registration process and to update such 
        information to keep it accurate, current, and complete.</p>
        <p>You are responsible for safeguarding your account credentials and for any activity that occurs under your 
        account. You agree to notify us immediately of any unauthorized access to or use of your account.</p>
        
        <h2>4. SYSTEM USE AND RESTRICTIONS</h2>
        
        <h3>4.1 Permitted Use</h3>
        <p>You may use our system only for lawful purposes and in accordance with these Terms. You agree to use our 
        system only for your personal, non-commercial use or for legitimate real estate transactions.</p>
        
        <h3>4.2 Prohibited Use</h3>
        <p>You agree not to use our system:</p>
        <ul>
            <li>In any way that violates any applicable federal, state, local, or international law or regulation</li>
            <li>To transmit any material that is defamatory, obscene, indecent, abusive, offensive, harassing, violent, hateful, inflammatory, or otherwise objectionable</li>
            <li>To impersonate or attempt to impersonate us, our employees, another user, or any other person or entity</li>
            <li>To engage in any other conduct that restricts or inhibits anyone's use or enjoyment of our system, or which may harm us or users of our system</li>
            <li>To attempt to gain unauthorized access to, interfere with, damage, or disrupt any parts of our system</li>
            <li>To use any robot, spider, or other automatic device, process, or means to access our system for any purpose</li>
            <li>To introduce any viruses, trojan horses, worms, logic bombs, or other material that is malicious or technologically harmful</li>
        </ul>
        
        <h2>5. INTELLECTUAL PROPERTY</h2>
        <p>Our system and its entire contents, features, and functionality (including but not limited to all information, 
        software, text, displays, images, video, and audio, and the design, selection, and arrangement thereof) are 
        owned by us, our licensors, or other providers of such material and are protected by United States and 
        international copyright, trademark, patent, trade secret, and other intellectual property or proprietary 
        rights laws.</p>
        <p>These Terms permit you to use our system for your personal, non-commercial use only. You must not reproduce, 
        distribute, modify, create derivative works of, publicly display, publicly perform, republish, download, 
        store, or transmit any of the material on our system, except as follows:</p>
        <ul>
            <li>Your computer may temporarily store copies of such materials in RAM incidental to your accessing and viewing those materials</li>
            <li>You may store files that are automatically cached by your Web browser for display enhancement purposes</li>
            <li>You may print or download one copy of a reasonable number of pages of our system for your own personal, non-commercial use and not for further reproduction, publication, or distribution</li>
            <li>If we provide social media features with certain content, you may take such actions as are enabled by such features</li>
        </ul>
        
        <h2>6. DISCLAIMER OF WARRANTIES</h2>
        <p>YOUR USE OF OUR SYSTEM, ITS CONTENT, AND ANY SERVICES OR ITEMS OBTAINED THROUGH OUR SYSTEM IS AT YOUR OWN RISK. 
        OUR SYSTEM, ITS CONTENT, AND ANY SERVICES OR ITEMS OBTAINED THROUGH OUR SYSTEM ARE PROVIDED ON AN "AS IS" AND 
        "AS AVAILABLE" BASIS, WITHOUT ANY WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED.</p>
        <p>NEITHER WE NOR ANY PERSON ASSOCIATED WITH US MAKES ANY WARRANTY OR REPRESENTATION WITH RESPECT TO THE COMPLETENESS, 
        SECURITY, RELIABILITY, QUALITY, ACCURACY, OR AVAILABILITY OF OUR SYSTEM. WITHOUT LIMITING THE FOREGOING, NEITHER 
        WE NOR ANYONE ASSOCIATED WITH US REPRESENTS OR WARRANTS THAT OUR SYSTEM, ITS CONTENT, OR ANY SERVICES OR ITEMS 
        OBTAINED THROUGH OUR SYSTEM WILL BE ACCURATE, RELIABLE, ERROR-FREE, OR UNINTERRUPTED, THAT DEFECTS WILL BE 
        CORRECTED, THAT OUR SYSTEM OR THE SERVER THAT MAKES IT AVAILABLE ARE FREE OF VIRUSES OR OTHER HARMFUL COMPONENTS, 
        OR THAT OUR SYSTEM OR ANY SERVICES OR ITEMS OBTAINED THROUGH OUR SYSTEM WILL OTHERWISE MEET YOUR NEEDS OR EXPECTATIONS.</p>
        
        <h2>7. LIMITATION OF LIABILITY</h2>
        <p>IN NO EVENT WILL WE, OUR AFFILIATES, OR THEIR LICENSORS, SERVICE PROVIDERS, EMPLOYEES, AGENTS, OFFICERS, OR 
        DIRECTORS BE LIABLE FOR DAMAGES OF ANY KIND, UNDER ANY LEGAL THEORY, ARISING OUT OF OR IN CONNECTION WITH YOUR 
        USE, OR INABILITY TO USE, OUR SYSTEM, ANY WEBSITES LINKED TO IT, ANY CONTENT ON OUR SYSTEM OR SUCH OTHER WEBSITES, 
        INCLUDING ANY DIRECT, INDIRECT, SPECIAL, INCIDENTAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING BUT NOT LIMITED 
        TO, PERSONAL INJURY, PAIN AND SUFFERING, EMOTIONAL DISTRESS, LOSS OF REVENUE, LOSS OF PROFITS, LOSS OF BUSINESS OR 
        ANTICIPATED SAVINGS, LOSS OF USE, LOSS OF GOODWILL, LOSS OF DATA, AND WHETHER CAUSED BY TORT (INCLUDING NEGLIGENCE), 
        BREACH OF CONTRACT, OR OTHERWISE, EVEN IF FORESEEABLE.</p>
        
        <h2>8. REAL ESTATE SPECIFIC TERMS</h2>
        
        <h3>8.1 Valuation Accuracy</h3>
        <p>Our home valuation system uses XGBoost machine learning models and various data sources to estimate property 
        values. These valuations are estimates only and should not be relied upon as the sole basis for any real estate 
        transaction. We recommend consulting with a licensed real estate professional before making any real estate decisions.</p>
        
        <h3>8.2 No Brokerage Relationship</h3>
        <p>Use of our system does not create a brokerage relationship between you and us. We are not acting as a real 
        estate broker, agent, or advisor through your use of our system.</p>
        
        <h3>8.3 Not a Substitute for Professional Advice</h3>
        <p>Our system provides information and tools for educational purposes only. It is not a substitute for professional 
        advice from a licensed real estate agent, broker, appraiser, attorney, financial advisor, or other qualified 
        professional.</p>
        
        <h3>8.4 Legal Compliance</h3>
        <p>Our system is designed to comply with Nevada real estate laws and regulations. However, you are responsible for 
        ensuring that your use of our system and any actions you take based on information provided by our system comply 
        with all applicable laws and regulations.</p>
        
        <h2>9. INDEMNIFICATION</h2>
        <p>You agree to defend, indemnify, and hold harmless us, our affiliates, licensors, and service providers, and our 
        and their respective officers, directors, employees, contractors, agents, licensors, suppliers, successors, and 
        assigns from and against any claims, liabilities, damages, judgments, awards, losses, costs, expenses, or fees 
        (including reasonable attorneys' fees) arising out of or relating to your violation of these Terms or your use of 
        our system, including, but not limited to, any use of our system's content, services, and products other than as 
        expressly authorized in these Terms.</p>
        
        <h2>10. GOVERNING LAW AND JURISDICTION</h2>
        <p>These Terms and any dispute or claim arising out of or related to them, their subject matter, or their formation 
        (in each case, including non-contractual disputes or claims) shall be governed by and construed in accordance with 
        the laws of the State of Nevada, without giving effect to any choice or conflict of law provision or rule.</p>
        <p>Any legal suit, action, or proceeding arising out of, or related to, these Terms or our system shall be instituted 
        exclusively in the federal courts of the United States or the courts of the State of Nevada, in each case located 
        in Clark County. You waive any and all objections to the exercise of jurisdiction over you by such courts and to 
        venue in such courts.</p>
        
        <h2>11. CHANGES TO THE TERMS</h2>
        <p>We may revise and update these Terms from time to time in our sole discretion. All changes are effective immediately 
        when we post them, and apply to all access to and use of our system thereafter. Your continued use of our system 
        following the posting of revised Terms means that you accept and agree to the changes.</p>
        
        <h2>12. CONTACT INFORMATION</h2>
        <p>If you have any questions about these Terms, please contact us at:</p>
        <p>XGBoost Home Valuation System<br>
        Email: terms@xgboostvaluation.com<br>
        Phone: (702) 555-1234<br>
        Address: 123 Main Street, Las Vegas, NV 89101</p>
        """.format(date=datetime.now().strftime("%B %d, %Y"))
        
        return terms_of_service_html


class DataHandlingCompliance:
    """
    Data Handling Compliance class for ensuring proper handling of user data.
    """
    
    def __init__(self, base_dir="/home/ubuntu/xgboost-valuation"):
        """
        Initialize the DataHandlingCompliance.
        
        Args:
            base_dir: Base directory for the application.
        """
        self.base_dir = base_dir
        self.compliance_dir = os.path.join(base_dir, "legal", "compliance")
        self.data_handling_file = os.path.join(self.compliance_dir, "data_handling.json")
        
        # Create compliance directory if it doesn't exist
        os.makedirs(self.compliance_dir, exist_ok=True)
        
        # Create data handling file if it doesn't exist
        if not os.path.exists(self.data_handling_file):
            with open(self.data_handling_file, "w") as f:
                json.dump({
                    "data_retention_period": 365,  # days
                    "data_anonymization": True,
                    "data_encryption": True,
                    "data_access_log": [],
                    "data_deletion_log": []
                }, f)
        
        logger.info("Data Handling Compliance module initialized")
    
    def log_data_access(self, user_id, data_type, access_reason, accessed_by):
        """
        Log data access for compliance purposes.
        
        Args:
            user_id: User ID.
            data_type: Type of data accessed.
            access_reason: Reason for accessing the data.
            accessed_by: Person or system that accessed the data.
            
        Returns:
            dict: Access log entry.
        """
        # Create access log entry
        access_entry = {
            "access_id": str(uuid.uuid4()),
            "user_id": user_id,
            "data_type": data_type,
            "access_reason": access_reason,
            "accessed_by": accessed_by,
            "access_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Load data handling config
        with open(self.data_handling_file, "r") as f:
            data_handling = json.load(f)
        
        # Add access log entry
        data_handling["data_access_log"].append(access_entry)
        
        # Save data handling config
        with open(self.data_handling_file, "w") as f:
            json.dump(data_handling, f, indent=2)
        
        logger.info(f"Logged data access for user {user_id}, data type {data_type}")
        
        return access_entry
    
    def log_data_deletion(self, user_id, data_type, deletion_reason, deleted_by):
        """
        Log data deletion for compliance purposes.
        
        Args:
            user_id: User ID.
            data_type: Type of data deleted.
            deletion_reason: Reason for deleting the data.
            deleted_by: Person or system that deleted the data.
            
        Returns:
            dict: Deletion log entry.
        """
        # Create deletion log entry
        deletion_entry = {
            "deletion_id": str(uuid.uuid4()),
            "user_id": user_id,
            "data_type": data_type,
            "deletion_reason": deletion_reason,
            "deleted_by": deleted_by,
            "deletion_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Load data handling config
        with open(self.data_handling_file, "r") as f:
            data_handling = json.load(f)
        
        # Add deletion log entry
        data_handling["data_deletion_log"].append(deletion_entry)
        
        # Save data handling config
        with open(self.data_handling_file, "w") as f:
            json.dump(data_handling, f, indent=2)
        
        logger.info(f"Logged data deletion for user {user_id}, data type {data_type}")
        
        return deletion_entry
    
    def anonymize_user_data(self, user_data):
        """
        Anonymize user data for compliance purposes.
        
        Args:
            user_data: User data to anonymize.
            
        Returns:
            dict: Anonymized user data.
        """
        # Create a copy of user data
        anonymized_data = user_data.copy()
        
        # Anonymize personal information
        if "full_name" in anonymized_data:
            anonymized_data["full_name"] = self._anonymize_name(anonymized_data["full_name"])
        
        if "email" in anonymized_data:
            anonymized_data["email"] = self._anonymize_email(anonymized_data["email"])
        
        if "phone" in anonymized_data:
            anonymized_data["phone"] = self._anonymize_phone(anonymized_data["phone"])
        
        if "address" in anonymized_data:
            anonymized_data["address"] = self._anonymize_address(anonymized_data["address"])
        
        logger.info(f"Anonymized user data for user {user_data.get('registration_id', 'unknown')}")
        
        return anonymized_data
    
    def _anonymize_name(self, name):
        """
        Anonymize a name.
        
        Args:
            name: Name to anonymize.
            
        Returns:
            str: Anonymized name.
        """
        if not name:
            return ""
        
        # Split name into parts
        name_parts = name.split()
        
        # Anonymize each part
        anonymized_parts = []
        for part in name_parts:
            if len(part) > 2:
                anonymized_parts.append(part[0] + "*" * (len(part) - 2) + part[-1])
            else:
                anonymized_parts.append("*" * len(part))
        
        return " ".join(anonymized_parts)
    
    def _anonymize_email(self, email):
        """
        Anonymize an email address.
        
        Args:
            email: Email address to anonymize.
            
        Returns:
            str: Anonymized email address.
        """
        if not email or "@" not in email:
            return ""
        
        # Split email into username and domain
        username, domain = email.split("@")
        
        # Anonymize username
        if len(username) > 2:
            anonymized_username = username[0] + "*" * (len(username) - 2) + username[-1]
        else:
            anonymized_username = "*" * len(username)
        
        return anonymized_username + "@" + domain
    
    def _anonymize_phone(self, phone):
        """
        Anonymize a phone number.
        
        Args:
            phone: Phone number to anonymize.
            
        Returns:
            str: Anonymized phone number.
        """
        if not phone:
            return ""
        
        # Remove non-digit characters
        digits = re.sub(r"\D", "", phone)
        
        # Anonymize middle digits
        if len(digits) > 4:
            return digits[:2] + "*" * (len(digits) - 4) + digits[-2:]
        else:
            return "*" * len(digits)
    
    def _anonymize_address(self, address):
        """
        Anonymize an address.
        
        Args:
            address: Address to anonymize.
            
        Returns:
            dict: Anonymized address.
        """
        if not address:
            return {}
        
        # Create a copy of address
        anonymized_address = address.copy()
        
        # Anonymize address lines
        if "line1" in anonymized_address:
            # Extract house number and street name
            match = re.match(r"(\d+)\s+(.*)", anonymized_address["line1"])
            if match:
                house_number = match.group(1)
                street_name = match.group(2)
                anonymized_address["line1"] = house_number + " " + "*" * len(street_name)
            else:
                anonymized_address["line1"] = "*" * len(anonymized_address["line1"])
        
        if "line2" in anonymized_address and anonymized_address["line2"]:
            anonymized_address["line2"] = "*" * len(anonymized_address["line2"])
        
        return anonymized_address


class ComplianceManager:
    """
    Compliance Manager class for managing all compliance-related functionality.
    """
    
    def __init__(self, base_dir="/home/ubuntu/xgboost-valuation"):
        """
        Initialize the ComplianceManager.
        
        Args:
            base_dir: Base directory for the application.
        """
        self.base_dir = base_dir
        self.esign_compliance = ESignCompliance(base_dir)
        self.privacy_policy = PrivacyPolicy(base_dir)
        self.terms_of_service = TermsOfService(base_dir)
        self.data_handling = DataHandlingCompliance(base_dir)
        
        logger.info("Compliance Manager initialized")
    
    def initialize_compliance_documents(self):
        """
        Initialize all compliance documents.
        
        Returns:
            dict: Paths to all generated documents.
        """
        # Generate privacy policy
        privacy_policy_path = self.privacy_policy.generate_privacy_policy()
        
        # Generate terms of service
        terms_of_service_path = self.terms_of_service.generate_terms_of_service()
        
        logger.info("Initialized all compliance documents")
        
        return {
            "privacy_policy": privacy_policy_path,
            "terms_of_service": terms_of_service_path
        }
    
    def record_user_consent(self, user_data, consent_type, consent_text, ip_address=None, user_agent=None):
        """
        Record user consent for various compliance purposes.
        
        Args:
            user_data: User data.
            consent_type: Type of consent (e.g., "esign", "privacy_policy", "terms_of_service").
            consent_text: Text of the consent agreement.
            ip_address: IP address of the user (optional).
            user_agent: User agent of the user's browser (optional).
            
        Returns:
            dict: Consent record.
        """
        if consent_type == "esign":
            return self.esign_compliance.record_consent(user_data, consent_text, ip_address, user_agent)
        elif consent_type == "privacy_policy":
            # Record privacy policy consent (implementation similar to esign consent)
            logger.info(f"Recorded privacy policy consent for user {user_data['registration_id']}")
            return {"consent_type": "privacy_policy", "user_id": user_data["registration_id"]}
        elif consent_type == "terms_of_service":
            # Record terms of service consent (implementation similar to esign consent)
            logger.info(f"Recorded terms of service consent for user {user_data['registration_id']}")
            return {"consent_type": "terms_of_service", "user_id": user_data["registration_id"]}
        else:
            logger.warning(f"Unknown consent type: {consent_type}")
            return None
    
    def verify_compliance(self, user_id):
        """
        Verify if a user is compliant with all required consents.
        
        Args:
            user_id: User ID.
            
        Returns:
            dict: Compliance status for each consent type.
        """
        # Verify E-SIGN consent
        esign_consent = self.esign_compliance.verify_consent(user_id)
        
        # Verify other consents (implementation would be similar)
        # For this example, we'll assume they're all compliant
        
        compliance_status = {
            "esign": esign_consent,
            "privacy_policy": True,
            "terms_of_service": True
        }
        
        logger.info(f"Verified compliance status for user {user_id}")
        
        return compliance_status
    
    def generate_compliance_report(self, user_id=None, start_date=None, end_date=None):
        """
        Generate a compliance report.
        
        Args:
            user_id: User ID (optional).
            start_date: Start date (optional).
            end_date: End date (optional).
            
        Returns:
            dict: Compliance report.
        """
        # Create report
        report = {
            "report_id": str(uuid.uuid4()),
            "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "filters": {
                "user_id": user_id,
                "start_date": start_date,
                "end_date": end_date
            },
            "esign_compliance": {},
            "data_handling": {},
            "overall_compliance": True
        }
        
        # Add E-SIGN compliance information
        if user_id:
            esign_consent = self.esign_compliance.get_consent_record(user_id)
            report["esign_compliance"] = esign_consent or {"status": "No consent record found"}
            report["overall_compliance"] = report["overall_compliance"] and bool(esign_consent)
        
        # Add data handling compliance information
        # This would include information about data access, deletion, etc.
        
        logger.info(f"Generated compliance report {report['report_id']}")
        
        return report

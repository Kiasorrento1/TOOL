#!/usr/bin/env python3
"""
Main application for the XGBoost Home Valuation System for Clark County, Nevada.
This script serves as the entry point for the application.
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules from the project
from api import zillow_api, clark_county_api, census_api, lvmpd_api, greatschools_api, economic_api
from models import xgboost_model
from legal import document_generation, compliance
from utils import config, data_utils

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("xgboost_valuation.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("main")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='XGBoost Home Valuation System for Clark County, Nevada')
    parser.add_argument('--mode', choices=['buyer', 'seller', 'both'], default='both',
                        help='Application mode: buyer, seller, or both')
    parser.add_argument('--port', type=int, default=8000,
                        help='Port to run the application on')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode')
    parser.add_argument('--config', type=str, default='config.json',
                        help='Path to configuration file')
    return parser.parse_args()

def initialize_apis(config_data):
    """Initialize all API clients."""
    logger.info("Initializing API clients...")
    
    # Initialize Zillow API
    zillow_client = zillow_api.ZillowAPI(
        api_key=config_data.get('zillow_api_key', ''),
        base_url=config_data.get('zillow_api_url', '')
    )
    
    # Initialize Clark County Assessor API
    clark_county_client = clark_county_api.ClarkCountyAPI(
        api_key=config_data.get('clark_county_api_key', ''),
        base_url=config_data.get('clark_county_api_url', '')
    )
    
    # Initialize Census Bureau API
    census_client = census_api.CensusAPI(
        api_key=config_data.get('census_api_key', ''),
        base_url=config_data.get('census_api_url', '')
    )
    
    # Initialize LVMPD API
    lvmpd_client = lvmpd_api.LVMPDAPI(
        api_key=config_data.get('lvmpd_api_key', ''),
        base_url=config_data.get('lvmpd_api_url', '')
    )
    
    # Initialize GreatSchools API
    greatschools_client = greatschools_api.GreatSchoolsAPI(
        api_key=config_data.get('greatschools_api_key', ''),
        base_url=config_data.get('greatschools_api_url', '')
    )
    
    # Initialize Economic API
    economic_client = economic_api.EconomicAPI(
        fred_api_key=config_data.get('fred_api_key', ''),
        bls_api_key=config_data.get('bls_api_key', ''),
        base_url=config_data.get('economic_api_url', '')
    )
    
    logger.info("API clients initialized successfully")
    
    return {
        'zillow': zillow_client,
        'clark_county': clark_county_client,
        'census': census_client,
        'lvmpd': lvmpd_client,
        'greatschools': greatschools_client,
        'economic': economic_client
    }

def initialize_models(config_data):
    """Initialize XGBoost models."""
    logger.info("Initializing XGBoost models...")
    
    # Initialize model for single family homes
    single_family_model = xgboost_model.XGBoostValuationModel(
        model_type='single_family',
        model_path=config_data.get('single_family_model_path', ''),
        feature_config=config_data.get('single_family_feature_config', {}),
        hyperparameters=config_data.get('single_family_hyperparameters', {})
    )
    
    # Initialize model for condos
    condo_model = xgboost_model.XGBoostValuationModel(
        model_type='condo',
        model_path=config_data.get('condo_model_path', ''),
        feature_config=config_data.get('condo_feature_config', {}),
        hyperparameters=config_data.get('condo_hyperparameters', {})
    )
    
    # Initialize model for townhouses
    townhouse_model = xgboost_model.XGBoostValuationModel(
        model_type='townhouse',
        model_path=config_data.get('townhouse_model_path', ''),
        feature_config=config_data.get('townhouse_feature_config', {}),
        hyperparameters=config_data.get('townhouse_hyperparameters', {})
    )
    
    logger.info("XGBoost models initialized successfully")
    
    return {
        'single_family': single_family_model,
        'condo': condo_model,
        'townhouse': townhouse_model
    }

def initialize_legal_components(config_data):
    """Initialize legal components."""
    logger.info("Initializing legal components...")
    
    # Initialize document generator
    document_generator = document_generation.DocumentGenerator(
        templates_dir=config_data.get('templates_dir', ''),
        output_dir=config_data.get('output_dir', '')
    )
    
    # Initialize compliance manager
    compliance_manager = compliance.ComplianceManager(
        base_dir=config_data.get('base_dir', '')
    )
    
    # Initialize compliance documents
    compliance_manager.initialize_compliance_documents()
    
    logger.info("Legal components initialized successfully")
    
    return {
        'document_generator': document_generator,
        'compliance_manager': compliance_manager
    }

def start_application(args, apis, models, legal_components):
    """Start the application based on the specified mode."""
    logger.info(f"Starting application in {args.mode} mode on port {args.port}...")
    
    if args.mode in ['buyer', 'both']:
        # Start buyer portal
        logger.info("Starting buyer portal...")
        # Implementation would start the buyer portal web application
        
    if args.mode in ['seller', 'both']:
        # Start seller portal
        logger.info("Starting seller portal...")
        # Implementation would start the seller portal web application
    
    logger.info(f"Application started successfully in {args.mode} mode on port {args.port}")

def main():
    """Main entry point for the application."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Load configuration
    config_data = config.load_config(args.config)
    
    # Set logging level based on debug flag
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize components
    apis = initialize_apis(config_data)
    models = initialize_models(config_data)
    legal_components = initialize_legal_components(config_data)
    
    # Start the application
    start_application(args, apis, models, legal_components)

if __name__ == "__main__":
    main()

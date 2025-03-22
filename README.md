# XGBoost Home Valuation System - Documentation

## Overview

This documentation provides comprehensive information about the XGBoost Home Valuation System for Clark County, Nevada. The system uses machine learning with XGBoost to provide accurate home valuations, cost of ownership calculations, and market trend analysis for both buyers and sellers.

## System Architecture

The system is organized into the following components:

1. **Data Integration APIs**: Modules for integrating with various data sources including Zillow, Clark County Assessor, Census Bureau, LVMPD, GreatSchools, and economic indicators.

2. **XGBoost Models**: Machine learning models for different property types (single family, condo, townhouse) that provide accurate valuations with confidence intervals.

3. **User Interfaces**: Separate portals for buyers and sellers, with a multi-step registration process.

4. **Document Generation**: System for generating Nevada-specific real estate disclosure forms and other legal documents.

5. **Legal Compliance**: Features to ensure compliance with E-SIGN Act, privacy regulations, and real estate laws.

## Installation and Setup

### Prerequisites

- Python 3.8 or higher
- pip package manager
- PostgreSQL database (for storing user data and property information)
- API keys for all data sources

### Installation Steps

1. Clone the repository or extract the provided ZIP file:
   ```
   git clone https://github.com/your-username/xgboost-valuation.git
   cd xgboost-valuation
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up the configuration file:
   - Copy `config.example.json` to `config.json`
   - Edit `config.json` to include your API keys and database connection information

4. Initialize the database:
   ```
   python scripts/init_db.py
   ```

5. Start the application:
   ```
   python main.py --mode both --port 8000
   ```

## Configuration

The system is configured through the `config.json` file, which includes:

- API keys for all data sources
- Database connection information
- Model paths and hyperparameters
- Legal document templates directory
- Output directory for generated documents

Example configuration:

```json
{
  "zillow_api_key": "your-zillow-api-key",
  "zillow_api_url": "https://api.bridgeinteractive.com/v2/",
  "clark_county_api_key": "your-clark-county-api-key",
  "clark_county_api_url": "https://opendata-clarkcountynv.hub.arcgis.com/api/",
  "census_api_key": "your-census-api-key",
  "census_api_url": "https://api.census.gov/data/",
  "lvmpd_api_key": "your-lvmpd-api-key",
  "lvmpd_api_url": "https://lvmpd.com/api/",
  "greatschools_api_key": "your-greatschools-api-key",
  "greatschools_api_url": "https://api.greatschools.org/",
  "fred_api_key": "your-fred-api-key",
  "bls_api_key": "your-bls-api-key",
  "economic_api_url": "https://api.stlouisfed.org/fred/",
  "database_host": "localhost",
  "database_port": 5432,
  "database_name": "xgboost_valuation",
  "database_user": "postgres",
  "database_password": "your-password",
  "single_family_model_path": "models/single_family_model.json",
  "condo_model_path": "models/condo_model.json",
  "townhouse_model_path": "models/townhouse_model.json",
  "single_family_feature_config": {
    "feature_list": ["sqft", "bedrooms", "bathrooms", "lot_size", "year_built", "pool", "garage", "school_rating", "crime_rate", "median_income"]
  },
  "condo_feature_config": {
    "feature_list": ["sqft", "bedrooms", "bathrooms", "floor", "year_built", "hoa_fee", "amenities", "school_rating", "crime_rate", "median_income"]
  },
  "townhouse_feature_config": {
    "feature_list": ["sqft", "bedrooms", "bathrooms", "lot_size", "year_built", "hoa_fee", "garage", "school_rating", "crime_rate", "median_income"]
  },
  "single_family_hyperparameters": {
    "max_depth": 6,
    "learning_rate": 0.1,
    "n_estimators": 100,
    "objective": "reg:squarederror",
    "booster": "gbtree",
    "subsample": 0.8,
    "colsample_bytree": 0.8
  },
  "condo_hyperparameters": {
    "max_depth": 5,
    "learning_rate": 0.1,
    "n_estimators": 100,
    "objective": "reg:squarederror",
    "booster": "gbtree",
    "subsample": 0.8,
    "colsample_bytree": 0.8
  },
  "townhouse_hyperparameters": {
    "max_depth": 6,
    "learning_rate": 0.1,
    "n_estimators": 100,
    "objective": "reg:squarederror",
    "booster": "gbtree",
    "subsample": 0.8,
    "colsample_bytree": 0.8
  },
  "templates_dir": "legal/templates",
  "output_dir": "legal/output",
  "base_dir": "/path/to/xgboost-valuation"
}
```

## Data Integration

### Zillow Bridge API

The system integrates with the Zillow Bridge API to obtain property details and Zestimates. The `ZillowAPI` class in `api/zillow_api.py` provides methods for:

- Getting property details by address
- Searching for properties by criteria
- Getting Zestimates for properties
- Getting comparable properties

### Clark County Assessor API

The system integrates with the Clark County Assessor's data for tax records. The `ClarkCountyAPI` class in `api/clark_county_api.py` provides methods for:

- Getting property tax records by APN (Assessor's Parcel Number)
- Getting property ownership information
- Getting property valuation history
- Getting tax rate information

### Census Bureau API

The system integrates with the Census Bureau API for demographic data. The `CensusAPI` class in `api/census_api.py` provides methods for:

- Getting demographic data for a specific area (using FIPS code 32003 for Clark County)
- Getting migration patterns
- Getting income and employment data
- Getting housing statistics

### LVMPD API

The system integrates with the Las Vegas Metropolitan Police Department (LVMPD) API for crime statistics. The `LVMPDAPI` class in `api/lvmpd_api.py` provides methods for:

- Getting crime statistics by area
- Getting crime trends over time
- Getting crime types and frequencies
- Getting safety ratings for neighborhoods

### GreatSchools API

The system integrates with the GreatSchools.org API for education quality metrics. The `GreatSchoolsAPI` class in `api/greatschools_api.py` provides methods for:

- Getting school ratings by location
- Getting school details
- Getting school district boundaries
- Getting school comparison data

### Economic API

The system integrates with FRED/BLS data for economic indicators. The `EconomicAPI` class in `api/economic_api.py` provides methods for:

- Getting interest rates
- Getting unemployment rates
- Getting economic forecasts
- Getting housing market trends

## XGBoost Model Architecture

The system uses XGBoost for machine learning models that provide accurate home valuations. The `XGBoostValuationModel` class in `models/xgboost_model.py` implements:

### Feature Engineering

The system performs feature engineering using data from all integrated sources:

- Property characteristics (size, bedrooms, bathrooms, etc.)
- Location features (neighborhood, school district, crime rate, etc.)
- Economic indicators (interest rates, unemployment, etc.)
- Market trends (absorption rates, days on market, etc.)

### Hyperparameter Tuning

The system uses cross-validation to tune hyperparameters for optimal performance:

- Learning rate
- Maximum depth
- Number of estimators
- Subsample ratio
- Column sample ratio
- Regularization parameters

### Model Training

The system trains separate models for different property types:

- Single family homes
- Condos
- Townhouses

### Confidence Intervals

The system generates confidence intervals for valuations using:

- Quantile regression
- Bootstrap sampling
- Prediction intervals

### Feature Importance Analysis

The system provides feature importance analysis for explainability:

- SHAP (SHapley Additive exPlanations) values
- Feature importance plots
- Feature contribution breakdowns

## User Interfaces

### Seller Portal

The seller portal provides a comprehensive valuation dashboard showing:

- Estimated market value with confidence intervals
- Comparable properties analysis
- Neighborhood trend visualization
- Value drivers breakdown (property features impact)
- Historical price appreciation chart

### Buyer Portal

The buyer portal provides a total cost of ownership calculator including:

- Mortgage payment projections
- Property tax estimates
- HOA fees when applicable
- Insurance cost estimates
- Maintenance cost projections
- Equity building visualization over time
- Appreciation/depreciation scenarios
- Monthly/annual expense breakdown

### Registration System

The system implements a multi-step registration process:

1. Basic information collection:
   - Full legal name
   - Email address (verified)
   - Phone number
   - Marital status (single, married, divorced)
   - Current address

2. Identity verification:
   - Property ownership declaration
   - Legal acknowledgment of accuracy under penalty of perjury
   - Electronic signature capability
   - State-specific disclosure acceptance

3. Agent notification system:
   - Automatic forwarding of completed forms to agent email
   - Configurable recipient list for team scenarios
   - PDF generation of all signed documents
   - Activity timestamp and audit trail

## Document Generation

The system generates Nevada-specific real estate disclosure forms and other legal documents. The `DocumentGenerator` class in `legal/document_generation.py` provides methods for:

- Generating registration confirmation
- Generating Nevada real estate disclosure forms
- Generating lead-based paint disclosure
- Generating listing agreements
- Generating buyer brokerage agreements

## Legal Compliance

The system ensures compliance with various legal requirements. The `ComplianceManager` class in `legal/compliance.py` manages:

### E-SIGN Act Compliance

The `ESignCompliance` class ensures compliance with the Electronic Signatures in Global and National Commerce Act:

- Recording user consent to use electronic signatures
- Verifying consent before allowing electronic signatures
- Generating consent forms
- Maintaining audit trails of consent

### Privacy Policy

The `PrivacyPolicy` class manages the system's privacy policy:

- Generating privacy policy documents
- Providing privacy policy text for display
- Ensuring compliance with privacy regulations

### Terms of Service

The `TermsOfService` class manages the system's terms of service:

- Generating terms of service documents
- Providing terms of service text for display
- Ensuring compliance with legal requirements

### Data Handling Compliance

The `DataHandlingCompliance` class ensures proper handling of user data:

- Logging data access for compliance purposes
- Logging data deletion for compliance purposes
- Anonymizing user data when necessary
- Implementing data retention policies

## API Reference

### Zillow API

```python
from api.zillow_api import ZillowAPI

# Initialize the API
zillow_api = ZillowAPI(api_key="your-api-key", base_url="https://api.bridgeinteractive.com/v2/")

# Get property details by address
property_details = zillow_api.get_property_by_address(
    address="123 Main St",
    city="Las Vegas",
    state="NV",
    zip_code="89101"
)

# Get Zestimate for a property
zestimate = zillow_api.get_zestimate(zpid="12345678")

# Search for properties by criteria
properties = zillow_api.search_properties(
    city="Las Vegas",
    state="NV",
    min_price=300000,
    max_price=500000,
    min_bedrooms=3,
    min_bathrooms=2
)

# Get comparable properties
comps = zillow_api.get_comps(zpid="12345678", count=10)
```

### XGBoost Valuation Model

```python
from models.xgboost_model import XGBoostValuationModel

# Initialize the model
model = XGBoostValuationModel(
    model_type="single_family",
    model_path="models/single_family_model.json",
    feature_config={
        "feature_list": ["sqft", "bedrooms", "bathrooms", "lot_size", "year_built", "pool", "garage", "school_rating", "crime_rate", "median_income"]
    },
    hyperparameters={
        "max_depth": 6,
        "learning_rate": 0.1,
        "n_estimators": 100,
        "objective": "reg:squarederror",
        "booster": "gbtree",
        "subsample": 0.8,
        "colsample_bytree": 0.8
    }
)

# Train the model
model.train(X_train, y_train)

# Make a prediction with confidence interval
prediction, confidence_interval = model.predict_with_confidence(
    property_features={
        "sqft": 2000,
        "bedrooms": 3,
        "bathrooms": 2,
        "lot_size": 7500,
        "year_built": 2005,
        "pool": 1,
        "garage": 2,
        "school_rating": 8,
        "crime_rate": 2.5,
        "median_income": 75000
    }
)

# Get feature importance
feature_importance = model.get_feature_importance()

# Save the model
model.save("models/updated_single_family_model.json")
```

### Document Generator

```python
from legal.document_generation import DocumentGenerator

# Initialize the document generator
doc_generator = DocumentGenerator(
    templates_dir="legal/templates",
    output_dir="legal/output"
)

# Generate a registration confirmation
registration_confirmation = doc_generator.generate_registration_confirmation(
    user_data={
        "registration_id": "REG12345",
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "702-555-1234",
        "marital_status": "married",
        "address": {
            "line1": "123 Main St",
            "line2": "Apt 4B",
            "city": "Las Vegas",
            "state": "NV",
            "zip": "89101"
        },
        "registration_date": "2025-03-21"
    }
)

# Generate a listing agreement
listing_agreement = doc_generator.generate_listing_agreement(
    user_data={
        "registration_id": "REG12345",
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "702-555-1234"
    },
    property_data={
        "address": "123 Main St, Las Vegas, NV 89101",
        "listing_price": 450000,
        "listing_period": 90,
        "commission_rate": 6.0
    },
    agent_data={
        "name": "Jane Smith",
        "license_number": "NV12345",
        "brokerage": "ABC Realty",
        "email": "jane.smith@abcrealty.com",
        "phone": "702-555-5678"
    }
)
```

### Compliance Manager

```python
from legal.compliance import ComplianceManager

# Initialize the compliance manager
compliance_manager = ComplianceManager(base_dir="/path/to/xgboost-valuation")

# Initialize compliance documents
documents = compliance_manager.initialize_compliance_documents()

# Record user consent
consent_record = compliance_manager.record_user_consent(
    user_data={
        "registration_id": "REG12345",
        "full_name": "John Doe",
        "email": "john.doe@example.com"
    },
    consent_type="esign",
    consent_text="I agree to use electronic signatures for documents related to my real estate transaction.",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)

# Verify compliance
compliance_status = compliance_manager.verify_compliance(user_id="REG12345")

# Generate compliance report
report = compliance_manager.generate_compliance_report(
    user_id="REG12345",
    start_date="2025-01-01",
    end_date="2025-03-31"
)
```

## Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Check your API keys in the configuration file
   - Verify your internet connection
   - Check if the API service is available

2. **Database Connection Issues**
   - Verify database credentials in the configuration file
   - Ensure the PostgreSQL service is running
   - Check database permissions

3. **Model Training Errors**
   - Ensure you have sufficient data for training
   - Check feature engineering pipeline for errors
   - Verify hyperparameter settings

### Logging

The system uses Python's logging module to log information, warnings, and errors. Log files are stored in the root directory:

- `xgboost_valuation.log`: Main application log
- `legal_compliance.log`: Legal compliance log

## Maintenance and Updates

### Model Retraining

The XGBoost models should be retrained regularly to maintain accuracy:

1. Collect new property data
2. Update feature engineering pipeline if necessary
3. Retrain models using the `train` method
4. Evaluate model performance
5. Save updated models

### API Key Rotation

For security, API keys should be rotated periodically:

1. Obtain new API keys from the respective services
2. Update the configuration file with the new keys
3. Restart the application

### Database Backup

Regular database backups are recommended:

```
pg_dump -U postgres -d xgboost_valuation > backup_$(date +%Y%m%d).sql
```

## Support and Contact

For support or questions about the XGBoost Home Valuation System, please contact:

- Email: support@xgboostvaluation.com
- Phone: (702) 555-1234
- Address: 123 Main Street, Las Vegas, NV 89101

import random
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import streamlit as st

VENDOR_NAMES = [
    "Super Steel Traders", "Reliable Logistics Pvt Ltd", "ABC Suppliers & Co", 
    "Quick Dispatch Services", "Global Import Export", "Metro Hardware Store",
    "Elite Manufacturing Ltd", "Premium Parts Suppliers", "Swift Cargo Services",
    "National Trading Company", "Golden Enterprises", "Silver Line Distributors",
    "Diamond Tools & Equipment", "Platinum Logistics", "Ruby Traders",
    "Sapphire Solutions Pvt Ltd", "Emerald Exports", "Pearl Industries",
    "Crystal Clear Suppliers", "Mega Wholesale Trading"
]

ADDRESS_TYPES = ['Registered Office', 'Factory', 'Warehouse', 'Rented Room', 'Virtual Office', 'Residential']

def generate_gstin():
    state_code = random.choice(['27', '29', '07', '19', '24', '09', '33', '06', '22', '23'])
    pan = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=5)) + ''.join(random.choices('0123456789', k=4)) + random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    entity = random.randint(1, 9)
    checksum = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    return f"{state_code}{pan}{entity}{checksum}"

def generate_mock_vendors(count=15):
    vendors = []
    
    for i in range(count):
        vendor = {
            'name': random.choice(VENDOR_NAMES) if i < len(VENDOR_NAMES) else f"Vendor {i+1}",
            'gstin': generate_gstin(),
            'registration_days': random.randint(5, 1500),
            'address_type': random.choice(ADDRESS_TYPES),
            'director_companies': random.randint(1, 50),
            'gstr1_status': random.choice(['Filed', 'Not Filed', 'Nil Return']),
            'gstr3b_status': random.choice(['Filed', 'Not Filed', 'Delayed']),
            'months_not_filed': random.randint(0, 6),
            'transaction_count': random.randint(5, 200),
            'itc_amount': random.randint(10000, 5000000),
            'cash_payments': random.randint(0, 100000),
        }
        
        vendor['risk_score'], vendor['risk_factors'] = calculate_vendor_risk_score(vendor)
        vendor['risk_level'] = get_risk_level(vendor['risk_score'])
        
        vendors.append(vendor)
    
    vendors = sorted(vendors, key=lambda x: x['risk_score'], reverse=True)
    
    return vendors

def calculate_vendor_risk_score(vendor):
    score = 0
    risk_factors = []
    
    if vendor['registration_days'] < 30:
        score += 35
        risk_factors.append(f"Recently registered ({vendor['registration_days']} days old) - High risk of fraudulent entity")
    elif vendor['registration_days'] < 90:
        score += 25
        risk_factors.append(f"New vendor ({vendor['registration_days']} days old) - Requires enhanced due diligence")
    elif vendor['registration_days'] < 180:
        score += 10
        risk_factors.append(f"Relatively new vendor ({vendor['registration_days']} days old)")
    
    if vendor['address_type'] in ['Rented Room', 'Virtual Office']:
        score += 25
        risk_factors.append(f"Operating from {vendor['address_type']} - Potential shell company indicator")
    elif vendor['address_type'] == 'Residential':
        score += 15
        risk_factors.append("Operating from residential address - Verify business legitimacy")
    
    if vendor['director_companies'] > 30:
        score += 20
        risk_factors.append(f"Director associated with {vendor['director_companies']} companies - Shell company network risk")
    elif vendor['director_companies'] > 15:
        score += 10
        risk_factors.append(f"Director associated with {vendor['director_companies']} companies - Monitor for suspicious activity")
    
    if vendor['gstr1_status'] == 'Nil Return':
        score += 15
        risk_factors.append("Filed NIL GSTR-1 returns - No outward supplies reported despite taking ITC")
    elif vendor['gstr1_status'] == 'Not Filed':
        score += 20
        risk_factors.append("GSTR-1 not filed - Non-compliant vendor")
    
    if vendor['months_not_filed'] > 3:
        score += 30
        risk_factors.append(f"GSTR-3B not filed for {vendor['months_not_filed']} months - Registration cancellation imminent")
    elif vendor['months_not_filed'] > 0:
        score += 15 + (vendor['months_not_filed'] * 3)
        risk_factors.append(f"GSTR-3B not filed for {vendor['months_not_filed']} months - ITC reversal risk")
    
    if vendor['cash_payments'] > 50000:
        score += 15
        risk_factors.append(f"Cash payments of ₹{vendor['cash_payments']:,} exceed Section 40A(3) limit of ₹10,000")
    
    if vendor['transaction_count'] < 10 and vendor['itc_amount'] > 500000:
        score += 15
        risk_factors.append(f"High ITC (₹{vendor['itc_amount']:,}) with low transaction count ({vendor['transaction_count']}) - Unusual pattern")
    
    if vendor['itc_amount'] > 2000000 and vendor['registration_days'] < 180:
        score += 10
        risk_factors.append(f"New vendor with high ITC exposure (₹{vendor['itc_amount']:,}) - Enhanced monitoring required")
    
    if vendor['registration_days'] < 15 and vendor['director_companies'] > 20:
        score += 15
        risk_factors.append("CRITICAL: Very new registration + director network = High fraud probability")
    
    score = min(score, 100)
    
    return score, risk_factors

def get_risk_level(risk_score):
    if risk_score >= 90:
        return "Critical"
    elif risk_score >= 70:
        return "High Risk"
    elif risk_score >= 40:
        return "Medium Risk"
    else:
        return "Low Risk"

def get_risk_color(risk_level):
    color_map = {
        'Critical': '#FF4444',
        'High Risk': '#FFA500',
        'Medium Risk': '#FFD700',
        'Low Risk': '#90EE90'
    }
    return color_map.get(risk_level, '#CCCCCC')

def check_compliance_breaches(vendor):
    breaches = []
    
    if vendor['cash_payments'] > 50000:
        breaches.append(f"Section 40A(3) Breach: Cash payments of ₹{vendor['cash_payments']:,} exceed ₹10,000 limit per transaction")
    
    if vendor['months_not_filed'] > 2:
        breaches.append(f"GSTR-3B Filing Breach: {vendor['months_not_filed']} consecutive months of non-filing")
    
    if vendor['gstr1_status'] == 'Not Filed' and vendor['itc_amount'] > 100000:
        breaches.append(f"GSTR-1 Not Filed: ITC of ₹{vendor['itc_amount']:,} claimed from non-compliant vendor")
    
    if vendor['registration_days'] < 30 and vendor['itc_amount'] > 500000:
        breaches.append(f"High Risk Transaction: ₹{vendor['itc_amount']:,} ITC from vendor registered only {vendor['registration_days']} days ago")
    
    return breaches

def calculate_itc_exposure(vendors_df, risk_threshold='High Risk'):
    if risk_threshold == 'Critical':
        risky_vendors = vendors_df[vendors_df['risk_level'] == 'Critical']
    elif risk_threshold == 'High Risk':
        risky_vendors = vendors_df[vendors_df['risk_level'].isin(['Critical', 'High Risk'])]
    else:
        risky_vendors = vendors_df[vendors_df['risk_level'].isin(['Critical', 'High Risk', 'Medium Risk'])]
    
    total_exposure = risky_vendors['itc_amount'].sum()
    vendor_count = len(risky_vendors)
    
    return total_exposure, vendor_count

def mock_gstn_api_call(gstin):
    registration_days = random.randint(5, 1500)
    status = "Active" if registration_days > 180 else random.choice(["Active", "Suspended", "Pending Verification"])
    
    return {
        "gstin": gstin,
        "legal_name": random.choice(VENDOR_NAMES),
        "trade_name": random.choice(VENDOR_NAMES),
        "registration_date": (datetime.now() - timedelta(days=registration_days)).strftime("%Y-%m-%d"),
        "status": status,
        "taxpayer_type": "Regular",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "gstr1_last_filed": random.choice(["2024-10", "2024-09", "2024-08", "Not Filed"]),
        "gstr3b_last_filed": random.choice(["2024-10", "2024-09", "2024-08", "Not Filed"]),
        "center_jurisdiction": "Mumbai",
        "state_jurisdiction": "Maharashtra"
    }

def mock_mca_api_call(gstin):
    company_count = random.randint(1, 45)
    
    return {
        "pan_linked_to_gstin": gstin[:10],
        "director_name": f"Director {random.randint(1, 100)}",
        "total_companies": company_count,
        "active_companies": random.randint(1, company_count),
        "dissolved_companies": random.randint(0, company_count // 2),
        "director_since": (datetime.now() - timedelta(days=random.randint(365, 3650))).strftime("%Y-%m-%d"),
        "din_number": f"0{random.randint(1000000, 9999999)}",
        "recent_incorporations": random.randint(0, 5),
        "flagged_entities": random.randint(0, 3),
        "compliance_status": random.choice(["Compliant", "Minor Defaults", "Major Defaults"])
    }

def process_tally_data(tally_df):
    required_columns = ['Vendor Name', 'GSTIN', 'Transaction Amount']
    
    missing_columns = [col for col in required_columns if col not in tally_df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
    
    tally_df['Transaction Amount'] = pd.to_numeric(tally_df['Transaction Amount'], errors='coerce')
    
    if 'Tax Amount' in tally_df.columns:
        tally_df['Tax Amount'] = pd.to_numeric(tally_df['Tax Amount'], errors='coerce')
    else:
        tally_df['Tax Amount'] = 0
    
    if 'Payment Mode' not in tally_df.columns:
        tally_df['Payment Mode'] = 'Bank Transfer'
    
    aggregated = tally_df.groupby(['GSTIN', 'Vendor Name']).agg({
        'Transaction Amount': 'sum',
        'Tax Amount': 'sum',
        'Payment Mode': lambda x: list(x)
    }).reset_index()
    
    aggregated['transaction_count'] = tally_df.groupby(['GSTIN', 'Vendor Name']).size().values
    aggregated['itc_amount'] = aggregated['Tax Amount']
    
    cash_df = tally_df[tally_df['Payment Mode'].str.contains('Cash', case=False, na=False)]
    if len(cash_df) > 0:
        cash_payments = cash_df.groupby(['GSTIN', 'Vendor Name'])['Transaction Amount'].sum()
        aggregated['cash_payments'] = aggregated.apply(
            lambda row: cash_payments.get((row['GSTIN'], row['Vendor Name']), 0), 
            axis=1
        )
    else:
        aggregated['cash_payments'] = 0
    
    new_vendors_count = 0
    updated_vendors_count = 0
    
    vendors_list = st.session_state.vendors
    
    for _, row in aggregated.iterrows():
        gstin = row['GSTIN']
        vendor_name = row['Vendor Name']
        
        existing_vendor = None
        for v in vendors_list:
            if v['gstin'] == gstin:
                existing_vendor = v
                break
        
        if existing_vendor:
            existing_vendor['transaction_count'] += int(row['transaction_count'])
            existing_vendor['itc_amount'] += float(row['itc_amount'])
            existing_vendor['cash_payments'] += float(row['cash_payments'])
            existing_vendor['name'] = vendor_name
            
            existing_vendor['risk_score'], existing_vendor['risk_factors'] = calculate_vendor_risk_score(existing_vendor)
            existing_vendor['risk_level'] = get_risk_level(existing_vendor['risk_score'])
            
            updated_vendors_count += 1
        else:
            gstn_data = mock_gstn_api_call(gstin)
            mca_data = mock_mca_api_call(gstin)
            
            reg_date_str = gstn_data['registration_date']
            reg_date = datetime.strptime(reg_date_str, "%Y-%m-%d")
            registration_days = (datetime.now() - reg_date).days
            
            new_vendor = {
                'name': vendor_name,
                'gstin': gstin,
                'registration_days': registration_days,
                'address_type': random.choice(ADDRESS_TYPES),
                'director_companies': mca_data['total_companies'],
                'gstr1_status': 'Filed' if gstn_data['gstr1_last_filed'] != 'Not Filed' else 'Not Filed',
                'gstr3b_status': 'Filed' if gstn_data['gstr3b_last_filed'] != 'Not Filed' else 'Not Filed',
                'months_not_filed': random.randint(0, 6),
                'transaction_count': int(row['transaction_count']),
                'itc_amount': float(row['itc_amount']),
                'cash_payments': float(row['cash_payments']),
            }
            
            new_vendor['risk_score'], new_vendor['risk_factors'] = calculate_vendor_risk_score(new_vendor)
            new_vendor['risk_level'] = get_risk_level(new_vendor['risk_score'])
            
            vendors_list.append(new_vendor)
            new_vendors_count += 1
    
    st.session_state.vendors = sorted(vendors_list, key=lambda x: x['risk_score'], reverse=True)
    
    return new_vendors_count, updated_vendors_count

import pandas as pd

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply standard cleaning steps to the dataframe.
    """
    return df


layanan_dict = {
    "ASTINet": ["ASTINet"],
    "Call Center": ["Call Center 140XY", "Call Center 500"],
    "Cloud": ["Cloud"],
    "HSI": ["High Speed Internet", "Speedy Instant", "HSI B2B"],
    "IP Transit": ["IP Transit"],
    "IPTV": ["IPTV"],
    "Manage Services": ["Manage Capacity Network"],
    "Metro E": ["Metro Ethernet"],
    "NTE": ["NTE"],
    "Pijar": ["Digital Ecosystem Education"],
    "USeeTV": ["USeeTV"],
    "Wifi": ["Wifi"],
    "POTs": ["Voice", "VoIP"],
    "Antares": ["Antares"],
    "VPN": ["VPN"],
    "Others": []  # Menampung seluruh nilai yang tidak memenuhi kriteria di atas
}
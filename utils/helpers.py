def format_currency(value: float) -> str:
    """
    Format a number as Indonesian Rupiah.
    """
    return f"Rp {value:,.0f}".replace(",", ".")

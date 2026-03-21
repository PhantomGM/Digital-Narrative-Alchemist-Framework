import random

def generate_region_dna():
    """Generates a DNA string for a Region in numeric format."""
    region_genes = ["RT", "TF", "CU", "PO", "WA", "EN", "HI", "TH", "IC", "LMK"]
    return ",".join(f"{gene}{random.randint(1, 10)}" for gene in region_genes)

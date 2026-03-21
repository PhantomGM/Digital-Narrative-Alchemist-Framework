import random

class WorldDNAGenerator:
    """Generates a random World DNA string based on the World DNA Decoding Key v3.2."""
    def __init__(self):
        self.version = "3.2-enhanced"
        self.scales_def = {'T': (1, 10), 'M': (1, 10), 'A': (1, 10), 'R': (2, 5)}
        self.blocks_def = {
            'COSMO': {'CM': (1, 5), 'MD': (1, 5), 'AL': (1, 5), 'FF': (1, 5)},
            'ECON': {'PS': (1, 5), 'WD': (1, 4), 'TN': (1, 4), 'TM': (1, 5)},
            'MAG': {'SRC': (1, 5), 'PRN': (1, 4), 'CST': (1, 5), 'LMT': (1, 5), 'ACQ': (1, 5), 'LAW': (1, 5)},
            'ENV': {'GEO': (1, 7), 'CLM': (1, 5), 'RES': (1, 4), 'ANO': (1, 5)},
            'SOC': {'GOV': (1, 6), 'CLS': (1, 5), 'VAL': (1, 6), 'LIF': (1, 5), 'TEC': (1, 5), 'MAG': (1, 5), 'ART': (1, 5), 'REL': (1, 5), 'FAM': (1, 5), 'GEN': (1, 5), 'MOR': (1, 5), 'LAW': (1, 5)},
            'CON': {'TYP': (1, 5), 'SCL': (1, 4), 'AGE': (1, 3)},
            'HIS': {'EVT': (1, 6), 'KNG': (1, 4), 'LGC': (1, 5)},
            'ORIGIN': {'MAG_SRC': (1, 4), 'MAG_DET': (1, 6), 'MAG_STAT': (1, 8)}
        }
        self.dynamic_blocks_def = {
            'REG': {'TER': (1, 7), 'SOC': (1, 6), 'ECO': (1, 5), 'LMK': (1, 5)},
            'CRIT': {'DOM': (1, 5), 'NAT': (1, 6), 'IMM': (1, 4)},
            'CHAIN': {'TRG': (1, 6), 'ACT': (1, 5), 'CNS': (1, 5)},
            'EVO': {'TRT': (1, 50), 'PTN': (1, 4)},
            'TREND': {'TRT': (1, 50), 'DIR': (1, 3)}
        }

    def _generate_block(self, block_name, definition):
        parts = [f"{gene}:{random.randint(*value_range)}" for gene, value_range in definition.items()]
        return f"{block_name}{{{';'.join(parts)}}}"

    def _generate_factions(self):
        factions = []
        for _ in range(random.randint(2, 4)):
            values = random.sample(range(1, 7), 3)
            highest_value = values[0]
            flaw_map = {1: 1, 2: 6, 3: 2, 4: 4, 5: 3, 6: 5}
            fact = {
                'TY': random.randint(1, 6), 'SC': random.randint(1, 5), 'GL': random.randint(1, 5),
                'VL': f"[{','.join(map(str, values))}]", 'FL': flaw_map.get(highest_value, 1),
                'LM': f"[{','.join(map(str, random.sample(range(1, 6), random.randint(1, 3))))}]"
            }
            factions.append(f"{{{' ; '.join(f'{k}:{v}' for k, v in fact.items())}}}")
        return f"FACT[{','.join(factions)}]"

    def _generate_pantheon(self):
        deities = []
        for _ in range(random.randint(2, 6)):
            deity = {
                'ALIGN': random.randint(1, 10),
                'DOM': f"[{','.join(map(str, random.sample(range(1, 9), random.randint(1, 3))))}]",
                'STATUS': random.randint(1, 20)
            }
            deities.append(f"{{{' ; '.join(f'{k}:{v}' for k, v in deity.items())}}}")
        return f"PANTHEON[{','.join(deities)}]"

    def _generate_shadow_societies(self):
        societies = []
        for _ in range(random.randint(1, 3)):
            society = {
                'TYPE': random.randint(1, 6),
                'SPEC': random.randint(1, 10),
                'GOAL': random.randint(1, 10)
            }
            societies.append(f"{{{' ; '.join(f'{k}:{v}' for k, v in society.items())}}}")
        return f"SHADOW[{','.join(societies)}]"

    def generate_dna(self):
        """Generates and assembles the complete World DNA string."""
        dna_parts = []
        scales = {s: random.randint(*r) for s, r in self.scales_def.items()}
        dna_parts.extend([f"{s}:{v}" for s, v in scales.items()])
        num_regions = scales['R']
        
        for name, defn in self.blocks_def.items():
            dna_parts.append(self._generate_block(name, defn))
        
        dna_parts.append(self._generate_factions())
        dna_parts.append(self._generate_pantheon())
        dna_parts.append(self._generate_shadow_societies())
        
        regions = [self._generate_block('', self.dynamic_blocks_def['REG']) for _ in range(num_regions)]
        dna_parts.append(f"REG[{','.join(regions)}]")
        
        for name in ['CRIT', 'CHAIN', 'EVO', 'TREND']:
            dna_parts.append(self._generate_block(name, self.dynamic_blocks_def[name]))
            
        return " ".join(dna_parts)

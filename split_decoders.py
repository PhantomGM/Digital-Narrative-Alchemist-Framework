import os
import re

source_file = r'C:\Users\nickd\Desktop\Vaults\DNA Notes\Master_Decoder_Knowledge_CLEANED.md'
output_dir = r'C:\Users\nickd\Desktop\OC2\src\agents\layer2_dna\decoders'
os.makedirs(output_dir, exist_ok=True)

with open(source_file, 'r', encoding='utf-8') as f:
    content = f.read()

# We can split the document by the word "SECTION: "
parts = re.split(r'(?:###? SECTION: |- -- SECTION: )', content)

name_map = {
    'NPC DECODING PROMPT': 'npc.md',
    'WORLD DECODING PROMPT': 'world.md',
    'FACTION DECODING PROMPT': 'faction.md',
    'ITEM DECODING PROMPT': 'item.md',
    'LOCATION DECODING PROMPT': 'location.md',
    'QUEST DECODING PROMPT': 'quest.md',
    'TRAVEL DECODING PROMPT': 'travel.md'
}

for part in parts[1:]: # Skip the first part before any section
    # The title might end with "---SYSTEM" or "---" without a newline
    match = re.match(r'(.*?)(?:---\s*SYSTEM|---\s*def|---)(.*)', part, re.IGNORECASE | re.DOTALL)
    if match:
        title_line = match.group(1).replace('---', '').strip().upper()
        # Add back the SYSTEM part if it was swallowed
        body_start = match.group(2)
        
        # Check if the split swallowed "SYSTEM/INSTRUCTION"
        if "SYSTEM/" not in body_start and "INSTRUCTION" not in body_start:
            body = "SYSTEM" + body_start
        else:
            body = body_start
            
        if title_line in name_map:
            filename = name_map[title_line]
            out_path = os.path.join(output_dir, filename)
            with open(out_path, 'w', encoding='utf-8') as out_f:
                out_f.write(body.strip() + "\n")
            print(f"Created {filename}")
    else:
        # Fallback to newline split
        lines = part.split('\n', 1)
        if len(lines) >= 2:
            title_line = lines[0].replace('---', '').strip().upper()
            body = lines[1].strip()
            if title_line in name_map:
                filename = name_map[title_line]
                out_path = os.path.join(output_dir, filename)
                with open(out_path, 'w', encoding='utf-8') as out_f:
                    out_f.write(body + "\n")
                print(f"Created {filename} (fallback)")

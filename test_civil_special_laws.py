"""Test that civil_law and special_laws from indian_law_dataset.json are loaded"""
from data_bridge.loader import JSONLoader

loader = JSONLoader("db")
sections, acts, cases = loader.load_and_normalize_directory()

# Find sections from indian_law_dataset.json
civil_sections = [s for s in sections if 'civil' in s.act_id.lower() and 'indian_law_dataset' in s.act_id]
special_sections = [s for s in sections if 'special' in s.act_id.lower() and 'indian_law_dataset' in s.act_id]

print(f"Civil Law Sections from indian_law_dataset.json: {len(civil_sections)}")
for section in civil_sections[:5]:
    print(f"  - {section.section_number}: {section.text[:100]}...")

print(f"\nSpecial Laws Sections from indian_law_dataset.json: {len(special_sections)}")
for section in special_sections:
    print(f"  - {section.section_number}: {section.text[:100]}...")

# Test search for banking dispute
banking_sections = [s for s in sections if 'banking' in s.text.lower() or 'banking' in s.section_number.lower()]
print(f"\nBanking-related sections: {len(banking_sections)}")
for section in banking_sections[:3]:
    print(f"  - {section.section_number} ({section.act_id}): {section.text[:80]}...")

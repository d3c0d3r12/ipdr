#!/usr/bin/env python3
"""Verify IP lookup results CSV file"""

import csv
from collections import Counter

def verify_csv(filename):
    """Verify and analyze CSV results"""
    
    print("=" * 70)
    print("📊 IP LOOKUP RESULTS VERIFICATION")
    print("=" * 70)
    
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = list(reader)
    
    # Basic stats
    total_rows = len(data)
    unique_ips = len(set(row['ip'] for row in data))
    
    print(f"\n✅ Total Records: {total_rows}")
    print(f"✅ Unique IP Addresses: {unique_ips}")
    print(f"✅ Duplicate IPs: {total_rows - unique_ips}")
    
    # Country analysis
    countries = Counter(row['country'] for row in data)
    print(f"\n🌍 COUNTRIES ({len(countries)} total):")
    for country, count in countries.most_common(10):
        percentage = (count / total_rows) * 100
        print(f"   {country:30s} {count:4d} ({percentage:5.1f}%)")
    
    # City analysis
    cities = Counter(row['city'] for row in data)
    print(f"\n🏙️  CITIES ({len(cities)} total):")
    for city, count in cities.most_common(10):
        percentage = (count / total_rows) * 100
        print(f"   {city:30s} {count:4d} ({percentage:5.1f}%)")
    
    # ISP analysis
    isps = Counter(row['isp'] for row in data)
    print(f"\n📡 ISPs ({len(isps)} total):")
    for isp, count in isps.most_common(10):
        percentage = (count / total_rows) * 100
        print(f"   {isp:50s} {count:4d} ({percentage:5.1f}%)")
    
    # Region analysis (for India)
    india_data = [row for row in data if 'India' in row['country']]
    if india_data:
        regions = Counter(row['region'] for row in india_data)
        print(f"\n🇮🇳 INDIAN REGIONS ({len(regions)} total):")
        for region, count in regions.most_common(10):
            percentage = (count / len(india_data)) * 100
            print(f"   {region:30s} {count:4d} ({percentage:5.1f}%)")
    
    # Data completeness
    print(f"\n📋 DATA COMPLETENESS:")
    fields = ['country', 'city', 'region', 'isp', 'postal_code']
    for field in fields:
        non_empty = sum(1 for row in data if row[field] and row[field] != 'Unknown')
        percentage = (non_empty / total_rows) * 100
        status = "✅" if percentage > 90 else "⚠️" if percentage > 50 else "❌"
        print(f"   {status} {field:15s}: {non_empty:4d}/{total_rows} ({percentage:5.1f}%)")
    
    # IP type analysis
    ipv4_count = sum(1 for row in data if '.' in row['ip'] and ':' not in row['ip'])
    ipv6_count = sum(1 for row in data if ':' in row['ip'])
    
    print(f"\n🔢 IP VERSION:")
    print(f"   IPv4: {ipv4_count} ({(ipv4_count/total_rows)*100:.1f}%)")
    print(f"   IPv6: {ipv6_count} ({(ipv6_count/total_rows)*100:.1f}%)")
    
    # Sample verification
    print(f"\n🔍 SAMPLE RECORDS (First 5):")
    for i, row in enumerate(data[:5], 1):
        print(f"\n   [{i}] {row['ip']}")
        print(f"       Location: {row['city']}, {row['region']}, {row['country']}")
        print(f"       ISP: {row['isp']}")
        print(f"       Postal: {row['postal_code']}")
    
    print("\n" + "=" * 70)
    print("✅ VERIFICATION COMPLETE!")
    print("=" * 70)
    
    return {
        'total_rows': total_rows,
        'unique_ips': unique_ips,
        'countries': len(countries),
        'cities': len(cities),
        'isps': len(isps)
    }

if __name__ == '__main__':
    stats = verify_csv('ip_lookup_results.csv')

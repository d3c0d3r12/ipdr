"""
IP Record Model - MongoDB Collection
"""
from datetime import datetime, timezone

IP_RECORDS_COLLECTION = "ip_records"

INDEXES = {
    IP_RECORDS_COLLECTION: [
        {"keys": "ip"},
        {"keys": "source_file"},
    ],
}


def new_ip_record(*, ip, timestamp=None, country=None, region=None,
                  city=None, isp=None, source_file=None):
    return {
        "timestamp": timestamp,
        "ip": ip,
        "country": country,
        "region": region,
        "city": city,
        "isp": isp,
        "source_file": source_file,
        "created_at": datetime.now(timezone.utc),
    }

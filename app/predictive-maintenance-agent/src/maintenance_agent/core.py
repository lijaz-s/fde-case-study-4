"""
Core implementation: parsers, discovery, normalization, and analysis.
"""

import os
import json
import csv
import re
import logging
from datetime import datetime, timedelta
from typing import Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# PARSER REGISTRY & PARSERS
# ============================================================================

class CSVParser:
    """Parser for CSV files."""

    def detect(self, file_path: str) -> bool:
        return file_path.lower().endswith('.csv')

    def parse(self, file_path: str) -> list[dict]:
        """Parse CSV file."""
        records = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row:
                        records.append(row)
            logger.info(f"Parsed {len(records)} records from {Path(file_path).name}")
        except Exception as e:
            logger.error(f"Error parsing CSV {file_path}: {e}")
        return records


class JSONParser:
    """Parser for JSON files."""

    def detect(self, file_path: str) -> bool:
        return file_path.lower().endswith('.json')

    def parse(self, file_path: str) -> list[dict]:
        """Parse JSON file."""
        records = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                records = [data]

            logger.info(f"Parsed {len(records)} records from {Path(file_path).name}")
        except Exception as e:
            logger.error(f"Error parsing JSON {file_path}: {e}")
        return records


class TextParser:
    """Parser for maintenance log text files."""

    def detect(self, file_path: str) -> bool:
        return file_path.lower().endswith('.txt')

    def parse(self, file_path: str) -> list[dict]:
        """Parse text maintenance logs."""
        records = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split by double newlines
            entries = re.split(r'\n\s*\n', content)

            for entry in entries:
                if entry.strip():
                    record = self._extract_record(entry)
                    if record:
                        records.append(record)

            logger.info(f"Parsed {len(records)} records from {Path(file_path).name}")
        except Exception as e:
            logger.error(f"Error parsing text {file_path}: {e}")

        return records

    def _extract_record(self, text: str) -> Optional[dict]:
        """Extract structured data from unstructured maintenance text."""
        record = {}

        # Extract machine ID
        machine_match = re.search(r'([A-Z]{3})-?(\d{3}|\d{2})', text)
        if machine_match:
            record['machine_id'] = f"{machine_match.group(1)}-{machine_match.group(2)}"

        # Extract date
        date_patterns = [
            r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    record['timestamp'] = match.group(0)
                except:
                    pass
                break

        # Extract downtime - look for expressions like "1.5 + 0.75"
        downtime_match = re.search(r'[Dd]owntime\s*=\s*([\d.+\-*/() ]+?)(?:\s|$|\.|\n)', text)
        if downtime_match:
            expr = downtime_match.group(1).strip()
            try:
                # Safe evaluation - only allow numbers, operators, parentheses
                if all(c in '0123456789+-.*/() ' for c in expr):
                    result = eval(expr, {"__builtins__": {}}, {})
                    record['downtime_hours'] = float(result)
            except:
                pass

        # Extract parts replaced
        parts_match = re.search(r'[Pp]arts?\s+replaced?:?\s*([^.]*?)(?=\.|$)', text)
        if parts_match:
            record['parts_replaced'] = parts_match.group(1).strip()

        # Store text as description
        record['description'] = text[:500]

        return record if record.get('machine_id') else None


class ParserRegistry:
    """Registry for data parsers."""

    def __init__(self):
        self._parsers = [CSVParser(), JSONParser(), TextParser()]

    def get_parser(self, file_path: str) -> Optional[Any]:
        """Get parser for file."""
        for parser in self._parsers:
            if parser.detect(file_path):
                return parser
        return None

    def parse_file(self, file_path: str) -> tuple[list[dict], Optional[str]]:
        """Parse file and return (records, error_message)."""
        parser = self.get_parser(file_path)
        if parser is None:
            return [], f"No parser for {file_path}"

        try:
            records = parser.parse(file_path)
            return records, None
        except Exception as e:
            return [], str(e)


# ============================================================================
# FILE DISCOVERY
# ============================================================================

def discover_files(input_paths: list[str]) -> list[dict]:
    """Discover all data files in input directories."""
    discovered = []

    for path_str in input_paths:
        path = Path(path_str)
        if path.is_file():
            discovered.append({
                'path': str(path),
                'name': path.name,
                'size': path.stat().st_size,
                'extension': path.suffix.lower()
            })
        elif path.is_dir():
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    discovered.append({
                        'path': str(file_path),
                        'name': file_path.name,
                        'size': file_path.stat().st_size,
                        'extension': file_path.suffix.lower()
                    })

    logger.info(f"Discovered {len(discovered)} files")
    return discovered


# ============================================================================
# NORMALIZATION
# ============================================================================

VENDOR_MAPPINGS = {
    'vendor_a': {
        'timestamp': 'timestamp',
        'machine_id': 'machine_id',
        'spindle_temp': 'spindle_temperature',
        'vibration_mm_s': 'vibration',
        'motor_current_a': 'motor_current',
        'status': 'dashboard_status',
    },
    'vendor_b': {
        'recordedAt': 'timestamp',
        'equipmentCode': 'machine_id',
        'hydPressure_bar': 'pressure',
        'cycleDuration_s': 'cycle_time',
        'alarmState': 'dashboard_status',
    }
}


def normalize_record(record: dict, vendor: str = '', record_type: str = 'telemetry') -> dict:
    """Normalize record to common schema."""
    if not vendor:
        vendor = 'vendor_a'

    mapping = VENDOR_MAPPINGS.get(vendor.lower(), {})
    normalized = {'_source_vendor': vendor, '_record_type': record_type}

    for src, dest in mapping.items():
        if src in record:
            value = record[src]
            # Try to convert numeric fields
            if dest in ['spindle_temperature', 'pressure', 'vibration', 'motor_current', 'spindle_load', 'cycle_time']:
                try:
                    normalized[dest] = float(value)
                except (ValueError, TypeError):
                    normalized[dest] = None
            else:
                normalized[dest] = str(value) if value is not None else None

    # Add unmapped fields
    normalized['_vendor_fields'] = {k: v for k, v in record.items() if k not in mapping}

    return normalized


# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def detect_threshold_violations(telemetry: list[dict], config: dict) -> list[dict]:
    """Detect measurements exceeding thresholds."""
    anomalies = []

    thresholds = {
        'spindle_temperature': {
            'alert': config.get('temp_alert', 90),
            'critical': config.get('temp_critical', 100)
        },
        'pressure': {
            'alert': config.get('pressure_alert', 150),
            'critical': config.get('pressure_critical', 160)
        },
        'vibration': {
            'alert': config.get('vib_alert', 4.0),
            'critical': config.get('vib_critical', 5.0)
        }
    }

    for event in telemetry:
        for field, thresh_dict in thresholds.items():
            if field in event and event[field] is not None:
                try:
                    value = float(event[field])
                    if value >= thresh_dict['critical']:
                        anomalies.append({
                            'timestamp': event.get('timestamp'),
                            'machine_id': event.get('machine_id'),
                            'field': field,
                            'value': value,
                            'severity': 'critical',
                            'threshold': thresh_dict['critical']
                        })
                    elif value >= thresh_dict['alert']:
                        anomalies.append({
                            'timestamp': event.get('timestamp'),
                            'machine_id': event.get('machine_id'),
                            'field': field,
                            'value': value,
                            'severity': 'alert',
                            'threshold': thresh_dict['alert']
                        })
                except (ValueError, TypeError):
                    pass

    return anomalies


def calculate_statistics(values: list[float]) -> dict:
    """Calculate mean, std, min, max for a list of values."""
    if not values:
        return {}

    values = [v for v in values if v is not None]
    if not values:
        return {}

    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std = variance ** 0.5

    return {
        'mean': mean,
        'std': std,
        'min': min(values),
        'max': max(values),
        'count': len(values)
    }


def compute_metrics(failures: list[dict], maintenance: list[dict]) -> dict:
    """Calculate summary metrics."""
    metrics = {
        'total_downtime_hours': 0.0,
        'incident_count': len(failures),
        'maintenance_count': len(maintenance),
    }

    for failure in failures:
        if failure.get('duration_hours'):
            metrics['total_downtime_hours'] += float(failure['duration_hours'])

    if failures:
        metrics['avg_downtime_per_incident'] = metrics['total_downtime_hours'] / len(failures)
    else:
        metrics['avg_downtime_per_incident'] = 0.0

    return metrics

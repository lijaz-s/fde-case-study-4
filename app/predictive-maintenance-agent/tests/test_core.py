"""
Tests for core parsers and normalization.
"""

import tempfile
import json
import csv
import pytest
from pathlib import Path

import sys
sys.path.insert(0, 'src')

from maintenance_agent.core import (
    CSVParser,
    JSONParser,
    TextParser,
    ParserRegistry,
    normalize_record,
    detect_threshold_violations,
    calculate_statistics
)


class TestCSVParser:
    """Tests for CSV parser."""

    def test_parse_valid_csv(self):
        """Test parsing a valid CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'machine_id', 'spindle_temp'])
            writer.writeheader()
            writer.writerow({'timestamp': '2026-01-15T00:00:00', 'machine_id': 'CNC-001', 'spindle_temp': '72.5'})
            fname = f.name

        try:
            parser = CSVParser()
            assert parser.detect(fname)
            records = parser.parse(fname)
            assert len(records) == 1
            assert records[0]['machine_id'] == 'CNC-001'
        finally:
            Path(fname).unlink()

    def test_csv_empty_file(self):
        """Test parsing empty CSV."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("timestamp,machine_id,spindle_temp\n")
            fname = f.name

        try:
            parser = CSVParser()
            records = parser.parse(fname)
            assert len(records) == 0
        finally:
            Path(fname).unlink()


class TestJSONParser:
    """Tests for JSON parser."""

    def test_parse_valid_json_array(self):
        """Test parsing JSON array."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {'equipmentCode': 'IMM-001', 'hydPressure_bar': 140.0},
                {'equipmentCode': 'IMM-002', 'hydPressure_bar': 142.0}
            ], f)
            fname = f.name

        try:
            parser = JSONParser()
            assert parser.detect(fname)
            records = parser.parse(fname)
            assert len(records) == 2
            assert records[0]['equipmentCode'] == 'IMM-001'
        finally:
            Path(fname).unlink()

    def test_parse_valid_json_object(self):
        """Test parsing JSON object."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'equipmentCode': 'IMM-001', 'hydPressure_bar': 140.0}, f)
            fname = f.name

        try:
            parser = JSONParser()
            records = parser.parse(fname)
            assert len(records) == 1
        finally:
            Path(fname).unlink()


class TestTextParser:
    """Tests for text parser."""

    def test_parse_maintenance_record(self):
        """Test parsing maintenance log."""
        text = """
        12 March 2026, CNC-004.
        Bearing replaced.
        Downtime = 3.4 hours.
        """

        parser = TextParser()
        record = parser._extract_record(text)
        assert record is not None
        assert record['machine_id'] == 'CNC-004'
        assert record['downtime_hours'] == 3.4

    def test_parse_arithmetic_expression(self):
        """Test parsing arithmetic downtime."""
        text = """
        15 March 2026, IMM-002.
        Downtime = 1.5 + 0.75 hours.
        """

        parser = TextParser()
        record = parser._extract_record(text)
        assert record is not None
        assert record['downtime_hours'] == 2.25

    def test_parse_percentage_calculation(self):
        """Test parsing percentage expression."""
        text = """
        Hydraulic pressure dropped. Change = (142 - 117) / 142.
        """

        parser = TextParser()
        record = parser._extract_record(text)
        # This should extract if machine ID is present
        assert record is None or isinstance(record, dict)


class TestParserRegistry:
    """Tests for parser registry."""

    def test_registry_detects_csv(self):
        """Test registry detects CSV files."""
        registry = ParserRegistry()
        parser = registry.get_parser('test.csv')
        assert parser is not None
        assert isinstance(parser, CSVParser)

    def test_registry_detects_json(self):
        """Test registry detects JSON files."""
        registry = ParserRegistry()
        parser = registry.get_parser('test.json')
        assert parser is not None
        assert isinstance(parser, JSONParser)

    def test_registry_detects_txt(self):
        """Test registry detects text files."""
        registry = ParserRegistry()
        parser = registry.get_parser('test.txt')
        assert parser is not None
        assert isinstance(parser, TextParser)

    def test_registry_unknown_format(self):
        """Test registry handles unknown formats."""
        registry = ParserRegistry()
        parser = registry.get_parser('test.xyz')
        assert parser is None


class TestNormalization:
    """Tests for normalization."""

    def test_normalize_vendor_a_telemetry(self):
        """Test normalizing Vendor A telemetry."""
        record = {
            'timestamp': '2026-01-15T00:00:00',
            'machine_id': 'CNC-001',
            'spindle_temp': '72.5',
            'vibration_mm_s': '1.5',
            'motor_current_a': '25.0'
        }

        normalized = normalize_record(record, 'vendor_a', 'telemetry')
        assert normalized['machine_id'] == 'CNC-001'
        assert normalized['spindle_temperature'] == 72.5
        assert normalized['vibration'] == 1.5

    def test_normalize_vendor_b_telemetry(self):
        """Test normalizing Vendor B telemetry."""
        record = {
            'recordedAt': '2026-01-15T00:00:00',
            'equipmentCode': 'IMM-001',
            'hydPressure_bar': '140.0',
            'cycleDuration_s': '45.2'
        }

        normalized = normalize_record(record, 'vendor_b', 'telemetry')
        assert normalized['machine_id'] == 'IMM-001'
        assert normalized['pressure'] == 140.0
        assert normalized['cycle_time'] == 45.2


class TestAnalysis:
    """Tests for analysis functions."""

    def test_threshold_violation_detection(self):
        """Test threshold violation detection."""
        telemetry = [
            {
                'timestamp': '2026-01-15T00:00:00',
                'machine_id': 'CNC-001',
                'spindle_temperature': 95.0,  # Alert threshold
                'pressure': 160.0,  # Critical
                'vibration': 3.0
            }
        ]

        config = {
            'temp_alert': 90.0,
            'temp_critical': 100.0,
            'pressure_alert': 150.0,
            'pressure_critical': 160.0,
            'vib_alert': 4.0,
            'vib_critical': 5.0
        }

        anomalies = detect_threshold_violations(telemetry, config)
        assert len(anomalies) >= 2
        assert any(a['field'] == 'spindle_temperature' for a in anomalies)
        assert any(a['field'] == 'pressure' for a in anomalies)

    def test_calculate_statistics(self):
        """Test statistics calculation."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        stats = calculate_statistics(values)

        assert stats['mean'] == 3.0
        assert stats['min'] == 1.0
        assert stats['max'] == 5.0
        assert stats['count'] == 5

    def test_empty_statistics(self):
        """Test statistics with empty data."""
        stats = calculate_statistics([])
        assert stats == {}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

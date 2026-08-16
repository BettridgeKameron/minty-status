import json
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check


class GatusFreshnessTests(unittest.TestCase):
    def response(self, age_seconds=30, name="Public edge"):
        timestamp = datetime.now(timezone.utc) - timedelta(seconds=age_seconds)
        return json.dumps([{
            "name": name,
            "results": [{"timestamp": timestamp.isoformat().replace("+00:00", "Z")}],
        }])

    def test_selected_endpoint_is_fresh(self):
        self.assertTrue(check.gatus_is_fresh(self.response(), 180, "Public edge"))

    def test_stale_or_missing_endpoint_fails_closed(self):
        self.assertFalse(check.gatus_is_fresh(self.response(181), 180, "Public edge"))
        self.assertFalse(check.gatus_is_fresh(self.response(name="Blog"), 180, "Public edge"))


if __name__ == "__main__":
    unittest.main()

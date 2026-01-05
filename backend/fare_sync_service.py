import requests
import threading
import json
from datetime import datetime

class FareSyncService:
    def __init__(self, base_url, driver_id):
        self.base_url = base_url.rstrip("/")
        self.driver_id = driver_id
        self.session = requests.Session()

    def attach(self, fare_calculator):
        """
        Connects to FareCalculator signals
        """
        fare_calculator.ride_completed.connect(self._on_ride_completed)

    def _on_ride_completed(self, passenger_id, ride_data):
        # Never block UI / GPS threads
        threading.Thread(
            target=self._send_to_backend,
            args=(passenger_id, ride_data),
            daemon=True
        ).start()

    def _send_to_backend(self, passenger_id, ride_data):
        try:
            payload = {
                "rideId": ride_data["ride_id"],
                "driverId": self.driver_id,
                "passengerId": str(passenger_id + 1),

                "startTime": ride_data["start_time"].isoformat(),
                "endTime": ride_data["end_time"].isoformat(),

                "startLatitude": ride_data["start_location"][0],
                "startLongitude": ride_data["start_location"][1],
                "endLatitude": ride_data["end_location"][0],
                "endLongitude": ride_data["end_location"][1],

                "distanceKm": ride_data["total_distance_km"],
                "fareAmount": ride_data["fare_amount"],
                "fareRate": ride_data["fare_rate_per_km"]
            }

            url = f"{self.base_url}/api/fares/autometer"

            response = self.session.post(
                url,
                json=payload,
                timeout=5
            )

            if response.status_code != 200:
                print(f"⚠️ Fare sync failed: {response.status_code} {response.text}")
            else:
                print("✅ Fare synced to backend")

        except Exception as e:
            print(f"❌ Backend sync error: {e}")

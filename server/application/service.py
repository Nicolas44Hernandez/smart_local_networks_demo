"""Wifi 5GHz band on/off managment package"""

import logging
from flask import Flask
from datetime import timedelta
from timeloop import Timeloop
from server.managers.smart_band_manager import band_5GHz_manager_service
from server.managers.wifi_bands_ssh_manager import wifi_bands_manager_service

logger = logging.getLogger(__name__)

predictions_timeloop = Timeloop()

class WiFiCountersPollAndPredict:
    """Manager for wifi band counters polling and on/off control"""
    counters_polling_period_in_secs: int

    def __init__(self, app: Flask = None) -> None:
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize WiFiBandManager"""
        if app is not None:
            logger.info("initializing the WiFiCountersPollAndPredict")
            # Initialize configuration
            self.counters_polling_period_in_secs = app.config["WIFI_COUNTERS_POLLING_PERIOD_IN_SECS"]

            # Activate all the wifi bands
            wifi_bands_manager_service.set_band_status(band="2.4GHz", status=True)
            wifi_bands_manager_service.set_band_status(band="5GHz", status=True)
            wifi_bands_manager_service.set_band_status(band="6GHz", status=True)

            # Schedule ressources polling
            self.schedule_predictions()

    def schedule_predictions(self):
        """Schedule the counters polling and predictions"""

        # 5GHz on/off management
        @predictions_timeloop.job(
            interval=timedelta(seconds=self.counters_polling_period_in_secs)
        )
        def poll_wifi_counters_and_perform_inference():
            # Notify service status to cloud server
            band_5GHz_manager_service.notify_service_status_to_cloud_server()
            #logger.info(f"Update counters and perform prediction")
            band_5GHz_manager_service.update_counters()
            #logger.info(f"5GHz prediction done")
            band_5GHz_manager_service.perform_rtt_predictions_model_1()
            # Evaluate 5GHz band status
            #band_5GHz_manager_service.evaluate_5GHz_band_on_off()

        predictions_timeloop.start(block=False)



poll_and_predict_manager_service: WiFiCountersPollAndPredict = WiFiCountersPollAndPredict()

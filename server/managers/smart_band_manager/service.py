"""Wifi 5GHz band on/off managment package"""

import logging
import json
import requests
from requests.exceptions import ConnectionError, InvalidURL
from flask import Flask
from datetime import datetime, timedelta
from statistics import mean
from server.managers.wifi_bands_ssh_manager import wifi_bands_manager_service
from .rtt_predictor import RttPredictor
from .model import BandCounters, StationCounters

logger = logging.getLogger(__name__)

class Wifi5GHzOnOffManager:
    """Manager for 5GHz on/off control"""
    box_counters_2GHz: BandCounters
    box_counters_5GHz: BandCounters
    wifi_5GHz_band_status: bool
    samples_array_len: int
    nb_of_rtt_predictions_to_store: int
    min_predicted_rtt: float
    stations_counters: dict
    connected_stations: dict
    max_last_seen_in_secs: int
    predictor: RttPredictor
    rtt_th_for_5GHz_on: float
    service_active: bool
    rtt_predictions_cloud_ip: str
    rtt_predictions_cloud_port: int
    rtt_predictions_cloud_path: str
    rtt_predictions_service_status_cloud_path: str
    last_sample_timestamp: datetime


    def __init__(self, app: Flask = None) -> None:
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize WiFiBandManager"""
        if app is not None:
            logger.info("initializing the WiFiBandManager")
            # Initialize configuration
            self.box_counters_2GHz = None
            self.box_counters_5GHz = None
            self.wifi_5GHz_band_status=wifi_bands_manager_service.get_band_status(band="5GHz")
            self.samples_array_len = app.config["PREDICTIONS_NB_OF_SAMPLES"]
            self.nb_of_rtt_predictions_to_store = app.config["NB_OF_RTT_PREDICTIONS_TO_STORE"]
            self.min_predicted_rtt = app.config["MIN_PREDICTED_RTT_IN_MS"]
            self.stations_counters = {}
            self.connected_stations = {}
            self.max_last_seen_in_secs = app.config["MAX_LAST_SEEN_IN_SECS"]
            self.predictor=RttPredictor(
                model_path=app.config["RTT_PREDICTOR_MODEL"],
                scaler_path=app.config["RTT_PREDICTOR_SCALER"],
                min_predicted_rtt=self.min_predicted_rtt,
            )

            self.rtt_th_for_5GHz_on=app.config["PREDICTED_RTT_TH_5GHZ_ON"]
            self.service_active=app.config["ON_OFF_5GHZ_SERVICE_ACTIVE"]
            self.rtt_predictions_cloud_ip=app.config["RTT_PREDICTIONS_CLOUD_IP"]
            self.rtt_predictions_cloud_port=app.config["RTT_PREDICTIONS_CLOUD_PORT"]
            self.rtt_predictions_cloud_path=app.config["RTT_PREDICTIONS_CLOUD_PATH"]
            self.rtt_predictions_service_status_cloud_path=app.config["RTT_PREDICTIONS_SERVICE_STATUS_PATH"]
            self.last_sample_timestamp = None


    def update_counters(self):
        """Update counters and perform prediction"""

        # Update band counters
        if self.update_bands_counters(datetime.now()) is None:
            #self.log_counters()
            return

        # Purge old station counters
        self.purge_old_station_counters(datetime.now())

        # Update connected stations list
        self.update_connected_stations_list()

        # Update connected stations counters
        self.update_stations_counters()

        #self.log_counters()
        #logger.info("Band counters updated!")
        return

    def log_counters(self):
        """Log current counters"""
        if self.box_counters_2GHz is not None and self.box_counters_5GHz.last_rx_bytes is not None:
            logger.info(f"last_sample_timestamp:{self.last_sample_timestamp}")
            logger.info(f"*** 2GHz  rxrtry_pps:{self.box_counters_2GHz.rxrtry_pps} txfail_pps:{self.box_counters_2GHz.txfail_pps} txretrans_pps:{self.box_counters_2GHz.txretrans_pps} txerror_pps:{self.box_counters_2GHz.txerror_pps}  rxcrc_pps:{self.box_counters_2GHz.rxcrc_pps} tx_Mbps:{self.box_counters_2GHz.tx_Mbps} rx_Mbps:{self.box_counters_2GHz.rx_Mbps}")
            logger.info(f"*** 5GHz  rxrtry_pps:{self.box_counters_5GHz.rxrtry_pps} txfail_pps:{self.box_counters_5GHz.txfail_pps} txretrans_pps:{self.box_counters_5GHz.txretrans_pps} txerror_pps:{self.box_counters_5GHz.txerror_pps}  rxcrc_pps:{self.box_counters_5GHz.rxcrc_pps} tx_Mbps:{self.box_counters_5GHz.tx_Mbps} rx_Mbps:{self.box_counters_5GHz.rx_Mbps}")

        # logger.info(f"Connected stations: {[self.stations_counters[station].mac for station in self.stations_counters]}")
        # logger.info(f"Stations counters:")
        # for station in self.stations_counters:
        #     tx_str = ','.join("{:2.02f}".format(x) for x in self.stations_counters[station].tx_Mbps)
        #     rx_str = ','.join("{:2.02f}".format(x) for x in self.stations_counters[station].rx_Mbps)
        #     rtt_str = ','.join("{:2.02f}".format(x) for x in self.stations_counters[station].rtt_predictions)
        #     logger.info(f"*** {station}: tx_Mbps:[{tx_str}]  rx_str:[{rx_str}]  rtt_pred:[{rtt_str}]")
            #logger.info(f"*** {station}: tx_Mbps:{self.stations_counters[station].tx_Mbps}   rx_Mbps:{self.stations_counters[station].rx_Mbps}   rtt_predictions:{self.stations_counters[station].rtt_predictions}")
            #logger.info(f"*** {station}: smooth_rssi:{self.stations_counters[station].smooth_rssi}")
            #logger.info(f"*** {station}: tx_retried_pps:{self.stations_counters[station].tx_retried_pps} rx_retried_pps:{self.stations_counters[station].rx_retried_pps}  tx_retries_pps:{self.stations_counters[station].tx_retries_pps} rx_decrypt_pps:{self.stations_counters[station].rx_decrypt_pps}  tx_failures_pps:{self.stations_counters[station].tx_failures_pps}  tx_pkts_pps:{self.stations_counters[station].tx_pkts_pps}  rx_pkts_pps:{self.stations_counters[station].rx_pkts_pps} tx_pkts_retries_rate:{self.stations_counters[station].tx_pkts_retries_rate} idle:{self.stations_counters[station].idle}")

    def restart_counters(self):
        """Restart bands counters and stations counters"""
        self.last_sample_timestamp = None
        self.box_counters_2GHz = None
        self.box_counters_2GHz = None
        self.stations_counters = {}

    def update_bands_counters(self, timestamp: datetime) -> bool:
        """Update wifi bands counters"""

        # Get bands counters sample
        txbytes_2GHz, rxbytes_2GHz, rxrtry_2GHz, txfail_2GHz, txretrans_2GHz, txerror_2GHz, rxcrc_2GHz = self.get_band_tx_rx_counters(band="2.4GHz")
        txbytes_5GHz, rxbytes_5GHz, rxrtry_5GHz, txfail_5GHz, txretrans_5GHz, txerror_5GHz, rxcrc_5GHz = self.get_band_tx_rx_counters(band="5GHz")

        # If its the first sample or values are set to None
        if self.last_sample_timestamp is None:
            self.last_sample_timestamp = timestamp
            self.box_counters_2GHz=BandCounters(
                tx_Mbps=[],
                rx_Mbps=[],
                last_tx_bytes=txbytes_2GHz,
                last_rx_bytes=rxbytes_2GHz,
                last_rxrtry=rxrtry_2GHz,
                last_txfail=txfail_2GHz,
                last_txretrans=txretrans_2GHz,
                last_txerror=txerror_2GHz,
                last_rxcrc=rxcrc_2GHz,
                rxrtry_pps=None,
                txfail_pps=None,
                txretrans_pps=None,
                txerror_pps=None,
                rxcrc_pps=None,
            )
            self.box_counters_5GHz=BandCounters(
                tx_Mbps=[],
                rx_Mbps=[],
                last_tx_bytes=txbytes_5GHz,
                last_rx_bytes=rxbytes_5GHz,
                last_rxrtry=rxrtry_5GHz,
                last_txfail=txfail_5GHz,
                last_txretrans=txretrans_5GHz,
                last_txerror=txerror_5GHz,
                last_rxcrc=rxcrc_5GHz,
                rxrtry_pps=None,
                txfail_pps=None,
                txretrans_pps=None,
                txerror_pps=None,
                rxcrc_pps=None,
            )
            logger.info("First txbytes and rxbytes sample setted")
            return None

        # Calculate deltatime with last sample
        _delta = timestamp - self.last_sample_timestamp
        delta_time_in_secs = _delta.seconds + (_delta.microseconds / 1000000.0)

        # If delta is too old restart counters
        if delta_time_in_secs > self.max_last_seen_in_secs:
            logger.info("Last sample taken is too old, restarting counters")
            self.restart_counters()
            return None

        # Log sample counters
        logger.info(f"*** 2GHz txbytes_2GHz:{txbytes_2GHz} rxbytes_2GHz:{rxbytes_2GHz} rxrtry_2GHz:{rxrtry_2GHz} txfail_2GHz:{txfail_2GHz} txretrans_2GHz:{txretrans_2GHz} txerror_2GHz:{txerror_2GHz} rxcrc_2GHz:{rxcrc_2GHz}")
        logger.info(f"*** 5GHz txbytes_5GHz:{txbytes_5GHz} rxbytes_5GHz:{rxbytes_5GHz} rxrtry_5GHz:{rxrtry_5GHz} txfail_5GHz:{txfail_5GHz} txretrans_5GHz:{txretrans_5GHz} txerror_5GHz:{txerror_5GHz} rxcrc_5GHz:{rxcrc_5GHz}")

        # Check that counters are not None
        if self.box_counters_2GHz is None or self.box_counters_2GHz is None:
            logger.error("Error, counters are None")
            return False

        # Compute rx and tx bytes since last sample
        txbytes_sample_2GHz = txbytes_2GHz - self.box_counters_2GHz.last_tx_bytes
        rxbytes_sample_2GHz = rxbytes_2GHz - self.box_counters_2GHz.last_rx_bytes
        txbytes_sample_5GHz = txbytes_5GHz - self.box_counters_5GHz.last_tx_bytes
        rxbytes_sample_5GHz = rxbytes_5GHz - self.box_counters_5GHz.last_rx_bytes

        # Fix for negative (32 bits cyclic counter)
        if txbytes_sample_2GHz < 0:
            txbytes_sample_2GHz = txbytes_2GHz + (2**32 - self.box_counters_2GHz.last_tx_bytes)
        if rxbytes_sample_2GHz < 0:
            rxbytes_sample_2GHz = rxbytes_2GHz + (2**32 - self.box_counters_2GHz.last_rx_bytes)
        if txbytes_sample_5GHz < 0:
            txbytes_sample_5GHz = txbytes_5GHz + (2**32 - self.box_counters_5GHz.last_tx_bytes)
        if rxbytes_sample_5GHz < 0:
            rxbytes_sample_5GHz = rxbytes_5GHz + (2**32 - self.box_counters_5GHz.last_rx_bytes)

        # Compute throughput in Mbps
        tx_rate_2GHz_Mbps = (txbytes_sample_2GHz * (8 / 1000000)) / delta_time_in_secs
        rx_rate_2GHz_Mbps = (rxbytes_sample_2GHz * (8 / 1000000)) / delta_time_in_secs
        tx_rate_5GHz_Mbps = (txbytes_sample_5GHz * (8 / 1000000)) / delta_time_in_secs
        rx_rate_5GHz_Mbps = (rxbytes_sample_5GHz * (8 / 1000000)) / delta_time_in_secs

        # Log throughput in Mbps
        logger.info(f"--- 2.4GHz tx_rate_2GHz_Mbps:{tx_rate_2GHz_Mbps} rx_rate_2GHz_Mbps:{rx_rate_2GHz_Mbps}")
        logger.info(f"---   5GHz tx_rate_5GHz_Mbps:{tx_rate_5GHz_Mbps} rx_rate_5GHz_Mbps:{rx_rate_5GHz_Mbps}")
        logger.info(f"deltatime: {delta_time_in_secs} secs")

        # Compute pps values
        rxrtry_pps_2GHz = (rxrtry_2GHz - self.box_counters_2GHz.last_rxrtry) / delta_time_in_secs
        txfail_pps_2GHz = (txfail_2GHz - self.box_counters_2GHz.last_txfail) / delta_time_in_secs
        txretrans_pps_2GHz = (txretrans_2GHz - self.box_counters_2GHz.last_txretrans) / delta_time_in_secs
        txerror_pps_2GHz = (txerror_2GHz - self.box_counters_2GHz.last_txerror) / delta_time_in_secs
        rxcrc_pps_2GHz = (rxcrc_2GHz - self.box_counters_2GHz.last_rxcrc) / delta_time_in_secs
        rxrtry_pps_5GHz = (rxrtry_5GHz - self.box_counters_5GHz.last_rxrtry) / delta_time_in_secs
        txfail_pps_5GHz = (txfail_5GHz - self.box_counters_5GHz.last_txfail) / delta_time_in_secs
        txretrans_pps_5GHz = (txretrans_5GHz - self.box_counters_5GHz.last_txretrans) / delta_time_in_secs
        txerror_pps_5GHz = (txerror_5GHz - self.box_counters_5GHz.last_txerror) / delta_time_in_secs
        rxcrc_pps_5GHz = (rxcrc_5GHz - self.box_counters_5GHz.last_rxcrc) / delta_time_in_secs

        # Log pps values
        logger.info(f"--- 2.4GHz rxrtry_pps_2GHz:{rxrtry_pps_2GHz} txfail_pps_2GHz:{txfail_pps_2GHz} txretrans_pps_2GHz:{txretrans_pps_2GHz} txerror_pps_2GHz:{txerror_pps_2GHz} rxcrc_pps_2GHz:{rxcrc_pps_2GHz}")
        logger.info(f"---   5GHz rxrtry_pps_5GHz:{rxrtry_pps_5GHz} txfail_pps_5GHz:{txfail_pps_5GHz} txretrans_pps_5GHz:{txretrans_pps_5GHz} txerror_pps_5GHz:{txerror_pps_5GHz} rxcrc_pps_5GHz:{rxcrc_pps_5GHz}")

        # Update last sample taken value
        self.last_sample_timestamp = timestamp
        self.box_counters_2GHz.last_tx_bytes = txbytes_2GHz
        self.box_counters_2GHz.last_rx_bytes = rxbytes_2GHz
        self.box_counters_2GHz.last_rxrtry = rxrtry_2GHz
        self.box_counters_2GHz.last_txfail = txfail_2GHz
        self.box_counters_2GHz.last_txretrans = txretrans_2GHz
        self.box_counters_2GHz.last_txerror = txerror_2GHz
        self.box_counters_2GHz.last_rxcrc = rxcrc_2GHz
        self.box_counters_2GHz.rxrtry_pps = rxrtry_pps_2GHz
        self.box_counters_2GHz.txfail_pps = txfail_pps_2GHz
        self.box_counters_2GHz.txretrans_pps = txretrans_pps_2GHz
        self.box_counters_2GHz.txerror_pps = txerror_pps_2GHz
        self.box_counters_2GHz.rxcrc_pps = rxcrc_pps_2GHz
        self.box_counters_5GHz.last_tx_bytes = txbytes_5GHz
        self.box_counters_5GHz.last_rx_bytes = rxbytes_5GHz
        self.box_counters_5GHz.last_rxrtry=rxrtry_5GHz
        self.box_counters_5GHz.last_txfail=txfail_5GHz
        self.box_counters_5GHz.last_txretrans=txretrans_5GHz
        self.box_counters_5GHz.last_txerror=txerror_5GHz
        self.box_counters_5GHz.last_rxcrc = rxcrc_5GHz
        self.box_counters_5GHz.rxrtry_pps = rxrtry_pps_5GHz
        self.box_counters_5GHz.txfail_pps = txfail_pps_5GHz
        self.box_counters_5GHz.txretrans_pps = txretrans_pps_5GHz
        self.box_counters_5GHz.txerror_pps = txerror_pps_5GHz
        self.box_counters_5GHz.rxcrc_pps = rxcrc_pps_5GHz

        # Fill trafics arrays
        # IF array not fully filled
        if len(self.box_counters_2GHz.tx_Mbps) < self.samples_array_len and len(self.box_counters_5GHz.tx_Mbps) < self.samples_array_len:
            self.box_counters_2GHz.tx_Mbps.append(tx_rate_2GHz_Mbps)
            self.box_counters_2GHz.rx_Mbps.append(rx_rate_2GHz_Mbps)
            self.box_counters_5GHz.tx_Mbps.append(tx_rate_5GHz_Mbps)
            self.box_counters_5GHz.rx_Mbps.append(rx_rate_5GHz_Mbps)
        # If array is already filled
        else:
            self.box_counters_2GHz.tx_Mbps = self.box_counters_2GHz.tx_Mbps[1:] + [tx_rate_2GHz_Mbps]
            self.box_counters_2GHz.rx_Mbps = self.box_counters_2GHz.rx_Mbps[1:] + [rx_rate_2GHz_Mbps]
            self.box_counters_5GHz.tx_Mbps = self.box_counters_5GHz.tx_Mbps[1:] + [tx_rate_5GHz_Mbps]
            self.box_counters_5GHz.rx_Mbps = self.box_counters_5GHz.rx_Mbps[1:] + [rx_rate_5GHz_Mbps]

        return True

    def get_band_tx_rx_counters(self, band:str):
        """Retrieve band tx and rx counters"""
        try:
            # Get tx and rx values
            commands_response = wifi_bands_manager_service.execute_commands(["WIFI", "counters", band])
            txbyte = int(commands_response.split("txbyte")[1].split(" ")[1])
            rxbyte = int(commands_response.split("rxbyte")[1].split(" ")[1])
            rxrtry = int(commands_response.split("rxrtry")[1].split(" ")[1])
            txfail = int(commands_response.split("txfail")[1].split(" ")[1])
            txretrans = int(commands_response.split("txretrans")[1].split(" ")[1])
            txerror = int(commands_response.split("txerror")[1].split(" ")[1])
            rxcrc = int(commands_response.split("rxcrc")[1].split(" ")[1])
            return txbyte, rxbyte, rxrtry, txfail, txretrans, txerror, rxcrc
        except Exception:
            logger.error("Error in counters command execution")
            return None, None, None, None, None, None, None

    def purge_old_station_counters(self, timestamp):
        # Get stations to delete
        stations_to_delete = []
        for station in self.stations_counters:
            delta = timestamp - self.stations_counters[station].last_sample_timestamp
            #logger.info(f"For station {station} delatime={delta}")
            if delta > timedelta(seconds=self.max_last_seen_in_secs):
                stations_to_delete.append(station)

        # Clean stations list
        for station_to_delete in stations_to_delete:
            logger.info(f"Deleting station: {station_to_delete}")
            self.stations_counters.pop(station_to_delete)

    def update_connected_stations_list(self):
        """Update connected stations list"""
        # Get connected stations and band
        self.connected_stations = {}
        total_connections, connected_stations_2_4GHz, connected_stations_5GHz = wifi_bands_manager_service.get_connected_stations_by_band_mac_list()
        for station in connected_stations_2_4GHz:
            self.connected_stations[station]="2.4GHz"
        for station in connected_stations_5GHz:
            self.connected_stations[station]="5GHz"

    def update_stations_counters(self) -> bool:
        """Update connected stations counters"""

        # Loop over connected stations to get samples
        for station in self.connected_stations:
            # Get connected stations counters
            current_sample_timestamp=datetime.now()
            _band=self.connected_stations[station]
            station_txbytes, station_rxbytes, station_smooth_rssi, station_tx_retried, station_rx_retried, station_tx_retries, station_rx_decrypt, station_tx_failures, station_tx_pkts, station_rx_pkts, station_idle = self.get_station_tx_rx_counters(station_mac=station, band=_band)

            # If its the first sample or values are set to None
            if station not in self.stations_counters or self.stations_counters[station].band != _band :
                self.stations_counters[station] = StationCounters(
                    mac = station,
                    tx_Mbps = [],
                    rx_Mbps = [],
                    smooth_rssi=[],
                    last_tx_bytes = station_txbytes,
                    last_rx_bytes = station_rxbytes,
                    last_tx_retried = station_tx_retried,
                    last_rx_retried = station_rx_retried,
                    last_tx_retries = station_tx_retries,
                    last_rx_decrypt = station_rx_decrypt,
                    last_tx_failures = station_tx_failures,
                    last_tx_pkts = station_tx_pkts,
                    last_rx_pkts = station_rx_pkts,
                    tx_retried_pps = 0,
                    rx_retried_pps = 0,
                    tx_retries_pps = 0,
                    rx_decrypt_pps = 0,
                    tx_failures_pps = 0,
                    tx_pkts_pps = 0,
                    rx_pkts_pps = 0,
                    tx_pkts_retries_rate = 0,
                    idle=station_idle,
                    band = _band,
                    last_sample_timestamp = current_sample_timestamp,
                    rtt_predictions=[]
                )

                logger.info(f"First counters sample setted for station {station}")
                continue

            # Compute rx and tx bytes since last sample
            txbytes_sample = station_txbytes - self.stations_counters[station].last_tx_bytes
            rxbytes_sample = station_rxbytes - self.stations_counters[station].last_rx_bytes

            # Calculate deltatime
            _delta = current_sample_timestamp - self.stations_counters[station].last_sample_timestamp
            delta_time_in_secs = _delta.seconds + (_delta.microseconds / 1000000.0)

            # Compute station throughputs
            station_tx_rate_Mbps = (txbytes_sample * (8 / 1000000)) / delta_time_in_secs
            station_rx_rate_Mbps = (rxbytes_sample * (8 / 1000000)) / delta_time_in_secs

            # Compute PPS values
            station_tx_retried_pps = (station_tx_retried - self.stations_counters[station].last_tx_retried) / delta_time_in_secs
            station_rx_retried_pps = (station_rx_retried - self.stations_counters[station].last_rx_retried) / delta_time_in_secs
            station_tx_retries_pps = (station_tx_retries - self.stations_counters[station].last_tx_retries) / delta_time_in_secs
            station_rx_decrypt_pps = (station_rx_decrypt - self.stations_counters[station].last_rx_decrypt) / delta_time_in_secs
            station_tx_failures_pps = (station_tx_failures - self.stations_counters[station].last_tx_failures) / delta_time_in_secs
            station_tx_pps = (station_tx_pkts - self.stations_counters[station].last_tx_pkts) / delta_time_in_secs
            station_rx_pps = (station_rx_pkts - self.stations_counters[station].last_rx_pkts) / delta_time_in_secs
            station_tx_pkts_retries_rate = 0 if station_tx_pps == 0 else station_tx_retries_pps*100/station_tx_pps


            # Fix for negative datates (32 bits cyclic counter)
            if station_tx_rate_Mbps < 0 or station_rx_rate_Mbps < 0:
                logger.error("Error in sample, data discarted")
                continue

            # Update station counters with new values from sample
            self.stations_counters[station].last_tx_bytes=station_txbytes
            self.stations_counters[station].last_rx_bytes=station_rxbytes
            self.stations_counters[station].last_tx_retried = station_tx_retried
            self.stations_counters[station].last_rx_retried = station_rx_retried
            self.stations_counters[station].last_tx_retries = station_tx_retries
            self.stations_counters[station].last_rx_decrypt = station_rx_decrypt
            self.stations_counters[station].last_tx_failures = station_tx_failures
            self.stations_counters[station].last_tx_pkts = station_tx_pkts
            self.stations_counters[station].last_rx_pkts = station_rx_pkts
            self.stations_counters[station].tx_retried_pps = station_tx_retried_pps
            self.stations_counters[station].rx_retried_pps = station_rx_retried_pps
            self.stations_counters[station].tx_retries_pps = station_tx_retries_pps
            self.stations_counters[station].rx_decrypt_pps = station_rx_decrypt_pps
            self.stations_counters[station].tx_failures_pps = station_tx_failures_pps
            self.stations_counters[station].tx_pkts_pps = station_tx_pps
            self.stations_counters[station].rx_pkts_pps = station_rx_pps
            self.stations_counters[station].tx_pkts_retries_rate = station_tx_pkts_retries_rate
            self.stations_counters[station].idle = station_idle
            self.stations_counters[station].band=_band
            self.stations_counters[station].last_sample_timestamp=current_sample_timestamp

            # Fill station traffic arrays in counters
            # IF array not fully filled
            if len(self.stations_counters[station].tx_Mbps) < self.samples_array_len:
                self.stations_counters[station].tx_Mbps.append(station_tx_rate_Mbps)
                self.stations_counters[station].rx_Mbps.append(station_rx_rate_Mbps)
                self.stations_counters[station].smooth_rssi.append(station_smooth_rssi)
            # If array is already filled
            else:
                self.stations_counters[station].tx_Mbps = self.stations_counters[station].tx_Mbps[1:] + [station_tx_rate_Mbps]
                self.stations_counters[station].rx_Mbps = self.stations_counters[station].rx_Mbps[1:] + [station_rx_rate_Mbps]
                self.stations_counters[station].smooth_rssi = self.stations_counters[station].smooth_rssi[1:] + [station_smooth_rssi]

    def get_station_tx_rx_counters(self, station_mac: str, band: str):
        """Get the station rx and rx counters"""

        if station_mac not in wifi_bands_manager_service.get_connected_stations_mac_list():
            logger.error(f"Station {station_mac} not connected")
            return None

        commands_response = wifi_bands_manager_service.execute_commands(["WIFI", "counters", "station_info", band], station_mac=station_mac)
        try:
            txbyte = int(commands_response.split("tx total bytes")[1].split(": ")[1].split("\n")[0])
            rxbyte = int(commands_response.split("rx data bytes")[1].split(": ")[1].split("\n")[0])
            smooth_rssi = int(commands_response.split("smoothed rssi")[1].split(": ")[1].split("\n")[0])
            tx_retried = int(commands_response.split("tx pkts retries")[1].split(": ")[1].split("\n")[0])
            rx_retried = int(commands_response.split("rx total pkts retried")[1].split(": ")[1].split("\n")[0])
            tx_retries = int(commands_response.split("tx pkts retries")[1].split(": ")[1].split("\n")[0])
            rx_decrypt = int(commands_response.split("rx decrypt succeeds")[1].split(": ")[1].split("\n")[0])
            tx_failures = int(commands_response.split("tx failures")[1].split(": ")[1].split("\n")[0])
            tx_pkts = int(commands_response.split("tx total pkts")[1].split(": ")[1].split("\n")[0])
            rx_pkts = int(commands_response.split("rx data pkts")[1].split(": ")[1].split("\n")[0])
            idle = int(commands_response.split("idle")[1].split(" ")[1])
        except:
            logger.error("Error retreiving counters all counters are assumed to 0 Mbps ")
            return 0,0,0,0,0,0,0,0,0,0,0
        return txbyte, rxbyte, smooth_rssi, tx_retried, rx_retried, tx_retries, rx_decrypt, tx_failures, tx_pkts, rx_pkts, idle

    def perform_rtt_predictions_model_1(self):
        """Get compute values and perform RTT predictions"""

        #Check if service is active
        if not self.service_active:
            logger.info(f"5GHz ON/OFF service is inactive")
            return

        # Update 5GHz band status
        self.wifi_5GHz_band_status=wifi_bands_manager_service.get_band_status(band="5GHz")

        # Flag for prediction
        perform_prediction = True

        # Evaluate last sample total throughput

        if len(self.box_counters_2GHz.tx_Mbps) < self.samples_array_len or len(self.box_counters_5GHz.tx_Mbps) < self.samples_array_len:
            logger.info(f"Not enought samples in box counters to perorm prediction")
            return

        last_sample_total_tx_throughput_Mbps = self.box_counters_2GHz.tx_Mbps[6] + self.box_counters_5GHz.tx_Mbps[6]
        last_sample_total_rx_throughput_Mbps = self.box_counters_2GHz.rx_Mbps[6] + self.box_counters_5GHz.rx_Mbps[6]
        last_sample_total_throughput =  last_sample_total_tx_throughput_Mbps + last_sample_total_rx_throughput_Mbps
        last_sample_2GHz_total_throughput =  self.box_counters_2GHz.tx_Mbps[6] + self.box_counters_2GHz.rx_Mbps[6]
        last_sample_5GHz_total_throughput =  self.box_counters_5GHz.tx_Mbps[6] + self.box_counters_5GHz.rx_Mbps[6]
        low_rtt = False

        if last_sample_total_throughput < 0.02:
            if not self.wifi_5GHz_band_status:
                logger.info("Prediction not performed, total throughput is too low")
                perform_prediction = False
            else:
                low_rtt=True
                logger.info("Prediction not performed, total throughput is too low and 5GHz is ON")

        if last_sample_total_throughput > 40:
            perform_prediction = False
            logger.info("Prediction not performed, total throughput is too high")

        # Used to notify cloud
        iteration_predictions = {}

        # Perform predictions
        for station in self.stations_counters:

            # Evaluate last sample total throughput
            if len(self.stations_counters[station].tx_Mbps) < self.samples_array_len:
                logger.info(f"Not enought samples in station {station} to predict")
                iteration_predictions[station]={"predicted_rtt": self.min_predicted_rtt, "traffic": 0}
                continue
            try:
                station_last_sample_tx_traffic = self.stations_counters[station].tx_Mbps[6]
                station_last_sample_rx_traffic = self.stations_counters[station].rx_Mbps[6]
                station_total_traffic = station_last_sample_tx_traffic + station_last_sample_rx_traffic
                high_rate = False

                if station_total_traffic > 40:
                    perform_prediction = False
                    high_rate = True
                    #logger.info(f"Prediction not performed, total throughput for station {station} is too high")

                # For low troughtputs assume low RTT
                if low_rtt or not perform_prediction:
                    predicted_rtt = self.min_predicted_rtt
                    #logger.info(f"RTT assumed for {station}: {self.min_predicted_rtt}")

                if high_rate and not perform_prediction:
                    #logger.info(f"RTT assumed for {station}: 180")
                    predicted_rtt = 180

                # if not low throughput in box but low traffic in station assume low RTT
                elif station_total_traffic < 0.02:
                    #logger.info(f"Prediction not performed, total throughput for station {station} is too low")
                    logger.info(f"RTT assumed for {station}: {self.min_predicted_rtt}")
                    predicted_rtt = self.min_predicted_rtt

                else:
                    predicted_rtt = self.predictor.predict_rtt(
                        tx_Mbps_2g=last_sample_total_tx_throughput_Mbps,
                        rx_Mbps_2g=last_sample_total_rx_throughput_Mbps,
                        tx_Mbps=station_last_sample_tx_traffic,
                        rx_Mbps=station_last_sample_rx_traffic,
                    )

                # Store prediction in array
                if len(self.stations_counters[station].rtt_predictions) < self.nb_of_rtt_predictions_to_store:
                    self.stations_counters[station].rtt_predictions.append(predicted_rtt)
                # If array is already filled
                else:
                    self.stations_counters[station].rtt_predictions = self.stations_counters[station].rtt_predictions[1:] + [predicted_rtt]

                iteration_predictions[station]={"predicted_rtt": predicted_rtt, "traffic": station_total_traffic}
                #logger.info(f"For station {station} instant predicted_RTT={predicted_rtt}")

            except Exception as e:
                logger.error("Error in prediction")

        # logger.info(f"LiveboxTraffic: {last_sample_total_throughput}")
        # logger.info(f"rtt_predictions: {iteration_predictions}")

        self.notify_rtt_prediction_to_cloud_server(
            livebox_traffic=last_sample_total_throughput,
            band_5GHz_traffic=last_sample_5GHz_total_throughput,
            band_2GHz_traffic=last_sample_2GHz_total_throughput,
            rtt_predictions=iteration_predictions
        )

    def notify_rtt_prediction_to_cloud_server(
            self,
            livebox_traffic: float,
            band_5GHz_traffic: float,
            band_2GHz_traffic: float,
            rtt_predictions: dict
        ):
        """Notify rtt predictions to cloud"""
        #logger.info(f"Posting HTTP to notify rtt predictions to RPI cloud")

        # Construct string
        station_counters = []
        for station in rtt_predictions:
            station_counters.append(
                {
                    "mac": station,
                    "rtt": rtt_predictions[station]["predicted_rtt"],
                    "traffic_Mbps": rtt_predictions[station]["traffic"]
                }
            )
        station_counters_str = json.dumps(station_counters)

        # Get band status
        band_status = 1 if self.wifi_5GHz_band_status else 0

        # Prepare data to send
        data_to_send = {
            "livebox_traffic": livebox_traffic,
            "traffic_5GHz": band_5GHz_traffic,
            "traffic_2GHz": band_2GHz_traffic,
            "band_5ghz_status": band_status,
            "stations_counters": station_counters_str,
        }
        # Post rtt predictions to rpi cloud
        post_url = (
                f"http://{self.rtt_predictions_cloud_ip}:{self.rtt_predictions_cloud_port}/{self.rtt_predictions_cloud_path}"
            )
        try:
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            rpi_cloud_response = requests.post(
                post_url, data=(data_to_send), headers=headers
            )
        except (ConnectionError, InvalidURL):
            logger.error(
                f"Error when posting rtt notification to rpi cloud, check if rpi cloud"
                f" server is running"
            )

    def notify_service_status_to_cloud_server(self):
        """Notify automatic 5GHz ON/OFF service status"""

        logger.info(f"notify service status {self.service_active} to cloud service ")
        # Prepare data to send
        data_to_send = {"status": self.service_active}
        # Post rtt predictions to rpi cloud
        post_url = (
                f"http://{self.rtt_predictions_cloud_ip}:{self.rtt_predictions_cloud_port}/{self.rtt_predictions_service_status_cloud_path}"
            )
        try:
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            rpi_cloud_response = requests.post(
                post_url, data=(data_to_send), headers=headers
            )
        except (ConnectionError, InvalidURL):
            logger.error(
                f"Error when posting rtt notification to rpi cloud, check if rpi cloud"
                f" server is running"
            )

    def set_service_status(self, status:bool):
        """Set service status active/inactive"""
        self.service_active=status

    def get_service_status(self):
        """Get service status"""
        return self.service_active

    def evaluate_5GHz_band_on_off(self):
        """Evaluate if its necessary to turn on/off  5GHz band"""

        new_band_status = None
        for station in self.stations_counters:
            #If the avg rtt predictions list for station is full
            if len(self.stations_counters[station].rtt_predictions) == self.nb_of_rtt_predictions_to_store:
                # Get max value
                avg_rtt = mean(self.stations_counters[station].rtt_predictions)
                max_rtt = max(self.stations_counters[station].rtt_predictions)
                logger.info(f"station:{station}  mean rtt:{avg_rtt}")
                # If average rtt for at least one station is higher than threshold turn on 5GHz band
                if avg_rtt >= self.rtt_th_for_5GHz_on:
                    new_band_status=True
                    break
                else:
                    new_band_status=False

        if new_band_status is not None:
            if self.wifi_5GHz_band_status != new_band_status:
                status = "ON" if new_band_status else "OFF"
                logger.info(f"Setting 5GHz BAND {status}")
                wifi_bands_manager_service.set_band_status(band="5GHz", status=new_band_status)
                self.wifi_5GHz_band_status=new_band_status


band_5GHz_manager_service: Wifi5GHzOnOffManager = Wifi5GHzOnOffManager()
""" Wifi 5GHz on/off manager service singleton"""

"""
RTT Classifier service
"""
import joblib
import pickle
import numpy as np
import logging
from server.common import ServerException, ErrorCode
from server.managers.smart_band_manager.model import BandCounters, StationCounters

logger = logging.getLogger(__name__)

class RttClassifier:
    """Service class for RTT Classification by using a ML model"""
    #TODO: new attributes ?
    model: str # TODO: add model type
    scaler: str # TODO: add scaler type
    min_predicted_rtt: float

    def __init__(self, model_path: str, scaler_path: str, min_predicted_rtt: float):
        #TODO: How to load model
        self.scaler = self.load_scaler(scaler_path=scaler_path)
        self.model = self.load_model(model_path=model_path)
        self.min_predicted_rtt=[min_predicted_rtt]

    def load_scaler(self, scaler_path: str):
        """Load scaler for data transformation"""
        # TODO: necessary ?
        logger.info(f"Loading scaler: {scaler_path}")
        try:
            return joblib.load(scaler_path)
        except:
            logger.error("Error in scaler load")
            raise ServerException(ErrorCode.ERROR_IN_PREDICTOR_MODEL_LOAD)

    def load_model(self, model_path: str):
        # TODO: necessary ?
        """Load model to RTT prediction inferences"""
        logger.info(f"Loading model: {model_path}")
        try:
            return pickle.load(open(model_path, 'rb'))
        except:
            logger.error("Error in model load")
            raise ServerException(ErrorCode.ERROR_IN_PREDICTOR_MODEL_LOAD)

    def validate_2GHz_counters_for_classification(self, band_counters: BandCounters, samples_array_len: int) -> bool:
        ################## BOX ########################
        #tx_Mbps=[],
        # rx_Mbps=[],
        # rxrtry_pps=None,
        # txfail_pps=None,
        # txretrans_pps=None,
        # txerror_pps=None,
        ###############################################
        """Healt check for band counters before perform prediction"""
        if len(band_counters.tx_Mbps)!= samples_array_len:
            logger.error(f"Error in array input tx_Mbps:{band_counters.tx_Mbps} len must be {samples_array_len}")
            raise ServerException(ErrorCode.ERROR_IN_RTT_CLASSIFICATION)
        if len(band_counters.rx_Mbps)!= samples_array_len:
            logger.error(f"Error in array input rx_Mbps:{band_counters.rx_Mbps} len must be {samples_array_len}")
            raise ServerException(ErrorCode.ERROR_IN_RTT_CLASSIFICATION)
        if band_counters.rxrtry_pps is None:
            logger.error(f"Error in input rxrtry_pps:{band_counters.rxrtry_pps} len must be not None")
            raise ServerException(ErrorCode.ERROR_IN_RTT_CLASSIFICATION)
        if band_counters.txfail_pps is None:
            logger.error(f"Error in input txfail_pps:{band_counters.txfail_pps} len must be not None")
            raise ServerException(ErrorCode.ERROR_IN_RTT_CLASSIFICATION)
        if band_counters.txretrans_pps is None:
            logger.error(f"Error in input txretrans_pps:{band_counters.txretrans_pps} len must be not None")
            raise ServerException(ErrorCode.ERROR_IN_RTT_CLASSIFICATION)
        if band_counters.txerror_pps is None:
            logger.error(f"Error in input txerror_pps:{band_counters.txerror_pps} len must be not None")
            raise ServerException(ErrorCode.ERROR_IN_RTT_CLASSIFICATION)

        # if everything is ok return True
        return True

    def validate_station_counters_for_classification(self, station_counters: StationCounters, samples_array_len: int) -> bool:
        """Healt check for station counters before perform prediction"""
        ################## STATION ########################
        # tx_Mbps = [],
        # rx_Mbps = [],
        # smooth_rssi=[],
        # tx_retried_pps = 0,
        # rx_retried_pps = 0,
        # tx_retries_pps = 0,
        # rx_decrypt_pps = 0,
        # tx_failures_pps = 0,
        # tx_pkts_pps = 0,
        # rx_pkts_pps = 0,
        # tx_pkts_retries_rate = 0,
        ###############################################

        if len(station_counters.tx_Mbps)!= samples_array_len:
            logger.error(f"Error in array input tx_Mbps:{station_counters.tx_Mbps} len must be {samples_array_len}")
            raise ServerException(ErrorCode.ERROR_IN_RTT_CLASSIFICATION)
        if len(station_counters.rx_Mbps)!= samples_array_len:
            logger.error(f"Error in array input rx_Mbps:{station_counters.rx_Mbps} len must be {samples_array_len}")
            raise ServerException(ErrorCode.ERROR_IN_RTT_CLASSIFICATION)
        if len(station_counters.smooth_rssi)!= samples_array_len:
            logger.error(f"Error in array input smooth_rssi:{station_counters.smooth_rssi} len must be {samples_array_len}")
            raise ServerException(ErrorCode.ERROR_IN_RTT_CLASSIFICATION)
        if station_counters.tx_retried_pps is None:
            logger.error(f"Error in input tx_retried_pps:{station_counters.tx_retried_pps} len must be not None")
            raise ServerException(ErrorCode.ERROR_IN_RTT_CLASSIFICATION)
        if station_counters.rx_retried_pps is None:
            logger.error(f"Error in input rx_retried_pps:{station_counters.rx_retried_pps} len must be not None")
            raise ServerException(ErrorCode.ERROR_IN_RTT_CLASSIFICATION)
        if station_counters.tx_retries_pps is None:
            logger.error(f"Error in input tx_retries_pps:{station_counters.tx_retries_pps} len must be not None")
            raise ServerException(ErrorCode.ERROR_IN_RTT_CLASSIFICATION)
        if station_counters.rx_decrypt_pps is None:
            logger.error(f"Error in input rx_decrypt_pps:{station_counters.rx_decrypt_pps} len must be not None")
            raise ServerException(ErrorCode.ERROR_IN_RTT_CLASSIFICATION)
        if station_counters.tx_failures_pps is None:
            logger.error(f"Error in input tx_failures_pps:{station_counters.tx_failures_pps} len must be not None")
            raise ServerException(ErrorCode.ERROR_IN_RTT_CLASSIFICATION)
        if station_counters.tx_pkts_pps is None:
            logger.error(f"Error in input tx_pkts_pps:{station_counters.tx_pkts_pps} len must be not None")
            raise ServerException(ErrorCode.ERROR_IN_RTT_CLASSIFICATION)
        if station_counters.rx_pkts_pps is None:
            logger.error(f"Error in input rx_pkts_pps:{station_counters.rx_pkts_pps} len must be not None")
            raise ServerException(ErrorCode.ERROR_IN_RTT_CLASSIFICATION)
        if station_counters.tx_pkts_retries_rate is None:
            logger.error(f"Error in input tx_pkts_retries_rate:{station_counters.tx_pkts_retries_rate} len must be not None")
            raise ServerException(ErrorCode.ERROR_IN_RTT_CLASSIFICATION)

        # if everything is ok return True
        return True


    def rtt_classification(self, box_counters_2GHz: BandCounters, station_counters: StationCounters, samples_array_len: int):
        """RTT Classification for values in args"""

        # Box counters healt check
        if not self.validate_2GHz_counters_for_classification(box_counters_2GHz,samples_array_len):
            logger.error("Prediction not performed, error in box counters input")
            return
        if not self.validate_station_counters_for_classification(station_counters,samples_array_len):
            logger.error("Prediction not performed, error in station counters input")
            return

        # Get box values
        tx_2GHz_Mbps = box_counters_2GHz.tx_Mbps[-1]
        tx_2GHz_Mbps_lag1 = box_counters_2GHz.tx_Mbps[-2]
        tx_2GHz_Mbps_lag3 = box_counters_2GHz.tx_Mbps[-4]
        tx_2GHz_Mbps_avg3 = np.mean(box_counters_2GHz.tx_Mbps[-3:])
        tx_2GHz_Mbps_avg5 = np.mean(box_counters_2GHz.tx_Mbps[-5:])
        tx_2GHz_Mbps_avg7 = np.mean(box_counters_2GHz.tx_Mbps)

        rx_2GHz_Mbps = box_counters_2GHz.rx_Mbps[-1]
        rx_2GHz_Mbps_lag1 = box_counters_2GHz.rx_Mbps[-2]
        rx_2GHz_Mbps_lag2 = box_counters_2GHz.rx_Mbps[-3]
        rx_2GHz_Mbps_lag3 = box_counters_2GHz.rx_Mbps[-4]
        rx_2GHz_Mbps_avg3 = np.mean(box_counters_2GHz.rx_Mbps[-3:])
        rx_2GHz_Mbps_avg5 = np.mean(box_counters_2GHz.rx_Mbps[-5:])
        rx_2GHz_Mbps_avg7 = np.mean(box_counters_2GHz.rx_Mbps)

        rxrtry_2GHz_pps = box_counters_2GHz.rxrtry_pps
        txfail_2GHz_pps = box_counters_2GHz.txfail_pps
        txretrans_2GHz_pps = box_counters_2GHz.txretrans_pps
        txerror_2GHz_pps = box_counters_2GHz.txerror_pps

        logger.info(f"Box 2.4GHz values to perform classification:\n",
                    f"tx_2GHz_Mbps:{tx_2GHz_Mbps}\n",
                    f"tx_2GHz_Mbps_lag1:{tx_2GHz_Mbps_lag1}\n",
                    f"tx_2GHz_Mbps_lag3:{tx_2GHz_Mbps_lag3}\n",
                    f"tx_2GHz_Mbps_avg3:{tx_2GHz_Mbps_avg3}\n",
                    f"tx_2GHz_Mbps_avg5:{tx_2GHz_Mbps_avg5}\n",
                    f"tx_2GHz_Mbps_avg7:{tx_2GHz_Mbps_avg7}\n",
                    f"rx_2GHz_Mbps:{rx_2GHz_Mbps}\n",
                    f"rx_2GHz_Mbps_lag1:{rx_2GHz_Mbps_lag1}\n",
                    f"rx_2GHz_Mbps_lag2:{rx_2GHz_Mbps_lag2}\n",
                    f"rx_2GHz_Mbps_lag3:{rx_2GHz_Mbps_lag3}\n",
                    f"rx_2GHz_Mbps_avg3:{rx_2GHz_Mbps_avg3}\n",
                    f"rx_2GHz_Mbps_avg5:{rx_2GHz_Mbps_avg5}\n",
                    f"rx_2GHz_Mbps_avg7:{rx_2GHz_Mbps_avg7}\n",
                    f"rxrtry_2GHz_pps:{rxrtry_2GHz_pps}\n",
                    f"txfail_2GHz_pps:{txfail_2GHz_pps}\n",
                    f"txretrans_2GHz_pps:{txretrans_2GHz_pps}\n",
                    f"txerror_2GHz_pps:{txerror_2GHz_pps}\n",
        )

        # Get station values
        tx_Mbps = station_counters.tx_Mbps[-1]
        tx_Mbps_lag1 = station_counters.tx_Mbps[-2]
        tx_Mbps_avg3 = np.mean(station_counters.tx_Mbps[-3:])

        rx_Mbps = station_counters.rx_Mbps[-1]
        rx_Mbps_lag1 = station_counters.rx_Mbps[-2]

        smooth_rssi = station_counters.smooth_rssi[-1]
        smooth_rssi_lag1 = station_counters.smooth_rssi[-2]
        smooth_rssi_lag2 = station_counters.smooth_rssi[-3]
        smooth_rssi_lag3 = station_counters.smooth_rssi[-4]
        smooth_rssi_avg3 = np.mean(station_counters.smooth_rssi[-3:])
        smooth_rssi_avg5 = np.mean(station_counters.smooth_rssi[-5:])
        smooth_rssi_avg7 = np.mean(station_counters.smooth_rssi)

        tx_retried_pps = station_counters.tx_retried_pps
        rx_retried_pps = station_counters.rx_retried_pps
        tx_retries_pps = station_counters.tx_retries_pps
        rx_decrypt_pps = station_counters.rx_decrypt_pps
        tx_failures_pps = station_counters.tx_failures_pps
        tx_pkts_pps = station_counters.tx_pkts_pps
        rx_pkts_pps = station_counters.rx_pkts_pps
        tx_pkts_retries_rate = station_counters.tx_pkts_retries_rate


        logger.info(f"Station values to perform classification:\n",
                    f"tx_Mbps:{tx_Mbps}\n",
                    f"tx_Mbps_lag1:{tx_Mbps_lag1}\n",
                    f"tx_Mbps_avg3:{tx_Mbps_avg3}\n",
                    f"rx_Mbps:{rx_Mbps}\n",
                    f"rx_Mbps_lag1:{rx_Mbps_lag1}\n",
                    f"smooth_rssi:{smooth_rssi}\n",
                    f"smooth_rssi_lag1:{smooth_rssi_lag1}\n",
                    f"smooth_rssi_lag2:{smooth_rssi_lag2}\n",
                    f"smooth_rssi_lag3:{smooth_rssi_lag3}\n",
                    f"smooth_rssi_avg3:{smooth_rssi_avg3}\n",
                    f"smooth_rssi_avg5:{smooth_rssi_avg5}\n",
                    f"smooth_rssi_avg7:{smooth_rssi_avg7}\n",
                    f"tx_retried_pps:{tx_retried_pps}\n",
                    f"rx_retried_pps:{rx_retried_pps}\n",
                    f"tx_retries_pps:{tx_retries_pps}\n",
                    f"rx_decrypt_pps:{rx_decrypt_pps}\n",
                    f"tx_failures_pps:{tx_failures_pps}\n",
                    f"tx_pkts_pps:{tx_pkts_pps}\n",
                    f"rx_pkts_pps:{rx_pkts_pps}\n",
                    f"tx_pkts_retries_rate:{tx_pkts_retries_rate}\n",
        )

        #TODO: Perform classification
        # TODO: What to do with results ?

"""Data model for 5GHz band on/off manager package"""
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

@dataclass
class Prediction:
    """Model for prediction"""
    station: str
    timestamp: datetime
    predicted_rtt: float

@dataclass
class BandCountersSample:
    """Model for bands  counters sampole"""
    tx_rate_2GHz_Mbps: float
    rx_rate_2GHz_Mbps: float
    tx_rate_5GHz_Mbps: float
    rx_rate_5GHz_Mbps: float

@dataclass
class StationCountersSample:
    """Model for Station counters sample"""
    txbytes: float
    rxbytes: float
    band: str
    timestamp: datetime

@dataclass
class StationThroughputSample:
    """Model for Station throughput sample"""
    tx_rate_Mbps: float
    rx_rate_Mbps: float


@dataclass
class BandCounters:
    """Model for wifi band counters"""
    tx_Mbps: Iterable[float]
    rx_Mbps: Iterable[float]
    last_tx_bytes: int
    last_rx_bytes: int
    last_rxrtry: int
    last_txfail: int
    last_txretrans: int
    last_txerror: int
    last_rxcrc: int
    rxrtry_pps: int
    txfail_pps: int
    txretrans_pps: int
    txerror_pps: int
    rxcrc_pps:int

@dataclass
class StationCounters:
    """Model for station counters"""
    mac:str
    tx_Mbps: Iterable[float]
    rx_Mbps: Iterable[float]
    smooth_rssi: Iterable[int]
    last_tx_bytes: int
    last_rx_bytes: int
    last_tx_retried: int
    last_rx_retried: int
    last_tx_retries: int
    last_rx_decrypt: int
    last_tx_failures: int
    last_tx_pkts: int
    last_rx_pkts: int
    tx_retried_pps: int
    rx_retried_pps: int
    tx_retries_pps: int
    rx_decrypt_pps: int
    tx_failures_pps: int
    tx_pkts_pps: int
    rx_pkts_pps: int
    tx_pkts_retries_rate: int
    idle: int
    band: str
    last_sample_timestamp: datetime
    rtt_predictions: Iterable[float]


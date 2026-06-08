"""
Preprocessing pipeline for WBAN coordinator packets. Modules in this package are
called in this order by the ingest router: 1. packet_validator.py validates structure
and detects duplicates, 2. imputation_service.py fills missing sensor values using
forward fill, profile mean, or KNN, 3. confidence_scorer.py assigns confidence scores
to each imputed value. All modules take plain Python dicts as input and return plain
Python dicts as output. No SQLAlchemy models are imported here — this keeps the
preprocessing layer independently testable.
"""

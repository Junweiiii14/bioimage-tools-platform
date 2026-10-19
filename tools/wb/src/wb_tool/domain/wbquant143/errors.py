class WBQuantError(Exception):
    """Base exception for user-facing wb_quant errors."""


class ImageValidationError(WBQuantError):
    """The input is not an unambiguous supported scientific TIFF."""


class ROIValidationError(WBQuantError):
    """One or more lane ROIs are invalid."""


class QuantificationError(WBQuantError):
    """Quantification cannot proceed for the supplied data."""


class OutputError(WBQuantError):
    """An output could not be written."""


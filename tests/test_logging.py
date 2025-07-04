import logging
from glacium.utils.logging import log, log_call


def test_log_call_logs_verbose(caplog):
    log.setLevel('VERBOSE')

    @log_call
    def add(a, b=0):
        return a + b

    with caplog.at_level(logging.VERBOSE, logger=log.name):
        result = add(1, b=2)
    assert result == 3
    assert any('add(a=1, b=2)' in rec.getMessage() for rec in caplog.records)

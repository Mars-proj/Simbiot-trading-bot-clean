import json
from logging_setup import logger_main, logger_trade_pool
from utils import log_exception
from json_handler import dumps

def add_trade_to_files(trade_data, trade_id, log_file, json_file):
    """Adds a trade to trade_pool.log and trades.json"""
    try:
        # Save to trade_pool.log file
        trade_json = dumps(trade_data)
        with open(log_file, 'a') as f:
            f.write(f"{trade_json}\n")
        logger_trade_pool.info(f"Trade added to trade_pool.log file: {trade_id} - {trade_data}")
        # Save to trades.json
        try:
            with open(json_file, 'r') as f:
                existing_trades = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_trades = []
        existing_trades.append(trade_data)
        with open(json_file, 'w') as f:
            json.dump(existing_trades, f, indent=2)
        logger_main.info(f"Trade added to trades.json: {trade_id}")
    except Exception as e:
        logger_main.error(f"Error adding trade to files: {str(e)}")
        log_exception(f"Error adding trade to files: {str(e)}", e)

def update_trade_pnl_in_files(trade_id, pnl, status, log_file, json_file):
    """Updates PNL and status of a trade in trade_pool.log and trades.json"""
    try:
        # Update in trade_pool.log file
        with open(log_file, 'a') as f:
            f.write(f"Update: {trade_id} - PNL={pnl}, status={status}\n")
        # Update in trades.json
        try:
            with open(json_file, 'r') as f:
                existing_trades = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_trades = []
        for i, trade_entry in enumerate(existing_trades):
            if trade_entry["trade_id"] == trade_id:
                existing_trades[i]["pnl"] = float(pnl)
                existing_trades[i]["status"] = status
                break
        with open(json_file, 'w') as f:
            json.dump(existing_trades, f, indent=2)
        logger_main.info(f"Trade {trade_id} updated in trades.json")
    except Exception as e:
        logger_main.error(f"Error updating trade in files: {str(e)}")
        log_exception(f"Error updating trade in files: {str(e)}", e)

__all__ = ['add_trade_to_files', 'update_trade_pnl_in_files']

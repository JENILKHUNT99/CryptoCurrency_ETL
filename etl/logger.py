import logging

def get_logger(name):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('crypto_etl.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(name)
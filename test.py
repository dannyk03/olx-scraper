import signal
import sys
import logging
import time

logging.basicConfig ( 
   filename = 'log.txt', 
   format = '%(levelname)s: %(message)s', 
   level = logging.INFO 
)

logger = logging.getLogger()
logger.info('this is test')	
while True:
	time.sleep(10)
	break
	pass

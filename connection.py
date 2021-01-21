import queue
import threading
import usbtmc
import time
import numpy as np

class Connection:
	def __init__(self, queue_in):
		self.queue = queue_in
		self.stop  = False
		
	def connect(self):
		# Connect to device
		self.agilent = usbtmc.Instrument(0x0957, 0x0D09)
		self.time_0  = time.time()
		
		# Start thread that reads out the data
		self.thr     = threading.Thread(target=self.create_data_sample,args=())
		self.thr.start()
		
	def create_data_sample(self):
		t               = self.time_0
		while True:
			t           = time.time()
                        
			if self.stop == True:
				return 0
			
			y_data      = self.get_y_data()
			x_data      = self.get_x_data()
			
			t_diff      = t-self.time_0
			dic         = {'x': x_data, 't': t, 't_diff': t_diff, 'y': y_data}
			self.queue.put(dic)
	
	def get_x_data(self):
		self.agilent.write(":SENS1:FREQ:DATA?")
		data        = self.agilent.read()
		data        = data.encode('ascii').decode()
		data        = data.split(',')
		data        = np.array(data)
		data        = data.astype(np.double)
		return data/1.e6
	
	def get_y_data(self):
		self.agilent.write(":CALC1:DATA:FDAT?")
		data        = self.agilent.read()
		data        = data.encode('ascii').decode()
		data        = data.split(',')
		data        = np.array(data)
		data        = data[::2]
		data        = data.astype(np.double)
		return data
		
def func():
	import queue
	con = Connection(queue.Queue())
	con.get_data()

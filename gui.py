import tkinter as tk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from tkinter import filedialog as fd

import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.use("TkAgg")

import threading

import numpy as np
import queue

import connection

import h5py
from os import path

import time

class MyGUI:
	def __init__(self, master):
		self.master = master
		master.title("Recording from E5061C (Agilent Technologies)")

		self.figure = Figure(figsize=(10,3.5),dpi=100)
		self.ax     = self.figure.add_axes([0.1,0.1,0.8,0.8])
		self.canvas = FigureCanvasTkAgg(self.figure, master)
		self.canvas.get_tk_widget().grid(row=0, column=0,columnspan=4)
		self.canvas.draw()
		
		self.figure1 = Figure(figsize=(10,3.5),dpi=100)
		self.ax1     = self.figure1.add_axes([0.1,0.1,0.8,0.8])
		self.canvas1 = FigureCanvasTkAgg(self.figure1, master)
		self.canvas1.get_tk_widget().grid(row=4, column=0,columnspan=4)
		self.canvas1.draw()
		
		self.filename_counter  = 0
		self.minima_y = []
		self.minima_x = []
				
		# All the buttons
		self.text_ss           = tk.StringVar()
		self.text_ss.set("Start recording")
		self.sfl_button        = tk.Button(master, text="Set file location", command=self.set_file_location).grid(row=2,column=0)
		self.start_stop_button = tk.Button(master, textvariable=self.text_ss, command=self.start_stop).grid(row=2,column=1)
		self.exit_button       = tk.Button(master, text="Close", command=self.close).grid(row=2,column=3)
		
		self.label1            = tk.Label(master, text="Peak: ").grid(row=1,column=0,sticky=tk.E+tk.N+tk.S)
		self.label2            = tk.Label(master, text="Bandwidth: ").grid(row=1,column=2,sticky=tk.E+tk.N+tk.S)
		
		self.fn_label          = tk.StringVar()
		self.label3            = tk.Label(master, textvariable=self.fn_label).grid(row=3,column=0,columnspan=4,sticky=tk.E+tk.N+tk.S+tk.W)
		
		self.text_peak         = tk.StringVar()
		self.text_peak.set("-")
		self.text_bw           = tk.StringVar()
		self.text_bw.set("-")
		self.lPeak             = tk.Label(master, textvariable=self.text_peak).grid(row=1,column=1,sticky=tk.W+tk.N+tk.S)
		self.lBandwidth        = tk.Label(master, textvariable=self.text_bw  ).grid(row=1,column=3,sticky=tk.W+tk.N+tk.S)
		
		self.queue             = queue.Queue()
		self.queue_save        = []
		self.con               = connection.Connection(self.queue)
		self.con.connect()
		self.flag              = False
		self.master            = master
		
		self.stop              = False
		
		self.thr               = threading.Thread(target=self.plot_data,args=())
		self.thr.start()
		
	def plot_data(self):
		while True:
			while self.queue.qsize() == 0:
				if self.stop:
					return 0
			if self.stop:
				return 0
			element = self.queue.get()	
			if self.flag:
				self.queue_save.append(element)	
			y_data  = element['y']
			x_data  = element['x']
			minimum_index = np.argmin(y_data)
			minimum_value = y_data[minimum_index]
			minimum_freq  = x_data[minimum_index]
			bandwidth     = (x_data[1]-x_data[0])*np.sum(((y_data-minimum_value)<3)*1.)
			if minimum_value < -0.1:
				self.minima_y.append(minimum_freq)
				self.minima_x.append(time.time())
				self.text_peak.set(str(np.round(minimum_freq,1)) + " [MHz]")
				self.text_bw.set(str(np.round(bandwidth,1)) + " [MHz]")
			else:
				self.text_peak.set("-")
				self.text_bw.set("-")


                        if self.queue.qsize() < 5:
                                self.ax.plot(x_data,y_data)
                                self.ax.grid(True)
                                self.ax.set_ylim([min(-1,minimum_value),1])
                                self.ax.set_xlim([x_data[0],x_data[-1]])
                                self.ax.set_xlabel('Frequency [MHz]')
                                self.ax.set_ylabel('Damping [dB]')
                                self.canvas.draw()
                                self.ax.clear()
                                
                                if len(self.minima_y) > 3:
                                        self.ax1.plot([i-self.minima_x[0] for i in self.minima_x],self.minima_y)
                                        self.ax1.grid(True)
                                        self.ax1.set_xlabel('Time (sec)')
                                        self.ax1.set_ylabel('Resonance frequency [MHz]')
                                        self.canvas1.draw()
                                        self.ax1.clear()
			
	def close(self):
		try:
			self.con.stop = True
			self.stop = True
			self.master.quit()
		except:
			print('cannot stop')

	def update_file_name(self):
		# Remove the ending, if applicable
		if self.filename_clean[-3:] == ".h5":
			self.filename_clean     = self.filename_clean[:-3]
		if self.filename_clean[-5:] == ".hdf5":
			self.filename_clean     = self.filename_clean[:-3]
		
		while path.exists(self.filename_clean + str(self.filename_counter).zfill(3) + ".h5"):
			self.filename_counter += 1;
		self.filename   = self.filename_clean + str(self.filename_counter).zfill(3) + ".h5"
		self.fn_label.set(self.filename)
		
	def set_file_location(self):
		filename              = fd.asksaveasfilename()
		self.filename_clean   = filename
		self.update_file_name()
		
	def start_stop(self):
		self.update_file_name() # This is always executed. This is okay, since if the file does not exists yet, nothing happens.
		if self.flag: # This means data must be saved
			t_0    = self.queue_save[0]['t'] # This is aproximately the time of experiment start
			t      = np.zeros(len(self.queue_save))
			x_data = np.zeros((len(self.queue_save),self.queue_save[0]['x'].shape[0]))
			y_data = np.zeros((len(self.queue_save),self.queue_save[0]['y'].shape[0]))
			for i in range(len(self.queue_save)):
				element     = self.queue_save[i]
				t[i]        = element['t']
				x_data[i,:] = element['x']
				y_data[i,:] = element['y']
			t               = t - t_0
			self.text_ss.set("Start recording")
			
			# Save data
			f = h5py.File(self.filename, 'w')
			f.create_dataset('t_0',      data=t_0)
			f.create_dataset('t',        data=t)
			f.create_dataset('x_data',   data=x_data)
			f.create_dataset('y_data',   data=y_data)
			f.close()
		else:
			self.text_ss.set("Stop recording")
			self.minima_y = []
			self.minima_x = []
			self.queue_save = []
			
			
		
		self.flag = not self.flag

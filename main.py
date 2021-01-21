import tkinter as tk
import gui

import matplotlib as mpl
import matplotlib.pyplot as plt

def main():
	root   = tk.Tk()
	my_gui = gui.MyGUI(root)
	root.mainloop()
	
if __name__ == '__main__':
	mpl.use("TkAgg")
	main()

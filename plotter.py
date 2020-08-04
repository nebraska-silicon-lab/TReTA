def backgroundThread(self):    # retrieve data
    time.sleep(1.0)  # give some buffer time for retrieving data
    self.serialConnection.reset_input_buffer()
    while (self.isRun):
        self.serialConnection.readinto(self.rawData)
        self.isReceiving = True
        #print(self.rawData)
        
def close(self):
    self.isRun = False
    self.thread.join()
    self.serialConnection.close()
    print('Disconnected...')
        
def main():
    portName = '/dev/ttyACM1'
    baudRate = 9600
    maxPlotLength = 100
    dataNumBytes = 4        # number of bytes of 1 data point
    s = serialPlot(portName, baudRate, maxPlotLength, dataNumBytes)   # initializes all required variables
    s.readSerialStart()                                               # starts background thread
    
    # plotting starts below
    pltInterval = 50    # Period at which the plot animation updates [ms]
    xmin = 0
    xmax = maxPlotLength
    ymin = -(1)
    ymax = 1
    fig = plt.figure()
    ax = plt.axes(xlim=(xmin, xmax), ylim=(float(ymin - (ymax - ymin) / 10), float(ymax + (ymax - ymin) / 10)))
    ax.set_title('Thermistor Temperature')
    ax.set_xlabel("Time")
    ax.set_ylabel("Temperature")
    
    lineLabel = 'Potentiometer Value'
    timeText = ax.text(0.50, 0.95, '', transform=ax.transAxes)
    lines = ax.plot([], [], label=lineLabel)[0]
    lineValueText = ax.text(0.50, 0.90, '', transform=ax.transAxes)
    anim = animation.FuncAnimation(fig, s.getSerialData, fargs=(lines, lineValueText, lineLabel, timeText), interval=pltInterval)    # fargs has to be a tuple
    
    plt.legend(loc="upper left")
    plt.show()
    
    s.close()
    
 
if __name__ == '__main__':
    main()

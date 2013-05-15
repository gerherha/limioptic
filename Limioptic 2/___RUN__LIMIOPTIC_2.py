#!/usr/bin/env python

"""
Hier wird hauptsaechlich die GUI definiert.
Der Text wird mit limioptic.ExecText() an limioptic.py uebergeben.
Dort sind die verschiedenen Funktionen definiert.
Die eigentliche Berechnung findet in limioptic.cpp statt.
"""

print "loading:",

print "imp",            # unterdruecken von import fehlern
import imp
print "sys",
import sys
print "Qt",
from PyQt4 import QtCore, QtGui
print "limioptic",
import limioptic        # ionenoptische berechnungen
print "threading",
import threading        # multithreading
print "time",
import time             # debuggen + sleep
#import serial          # auslesen des potis
try:
    imp.find_module("vtk")
    import vtk          # grafische ausgabe ueber VTK
    print "vtk",
except:
    print "<vtk NOT FOUND>",
    vtk = False
print "urllib",
import urllib           # zum ueberpruefen auf updates
print "ams_spicker",
import ams_spicker
print "importsrc",
from importsrc import ImportSource
print "syntax:highlighting",
import syntax
try:
    imp.find_module("pyqtgraph")
    import pyqtgraph as pg
    print "PyQtGraph"
except:
    print "<PyQtGraph NOT FOUND>"
    pg = False


#################################################
#################################################


class inputcontrol(QtGui.QDialog):
        """ Hier wird das Fenster mit den Schiebereglern zur Variablenmanipulation definiert """
        def __init__(self, mode):
                QtGui.QDialog.__init__(self)
                self.mode = mode
                self.changing = False

                if (mode == "qt"):  self.plotwindow = doitqt2(self)    # PyQtGraph
                if (mode == "2d"):  self.plotwindow = doitXY(self)     # VTK
                if (mode == "3d"):  self.plotwindow = doit3d(self)     # VTK

                ### Ab hier Definition des Layouts
                self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
                self.setGeometry(100, screen.height() - 300, 500, 50)

                self.setWindowTitle("input control")
                self.vbox = QtGui.QVBoxLayout()
                layout = QtGui.QGridLayout()

                CheckInputNumber = True
                myapp.textedit.moveCursor(QtGui.QTextCursor.Start)
                NumberOfInputs = -1
                while (CheckInputNumber):
                                NumberOfInputs += 1
                                texttofind = QtCore.QString("INPUT[{}]".format(NumberOfInputs))
                                if not (myapp.textedit.find(texttofind)): CheckInputNumber = False
                NumberOfInputs += 1
                if (NumberOfInputs < 8): NumberOfInputs = 8

                self.min     = []
                self.input   = []
                self.slider  = []
                self.info    = []
                self.infobox = []

                for i in xrange(NumberOfInputs):
                        self.info.append(QtGui.QLabel("#%1.0f" % (i)))
                        self.min.append(QtGui.QDoubleSpinBox())
                        self.slider.append(QtGui.QSlider(QtCore.Qt.Horizontal, self))
                        self.input.append(QtGui.QDoubleSpinBox())
                        self.infobox.append(QtGui.QLineEdit())
                        self.min[i].setRange(-100., 100.)
                        self.infobox[i].setPlaceholderText("Beschreibung")
                        self.infobox[i].setText(BEZEICHNUNGEN[i])
                        self.input[i].setDecimals(4)
                        self.slider[i].setOrientation(QtCore.Qt.Horizontal)
                        self.slider[i].setRange(0, 500000)
                        self.slider[i].setSingleStep(500)
                        self.input[i].setSingleStep(0.0001)
                        self.input[i].setRange(-100., 100.)
                        self.input[i].setPrefix("= ")
                        self.min[i].setSingleStep(.01)
                        self.input[i].setValue(INPUT[i])

                        if (INPUT[i] > 5.):   self.min[i].setValue(INPUT[i] - 5.)
                        self.slider[i].setValue(int(INPUT[i] * 100000.))

                        layout.addWidget(self.info[i], i, 0)
                        layout.addWidget(self.min[i], i, 1)
                        layout.addWidget(self.slider[i], i, 2)
                        layout.addWidget(self.input[i], i, 3)
                        layout.addWidget(self.infobox[i], i, 4)
                layout.setColumnStretch(2, 100)
                self.vbox.addLayout(layout)

                if (self.mode == "3d"):
                        opacitybox   = QtGui.QHBoxLayout()
                        self.olabel  = QtGui.QLabel("Opacity")
                        self.oslider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
                        self.oslider.setRange(0, 100)
                        self.oslider.setValue(OPACITY)
                        opacitybox.addWidget(self.olabel)
                        opacitybox.addWidget(self.oslider)
                        self.vbox.addLayout(opacitybox)

                self.setLayout(self.vbox)

                # Die Elementgroessen werden neu angepasst (Buttons, Slider, ...)
                self.adjustSize()

                # Der Thread des Output-Fensters wird gestartet
                self.plotwindow.start()

                # Wichtig, damit Aenderungen von Variablen nicht waerend des Berechnens/Plottens stattfinden
                self.threadlock = threading.Lock()

                for i in xrange(NumberOfInputs):
                        self.connect(self.slider[i], QtCore.SIGNAL("valueChanged(int)"), self.slidertoinput)
                        self.connect(self.input[i], QtCore.SIGNAL("valueChanged(double)"), self.inputtoslider)
                        self.connect(self.min[i], QtCore.SIGNAL("valueChanged(double)"), self.slidertoinput)
                        self.connect(self.infobox[i], QtCore.SIGNAL("textChanged(const QString)"), self.infochange)
                if (self.mode == "3d"): self.connect(self.oslider, QtCore.SIGNAL("valueChanged(int)"), self.setopacity)

                self.show()

                # Solange True findet Kommunikation mit Interface statt.
                self.update_on = True

                # Serielle Kommunikation findet in eigenem Thread statt.
                if (PORT != "NONE"):
                        t_readserial = threading.Thread(target=self.readserial, args=())
                        t_readserial.start()

        def setopacity(self):
                """ Nur fuer die 3D-Ausgabe """
                OPACITY = self.oslider.value()
                self.plotwindow.actor.GetProperty().SetOpacity(OPACITY/1000.)
                self.plotwindow.render = True

        def readserial(self):
                """ Serielle Kommunikation mit dem Interface (obsolet) """
                ser = serial.Serial(PORT, 9600)
                time.sleep(2)
                print "serial start"
                while (self.update_on):
                        ser.write(1)
                        # Interface braucht kurz Zeit zum Antworten
                        time.sleep(0.1)
                        a = ser.readline().split()
                        self.slider[0].setValue(int(a[0]) * 488)
                        self.slider[1].setValue(int(a[1]) * 488)
                        self.slider[2].setValue(int(a[2]) * 488)
                print "serial end"

        def inputtoslider(self):
                """ Variablenaenderungen werden auf Slider uebertragen. """
                if not self.changing:
                    global INPUT
                    self.changing = True
                    for i in xrange(NumberOfInputs):
                            INPUT[i] = self.input[i].value()
                    for i in xrange(NumberOfInputs):
                            self.slider[i].setValue(int((INPUT[i] - self.min[i].value()) * 100000.))
                    if (RUNNINGQT): self.plotwindow.update(self.calculate())
                    if (RUNNING2D): self.plotwindow.update = True
                    if (RUNNING3D): self.plotwindow.neu()
                    self.changing = False

        def slidertoinput(self):
                """ Aenderung des Sliders wird auf self.INPUT uebertragen. """
                if not self.changing:
                    global INPUT
                    self.changing = True
                    for i in xrange(NumberOfInputs):
                            self.input[i].setValue(self.slider[i].value() / 100000. + self.min[i].value())
                    for i in xrange(NumberOfInputs):
                            INPUT[i] = self.input[i].value()
                    if (RUNNINGQT): self.plotwindow.update(self.calculate())
                    if (RUNNING2D): self.plotwindow.update = True
                    if (RUNNING3D): self.plotwindow.neu()
                    self.changing = False

        def closeit(self):
                """ Wird aufgerufen, wenn das Outputfenster geschlossen wird. """
                global BEZEICHNUNGEN, RUNNING2D, RUNNING3D
                for i in xrange(NumberOfInputs):
                        BEZEICHNUNGEN[i] = self.infobox[i].text()

                self.update_on = False

                try:
                    self.plotwindow.iren.Disable()
                    self.plotwindow.iren.EnableRenderOff()
                    self.plotwindow.iren.TerminateApp()
                    self.plotwindow.iren.DestroyTimer(self.plotwindow.timer)
                    if (self.mode == "2d"):
                        RUNNING2D = False
                        del self.plotwindow.view
                        del self.plotwindow.iren
                        del self.plotwindow.chart
                    if (self.mode == "3d"):
                        RUNNING3D = False
                        del self.plotwindow.ren
                        del self.plotwindow.actor
                        del self.plotwindow.mapper
                        del self.plotwindow.iren
                        del self.plotwindow.renwin
                        del self.plotwindow.mydata
                        del self.plotwindow.polylines
                        del self.plotwindow.mycells
                except: pass
                del self.plotwindow

                print "closed"
                time.sleep(.1)
                self.close()

        def infochange(self):
                """ Spezialbefehle im "Beschreibung" Feld """
                for i in xrange(NumberOfInputs):
                        if self.infobox[i].text()[-1:] == ">":
                                myapp.textedit.setText("{0}\t=\tINPUT[{1}]\t# {2}\n{3}".format(self.infobox[i].text()[:-1], i, INPUT[i], myapp.textedit.toPlainText()))
                                self.infobox[i].setText(self.infobox[i].text()[:-1])
                        if self.infobox[i].text()[-1:] == "#":
                                myapp.textedit.setText("{0}\t=\t{2}\t# INPUT[{1}]\n{3}".format(self.infobox[i].text()[:-1], i, INPUT[i], myapp.textedit.toPlainText()))
                                self.infobox[i].setText(self.infobox[i].text()[:-1])

        def calculate(self):
            """ Neuberechnung """
            limioptic.optic.Clear()
            limioptic.geo_s.Reset()
            limioptic.geo_y.Reset()
            limioptic.s = 0.
            try:
                    limioptic.ExecText(str(myapp.textedit.toPlainText()), INPUT, SourceObj.Source)
                    limioptic.optic.CalculateTrajectories()
            except:
                    print "\n\nFehler in der Eingabe! ({})".format(limioptic.lastFunction)
                    return -1

            parts = limioptic.optic.GetParticleNum()                    # Anz. Partikel
            segs  = limioptic.optic.GetTrajectoriesSize() / parts / 8   # Anz. Segmente

            # Die Trajektorien liegen als array.array("d", ..) vor
            _xi = [limioptic.GetTrajectory(i, 0) for i in xrange(parts)]
            _yi = [limioptic.GetTrajectory(i, 2) for i in xrange(parts)]
            _z  = limioptic.GetTrajectory(0, 6)

            # Umwandlung in float arrays
            xi = [None] * parts
            yi = [None] * parts
            for part in xrange(parts):
                xi[part] = [None] * segs
                yi[part] = [None] * segs
                for seg in xrange(segs):
                    xi[part][seg] = float(_xi[part][seg])
                    yi[part][seg] = float(_yi[part][seg])
            zi = [float(_z[seg]) for seg in xrange(segs)]

            return xi, yi, zi, segs, parts


class doitqt2(threading.Thread):
    """ 2D Plot mit PyQtGraph """
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.parent = parent
        self.win = pg.GraphicsWindow(title="Limioptic 2 - Output (2D)")
        self.win.resize(800, 350)
        self.plot1 = self.win.addPlot()
        self.plot1.showGrid(x=True, y=True)
        self.lineX = self.plot1.plot()
        self.lineY = self.plot1.plot()
        self.linegeo = self.plot1.plot()

    def run(self):
        self.update(self.parent.calculate())

    def update(self, (xi, yi, zi, segs, parts)=(None, None, None, None, None)):
        if xi is None:   (xi, yi, zi, segs, parts) = self.parent.calculate()

        # viel schneller, als mehrere plots
        x_all = []
        y_all = []
        z_all = []
        for part in xrange(parts):
            x_all += xi[part] + [0., 0.]
            y_all += yi[part] + [0., 0.]
            z_all += zi + [zi[-1], zi[0]]
        self.lineX.setData(x=z_all, y=x_all, pen=(255, 0, 0))
        self.lineY.setData(x=z_all, y=y_all, pen=(0, 255, 0))

        iele  = limioptic.geo_s.GetNumberOfTuples()
        geo_s = [limioptic.geo_s.GetValue(i) for i in xrange(iele)]
        geo_y = [limioptic.geo_y.GetValue(i) for i in xrange(iele)]
        self.linegeo.setData(x=geo_s, y=geo_y, pen=(170, 170, 170.))


class doit3d(threading.Thread):
        """ 3D-Ausgabe """
        def __init__(self, parent):
                threading.Thread.__init__(self)
                self.parent = parent
                self.render = False
                self.threadlock = threading.Lock()

        def run(self):
                (xi, yi, zi, segs, parts) = self.parent.calculate()

                # Hier landen alle Punkte
                self.mypoints = vtk.vtkPoints()

                # Wir erzeugen nur eine Cell, dh. eine lange Polyline (Geschwindigkeit)
                self.mycells = vtk.vtkCellArray()

                # Alle Punkte in mypoints laden
                for part in xrange(parts):
                        for seg in xrange(segs):
                                self.mypoints.InsertNextPoint(zi[seg] * SCALE3D, xi[part][seg], yi[part][seg])
                        self.mypoints.InsertNextPoint(zi[seg] * SCALE3D, .0, .0)
                        self.mypoints.InsertNextPoint(.0, .0, .0)

                # Eine neue Polygonlinie definieren.
                self.polylines = vtk.vtkPolyLine()
                self.polylines.GetPointIds().SetNumberOfIds(parts * segs + parts * 2)

                # Der i-te Punkt der Polyline entspricht dem i-ten Punkt des PointArrays (noch nicht verknuepft)
                for i in xrange(parts * segs + parts * 2):   self.polylines.GetPointIds().SetId(i, i)

                # Polylinie an Cell uebergeben
                self.mycells.InsertNextCell(self.polylines)

                # Datenobjekt erzeugen
                self.mydata = vtk.vtkPolyData()

                # Punkte hinzufuegen
                self.mydata.SetPoints(self.mypoints)

                # Polyline hinzufuegen. Ab nun verknuepft
                self.mydata.SetLines(self.mycells)

                # Der Mapper macht aus Daten mehr
                self.mapper = vtk.vtkPolyDataMapper()

                # Hier bekommt er die Daten
                self.mapper.SetInput(self.mydata)

                # Der Actor platziert den Mapper im Raum
                self.actor = vtk.vtkActor()

                # Hier bekommt er den Mapper
                self.actor.SetMapper(self.mapper)
                self.actor.GetProperty().SetOpacity(OPACITY / 1000.)

                self.ren = vtk.vtkRenderer()
                self.ren.SetBackground(.1, .2, .4)
                self.ren.AddActor(self.actor)

                ### Axen
                self.axisactor = vtk.vtkCubeAxesActor()
                self.axisactor.SetXAxisRange(0., zi[-1])
                self.axisactor.SetBounds(self.actor.GetBounds())
                self.axisactor.SetXTitle("s in m")
                self.axisactor.YAxisVisibilityOff()
                self.axisactor.ZAxisVisibilityOff()
                self.axisactor.SetCamera(self.ren.GetActiveCamera())
                self.ren.AddActor(self.axisactor)
                self.ren.ResetCamera()

                ### Renderfenster
                self.renwin = vtk.vtkRenderWindow()
                self.renwin.AddRenderer(self.ren)
                self.renwin.SetSize(900, 450)

                self.iren = vtk.vtkRenderWindowInteractor()

                self.iren.SetRenderWindow(self.renwin)
                self.iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

                # Damit der Speicher wieder freigegeben wird, wenn das Fenster geschlossen wird.
                self.iren.AddObserver("ExitEvent", lambda o, e, a=myapp.inputwindow3d: a.closeit())

                # Linien glatter machen
                if (myapp.menu_output_smoothing.isChecked()):   self.renwin.LineSmoothingOn()

                # Rot-Gruen-Brille (aktivieren mit '3')
                self.renwin.SetStereoTypeToAnaglyph()

                self.iren.Initialize()
                self.renwin.Render()

                self.renwin.SetWindowName("Limioptic 2 - Output (3D)")

                # self.animate wird aufgerufen wenn der Timer zuschlaegt (alle 50 ms)
                self.iren.AddObserver("TimerEvent", self.animate)
                self.timer = self.iren.CreateRepeatingTimer(50)

                # Ab hier laeuft die Schleife bis das Fenster geschlossen wird
                self.iren.Start()

        def neu(self, (xi, yi, zi, segs, parts)=(None, None, None, None, None)):
                """ Wird aufgerufen wenn eine Variable geaendert wird, oder Strg + H gedrueckt wird """

                if xi is None:  (xi, yi, zi, segs, parts) = self.parent.calculate()

                self.mypoints = vtk.vtkPoints()
                for part in xrange(parts):
                        for seg in xrange(segs):
                                self.mypoints.InsertNextPoint(zi[seg] * SCALE3D, xi[part][seg], yi[part][seg])
                        self.mypoints.InsertNextPoint(zi[seg] * SCALE3D, .0, .0)
                        self.mypoints.InsertNextPoint(.0, .0, .0)

                for i in xrange(parts * segs + parts * 2):
                        self.polylines.GetPointIds().SetId(i, i)

                self.mycells.Reset()
                self.mycells.InsertNextCell(self.polylines)

                self.mydata.SetPoints(self.mypoints)
                self.mydata.SetLines(self.mycells)

                self.mapper.SetInput(self.mydata)
                self.actor.SetMapper(self.mapper)

                self.render = True

        def animate(self, obj=None, event=None):
                """ Nur animieren, wenn etwas geaendert wurde. Die Funktion wird alle 50 ms aufgerufen """
                if self.render:
                        self.render = False
                        self.threadlock.acquire()
                        self.renwin.Render()
                        self.threadlock.release()


class doitXY(threading.Thread):
        """ Die Ausgabe in 2D """
        def __init__(self, parent):
                self.parent = parent
                threading.Thread.__init__(self)
                self.activeInput = 0
                self.render = False
                self.update = False
                self.threadlock = threading.Lock()

        def run(self):
                ### 2d Szene und xy Chart erzeugen.
                self.view = vtk.vtkContextView()
                self.view.GetRenderer().SetBackground(1., 1., 1.)
                if myapp.menu_plot_bg.isChecked():  self.view.GetRenderer().SetBackground(0., 0., 0.)
                self.view.GetRenderWindow().SetSize(screen.width() - 375, screen.height() - 40)

                self.chart = vtk.vtkChartXY()
                self.chart.GetAxis(vtk.vtkAxis.BOTTOM).SetTitle("beamline (m)")
                self.chart.GetAxis(vtk.vtkAxis.LEFT).SetTitle("deviation (mm)")

                self.Ticks  = vtk.vtkDoubleArray()
                self.Labels = vtk.vtkStringArray()

                self.view.GetScene().AddItem(self.chart)

                if (myapp.menu_plot_geo.isChecked()):
                    limioptic.geo_s.Reset()
                    limioptic.geo_y.Reset()
                    limioptic.s = 0.
                else:
                    limioptic.s = -1.

                ### Berechnungen durchfuehren
                (xi, yi, zi, segs, parts) = self.parent.calculate()
                iele = limioptic.GetTrajectory(0, 7)

                if (myapp.menu_output_file.isChecked()):    ausgabe = open("output_markers.dat", "w")

                ### Marker setzen
                if myapp.menu_plot_marker.isChecked():
                        self.markertable = vtk.vtkTable()
                        self.markersY = vtk.vtkFloatArray()
                        self.markersY.SetName("Marker")
                        self.markersY.InsertNextValue(-10)
                        self.markersY.InsertNextValue(10)
                        self.markertable.AddColumn(self.markersY)

                        self.markersX = []

                        self.linelist = []
                        if (len(iele) > 0):
                                for i in xrange(1, len(iele)):
                                        if (iele[i] != iele[i-1]):
                                                self.linelist.append(zi[i-1])
                                self.linelist.append(zi[len(iele)-1])

                        if (myapp.menu_output_file.isChecked()):    print >> ausgabe, 0, 0
                        for i in xrange(1, len(self.linelist)):
                                self.markersX.append(vtk.vtkFloatArray())
                                self.markersX[i-1].SetName("Marker %1.0f" % (i))
                                self.markersX[i-1].InsertNextValue(self.linelist[i-1])
                                self.markersX[i-1].InsertNextValue(self.linelist[i-1])
                                if (myapp.menu_output_file.isChecked()):
                                        print >> ausgabe, self.linelist[i-1], 0
                                        print >> ausgabe, self.linelist[i-1], 10
                                        print >> ausgabe, self.linelist[i-1], -10
                                        print >> ausgabe, self.linelist[i-1], 0
                                self.markertable.AddColumn(self.markersX[i-1])
                                self.line2 = self.chart.AddPlot(0)
                                self.line2.SetInput(self.markertable, i, 0)
                                self.line2.SetColor(.7, .7, .7)
                                self.line2.SetWidth(1.)
                        if (myapp.menu_output_file.isChecked()):    ausgabe.close()

                ### Erzeuge Wertetabelle
                self.table = vtk.vtkTable()
                self.arrZ = vtk.vtkFloatArray()
                self.arrZ.SetName("Z Achse")
                self.arrX = []
                self.arrY = []

                self.arrZ.SetNumberOfValues(segs)
                self.arrZ.Reset()
                for seg in xrange(segs):    self.arrZ.InsertNextValue(zi[seg])

                self.table.AddColumn(self.arrZ)

                j = 0
                if (plotx):
                        if (myapp.menu_output_file.isChecked()):    ausgabe = open("output_xbeam.dat", "w")
                        for j in xrange(parts):
                                self.arrX.append(vtk.vtkFloatArray())
                                self.arrX[j].SetName("X-Strahl %1.0f Start: %1.2f" % (j, xi[j][0]))
                                for i in xrange(segs):
                                        self.arrX[j].InsertNextValue(xi[j][i])
                                        if (myapp.menu_output_file.isChecked()):    print >> ausgabe, zi[i], xi[j][i]
                                self.table.AddColumn(self.arrX[j])
                                if (myapp.menu_output_file.isChecked()):    ausgabe.write("\n")

                                self.line = self.chart.AddPlot(0)
                                self.line.SetInput(self.table, 0, j + 1)
                                self.line.SetColor(255, 0, 0, 255)
                                self.line.SetWidth(.7)
                        if (myapp.menu_output_file.isChecked()):    ausgabe.close()
                if (ploty):
                        if (myapp.menu_output_file.isChecked()):    ausgabe = open("output_ybeam.dat", "w")
                        for l in xrange(parts):
                                self.arrY.append(vtk.vtkFloatArray())
                                self.arrY[l].SetName("Y-Strahl %1.0f Start: %1.2f" % (l, yi[l][0]))
                                for i in xrange(segs):
                                        self.arrY[l].InsertNextValue(yi[l][i])
                                        if (myapp.menu_output_file.isChecked()):    print >> ausgabe, zi[i], yi[l][i]
                                self.table.AddColumn(self.arrY[l])
                                if (myapp.menu_output_file.isChecked()):    ausgabe.write("\n")

                                self.line = self.chart.AddPlot(0)
                                self.line.SetInput(self.table, 0, l + j + xy)
                                self.line.SetColor(0, 255, 0, 255)
                                self.line.SetWidth(.7)
                        if (myapp.menu_output_file.isChecked()):    ausgabe.close()

                if (myapp.menu_plot_geo.isChecked()):
                        limioptic.geolines.AddColumn(limioptic.geo_s)
                        limioptic.geolines.AddColumn(limioptic.geo_y)
                        self.line3 = self.chart.AddPlot(0)
                        self.line3.SetInput(limioptic.geolines, 0, 1)
                        self.line3.SetColor(0., 0., 1.)
                        self.line3.SetWidth(.7)

                for name in limioptic.textArray:
                    self.Ticks.InsertNextValue(name[0])
                    self.Labels.InsertNextValue(name[1])

                if (myapp.menu_output_smoothing.isChecked()):   self.view.GetRenderWindow().LineSmoothingOn()
                self.view.Render()

                self.iren = self.view.GetInteractor()
                self.iren.AddObserver("TimerEvent", self.animate)
                self.iren.AddObserver("KeyPressEvent", self.keypress)
                self.iren.AddObserver("ExitEvent", lambda o, e, a=myapp.inputwindow2d: a.closeit())
                self.timer = self.iren.CreateRepeatingTimer(50)

                self.view.GetRenderWindow().SetWindowName("Limioptic 2 - Output (2D)")

                self.iren.Start()

        def keypress(self, obj=None, event=None):
            key = obj.GetKeySym()
            if key == "space":
                if self.chart.GetAxis(vtk.vtkAxis.BOTTOM).GetBehavior() == vtk.vtkAxis.CUSTOM:
                    self.chart.GetAxis(vtk.vtkAxis.BOTTOM).SetBehavior(vtk.vtkAxis.AUTO)
                else:
                    self.chart.GetAxis(vtk.vtkAxis.BOTTOM).SetBehavior(vtk.vtkAxis.CUSTOM)
                    self.Ticks.Reset()
                    self.Labels.Reset()
                    for name in limioptic.textArray:
                        self.Ticks.InsertNextValue(name[0])
                        self.Labels.InsertNextValue(name[1])
                    self.chart.GetAxis(vtk.vtkAxis.BOTTOM).SetTickPositions(self.Ticks)
                    self.chart.GetAxis(vtk.vtkAxis.BOTTOM).SetTickLabels(self.Labels)
                self.render = True
            elif key in (str(i) for i in xrange(8)):
                self.activeInput = int(key)
                self.parent.setWindowTitle("input control (INPUT[{}])".format(self.activeInput))
            elif key in ("Up", "Down", "Left", "Right"):
                self.threadlock.acquire()
                if key == "Up":     self.parent.min[self.activeInput].setValue(self.parent.min[self.activeInput].value() + .01)
                if key == "Down":   self.parent.min[self.activeInput].setValue(self.parent.min[self.activeInput].value() - .01)
                if key == "Right":  self.parent.input[self.activeInput].setValue(self.parent.input[self.activeInput].value() + .0001)
                if key == "Left":   self.parent.input[self.activeInput].setValue(self.parent.input[self.activeInput].value() - .0001)
                self.threadlock.release()

        def animate(self, obj=None, event=None):
                if self.render:
                    self.render = False
                    self.threadlock.acquire()
                    self.view.Render()
                    self.threadlock.release()
                if self.update:
                    self.update = False
                    self.neu()

        def neu(self, (xi, yi, zi, segs, parts)=(None, None, None, None, None)):
                self.threadlock.acquire()
                if (myapp.menu_plot_geo.isChecked()):
                        limioptic.geo_s.Reset()
                        limioptic.geo_y.Reset()
                        limioptic.s = 0.
                else:
                        limioptic.s = -1.

                if xi is None:  (xi, yi, zi, segs, parts) = self.parent.calculate()
                iele = limioptic.GetTrajectory(0, 7)

                ### erzeuge wertetabelle
                if (plotx):
                        for part in xrange(parts):
                                self.arrX[part].Reset()
                                for seg in xrange(segs):
                                        self.arrX[part].InsertNextValue(xi[part][seg])
                if (ploty):
                        for part in xrange(parts):
                                self.arrY[part].Reset()
                                for seg in xrange(segs):
                                        self.arrY[part].InsertNextValue(yi[part][seg])

                self.arrZ.Reset()
                for i in xrange(segs):  self.arrZ.InsertNextValue(zi[i])

                ### Marker setzen
                if myapp.menu_plot_marker.isChecked():
                        self.linelist = []
                        if (len(iele) > 0):
                                for i in xrange(1, len(iele)):
                                        if (iele[i] != iele[i-1]):
                                                self.linelist.append(zi[i-1])
                                self.linelist.append(zi[len(iele) - 1])

                        for i in xrange(1, len(self.linelist)):
                                try:    # error falls neues element hinzugefuegt wurde
                                        self.markersX[i-1].Reset()
                                        self.markersX[i-1].InsertNextValue(self.linelist[i-1])
                                        self.markersX[i-1].InsertNextValue(self.linelist[i-1])
                                except: # neu initialisieren
                                        self.markersX.append(vtk.vtkFloatArray())
                                        self.markersX[i-1].SetName("Marker {}".format(i))
                                        self.markersX[i-1].InsertNextValue(self.linelist[i-1])
                                        self.markersX[i-1].InsertNextValue(self.linelist[i-1])
                                        self.markertable.AddColumn(self.markersX[i-1])
                                        print "you need to close the output-window and rerender (Ctrl+G) to show the markers correctly"
                                        msg = QtGui.QMessageBox()
                                        msg.setText("you need to close the output-window and rerender\n(Ctrl+G) to show the markers correctly")
                                        msg.exec_()

                self.table.Modified()
                self.markertable.Modified()
                if (myapp.menu_plot_geo.isChecked()):   limioptic.geolines.Modified()
                if myapp.menu_plot_bg.isChecked():
                    self.view.GetRenderer().SetBackground(0, 0, 0)
                else:
                    self.view.GetRenderer().SetBackground(1, 1, 1)

                if self.chart.GetAxis(vtk.vtkAxis.BOTTOM).GetBehavior() == vtk.vtkAxis.CUSTOM:
                    self.Ticks.Reset()
                    self.Labels.Reset()
                    for name in limioptic.textArray:
                        self.Ticks.InsertNextValue(name[0])
                        self.Labels.InsertNextValue(name[1])
                    self.chart.GetAxis(vtk.vtkAxis.BOTTOM).SetTickPositions(self.Ticks)
                    self.chart.GetAxis(vtk.vtkAxis.BOTTOM).SetTickLabels(self.Labels)

                self.threadlock.release()

                self.render = True


#################################################
#################################################
class CQtLimioptic(QtGui.QMainWindow):
        """ Hier wird das Hauptfenster definiert in dem die Beamline eingegeben werden kann """
        def __init__(self):
                QtGui.QMainWindow.__init__(self)
                self.setGeometry(screen.width()-350, 30, 350-10, screen.height()-40)
                self.setWindowTitle('Limioptic 2')

                # enable the staus bar
                self.statusBar().showMessage('')

                # erzeuge Menu->File->Load Action
                menu_file_load = QtGui.QAction('Open', self)
                menu_file_load.setShortcut('Ctrl+O')
                menu_file_load.setStatusTip('Load Data from File')
                self.connect(menu_file_load, QtCore.SIGNAL('triggered()'), self.LoadFile)

                menu_file_loadauto = QtGui.QAction('Open _save.lim', self)
                menu_file_loadauto.setShortcut('Ctrl+-')
                menu_file_loadauto.setStatusTip('Load last autosave')
                self.connect(menu_file_loadauto, QtCore.SIGNAL('triggered()'), self.LoadAutosave)

                # erzeuge Menu->File->SaveAs Action
                menu_file_saveas = QtGui.QAction('Save as..', self)
                menu_file_saveas.setStatusTip('Save File as')
                menu_file_saveas.setShortcut('Ctrl+Alt+S')
                self.connect(menu_file_saveas, QtCore.SIGNAL('triggered()'), self.SaveFileAs)

                menu_file_save = QtGui.QAction('Save', self)
                menu_file_save.setStatusTip('Save File')
                menu_file_save.setShortcut('Ctrl+S')
                self.connect(menu_file_save, QtCore.SIGNAL('triggered()'), self.SaveFile)

                # erzeuge Menu->File->Exit Action
                menu_file_exit = QtGui.QAction(QtGui.QIcon('icon/exit.png'), 'Exit', self)
                menu_file_exit.setShortcut('Ctrl+Q')
                menu_file_exit.setStatusTip('Exit Program')
                self.connect(menu_file_exit, QtCore.SIGNAL('triggered()'), QtCore.SLOT('close()'))

                # translate 2d
                menu_translate_2d = QtGui.QAction('2D (VTK)', self)
                menu_translate_2d.setShortcut('Ctrl+G')
                menu_translate_2d.setStatusTip('Translate Text to GUI 2D')
                if not vtk: menu_translate_2d.setEnabled(False)
                self.connect(menu_translate_2d, QtCore.SIGNAL('triggered()'), self.plot2d)
                # translate 3d
                menu_translate_3d = QtGui.QAction('3D (VTK)', self)
                menu_translate_3d.setShortcut('Ctrl+H')
                menu_translate_3d.setStatusTip('Translate Text to GUI 3D')
                if not vtk: menu_translate_3d.setEnabled(False)
                self.connect(menu_translate_3d, QtCore.SIGNAL('triggered()'), self.plot3d)
                # translate qt 2d
                menu_translate_qt = QtGui.QAction('2D (PyQtGraph)', self)
                menu_translate_qt.setShortcut('Ctrl+F')
                menu_translate_qt.setStatusTip('Translate Text to GUI 2D')
                if not pg: menu_translate_qt.setEnabled(False)
                self.connect(menu_translate_qt, QtCore.SIGNAL('triggered()'), self.plotqt)

                # Plot markers
                self.menu_plot_marker = QtGui.QAction('marker', self)
                self.menu_plot_marker.setCheckable(True)
                self.menu_plot_marker.setChecked(True)
#               self.connect(self.menu_plot_marker, QtCore.SIGNAL('triggered()'),)
                # Plot geo
                self.menu_plot_geo = QtGui.QAction('geometry', self)
                self.menu_plot_geo.setCheckable(True)
                self.menu_plot_geo.setChecked(True)
                # Plot x
                self.menu_plot_x = QtGui.QAction('x', self)
                self.menu_plot_x.setCheckable(True)
                self.menu_plot_x.setChecked(True)
                self.connect(self.menu_plot_x, QtCore.SIGNAL('triggered()'), self.setxy)
                # Plot y
                self.menu_plot_y = QtGui.QAction('y', self)
                self.menu_plot_y.setCheckable(True)
                self.menu_plot_y.setChecked(True)
                self.connect(self.menu_plot_y, QtCore.SIGNAL('triggered()'), self.setxy)
                # Background
                self.menu_plot_bg = QtGui.QAction('black background', self)
                self.menu_plot_bg.setCheckable(True)
                self.menu_plot_bg.setChecked(False)

                # Source
                self.menu_insert_source = QtGui.QAction('Source', self)
                self.menu_insert_source.setStatusTip('Use input file')
                self.connect(self.menu_insert_source, QtCore.SIGNAL('triggered()'), self.InsertSource)
                # Particle
                self.menu_insert_particle = QtGui.QAction('Particle', self)
                self.menu_insert_particle.setStatusTip('Insert a particle')
                self.connect(self.menu_insert_particle, QtCore.SIGNAL('triggered()'), self.InsertParticle)
                # Beam
                self.menu_insert_beam = QtGui.QAction('Beam', self)
                self.menu_insert_beam.setShortcut('Ctrl+Shift+B')
                self.menu_insert_beam.setStatusTip('Insert a particle beam')
                self.connect(self.menu_insert_beam, QtCore.SIGNAL('triggered()'), self.InsertBeam)
                # Beam X
                self.menu_insert_beamx = QtGui.QAction('BeamX (3d)', self)
                self.menu_insert_beamx.setStatusTip('Insert a simple 3d beam')
                self.connect(self.menu_insert_beamx, QtCore.SIGNAL('triggered()'), self.InsertBeamX)
                # Beam 3D
                self.menu_insert_beam3d = QtGui.QAction('Beam3D (3d)', self)
                self.menu_insert_beam3d.setStatusTip('Insert a NICE 3d beam')
                self.connect(self.menu_insert_beam3d, QtCore.SIGNAL('triggered()'), self.InsertBeam3d)
                # Beam Gauss
                self.menu_insert_rgauss = QtGui.QAction('BeamRandomGauss (3d)', self)
                self.menu_insert_rgauss.setStatusTip('Insert a gaussian beam')
                self.connect(self.menu_insert_rgauss, QtCore.SIGNAL('triggered()'), self.InsertRGauss)

                # Slit
                self.menu_insert_slit = QtGui.QAction('Slit', self)
                self.menu_insert_slit.setStatusTip('Insert a slit')
                self.menu_insert_slit.setShortcut('Ctrl+Shift+S')
                self.connect(self.menu_insert_slit, QtCore.SIGNAL('triggered()'), self.InsertSlit)
                # BeamProfile
                self.menu_insert_bpm = QtGui.QAction('Beam Profile Monitor', self)
                self.menu_insert_bpm.setStatusTip('Insert a BPM')
                self.connect(self.menu_insert_bpm, QtCore.SIGNAL('triggered()'), self.InsertBPM)
                # Modify Emittance
                self.menu_insert_modifyemittance = QtGui.QAction('Modify Emittance', self)
                self.connect(self.menu_insert_modifyemittance, QtCore.SIGNAL('triggered()'), self.InsertModifyEmittance)
                # general 6x6 Matrix
                self.menu_insert_matrix = QtGui.QAction('General 6x6 matrix', self)
                self.menu_insert_matrix.setStatusTip('Insert a general 6x6 transfer matrix')
                self.connect(self.menu_insert_matrix, QtCore.SIGNAL('triggered()'), self.InsertMatrix)
                # Drift
                self.menu_insert_drift = QtGui.QAction('Drift', self)
                self.menu_insert_drift.setShortcut('Ctrl+Shift+D')
                self.menu_insert_drift.setStatusTip('Insert a drift')
                self.connect(self.menu_insert_drift, QtCore.SIGNAL('triggered()'), self.InsertDrift)
                # ESD
                self.menu_insert_esd = QtGui.QAction('ESD', self)
                self.menu_insert_esd.setShortcut('Ctrl+Shift+E')
                self.menu_insert_esd.setStatusTip('Insert an ESD')
                self.connect(self.menu_insert_esd, QtCore.SIGNAL('triggered()'), self.InsertESD)
                # MSA
                self.menu_insert_hdm = QtGui.QAction('MSA', self)
                self.menu_insert_hdm.setShortcut('Ctrl+Shift+M')
                self.menu_insert_hdm.setStatusTip('Insert a homogeneous deflecting magnet')
                self.connect(self.menu_insert_hdm, QtCore.SIGNAL('triggered()'), self.InsertHomDeflectingMagnet)
                # Quadrupol
                self.menu_insert_quadrupol = QtGui.QAction('Quadrupol', self)
                self.menu_insert_quadrupol.setShortcut('Ctrl+Shift+Q')
                self.menu_insert_quadrupol.setStatusTip('Open Dialog : Insert a quadrupol')
                self.connect(self.menu_insert_quadrupol, QtCore.SIGNAL('triggered()'), self.InsertQuadrupol)
                # ThinLens
                self.menu_insert_ThinLens = QtGui.QAction('Einzel lens', self)
                self.menu_insert_ThinLens.setShortcut('Ctrl+Shift+L')
                self.menu_insert_ThinLens.setStatusTip('Open Dialog : Insert a thin lense')
                self.connect(self.menu_insert_ThinLens, QtCore.SIGNAL('triggered()'), self.InsertThinLens)

                # SO110-EL
                self.menu_insert_so110el = QtGui.QAction('AMS SO110-EL', self)
                self.menu_insert_so110el.setStatusTip('Cologne AMS SO110 einzel lens')
                self.connect(self.menu_insert_so110el, QtCore.SIGNAL('triggered()'), self.InsertSO110EL)
                # FN-EL
                self.menu_insert_fnel = QtGui.QAction('FN EL', self)
                self.menu_insert_fnel.setStatusTip('HVEC-FN 7 einzel lens')
                self.connect(self.menu_insert_fnel, QtCore.SIGNAL('triggered()'), self.InsertFNEL)
                # BI-EL
                self.menu_insert_biel = QtGui.QAction('AMS BI-EL', self)
                self.menu_insert_biel.setStatusTip('Cologne AMS BI einzel lens')
                self.connect(self.menu_insert_biel, QtCore.SIGNAL('triggered()'), self.InsertBIEL)
                # AMSQPT
                self.menu_insert_amsqpt = QtGui.QAction('AMS QPT', self)
                self.menu_insert_amsqpt.setStatusTip('Cologne AMS Quadrupole Triplet')
                self.connect(self.menu_insert_amsqpt, QtCore.SIGNAL('triggered()'), self.InsertAMSQPT)
                # VBFN
                self.menu_insert_vbfn = QtGui.QAction('FN VB', self)
                self.menu_insert_vbfn.setShortcut('Ctrl+Shift+V')
                self.menu_insert_vbfn.setStatusTip('Insert Cologne FN preacceleration segment')
                self.connect(self.menu_insert_vbfn, QtCore.SIGNAL('triggered()'), self.InsertVBFN)
                # FNACC
                self.menu_insert_fnacc = QtGui.QAction('FN acceleration tube', self)
                #self.menu_insert_fnacc.setShortcut('Ctrl+Shift+F')
                self.menu_insert_fnacc.setStatusTip('Insert HVEC-FN 7 acceleration tube')
                self.connect(self.menu_insert_fnacc, QtCore.SIGNAL('triggered()'), self.InsertFNAcc)
                # FNACCNeu
                self.menu_insert_fnaccneu = QtGui.QAction('FN acceleration tube', self)
                self.menu_insert_fnaccneu.setShortcut('Ctrl+Shift+F')
                self.menu_insert_fnaccneu.setStatusTip('Insert HVEC-FN 7 acceleration tube')
                self.connect(self.menu_insert_fnaccneu, QtCore.SIGNAL('triggered()'), self.InsertFNAccNeu)
                # AMS-Acc
                self.menu_insert_amsacc = QtGui.QAction('AMS acceleration tube', self)
                self.menu_insert_amsacc.setStatusTip('Insert Cologne AMS acceleration tube')
                self.menu_insert_amsacc.setShortcut('Ctrl+Shift+A')
                self.connect(self.menu_insert_amsacc, QtCore.SIGNAL('triggered()'), self.InsertAMSAcc)

                ## OUTPUT
                # dat
                self.menu_output_file = QtGui.QAction('-> output_*.dat', self)
                self.menu_output_file.setStatusTip('send output -> *.dat files for publication.')
                self.menu_output_file.setCheckable(True)
                self.menu_output_file.setChecked(False)
                self.connect(self.menu_output_file, QtCore.SIGNAL("triggered()"), self.todat)
                # smoothing
                self.menu_output_smoothing = QtGui.QAction("line smoothing", self)
                self.menu_output_smoothing.setStatusTip('draw smoother lines (apply before rendering)')
                self.menu_output_smoothing.setCheckable(True)
                self.menu_output_smoothing.setChecked(True)
                # AMS-Spicker
                self.menu_output_spicker = QtGui.QAction("AMS Spicker", self)
                self.menu_output_spicker.setStatusTip('Cologne AMS Spicker')
                self.menu_output_spicker.setCheckable(False)
                self.connect(self.menu_output_spicker, QtCore.SIGNAL('triggered()'), self.spicker)

                ## Interface
                self.menu_setcom1 = QtGui.QAction('COM1', self)
                self.menu_setcom1.setStatusTip('search interface on com1')
                self.connect(self.menu_setcom1, QtCore.SIGNAL('triggered()'), self.setcom1)
                self.menu_setcom2 = QtGui.QAction('COM2', self)
                self.menu_setcom2.setStatusTip('search interface on com2')
                self.connect(self.menu_setcom2, QtCore.SIGNAL('triggered()'), self.setcom2)
                self.menu_setcom3 = QtGui.QAction('COM3', self)
                self.menu_setcom3.setStatusTip('search interface on com3')
                self.connect(self.menu_setcom3, QtCore.SIGNAL('triggered()'), self.setcom3)
                self.menu_setcom4 = QtGui.QAction('COM4', self)
                self.menu_setcom4.setStatusTip('search interface on com4')
                self.connect(self.menu_setcom4, QtCore.SIGNAL('triggered()'), self.setcom4)
                self.menu_setcom5 = QtGui.QAction('COM5', self)
                self.menu_setcom5.setStatusTip('search interface on com5')
                self.connect(self.menu_setcom5, QtCore.SIGNAL('triggered()'), self.setcom5)

                ## About
                self.menu_about = QtGui.QAction("About", self)
                self.connect(self.menu_about, QtCore.SIGNAL('triggered()'), self.About)
                self.menu_licence = QtGui.QAction("Licence", self)
                self.connect(self.menu_licence, QtCore.SIGNAL("triggered()"), self.Licence)

                ## Menubar
                menubar = self.menuBar()

                ##FILE
                menu_file = menubar.addMenu('File')
                menu_file.addAction(menu_file_load)

                menu_file.addAction(menu_file_saveas)
                menu_file.addAction(menu_file_save)
                menu_file.addAction(menu_file_exit)

                ## TRANSLATE
                menu_translate = menubar.addMenu('Plot')
                menu_translate.addAction(menu_translate_2d)
                menu_translate.addAction(menu_translate_qt)
                menu_translate.addAction(menu_translate_3d)

                ## PLOT
                menu_plot = menubar.addMenu('Options')
                menu_plot.addAction(self.menu_plot_marker)
                menu_plot.addAction(self.menu_plot_geo)
                menu_plot.addAction(self.menu_plot_x)
                menu_plot.addAction(self.menu_plot_y)
                menu_plot.addAction(self.menu_output_smoothing)
                menu_plot.addAction(self.menu_plot_bg)

                ## INSERT
                menu_insert = menubar.addMenu('Insert')
                menu_insert.addAction(self.menu_insert_source)
                menu_insert.addAction(self.menu_insert_particle)
                menu_insert.addAction(self.menu_insert_beam)
                menu_insert.addAction(self.menu_insert_beamx)
                menu_insert.addAction(self.menu_insert_beam3d)
                menu_insert.addAction(self.menu_insert_rgauss)
                menu_insert.addSeparator()
                menu_insert.addAction(self.menu_insert_drift)
                menu_insert.addAction(self.menu_insert_esd)
                menu_insert.addAction(self.menu_insert_hdm)
                menu_insert.addAction(self.menu_insert_quadrupol)
                menu_insert.addAction(self.menu_insert_ThinLens)
                menu_insert.addAction(self.menu_insert_slit)
                menu_insert.addAction(self.menu_insert_bpm)
                menu_insert.addAction(self.menu_insert_modifyemittance)
                menu_insert.addAction(self.menu_insert_matrix)
                menu_insert.addSeparator()
                menu_insert.addAction(self.menu_insert_so110el)
                menu_insert.addAction(self.menu_insert_biel)
                menu_insert.addAction(self.menu_insert_amsqpt)
                menu_insert.addAction(self.menu_insert_amsacc)
                menu_insert.addAction(self.menu_insert_fnel)
                menu_insert.addAction(self.menu_insert_vbfn)
                menu_insert.addAction(self.menu_insert_fnaccneu)

                ## OUTPUT
                menu_output = menubar.addMenu('Tools')
                menu_output.addAction(self.menu_output_file)
                menu_output.addAction(self.menu_output_spicker)

                ## INTERFACE
                """
                menu_interface = menubar.addMenu('# interface')
                menu_interface.addAction(self.menu_setcom1)
                menu_interface.addAction(self.menu_setcom2)
                menu_interface.addAction(self.menu_setcom3)
                menu_interface.addAction(self.menu_setcom4)
                menu_interface.addAction(self.menu_setcom5)
                """

                ## ABOUT
                menu_aboutbar = menubar.addMenu('About')
                menu_aboutbar.addAction(self.menu_about)
                menu_aboutbar.addAction(self.menu_licence)

                ### GUI definieren
                self.main_frame = QtGui.QWidget()
                self.textedit = QtGui.QTextEdit()
                self.textedit.setLineWrapMode(QtGui.QTextEdit.NoWrap)
                self.highlighter = syntax.PythonHighlighter(self.textedit.document())
                hbox1 = QtGui.QHBoxLayout()
                hbox1.addWidget(self.textedit)
                self.main_frame.setLayout(hbox1)
                self.setCentralWidget(self.main_frame)

                self.connect(self.textedit, QtCore.SIGNAL("textChanged()"), self.setunsaved)
                # print "started"

                try:
                        self.LoadAutosave()
                        print "last autosave was restored"
                except:
                        print "last savefile was not found"

                ## UPDATE
                updatethread = threading.Thread(target=self.update, args=())
                updatethread.start()

        def update(self):
                """ Check uebers Internet ob Updates verfuegbar sind """
                print "checking for updates..",
                try:
                        a = urllib.urlopen("http://ams.amstolz.de/version.txt")
                        ver = a.read()
                        a.close()
                        if (ver == VERSION):
                                print "this is the newest version\n"
                        else:
                                print "there is a newer version online. run \"__update.bat\" to update\n"
                                print "Your version:", VERSION, "Latest Version:", ver, "\n"
                except:
                        print "update check failed\n"

#############################
        def setunsaved(self):
                try:
                        self.setWindowTitle("Limioptic 2 -     changed     - {}".format(self.FileName))
                except:
                        self.setWindowTitle("Limioptic 2 - unsaved")

#############################
        def setcom1(self):
                global PORT
                PORT = "COM1"

        def setcom2(self):
                global PORT
                PORT = "COM2"

        def setcom3(self):
                global PORT
                PORT = "COM3"

        def setcom4(self):
                global PORT
                PORT = "COM4"

        def setcom5(self):
                global PORT
                PORT = "COM5"

##############################
        def setxy(self):
                """ Nur x, nur y, oder beides zeichnen. """
                global xy, plotx, ploty
                xy = 0
                plotx = False
                ploty = False
                if (self.menu_plot_x.isChecked()):
                        xy += 1
                        plotx = True
                if (self.menu_plot_y.isChecked()):
                        xy += 1
                        ploty = True

#############################
        def spicker(self):
                """ Der AMS-Spicker """
                self.swidget = ams_spicker.Spicker()
                self.swidget.show()

#############################
        def todat(self):
                """ Ausgabe in Datei """
                if (self.menu_output_file.isChecked()):
                        if (RUNNING2D):
                                msg = QtGui.QMessageBox()
                                msg.setText("Please close the plot-window and rerender!\n*.dat files will be produced every time the plot-window opens.")
                                msg.exec_()
                        else:
                                msg = QtGui.QMessageBox()
                                msg.setText("Press Ctrl+G to produce *.dat files!")
                                msg.exec_()

#############################
        def LoadFile(self):
                self.FileName = QtGui.QFileDialog.getOpenFileName(self, "Open file", ".", "*.lim;;*.*")
                if (self.FileName != ''):
                        myfile = open(self.FileName, 'r')
                        self.textedit.setText(myfile.read())
                        myfile.close()
                        self.setWindowTitle("Limioptic 2  -  {}".format(self.FileName))

                        try:
                            global NumberOfInputs, BEZEICHNUNGEN, INPUT
                            i = -1
                            for line in open(self.FileName.split(".", 1)[0] + ".var"):
                                i += 1
                                BEZEICHNUNGEN[i] = line.split(" = ")[0]
                                INPUT[i] = float(line.split(" = ")[1])
                            NumberOfInputs = i + 1
                            print "the last values were restored"
                        except:
                            print "could not load variables"

        def LoadAutosave(self):
                try:
                        myfile = open("_save.lim", "r")
                        self.textedit.setText(myfile.read())
                        myfile.close()
                        self.setWindowTitle("Limioptic 2  -  _save.lim")
                except:
                        print "_save.lim not found!"

                try:
                    global NumberOfInputs, BEZEICHNUNGEN, INPUT
                    i = -1
                    for line in open("_save.var", "r"):
                        i += 1
                        BEZEICHNUNGEN[i] = line.split(" = ")[0]
                        INPUT[i] = float(line.split(" = ")[1])
                    NumberOfInputs = i + 1
                except:
                    print "_save.var not found"

        def SaveFileAs(self):
                self.FileName = QtGui.QFileDialog.getSaveFileName(self, "Save file", ".", "*.lim;;*.*")
                if (self.FileName != ""):
                        myfile = open(self.FileName, "w")
                        myfile.write(str(self.textedit.toPlainText()))
                        myfile.close()
                        self.setWindowTitle("Limioptic 2")
                        print "saved to", self.FileName
                        self.setWindowTitle("Limioptic 2  -  {}".format(self.FileName))

                        myfile = open(self.FileName.split(".", 1)[0] + ".var", "w")
                        for i in xrange(NumberOfInputs):
                                print >> myfile, "{} = {}".format(BEZEICHNUNGEN[i], INPUT[i])
                        myfile.close()

        def SaveFile(self):
                try:
                        if (self.FileName != ""):
                                myfile = open(self.FileName, "w")
                                myfile.write(str(self.textedit.toPlainText()))
                                myfile.close()
                                self.setWindowTitle('Limioptic 2')
                                print "saved to", self.FileName
                                self.setWindowTitle("Limioptic 2  -  {}".format(self.FileName))
                                saved = True
                except:
                        print "Noch kein Filename definiert!"
                        self.SaveFileAs()

                if saved:
                        myfile = open(self.FileName.split(".", 1)[0] + ".var", "w")
                        for i in xrange(NumberOfInputs):
                                print >> myfile, "{} = {}".format(BEZEICHNUNGEN[i], INPUT[i])
                        myfile.close()

#############################
        def plot2d(self):
                global RUNNING2D, RUNNING
                myfile = open("_save.lim", "w")
                myfile.write(str(self.textedit.toPlainText()))
                myfile.close()

                myfile = open("_save.var", "w")
                for i in xrange(NumberOfInputs):
                        print >> myfile, "{} = {}".format(BEZEICHNUNGEN[i], INPUT[i])
                myfile.close()

                if not RUNNING:
                        print "Sicherungsdatei: _save.lim"
                        self.inputwindow2d = inputcontrol("2d")
                        RUNNING2D = RUNNING = True
                        self.inputwindow2d.exec_()
                        RUNNING2D = RUNNING = False
                elif RUNNING2D:
                        self.inputwindow2d.plotwindow.neu()

        def plotqt(self):
                global RUNNINGQT, RUNNING
                myfile = open("_save.lim", "w")
                myfile.write(str(self.textedit.toPlainText()))
                myfile.close()

                myfile = open("_save.var", "w")
                for i in xrange(NumberOfInputs):
                        print >> myfile, "{} = {}".format(BEZEICHNUNGEN[i], INPUT[i])
                myfile.close()

                if not RUNNING:
                        print "Sicherungsdatei: _save.lim"
                        self.inputwindowqt = inputcontrol("qt")
                        RUNNINGQT = RUNNING = True
                        self.inputwindowqt.exec_()
                        RUNNINGQT = RUNNING = False
                elif RUNNINGQT:
                        self.inputwindowqt.plotwindow.update()

        def plot3d(self):
                global RUNNING3D, RUNNING
                myfile = open("_save.lim", "w")
                myfile.write(str(self.textedit.toPlainText()))
                myfile.close()

                myfile = open("_save.var", "w")
                for i in xrange(NumberOfInputs):
                        print >> myfile, "{} = {}".format(BEZEICHNUNGEN[i], INPUT[i])
                myfile.close()

                if not RUNNING:
                        print "Sicherungsdatei: _save.lim"
                        self.inputwindow3d = inputcontrol("3d")
                        RUNNING3D = RUNNING = True
                        self.inputwindow3d.exec_()
                        RUNNING3D = RUNNING = False
                elif RUNNING3D:
                        self.inputwindow3d.plotwindow.neu()

##### INSERT Funktionen #####
#############################
        def InsertParticle(self):
                self.textedit.textCursor().insertText("AddParticle(4,15,4,15,0,0)  # (x, x\', y, y\', dk, dm)\n")

        def InsertSource(self):
                global SourceObj
                SourceObj.LoadSource(QtGui.QFileDialog.getOpenFileName(self, "Open file", "."))
                SourceObj.NormalizeEnergy()
                SourceObj.ShowFits()
                SourceObj.UserInteraction.ChooseFilter()
                #SourceObj.Source = SourceObj.Selection
                #SourceObj.ShowFits()
                print "Source", SourceObj.SourceFile, "loaded"
                self.textedit.textCursor().insertText("AddSource()")

        def InsertBeam(self):
            self.textedit.textCursor().insertText('############################################\nAddBeam(4,15,4,15,0,0,10)\t# (xmax, x\'max, ymax, y\'max, dk, dm, delta: 1...360)\n############################################\n\n')

        def InsertBeamX(self):
            self.textedit.textCursor().insertText('############################################\nAddBeamX(4,15,4,15,0,0,10)\t# (xmax, x\'max, ymax, y\'max, dk, dm, delta: 1...360)\n############################################\n\n')

        def InsertBeam3d(self):
            self.textedit.textCursor().insertText('############################################\nAddBeam3d(4,15,4,15,0,0,10)\t# (xmax, x\'max, ymax, y\'max, dk, dm, delta_phi: 1...360)\n############################################\n\n')

        def InsertRGauss(self):
            self.textedit.textCursor().insertText('############################################\nAddBeamRandomGauss(4,15,4,15,0,0,1000)\t# (xmax, x\'max, ymax, y\'max, dk, dm, num)\n############################################\n\n')

        def InsertAMSAcc(self):
            self.textedit.textCursor().insertText('AddAMSAcc(50.e3, 5500.e3, 35.e3, 4)\t# (v_qsnout, v_terminal, v_ext, q)\n\n')

        def InsertFNAcc(self):
            #self.textedit.textCursor().insertText('AddFNAcc(6000.e3, 100.e3, 5)\t# (v_terminal, v_vorbeschl, q)\n\n')
            self.InsertFNAccNeu()

        def InsertFNAccNeu(self):
            self.textedit.textCursor().insertText('AddFNAccNeu(vt, T0, q, b = 0.57, b1 = -1., b2 = -1., D1 = .088, factor1 = 1., factor2 = 1., beamprofile = False)\n\n')

        def InsertVBFN(self):
            self.textedit.textCursor().insertText('AddVBFN(extraktion, deltaV, laenge)\t# (v_ext, deltaV, length, [b, b1, b2])\n\n')

        def InsertMatrix(self):
            # uebergebe Zeiger auf das TextEdit an den Dialog
            self.dialog = CInsertMatrixDialog(self.textedit)
            self.dialog.exec_()

        def InsertDrift(self):
            self.textedit.textCursor().insertText('AddDrift(1, 1, 5)\t# (n, gamma^2, length)\n')

        def InsertSlit(self):
            self.textedit.textCursor().insertText('AddSlit(0,10,0,10)\t# (x, dx, y, dy)\n')

        def InsertBPM(self):
            self.textedit.textCursor().insertText('AddBeamProfile()\n')

        def InsertModifyEmittance(self):
            self.textedit.textCursor().insertText('AddModifyEmittance(1., 1.)\t# (factor x, factor dx)\n')

        def InsertESD(self):
            self.textedit.textCursor().insertText('AddESD(10,1.,.5*math.pi,2.,1.e9,0.,25)\t# (n, gamma^2, alpha, r_hor, r_vert, beta0, R)\n\n')

        def InsertHomDeflectingMagnet(self):
            self.textedit.textCursor().insertText('AddEdgeFocusing(r,beta,K,R)\n')    # Kantenfokussierung
            self.textedit.textCursor().insertText('AddMSA(n,gamma^2,r,alpha,R)\n')    # Magnet
            self.textedit.textCursor().insertText('AddEdgeFocusing(r,beta,K,R)\n\n')  # Kantenfokussierung

        def InsertQuadrupol(self):
            self.textedit.textCursor().insertText('AddQuadrupolRadFoc(n,gamma^2,k,l,R)\n')   # radial fokussierend
            self.textedit.textCursor().insertText('AddQuadrupolAxFoc(n,gamma^2,k,l,R)\n\n')  # axial fokusierend

        def InsertThinLens(self):
            self.textedit.textCursor().insertText('AddThinLens(.5,.5,25)\t# (fx, fy, R)\n\n')

        def InsertSO110EL(self):
            self.textedit.textCursor().insertText('AddAMSSO110EL(vext,vlens)\n\n')

        def InsertBIEL(self):
            self.textedit.textCursor().insertText('AddAMSBIEL(vext,vlens)\n\n')

        def InsertFNEL(self):
            self.textedit.textCursor().insertText('AddFNEL(v_ext,17.e3)\t# (v_ext, v_lens)\n\n')

        def InsertAMSQPT(self):
            self.textedit.textCursor().insertText('AddAMSQPT(gamma2,prozent,astigm,v_terminal,v_ext,q,geo)\n\n')

        def About(self):
            title = "About Limioptic 2"
            text = "Limioptic 2 by Alexander Stolz\nVersion {}\n\nFeel free to send me any feedback or suggestions to amstolz@gmail.com.\n\nVisit ams.amstolz.de for more information.\n\nThanks for using Limioptic!\n\nWhy the 2?\nThe very first version based on the program Limioptic by Stefan Heinze. Thanks!\n\nThanks Mama, Papa and the rest of my beautiful family!".format(VERSION)
            self.dialog = DialogWindow(title, text)

        def Licence(self):
            title = "Limioptic 2 Licence"
            text = "The program Limioptic 2 maintained by Alexander Stolz is freely available and distributable. However, if you use it for some work whose results are made public, then you have to reference it properly."
            self.dialog = DialogWindow(title, text)


##### Dialoge #####
###################
class CInsertParticleDialog(QtGui.QDialog):
        """ Wird nicht mehr benoetigt """
        def __init__(self, myarg1):
                QtGui.QDialog.__init__(self)
                self.setFixedSize(400, 200)
                self.setWindowTitle('Insert Particle Dialog')

                # Zeiger auf das QTextEdit speichern
                self.parent_textedit = myarg1

                self.insert_syntax_button = QtGui.QPushButton('just insert syntax', self)
                self.insert_syntax_button.setGeometry(50, 50, 160, 25)
                self.connect(self.insert_syntax_button, QtCore.SIGNAL('clicked()'), self.InsertSyntax)


class DialogWindow(QtGui.QDialog):
        def __init__(self, title, text):
                QtGui.QDialog.__init__(self)
                self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
                self.setWindowTitle(title)
                self.abouttext = QtGui.QTextEdit()
                hbox = QtGui.QHBoxLayout()
                hbox.addWidget(self.abouttext)
                self.setLayout(hbox)
                self.abouttext.setText(text)
                self.show()


class CInsertMatrixDialog(QtGui.QDialog):
        def __init__(self, myarg1):
                QtGui.QDialog.__init__(self)
                self.setFixedSize(200, 100)
                self.setWindowTitle('Insert general 6x6 Matrix Dialog')

                # Zeiger auf das QTextEdit speichern
                self.parent_textedit = myarg1

                self.insert_ThinLens_example_button = QtGui.QPushButton('insert unity matrix', self)
                self.insert_ThinLens_example_button.setGeometry(50, 50, 100, 50)
                self.connect(self.insert_ThinLens_example_button, QtCore.SIGNAL('clicked()'), self.InsertThinLensExample)

        def InsertThinLensExample(self):
                # nur die Syntax fuer 'AddMatrix' einfuegen
                self.parent_textedit.textCursor().insertText('AddMatrix(n,\n')
                self.parent_textedit.textCursor().insertText('           [1.,0.,0.,0.,0.,0.,\n')
                self.parent_textedit.textCursor().insertText('           0.,1.,0.,0.,0.,0.,\n')
                self.parent_textedit.textCursor().insertText('           0.,0.,1.,0.,0.,0.,\n')
                self.parent_textedit.textCursor().insertText('           0.,0.,0.,1.,0.,0.,\n')
                self.parent_textedit.textCursor().insertText('           0.,0.,0.,0.,1.,0.,\n')
                self.parent_textedit.textCursor().insertText('           0.,0.,0.,0.,0.,1.],\n')
                self.parent_textedit.textCursor().insertText('           length)\n')

################################

VERSION = "2013-05-08"
PORT = "NONE"
INPUT = []
BEZEICHNUNGEN = []
OPACITY = 50
NumberOfInputs = 8
SCALE3D = 10.

for i in xrange(32):
        INPUT.append(1.)
        BEZEICHNUNGEN.append("")

plotx = True
ploty = True
xy = 2

RUNNING = False
RUNNINGQT = False
RUNNING2D = False
RUNNING3D = False


app = QtGui.QApplication(sys.argv)

#screen = QtGui.QDesktopWidget().screenGeometry()
screen = QtGui.QDesktopWidget().availableGeometry()
#screen = QtGui.QDesktopWidget().desktop()

SourceObj = ImportSource()
myapp = CQtLimioptic()

myapp.show()

sys.exit(app.exec_())
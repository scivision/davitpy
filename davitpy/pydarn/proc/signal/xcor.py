# -*- coding: utf-8 -*-
from __future__ import absolute_import
import copy
import datetime
from matplotlib import pyplot as mp
import numpy as np
import scipy as sp
from .signalCommon import *
import logging

# Cross Correlation Objects Start Here


class xcor(object):

    def __init__(self, sig0, sig1, mode='full', comment=None, **metadata):
        """Define a vtsd sig cross correlation object.

        Parameters
        ---------
        sig0
        sig1
        mode : Optional[str]
        comment : Optional[str]
        metadata : dict

        Attributes
        ----------
        norm0
        norm1
        metadata
        xcor
        active

        Returns
        -------
        xcor object

        """
        sig0 = prepForProc(sig0)
        sig1 = prepForProc(sig1)

        assert sig0.samplePeriod() == sig1.samplePeriod(
        ), 'Sample period must be the same!'
        samplePeriod = sig0.samplePeriod()

        norm0 = sig0.data / np.nanmax(np.abs(sig0.data))
        norm1 = sig1.data / np.nanmax(np.abs(sig1.data))

        self.norm0 = norm0
        self.norm1 = norm1
        xcor = sp.signal.correlate(norm0, norm1, mode=mode)

        xcor = sp.signal.correlate(sig0.data, sig1.data, mode=mode)

        lag = np.array(list(range(np.size(xcor)))) - np.size(xcor) / 2.
        lag = lag * samplePeriod / 60.  # Lag in minutes

        md0 = sig0.getAllMetaData()
        md1 = sig1.getAllMetaData()

        defaults = {}
        defaults['ylabel'] = 'Cross Correlation Coefficient'
        defaults['xlabel'] = 'Lag [min]'
        defaults['title'] = '\n'.join([md0['title'], md1['title']])
        defaults['fft_xlabel'] = 'Frequency [Hz]'
        defaults['fft_ylabel'] = 'FFT Spectrum Magnitude'
        defaults['validTimes'] = sig0.getValidTimes()

        self.metadata = dict(list(defaults.items()) + list(metadata.items()))
        self.xcor = xcorStruct(lag, xcor, comment=comment, parent=self)
        self.active = self.xcor

    def plot(self):
        """Plots the currently active signal.
        """
        self.active.plot()

    def plotfft(self, **metadata):
        """Plots the spectrum of the currently active signal.
        """
        self.active.plotfft(**metadata)


class xcorStruct(xcor):

    def __init__(self, dtv, data, comment=None, parent=0, **metadata):
        self.parent = parent
        """Define a vtsd sigStruct object.

        Parameters
        ---------
        dtv : list
            datetime.datetime list
        data : list
            raw data
        comment : Optional[str]
            info message
        parent : Optional[int]
        metadata : dict
            keywords sent to matplot lib, etc.

        Attributes
        ----------
        parent : int
        dtv : list
            datetime.datetime list
        data : list
            raw data
        metadata : dict
            keywords sent to matplot lib, etc.
        history : dict

        Returns
        -------
        xcorStruct object

        """
        self.dtv = np.array(dtv)
        self.data = np.array(data)
        self.metadata = {}
        for key in metadata:
            self.metadata[key] = metadata[key]

        self.history = {datetime.datetime.now(): comment}

    def copy(self, newsig, comment):
        """Copy a vtsig object. This deep copies data and metadata,
        updates the serial number, and logs a comment in the history.
        Methods such as plot are kept as a reference.

        Parameters
        ---------
        newsig : str
            A string with the name for the new signal.
        comment :  str
            A string comment describing the new signal.

        Returns
        -------
        xcorStruct object

        """
        if hasattr(self.parent, newsig):
            xx = 0
            ok = False
            while ok is False:
                xx += 1
                testsig = '_'.join([newsig, '%03d' % xx])
                if hasattr(self.parent, testsig) is False:
                    newsig = testsig
                    ok = True

        setattr(self.parent, newsig, copy.copy(self))
        newsigobj = getattr(self.parent, newsig)

        newsigobj.dtv = copy.deepcopy(self.dtv)
        newsigobj.data = copy.deepcopy(self.data)
        newsigobj.metadata = copy.deepcopy(self.metadata)
        newsigobj.history = copy.deepcopy(self.history)

        newsigobj.history[datetime.datetime.now()] = comment

        return newsigobj

    def makeNewSignal(self, newsig, dtv, data, comment, **kwargs):
        """Create a new vt sigStruct object that is a derivative of this one.
        This deep copies data and metadata, updates the serial number,
        and logs a comment in the history.  Methods such as plot are kept
        as a reference.

        Parameters
        ---------
        newsig : str
            A string with the name for the new signal.
        dtv : list
            datetime.datetime list
        data : list
            raw data
        comment : str
            A string comment describing the new signal.
        kwargs
            appendTitle : str
                String that will be appended to plot's title.

        Returns
        -------
        xcorStruct object

        """
        newobj = self.copy(newsig, comment)
        newobj.dtv = dtv
        newobj.data = data

        if 'appendTitle' in kwargs:
            md = newobj.getAllMetaData()
            if 'title' in md:
                newobj.metadata['title'] = ' '.join(
                    [kwargs['appendTitle'], md['title']])

        newobj.setActive()

    def setActive(self):
        """Sets this signal as the currently active signal.
        """
        self.parent.active = self

    def nyquistFrequency(self, dtv=None):
        """Calculate the Nyquist frequency of a vt sigStruct signal.

        Parameters
        ---------
        dtv : Optional[list]
            datetime.datetime list

        Returns
        -------
        nyq : float
            Nyquist frequency of the signal in Hz.

        """
        dt = self.samplePeriod(dtv=dtv)
        nyq = 1. / (2 * dt)
        return nyq

    def samplePeriod(self, dtv=None):
        """Calculate the sample period of a vt sigStruct signal.

        Parameters
        ---------
        dtv : Optional[list]
            datetime.datetime list

        Returns
        -------
        samplePeriod : int or float
            sample period of signal in seconds.

        """
        if dtv is None:
            dtv = self.dtv

        diffs = np.unique(np.diff(dtv))
        self.diffs = diffs

        if len(diffs) == 1:
            samplePeriod = diffs[0].total_seconds()
        else:
            maxDt = np.max(diffs) - np.min(diffs)
            maxDt = maxDt.total_seconds()
            avg = np.sum(diffs) / len(diffs)
            avg = avg.total_seconds()
            md = self.getAllMetaData()
            warn = 'WARNING'
            if 'title' in md:
                warn = ' '.join([warn, 'FOR', '"' + md['title'] + '"'])
            logging.warning(warn + ':\n' +
                            '   Date time vector is not regularly sampled!\n' +
                            '   Maximum difference in sampling rates is ' +
                            str(maxDt) + ' sec.\n' +
                            '   Using average sampling period of ' + str(avg) +
                            ' sec.')
            samplePeriod = avg

        return samplePeriod

    def updateValidTimes(self, times):
        """Update the metadata block times that a signal is valid for.

        Parameters
        ---------
        times : list
            List of times between which the signal is valid.

        """
        if 'validTimes' in self.metadata:
            if self.metadata['validTimes'][0] < times[0]:
                self.metadata['validTimes'][0] = times[0]
            if self.metadata['validTimes'][1] > times[1]:
                self.metadata['validTimes'][1] = times[1]
        else:
            self.metadata['validTimes'] = times

    def getAllMetaData(self):
        return dict(list(self.parent.metadata.items()) + list(self.metadata.items()))

    def setMetaData(self, **metadata):
        self.metadata = dict(list(self.metadata.items()) + list(metadata.items()))

    def truncate(self):
        """Trim the ends of the current signal to match the valid time and
        sets the truncated signal to active.
        """

        # Don't do anything if the whole thing is valid.
        valid = self.getValidTimes()

        if valid is None:
            return self
        elif (valid[0] <= self.dtv[0]) & (valid[1] >= self.dtv[1]):
            return self

        comment = ' - '.join([x.strftime('%Y%b%d %H:%M UT').upper()
                              for x in valid])
        comment = 'Truncate: ' + comment
        newsig = self.copy('truncate', comment)

        inx = self.getValidInx()
        newsig.dtv = newsig.dtv[inx]
        newsig.data = newsig.data[inx]
        newsig.updateValidTimes([newsig.dtv[0], newsig.dtv[-1]])

        # Remove old time limits.
        if 'xmin' in newsig.metadata:
            if newsig.metadata['xmin'] <= newsig.dtv[0]:
                del newsig.metadata['xmin']

        if 'xmax' in newsig.metadata:
            if newsig.metadata['xmax'] >= newsig.dtv[-1]:
                del newsig.metadata['xmax']

        newsig.setActive()
        return newsig

    def plot(self):
        # from matplotlib import pyplot as mp

        # Metadata of "processed" signal overrides defaults.
        md = self.getAllMetaData()

        if 'lineStyle' in md:
            lineStyle = md['lineStyle']
        else:
            lineStyle = '-'
        fig = mp.figure()
        mp.plot(self.dtv, self.data, lineStyle)

        if 'xmin' in md:
            mp.xlim(xmin=md['xmin'])
        if 'xmax' in md:
            mp.xlim(xmax=md['xmax'])

        if 'ymin' in md:
            mp.ylim(ymin=md['ymin'])
        if 'ymax' in md:
            mp.ylim(ymax=md['ymax'])

        mp.xlabel(md['xlabel'])
        mp.ylabel(md['ylabel'])
        mp.title(md['title'])
        mp.grid()

        # Print the time window of the FFT on the side of the plot.
        valid = self.getValidTimes()
        s = ' - '.join([x.strftime('%Y%b%d %H:%M UT').upper() for x in valid])
        mp.annotate(s, xy=(1.01, 0.95), xycoords="axes fraction", rotation=90)

    def getFftTimes(self):
        """Returns the time window for which to calculate the FFT times for
        a given signal. This will look in the for the signal's metadata object
        and return the most restrictive range of metadata['validTimes'] and
        metadata['fftTimes'] ranges.

        Returns
        -------
        None or 2-element list of datetime.dateime where the FFT should
        be taken.

        """
        md = self.getAllMetaData()
        start = []
        end = []

        keys = ['validTimes', 'fftTimes']
        for kk in keys:
            if kk in md:
                start.append(md[kk][0])
                end.append(md[kk][1])

        start.sort(reverse=True)
        end.sort()

        if start == []:
            return [self.dtv[0], self.dtv[-1]]
        else:
            return [start[0], end[0]]

    def getFftInx(self):
        """Returns indices of the signal for the time range over which the FFT
        is going to be taken. Uses time range from getFftTimes().

        Returns
        -------
        inx : list
            list of indices of the signal for the time range over which
            the FFT is going to be taken.

        """
        valid = self.getFftTimes()
        if valid is None:
            inx = list(range(len(self.dtv)))
        else:
            inx = np.where((self.dtv >= valid[0]) & (self.dtv <= valid[1]))

        return inx

    def getValidTimes(self):
        """Returns the time window for which the signal is valid.
        This will look in the for the signal's metadata object and return the
        range of metadata['validTimes'].

        Returns
        -------
        None or 2-element list of datetime.dateime.

        """
        md = self.getAllMetaData()
        if 'validTimes' in md:
            valid = md['validTimes']
        else:
            valid = [self.dtv[0], self.dtv[-1]]

        return valid

    def getValidInx(self):
        """Returns indices of the signal for the time range over which
        the signal is valid. Uses time range from getValidTimes().

        Returns
        -------
        inx : list
            list of indices of the signal for the time range over which
            the signal is valid.

        """
        valid = self.getValidTimes()
        if valid is None:
            inx = list(range(len(self.dtv)))
        else:
            inx = np.where((self.dtv >= valid[0]) & (self.dtv <= valid[1]))

        return inx

    def fft(self):
        """Calculates the FFT spectral magnitude for the signal.
        """

        valid = self.getFftTimes()
        inx = self.getFftInx()
        dtv = self.dtv[inx]
        data = self.data[inx]

        self.preFftDtv = dtv
        self.preFftData = data

        nsamp = len(data)

        # Nyquist Frequency
        nyq = self.nyquistFrequency(dtv)

        freq_ax = np.arange(nsamp, dtype='f8')
        freq_ax = (freq_ax / max(freq_ax)) - 0.5
        freq_ax = freq_ax * 2. * nyq

        window = np.hanning(nsamp)
        signal = data * window

        sig_fft = sp.fftpack.fft(signal)
        sig_fft = sp.fftpack.fftshift(sig_fft)

        self.fftTimes = valid
        self.freqVec = freq_ax
        self.spectrum = sig_fft

# Plot FFT of Some Signal
    def plotfft(self, **metadata):
        """Plots the FFT spectral magnitude for the signal.
        """

        self.fft()
        freq_ax = self.freqVec
        sig_fft = self.spectrum

        self.setMetaData(**metadata)
        # Metadata of "processed" signal overrides defaults.
        md = self.getAllMetaData()

        fig = mp.figure()
        ax = fig.add_subplot(111)

        if 'fft_lineStyle' in md:
            lineStyle = md['fft_lineStyle']
        else:
            lineStyle = '-'
        ax.plot(freq_ax, abs(sig_fft), lineStyle)

        if 'title' in md:
            mp.title(md['title'])
        if 'fft_title' in md:
            mp.title(md['fft_title'])

        if 'fft_xlabel' in md:
            mp.xlabel(md['fft_xlabel'])
        if 'fft_ylabel' in md:
            mp.ylabel(md['fft_ylabel'])

        if 'fft_xmin' in md:
            mp.xlim(xmin=md['fft_xmin'])
        else:
            mp.xlim(xmin=0)

        if 'fft_xmax' in md:
            mp.xlim(xmax=md['fft_xmax'])

        if 'fft_ymin' in md:
            mp.ylim(ymin=md['fft_ymin'])
        if 'fft_ymax' in md:
            mp.ylim(ymax=md['fft_ymax'])

        # Print the time window of the FFT on the side of the plot.
        valid = self.getFftTimes()
        s = ' - '.join([x.strftime('%Y%b%d %H:%M UT').upper() for x in valid])
        mp.annotate(s, xy=(1.01, 0.95), xycoords="axes fraction", rotation=90)

        mp.show()

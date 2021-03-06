"""
Plotting utilities, including routines for plotting:
    * time series (and comparing with reference data sets)
    * remapped horizontal fields (and comparing with reference data sets)
    * vertical sections on native grid
    * NINO34 time series and spectra

Authors
-------
Xylar Asay-Davis, Milena Veneziani, Luke Van Roekel, Greg Streletz
"""

import matplotlib.pyplot as plt
import matplotlib.colors as cols
import xarray as xr
import pandas as pd
from mpl_toolkits.basemap import Basemap
from matplotlib.ticker import FuncFormatter, FixedLocator
import numpy as np
from functools import partial
from mpl_toolkits.axes_grid1 import make_axes_locatable, ImageGrid

from ..timekeeping.utility import days_to_datetime, date_to_days

from ..constants import constants

import ConfigParser


def timeseries_analysis_plot(config, dsvalues, N, title, xlabel, ylabel,
                             fileout, lineStyles, lineWidths, legendText,
                             calendar, titleFontSize=None, figsize=(15, 6),
                             dpi=None, maxXTicks=20):

    """
    Plots the list of time series data sets and stores the result in an image
    file.

    Parameters
    ----------
    config : instance of ConfigParser
        the configuration, containing a [plot] section with options that
        control plotting

    dsvalues : list of xarray DataSets
        the data set(s) to be plotted

    N : int
        the numer of time points over which to perform a moving average

    title : str
        the title of the plot

    xlabel, ylabel : str
        axis labels

    fileout : str
        the file name to be written

    lineStyles, lineWidths, legendText : list of str
        control line style/width and corresponding legend text

    calendar : str
        the calendar to use for formatting the time axis

    titleFontSize : int, optional
        the size of the title font

    figsize : tuple of float, optional
        the size of the figure in inches

    dpi : int, optional
        the number of dots per inch of the figure, taken from section ``plot``
        option ``dpi`` in the config file by default

    maxXTicks : int, optional
        the maximum number of tick marks that will be allowed along the x axis.
        This may need to be adjusted depending on the figure size and aspect
        ratio.

    Authors
    -------
    Xylar Asay-Davis, Milena Veneziani
    """

    if dpi is None:
        dpi = config.getint('plot', 'dpi')
    plt.figure(figsize=figsize, dpi=dpi)

    minDays = []
    maxDays = []
    for dsIndex in range(len(dsvalues)):
        dsvalue = dsvalues[dsIndex]
        if dsvalue is None:
            continue
        mean = pd.Series.rolling(dsvalue.to_pandas(), N, center=True).mean()
        mean = xr.DataArray.from_series(mean)
        minDays.append(mean.Time.min())
        maxDays.append(mean.Time.max())
        plt.plot(mean['Time'], mean,
                 lineStyles[dsIndex],
                 linewidth=lineWidths[dsIndex],
                 label=legendText[dsIndex])
    plt.legend(loc='lower left')

    ax = plt.gca()

    if titleFontSize is None:
        titleFontSize = config.get('plot', 'titleFontSize')
    axis_font = {'size': config.get('plot', 'axisFontSize')}
    title_font = {'size': titleFontSize,
                  'color': config.get('plot', 'titleFontColor'),
                  'weight': config.get('plot', 'titleFontWeight')}

    # Add a y=0 line if y ranges between positive and negative values
    yaxLimits = ax.get_ylim()
    if yaxLimits[0]*yaxLimits[1] < 0:
        indgood = np.where(np.logical_not(np.isnan(mean)))
        x = mean['Time'][indgood]
        plt.plot(x, np.zeros(np.size(x)), 'k-', linewidth=1.2)

    plot_xtick_format(plt, calendar, minDays, maxDays, maxXTicks)

    if title is not None:
        plt.title(title, **title_font)
    if xlabel is not None:
        plt.xlabel(xlabel, **axis_font)
    if ylabel is not None:
        plt.ylabel(ylabel, **axis_font)
    if fileout is not None:
        plt.savefig(fileout, dpi=dpi, bbox_inches='tight', pad_inches=0.1)

    if not config.getboolean('plot', 'displayToScreen'):
        plt.close()


def timeseries_analysis_plot_polar(config, dsvalues, N, title,
                                   fileout, lineStyles, lineWidths,
                                   legendText, titleFontSize=None,
                                   figsize=(15, 6), dpi=None):

    """
    Plots the list of time series data sets on a polar plot and stores
    the result in an image file.

    Parameters
    ----------
    config : instance of ConfigParser
        the configuration, containing a [plot] section with options that
        control plotting

    dsvalues : list of xarray DataSets
        the data set(s) to be plotted

    N : int
        the numer of time points over which to perform a moving average

    title : str
        the title of the plot

    fileout : str
        the file name to be written

    lineStyles, lineWidths, legendText : list of str
        control line style/width and corresponding legend text

    titleFontSize : int, optional
        the size of the title font

    figsize : tuple of float, optional
        the size of the figure in inches

    dpi : int, optional
        the number of dots per inch of the figure, taken from section ``plot``
        option ``dpi`` in the config file by default

    Authors
    -------
    Adrian K. Turner, Xylar Asay-Davis
    """
    if dpi is None:
        dpi = config.getint('plot', 'dpi')
    plt.figure(figsize=figsize, dpi=dpi)

    minDays = []
    maxDays = []
    for dsIndex in range(len(dsvalues)):
        dsvalue = dsvalues[dsIndex]
        if dsvalue is None:
            continue
        mean = pd.Series.rolling(dsvalue.to_pandas(), N, center=True).mean()
        mean = xr.DataArray.from_series(mean)
        minDays.append(mean.Time.min())
        maxDays.append(mean.Time.max())
        plt.polar((mean['Time']/365.0)*np.pi*2.0, mean,
                  lineStyles[dsIndex],
                  linewidth=lineWidths[dsIndex],
                  label=legendText[dsIndex])
    plt.legend(loc='lower left')

    ax = plt.gca()

    # set azimuthal axis formatting
    majorTickLocs = np.zeros(12)
    minorTickLocs = np.zeros(12)
    majorTickLocs[0] = 0.0
    minorTickLocs[0] = (constants.daysInMonth[0] * np.pi) / 365.0
    for month in range(1, 12):
        majorTickLocs[month] = majorTickLocs[month-1] + \
            ((constants.daysInMonth[month-1] * np.pi * 2.0) / 365.0)
        minorTickLocs[month] = minorTickLocs[month-1] + \
            (((constants.daysInMonth[month-1] + \
               constants.daysInMonth[month]) * np.pi) / 365.0)

    ax.set_xticks(majorTickLocs)
    ax.set_xticklabels([])

    ax.set_xticks(minorTickLocs, minor=True)
    ax.set_xticklabels(constants.abrevMonthNames, minor=True)

    if titleFontSize is None:
        titleFontSize = config.get('plot', 'titleFontSize')

    axis_font = {'size': config.get('plot', 'axisFontSize')}
    title_font = {'size': titleFontSize,
                  'color': config.get('plot', 'titleFontColor'),
                  'weight': config.get('plot', 'titleFontWeight')}
    if title is not None:
        plt.title(title, **title_font)

    if fileout is not None:
        plt.savefig(fileout, dpi=dpi, bbox_inches='tight', pad_inches=0.1)

    if not config.getboolean('plot', 'displayToScreen'):
        plt.close()


def plot_polar_comparison(
        config,
        Lons,
        Lats,
        modelArray,
        obsArray,
        diffArray,
        cmapModelObs,
        clevsModelObs,
        cmapDiff,
        clevsDiff,
        fileout,
        title=None,
        plotProjection='npstere',
        latmin=50.0,
        lon0=0,
        modelTitle='Model',
        obsTitle='Observations',
        diffTitle='Model-Observations',
        cbarlabel='units',
        titleFontSize=None,
        figsize=None,
        dpi=None,
        vertical=False):

    """
    Plots a data set around either the north or south pole.

    Parameters
    ----------
    config : instance of ConfigParser
        the configuration, containing a [plot] section with options that
        control plotting

    Lons, Lats : float arrays
        longitude and latitude arrays

    modelArray, obsArray : float arrays
        model and observational data sets

    diffArray : float array
        difference between modelArray and obsArray

    cmapModelObs : str
        colormap of model and observations panel

    clevsModelObs : int array
        colorbar values for model and observations panel

    cmapDiff : str
        colormap of difference (bias) panel

    clevsDiff : int array
        colorbar values for difference (bias) panel

    fileout : str
        the file name to be written

    title : str, optional
        the subtitle of the plot

    plotProjection : str, optional
        Basemap projection for the plot

    modelTitle : str, optional
        title of the model panel

    obsTitle : str, optional
        title of the observations panel

    diffTitle : str, optional
        title of the difference (bias) panel

    cbarlabel : str, optional
        label on the colorbar

    titleFontSize : int, optional
        size of the title font

    figsize : tuple of float, optional
        the size of the figure in inches.  If ``None``, the figure size is
        ``(8, 22)`` if ``vertical == True`` and ``(22, 8)`` otherwise.

    dpi : int, optional
        the number of dots per inch of the figure, taken from section ``plot``
        option ``dpi`` in the config file by default

    vertical : bool, optional
        whether the subplots should be stacked vertically rather than
        horizontally

    Authors
    -------
    Xylar Asay-Davis, Milena Veneziani
    """

    def do_subplot(ax, field, title, cmap, norm, levels):
        """
        Make a subplot within the figure.
        """

        m = Basemap(projection=plotProjection, boundinglat=latmin,
                    lon_0=lon0, resolution='l', ax=ax)
        x, y = m(Lons, Lats)  # compute map proj coordinates

        ax.set_title(title, y=1.06, **axis_font)
        m.drawcoastlines()
        m.fillcontinents(color='grey', lake_color='white')
        m.drawparallels(np.arange(-80., 81., 10.))
        m.drawmeridians(np.arange(-180., 181., 20.),
                        labels=[True, False, True, True])
        cs = m.contourf(x, y, field, cmap=cmap, norm=norm,
                        levels=levels)

        cbar = m.colorbar(cs, location='right', pad="3%", spacing='uniform',
                          ticks=levels, boundaries=levels)
        cbar.set_label(cbarlabel)

    if dpi is None:
        dpi = config.getint('plot', 'dpi')

    if vertical:
        if figsize is None:
            figsize = (8, 22)
        subplots = [311, 312, 313]
    else:
        if figsize is None:
            figsize = (22, 8.5)
        subplots = [131, 132, 133]

    fig = plt.figure(figsize=figsize, dpi=dpi)

    if (title is not None):
        if titleFontSize is None:
            titleFontSize = config.get('plot', 'titleFontSize')
        title_font = {'size': titleFontSize,
                      'color': config.get('plot', 'titleFontColor'),
                      'weight': config.get('plot', 'titleFontWeight')}
        fig.suptitle(title, y=0.95, **title_font)
    axis_font = {'size': config.get('plot', 'axisFontSize')}

    normModelObs = cols.BoundaryNorm(clevsModelObs, cmapModelObs.N)
    normDiff = cols.BoundaryNorm(clevsDiff, cmapDiff.N)

    ax = plt.subplot(subplots[0])
    do_subplot(ax=ax, field=modelArray, title=modelTitle, cmap=cmapModelObs,
               norm=normModelObs, levels=clevsModelObs)

    ax = plt.subplot(subplots[1])
    do_subplot(ax=ax, field=obsArray, title=obsTitle, cmap=cmapModelObs,
               norm=normModelObs, levels=clevsModelObs)

    ax = plt.subplot(subplots[2])
    do_subplot(ax=ax, field=diffArray, title=diffTitle, cmap=cmapDiff,
               norm=normDiff, levels=clevsDiff)

    plt.tight_layout(pad=4.)
    if vertical:
        plt.subplots_adjust(top=0.9)

    if (fileout is not None):
        plt.savefig(fileout, dpi=dpi, bbox_inches='tight', pad_inches=0.1)

    if not config.getboolean('plot', 'displayToScreen'):
        plt.close()


def plot_global_comparison(
    config,
    Lons,
    Lats,
    modelArray,
    obsArray,
    diffArray,
    cmapModelObs,
    clevsModelObs,
    cmapDiff,
    clevsDiff,
    fileout,
    title=None,
    modelTitle='Model',
    obsTitle='Observations',
    diffTitle='Model-Observations',
    cbarlabel='units',
    titleFontSize=None,
    figsize=(8, 12),
    dpi=None):

    """
    Plots a data set as a longitude/latitude map.

    Parameters
    ----------
    config : instance of ConfigParser
        the configuration, containing a [plot] section with options that
        control plotting

    Lons, Lats : float arrays
        longitude and latitude arrays

    modelArray, obsArray : float arrays
        model and observational data sets

    diffArray : float array
        difference between modelArray and obsArray

    cmapModelObs : str
        colormap of model and observations panel

    clevsModelObs : int array
        colorbar values for model and observations panel

    cmapDiff : str
        colormap of difference (bias) panel

    clevsDiff : int array
        colorbar values for difference (bias) panel

    fileout : str
        the file name to be written

    title : str, optional
        the subtitle of the plot

    modelTitle : str, optional
        title of the model panel

    obsTitle : str, optional
        title of the observations panel

    diffTitle : str, optional
        title of the difference (bias) panel

    cbarlabel : str, optional
        label on the colorbar

    titleFontSize : int, optional
        size of the title font

    figsize : tuple of float, optional
        the size of the figure in inches

    dpi : int, optional
        the number of dots per inch of the figure, taken from section ``plot``
        option ``dpi`` in the config file by default

    Authors
    -------
    Xylar Asay-Davis, Milena Veneziani
    """

    # set up figure
    if dpi is None:
        dpi = config.getint('plot', 'dpi')
    fig = plt.figure(figsize=figsize, dpi=dpi)
    if (title is not None):
        if titleFontSize is None:
            titleFontSize = config.get('plot', 'titleFontSize')
        title_font = {'size': titleFontSize,
                      'color': config.get('plot', 'titleFontColor'),
                      'weight': config.get('plot', 'titleFontWeight')}
        fig.suptitle(title, y=0.95, **title_font)
    axis_font = {'size': config.get('plot', 'axisFontSize')}

    m = Basemap(projection='cyl', llcrnrlat=-85, urcrnrlat=86, llcrnrlon=-180,
                urcrnrlon=181, resolution='l')
    x, y = m(Lons, Lats)  # compute map proj coordinates

    normModelObs = cols.BoundaryNorm(clevsModelObs, cmapModelObs.N)
    normDiff = cols.BoundaryNorm(clevsDiff, cmapDiff.N)

    plt.subplot(3, 1, 1)
    plt.title(modelTitle, y=1.06, **axis_font)
    m.drawcoastlines()
    m.fillcontinents(color='grey', lake_color='white')
    m.drawparallels(np.arange(-80., 80., 20.),
                    labels=[True, False, False, False])
    m.drawmeridians(np.arange(-180., 180., 60.),
                    labels=[False, False, False, True])
    cs = m.contourf(x, y, modelArray, cmap=cmapModelObs, norm=normModelObs,
                    levels=clevsModelObs, extend='both')
    cbar = m.colorbar(cs, location='right', pad="5%", spacing='uniform',
                      ticks=clevsModelObs, boundaries=clevsModelObs)
    cbar.set_label(cbarlabel)

    plt.subplot(3, 1, 2)
    plt.title(obsTitle, y=1.06, **axis_font)
    m.drawcoastlines()
    m.fillcontinents(color='grey', lake_color='white')
    m.drawparallels(np.arange(-80., 80., 20.),
                    labels=[True, False, False, False])
    m.drawmeridians(np.arange(-180., 180., 40.),
                    labels=[False, False, False, True])
    cs = m.contourf(x, y, obsArray, cmap=cmapModelObs, norm=normModelObs,
                    levels=clevsModelObs, extend='both')
    cbar = m.colorbar(cs, location='right', pad="5%", spacing='uniform',
                      ticks=clevsModelObs, boundaries=clevsModelObs)
    cbar.set_label(cbarlabel)

    plt.subplot(3, 1, 3)
    plt.title(diffTitle, y=1.06, **axis_font)
    m.drawcoastlines()
    m.fillcontinents(color='grey', lake_color='white')
    m.drawparallels(np.arange(-80., 80., 20.),
                    labels=[True, False, False, False])
    m.drawmeridians(np.arange(-180., 180., 40.),
                    labels=[False, False, False, True])
    cs = m.contourf(x, y, diffArray, cmap=cmapDiff, norm=normDiff,
                    levels=clevsDiff, extend='both')
    cbar = m.colorbar(cs, location='right', pad="5%", spacing='uniform',
                      ticks=clevsDiff, boundaries=clevsModelObs)
    cbar.set_label(cbarlabel)

    if (fileout is not None):
        plt.savefig(fileout, dpi=dpi, bbox_inches='tight', pad_inches=0.1)

    if not config.getboolean('plot', 'displayToScreen'):
        plt.close()


def _date_tick(days, pos, calendar='gregorian', includeMonth=True):
    days = np.maximum(days, 0.)
    date = days_to_datetime(days, calendar)
    if includeMonth:
        return '{:04d}-{:02d}'.format(date.year, date.month)
    else:
        return '{:04d}'.format(date.year)


def plot_1D(config, xArrays, fieldArrays, errArrays,
            lineColors, lineWidths, legendText,
            title=None, xlabel=None, ylabel=None,
            fileout='plot_1D.png',
            figsize=(10, 4), dpi=None,
            xLim=None,
            yLim=None,
            invertYAxis=False):  # {{{

    """
    Plots a 1D line plot with error bars if available.

    Parameters
    ----------
    config : instance of ConfigParser
        the configuration, containing a [plot] section with options that
        control plotting

    xArrays : list of float arrays
        x array (latitude, or any other x axis except time)

    fieldArrays : list of float arrays
        y array (any field as function of x)

    errArrays : list of float arrays
        error array (y errors)

    lineColors, legendText : list of str
        control line color and legend

    lineWidths : list of int
        control line width

    title : str, optional
        title of plot

    xlabel, ylabel : str, optional
        label of x- and y-axis

    fileout : str, optional
        the file name to be written

    figsize : tuple of float, optional
        size of the figure in inches

    dpi : int, optional
        the number of dots per inch of the figure, taken from section ``plot``
        option ``dpi`` in the config file by default

    xLim : float array, optional
        x range of plot

    yLim : float array, optional
        y range of plot

    invertYAxis : logical, optional
        if True, invert Y axis

    Authors
    -------
    Mark Petersen, Milena Veneziani
    """

    # set up figure
    if dpi is None:
        dpi = config.getint('plot', 'dpi')
    plt.figure(figsize=figsize, dpi=dpi)

    for dsIndex in range(len(xArrays)):
        xArray = xArrays[dsIndex]
        fieldArray = fieldArrays[dsIndex]
        errArray = errArrays[dsIndex]
        if xArray is None:
            continue
        if errArray is None:
            plt.plot(xArray, fieldArray,
                     color=lineColors[dsIndex],
                     linewidth=lineWidths[dsIndex],
                     label=legendText[dsIndex])
        else:
            plt.plot(xArray, fieldArray,
                     color=lineColors[dsIndex],
                     linewidth=lineWidths[dsIndex],
                     label=legendText[dsIndex])
            plt.fill_between(xArray, fieldArray, fieldArray+errArray,
                             facecolor=lineColors[dsIndex], alpha=0.2)
            plt.fill_between(xArray, fieldArray, fieldArray-errArray,
                             facecolor=lineColors[dsIndex], alpha=0.2)
    plt.grid()
    plt.axhline(0.0, linestyle='-', color='k')  # horizontal lines
    if dsIndex > 0:
        plt.legend()

    axis_font = {'size': config.get('plot', 'axisFontSize')}
    title_font = {'size': config.get('plot', 'titleFontSize'),
                  'color': config.get('plot', 'titleFontColor'),
                  'weight': config.get('plot', 'titleFontWeight')}
    if title is not None:
        plt.title(title, **title_font)
    if xlabel is not None:
        plt.xlabel(xlabel, **axis_font)
    if ylabel is not None:
        plt.ylabel(ylabel, **axis_font)

    if invertYAxis:
        plt.gca().invert_yaxis()

    if xLim:
        plt.xlim(xLim)
    if yLim:
        plt.ylim(yLim)

    if (fileout is not None):
        plt.savefig(fileout, dpi=dpi, bbox_inches='tight', pad_inches=0.1)

    if not config.getboolean('plot', 'displayToScreen'):
        plt.close()

    return  # }}}


def plot_vertical_section(
    config,
    xArray,
    depthArray,
    fieldArray,
    colormapName,
    colorbarLevels,
    contourLevels,
    colorbarLabel=None,
    title=None,
    xlabel=None,
    ylabel=None,
    fileout='moc.png',
    figsize=(10, 4),
    dpi=None,
    xLim=None,
    yLim=None,
    linewidths=2,
    invertYAxis=True,
    xArrayIsTime=False,
    N=None,
    maxXTicks=20,
    calendar='gregorian'):  # {{{

    """
    Plots a data set as a x distance (latitude, longitude,
    or spherical distance) vs depth map (vertical section).

    Or, if xArrayIsTime is True, plots data set on a vertical
    Hovmoller plot (depth vs. time).

    Parameters
    ----------
    config : instance of ConfigParser
        the configuration, containing a [plot] section with options that
        control plotting

    xArray : float array
        x array (latitude, longitude, or spherical distance; or, time for a Hovmoller plot)

    depthArray : float array
        depth array [m]

    fieldArray : float array
        field array to plot

    colormapName : str
        colormap of plot

    colorbarLevels : int array
        colorbar levels of plot

    contourLevels : int levels
        levels of contours to be drawn

    colorbarLabel : str, optional
        label of the colorbar

    title : str, optional
        title of plot

    xlabel, ylabel : str, optional
        label of x- and y-axis

    fileout : str, optional
        the file name to be written

    figsize : tuple of float, optional
        size of the figure in inches

    dpi : int, optional
        the number of dots per inch of the figure, taken from section ``plot``
        option ``dpi`` in the config file by default

    xLim : float array, optional
        x range of plot

    yLim : float array, optional
        y range of plot

    linewidths : int, optional
        linewidths for contours

    invertYAxis : logical, optional
        if True, invert Y axis

    xArrayIsTime : logical, optional
        if True, format X axis for time

    N : int, optional
        the number of points over which to perform a moving average
        NOTE: this option is mostly intended for use when xArrayIsTime is True,
        although it will work with other data as well.  Also, the moving average
        calculation is based on number of points, not actual x axis values, so for
        best results, the values in the xArray should be equally spaced.

    maxXTicks : int, optional
        the maximum number of tick marks that will be allowed along the x axis.
        This may need to be adjusted depending on the figure size and aspect
        ratio.  NOTE:  maxXTicks is only used if xArrayIsTime is True

    calendar : str, optional
        the calendar to use for formatting the time axis
        NOTE:  calendar is only used if xArrayIsTime is True

    Authors
    -------
    Milena Veneziani, Mark Petersen, Xylar Asay-Davis, Greg Streletz
    """

    # verify that the dimensions of fieldArray are consistent with those of xArray and depthArray
    if len(xArray) != fieldArray.shape[1]:
        raise ValueError('size mismatch between xArray and fieldArray')
    elif len(depthArray) != fieldArray.shape[0]:
        raise ValueError('size mismatch between depthArray and fieldArray')

    # set up figure
    if dpi is None:
        dpi = config.getint('plot', 'dpi')
    plt.figure(figsize=figsize, dpi=dpi)

    if N is not None and N != 1:   # compute moving averages with respect to the x dimension
        movingAverageDepthSlices = []
        for nVertLevel in range(len(depthArray)):
            depthSlice = fieldArray[[nVertLevel]][0]
            depthSlice = xr.DataArray(depthSlice)  # in case it's not an xarray already
            mean = pd.Series.rolling(depthSlice.to_series(), N, center=True).mean()
            mean = xr.DataArray.from_series(mean)
            mean = mean[int(N/2.0):-int(round(N/2.0)-1)]
            movingAverageDepthSlices.append(mean)
        xArray = xArray[int(N/2.0):-int(round(N/2.0)-1)]
        fieldArray = xr.DataArray(movingAverageDepthSlices)

    x, y = np.meshgrid(xArray, depthArray)  # change to zMid

    if colorbarLevels is None:
        normModelObs = None
    else:
        normModelObs = cols.BoundaryNorm(colorbarLevels, colormapName.N)

    cs = plt.contourf(x, y, fieldArray, cmap=colormapName, norm=normModelObs,
                      levels=colorbarLevels, extend='both')

    if contourLevels is not None:
        if len(contourLevels) == 0:
            contourLevels = None   # automatic calculation of contour levels
        plt.contour(x, y, fieldArray, levels=contourLevels, colors='k', linewidths=linewidths)

    cbar = plt.colorbar(cs, orientation='vertical', spacing='uniform',
                        ticks=colorbarLevels, boundaries=colorbarLevels)

    if colorbarLabel is not None:
        cbar.set_label(colorbarLabel)

    axis_font = {'size': config.get('plot', 'axisFontSize')}
    title_font = {'size': config.get('plot', 'titleFontSize'),
                  'color': config.get('plot', 'titleFontColor'),
                  'weight': config.get('plot', 'titleFontWeight')}
    if title is not None:
        plt.title(title, **title_font)
    if xlabel is not None:
        plt.xlabel(xlabel, **axis_font)
    if ylabel is not None:
        plt.ylabel(ylabel, **axis_font)

    if invertYAxis:
        plt.gca().invert_yaxis()

    if xLim:
        plt.xlim(xLim)
    if yLim:
        plt.ylim(yLim)

    if xArrayIsTime:
        minDays = [xArray[0]]
        maxDays = [xArray[-1]]
        plot_xtick_format(plt, calendar, minDays, maxDays, maxXTicks)

    if (fileout is not None):
        plt.savefig(fileout, dpi=dpi, bbox_inches='tight', pad_inches=0.1)

    if not config.getboolean('plot', 'displayToScreen'):
        plt.close()

    return  # }}}


def setup_colormap(config, configSectionName, suffix=''):

    '''
    Set up a colormap from the registry

    Parameters
    ----------
    config : instance of ConfigParser
        the configuration, containing a [plot] section with options that
        control plotting

    configSectionName : str
        name of config section

    suffix: str, optional
        suffix of colormap related options

    Returns
    -------
    colormap : srt
        new colormap

    colorbarLevels : int array
        colorbar levels

    Authors
    -------
    Xylar Asay-Davis, Milena Veneziani, Greg Streletz
    '''

    colormap = plt.get_cmap(config.get(configSectionName,
                                       'colormapName{}'.format(suffix)))

    indices = config.getExpression(configSectionName,
                                   'colormapIndices{}'.format(suffix),
                                   usenumpyfunc=True)

    try:
        colorbarLevels = config.getExpression(configSectionName,
                                              'colorbarLevels{}'.format(suffix),
                                              usenumpyfunc=True)
    except(ConfigParser.NoOptionError):
        colorbarLevels = None

    if colorbarLevels is not None:
        # set under/over values based on the first/last indices in the colormap
        underColor = colormap(indices[0])
        overColor = colormap(indices[-1])
        if len(colorbarLevels)+1 == len(indices):
            # we have 2 extra values for the under/over so make the colormap
            # without these values
            indices = indices[1:-1]
        elif len(colorbarLevels)-1 != len(indices):
            # indices list must be either one element shorter
            # or one element longer than colorbarLevels list
            raise ValueError('length mismatch between indices and colorbarLevels')
        colormap = cols.ListedColormap(colormap(indices),
                                       'colormapName{}'.format(suffix))
        colormap.set_under(underColor)
        colormap.set_over(overColor)

    return (colormap, colorbarLevels)


def plot_size_y_axis(plt, xaxisValues, **data):
    '''
    Resize the y-axis limit based on the curves being plotted

    Parameters
    ----------
    plt : plot handle

    xaxisValues : numpy.array
       Values plotted along the x-axis

    data : dictionary entries must be numpy.array
       data for curves on plot

    Authors
    -------
    Luke Van Roekel
    '''

    ax = plt.gca()
    xmin = ax.get_xlim()[0]
    xmax = ax.get_xlim()[1]

    # find period/frequency bounds for chosen xmin/xmax
    minIndex = np.abs(xaxisValues - xmin).argmin()
    maxIndex = np.abs(xaxisValues - xmax).argmin()

    # find maximum value of three curves plotted
    maxCurveVal = -1E20
    for key in data:
        maxTemp = data[key][minIndex:maxIndex].max()
        maxCurveVal = max(maxTemp, maxCurveVal)

    return maxCurveVal


def plot_xtick_format(plt, calendar, minDays, maxDays, maxXTicks):
    '''
    Formats tick labels and positions along the x-axis for time series
    / index plots

    Parameters
    ----------
    plt : plt handle on which to change ticks

    calendar : specified calendar for the plot

    minDays : start time for labels

    maxDays : end time for labels

    Authors
    -------
    Xylar Asay-Davis
    '''
    ax = plt.gca()

    start = days_to_datetime(np.amin(minDays), calendar=calendar)
    end = days_to_datetime(np.amax(maxDays), calendar=calendar)

    if (end.year - start.year > maxXTicks/2):
        major = [date_to_days(year=year, calendar=calendar)
                 for year in np.arange(start.year, end.year+1)]
        formatterFun = partial(_date_tick, calendar=calendar,
                               includeMonth=False)
    else:
        # add ticks for months
        major = []
        for year in range(start.year, end.year+1):
            for month in range(1, 13):
                major.append(date_to_days(year=year, month=month,
                                          calendar=calendar))
        formatterFun = partial(_date_tick, calendar=calendar,
                               includeMonth=True)

    ax.xaxis.set_major_locator(FixedLocator(major, maxXTicks))
    ax.xaxis.set_major_formatter(FuncFormatter(formatterFun))

    plt.setp(ax.get_xticklabels(), rotation=30)

    plt.autoscale(enable=True, axis='x', tight=True)



# vim: foldmethod=marker ai ts=4 sts=4 et sw=4 ft=python

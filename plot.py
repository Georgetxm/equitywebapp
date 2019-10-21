import plotly.plotly as py
import plotly.graph_objs as go
import plotly
import pandas as pd
from datetime import datetime
from flask import request

# 'GET' Alpha Vantage's price data in CSV format and use panda lib to plot with Plotly API


def plotGraph(tickerCode):
    alpha_api_key = 'alpha vantage api key'
    plotly_api_key = 'plotly api key'
    plotly.tools.set_credentials_file(
        username='xuanmingt', api_key=plotly_api_key)

    # GET Alphavantage daily stock data in CSV format
    # Using panda library to read it in CSV format
    df = pd.read_csv("https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=" +
                     tickerCode + "&apikey=" + alpha_api_key + "&datatype=csv")

    # POST read data to plotly graph object
    trace = go.Ohlc(x=df['timestamp'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'])

    # Plot with graph object data
    data = [trace]
    py.iplot(data, filename='simple_candlestick', auto_open=False)


def plotPieChart(labels, values):

    plotly_api_key = 'plotly api key'
    plotly.tools.set_credentials_file(
        username='xuanmingt', api_key=plotly_api_key)

    trace = go.Pie(labels=labels, values=values,
                   hoverinfo='value', textinfo='label+percent')

    py.plot([trace], filename='basic_pie_chart', auto_open=False)

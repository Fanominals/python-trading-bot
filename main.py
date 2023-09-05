import numpy as np
from AlgorithmImports import *

class BreakOutTradingBot(QCAlgorithm):

    def Initialize(self):
        self.SetCash(100000)
        self.SetStartDate(2018, 8, 1)
        self.SetEndDate(2023, 8, 1)

        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
        self.lookback = 20

        self.ceiling, self.floor = 30, 10

        self.initialStopRisk  = 0.98
        self.trailingStopRisk = 0.9

        self.Schedule.On(self.DateRules.EveryDay(self.symbol), 
        self.TimeRules.AfterMarketOpen(self.symbol, 20), 
        Action(self.EveryMarketOpen)) 
        #turns on bot every day that set symbol trades, is open 20 minutes after market opens,and runs the function
        #EveryMarketOpen


    def OnData(self, data):
        self.Plot("Data Chart", self.symbol, self.Securities[self.symbol].Close)

    def EveryMarketOpen(self):
        # a list of the daily closing price in the last 30 days
        close = self.History(self.symbol, 31, Resolution.Daily)["close"] 
        
        todayvol = np.std(close[1:31])
        yesterdayvol = np.std(close[0:30])
        deltavol = (todayvol-yesterdayvol)/todayvol

        #sets lookback to the current lookback with a multiplier based on volatility. rounds to nearest integer
        self.lookback = round(self.lookback * (1 + deltavol)) 


        # makes sure our calculated lookback is within our max and min(ceiling and floor) values
        if self.lookback > self.ceiling: 
            self.lookback = self.ceiling
        elif self.lookback < self.floor:
            self.lookback = self.floor


        # gets a list of all daily price highs within our lookback length
        self.high = self.History(self.symbol, self.lookback, Resolution.Daily)["high"]


        # checks if not invested in security and whether the closing price of the security was greater than the 
        # highest daily price in the last 30 days, not including yesterday's daily high because we don't want
        # to compare yesterday's highs with yesterday's close
        if not self.Securities[self.symbol].Invested and self.Securities[self.symbol].Close >= max(self.high[:-1]):
            self.SetHoldings(self.symbol, 1)
            self.breakoutlvl = max(self.high[:-1])
            self.highestPrice = self.breakoutlvl

        # if there is a position in the current security
        if (self.Securities[self.symbol].Invested):
            # if there are no current open orders
            if not self.Transactions.GetOpenOrders(self.symbol):
                # open a stop loss order with entire position at a 2% risk
                self.stopMarketTicket = self.StopMarketOrder(self.symbol, -self.Portfolio[self.symbol].Quantity,
                self.initialStopRisk * self.breakoutlvl)
            # if the close price is greater than the highest price (making a new high), and 
            # the current close price multiplied by trailingStopRisk (0.9) is greater than the stop loss,
            # update stop loss order to the current close price multiplied by trailingStopRisk
            if self.Securities[self.symbol].Close > self.highestPrice and \
                    self.initialStopRisk * self.breakoutlvl < self.Securities[self.symbol].Close * self.trailingStopRisk:
                self.highestPrice = self.Securities[self.symbol].Close
                updateFields = UpdateOrderFields()
                updateFields.StopPrice = self.Securities[self.symbol].Close * self.trailingStopRisk
                self.stopMarketTicket.Update(updateFields)

                self.Debug(updateFields.StopPrice) # prints new stop loss to console

            # plot a stop loss line at current stop loss
            self.Plot("Data Chart", "Stop Price", self.stopMarketTicket.Get(OrderField.StopPrice))

        

      
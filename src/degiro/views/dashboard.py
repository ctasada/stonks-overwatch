from datetime import date, datetime, timedelta
from django.views import View
from django.shortcuts import render
from django.db import connection

import pandas as pd

from degiro.utils.db_utils import dictfetchall
from degiro.integration.portfolio import PortfolioData
from degiro.utils.localization import LocalizationUtility
from degiro_connector.quotecast.models.chart import Interval
from degiro.utils.degiro import DeGiro

import logging
import json

class Dashboard(View):
    logger = logging.getLogger("stocks_portfolio.dashboard.views")

    def __init__(self):
        self.portfolio = PortfolioData()

    def get(self, request):
        sectorsContext = self._getSectors()
        growthContext = self._getGrowth()

        context = {
            "growth": growthContext,
            "sectors": sectorsContext
        }

        # self.logger.debug(context)
        
        # FIXME: Simplify this response
        return render(request, 'dashboard.html', context)

    def _getSectors(self):
        portfolio = self.portfolio.get_portfolio()
        portfolio = sorted(portfolio, key=lambda k: k['sector'])
        # self.logger.debug(json.dumps(portfolio, indent=2))

        sectors = {}

        stockLabels = []
        stockValues = []

        for stock in portfolio:
            if stock['isOpen']:
                sectorName = stock['sector']
                sectors[sectorName] = sectors.get(sectorName, 0) + stock['value']
                stockLabels.append(stock['symbol'])
                stockValues.append(stock['value'])

        sectorLabels = []
        sectorValues = []
        for key in sectors:
            sectorLabels.append(key)
            sectorValues.append(sectors[key])

        return {
                "sectors": {
                    "labels": sectorLabels,
                    "values": sectorValues,
                },
                "stocks": {
                    "labels": stockLabels,
                    "values": stockValues,
                },
                "currencySymbol": LocalizationUtility.get_base_currency_symbol(),
            }
    
    def _getGrowth(self):
        cash_contributions = self._calculate_cash_contributions()
        portfolio_growth = self._calculate_growth()

        return {
            "cash_contributions": cash_contributions,
            "portfolio_growth": portfolio_growth
        }

    def _calculate_cash_contributions(self) -> dict:
        # FIXME: DeGiro doesn't have a consistent description or type. Missing the new value for 'Refund'
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT date, description, change 
                FROM degiro_cashmovements 
                WHERE currency = 'EUR' 
                    AND description IN ('iDEAL storting', 'iDEAL Deposit', 'Terugstorting')
                """
                )
            cashContributions = dictfetchall(cursor)

        df = pd.DataFrame.from_dict(cashContributions)
        # Remove hours and keep only the day
        df['date'] = pd.to_datetime(df['date']).dt.date
        # Group by day, adding the values
        df.set_index('date', inplace=True)
        df = df.sort_values(by='date')
        df = df.groupby(df.index)['change'].sum().reset_index()
        # Do the cummulative sum
        df['contributed'] = df['change'].cumsum()

        cashContributions = df.to_dict('records')
        for contribution in cashContributions:
            contribution['date'] = contribution['date'].strftime('%Y-%m-%d')

        dataset = []
        for contribution in cashContributions:
            dataset.append({'x': contribution['date'], 'y': contribution['contributed']})

        # Append today with the last value to draw the line properly
        dataset.append({'x': date.today().strftime('%Y-%m-%d'), 'y': cashContributions[-1]['contributed']})

        return dataset

    def _get_productInfo(self, productId: int) -> dict:
        """
        Gets product information from the given product id. The information is retrieved from the DB.
        ### Parameters
            * productId: int
                - The product id to query
        ### Returns
            list: list of product ids
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM degiro_productinfo WHERE id = %s
                """,
                [productId]
                )
            result = dictfetchall(cursor)[0]
        
        return result

    def _get_product_quotations(self, productId: int) -> dict:
        """
        Gets the list of product ids from the DB.

        ### Returns
            list: list of product ids
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT quotations FROM degiro_productquotation WHERE id = %s
                """,
                [productId]
                )
            # FIXME: Avoid this manual conversion
            results = dictfetchall(cursor)[0]['quotations']
        
        return json.loads(results)

    def _calculate_growth(self) -> list:
        data = self._create_products_quotation()

        fx_rate = self._get_usd_conversion()
        # FIXME: Maybe Pandas/Polar provides a better way
        # FIXME: We need to convert USD/EUR, here we ignore the currency
        # FIXME: Result seems that needs to be divided by TODAY's USD/EUR exchange rate.
        aggregate = dict()
        for key in data:
            entry = data[key]
            position_value_growth = self._calculate_position_growth(entry)
            convert_fx = entry['product']['currency'] == 'USD'
            for date in position_value_growth:
                aggregate_value = aggregate.get(date, 0)
                if fx_rate:
                    aggregate_value += position_value_growth[date] / fx_rate
                else:
                    aggregate_value += position_value_growth[date]
                aggregate[date] = aggregate_value

        dataset = []
        for day in aggregate:
            dataset.append({'x': day, 'y': aggregate[day]})

        return dataset

    def _calculate_position_growth(self, entry: dict) -> dict:
        self.logger.info(f"Processing {entry['product']['name']}")
        
        product_history_dates = list(entry['history'].keys())
        
        start_date = datetime.strptime(product_history_dates[0], LocalizationUtility.DATE_FORMAT).date()
        if product_history_dates[-1] == 0:
            final_date = datetime.strptime(product_history_dates[-1], LocalizationUtility.DATE_FORMAT).date()
        else:
            final_date = datetime.today().date()

        # difference between current and previous date
        delta = timedelta(days=1)
        # store the dates between two dates in a list
        dates = []
        while start_date <= final_date:
            # add current date to list by converting  it to iso format
            dates.append(start_date.strftime(LocalizationUtility.DATE_FORMAT))
            # increment start date by timedelta
            start_date += delta

        position_value = dict()
        for date in entry['history']:
            index = dates.index(date)
            for d in dates[index:]:
                position_value[d] = entry['history'][date]

        aggregate = dict()
        for date in entry['quotation']['quotes']:
            aggregate[date] = position_value[date] * entry['quotation']['quotes'][date]

        return aggregate

    def _get_usd_conversion(self) -> float:
        """
        Gets the USD/EUR relation.

        The value is retrieved from the DeGiro `get_products_info` method.

        ### Returns
            fx: The USD-EUR conversion rate
        """
        trading_api = DeGiro.get_client()
        usd_info = trading_api.get_products_info(
            product_list=[705366], # 705366 is the product id for the USD/EUR
            raw=True,
        )

        return usd_info['data']['705366']['closePrice']
    
    def _calculate_interval(self, date_from) -> Interval:
        """
        Calculates the interval between the provided date and today
        ### Parameters
            date_from: date from to calculate the interval
        ### Returns
            Interval: Interval that representes the range from date_from to today
        """
        # Convert String to date object
        d1 = datetime.strptime(date_from, LocalizationUtility.DATE_FORMAT)
        today = datetime.today()
        # difference between dates in timedelta
        delta = (today - d1).days

        interval = None
        match delta:
            case diff if diff in range(1, 7):
                interval = Interval.P1W
            case diff if diff in range(7, 30):
                interval = Interval.P1M
            case diff if diff in range(30, 90):
                interval = Interval.P3M
            case diff if diff in range(90, 180):
                interval = Interval.P6M
            case diff if diff in range(180, 365):
                interval = Interval.P1Y
            case diff if diff in range(365, 3*365):
                interval = Interval.P3Y
            case diff if diff in range(3*365, 5*365):
                interval = Interval.P5Y
            case diff if diff in range(5*365, 10*365):
                interval = Interval.P10Y

        return interval

    def _create_products_quotation(self) -> dict:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT date, productId, buysell, quantity, price, total FROM degiro_transactions
                """
                )
            results = dictfetchall(cursor)
        
        product_growth = {}
        for entry in results:
            key = entry['productId']
            product = product_growth.get(key, {})
            carry_total = product.get('carry_total', 0)

            stock_date = entry['date'].strftime(LocalizationUtility.DATE_FORMAT)
            carry_total += entry['quantity']
            
            product['carry_total'] = carry_total
            if 'history' not in product:
                product['history'] = {}    
            product['history'][stock_date] = carry_total
            product_growth[key] = product
        
        # Cleanup 'carry_total' from result
        for key in product_growth.keys():
            del product_growth[key]['carry_total']

        delete_keys = []
        for key in product_growth.keys():
            product = self._get_productInfo(key)
            
            # If the product is NOT tradable, we shouldn't consider it for Growth
            if product['tradable'] == False:
                delete_keys.append(key)
                continue
            
            product_growth[key]['product'] = {}
            product_growth[key]['product']['name'] = product['name']
            product_growth[key]['product']['isin'] = product['isin']
            product_growth[key]['product']['symbol'] = product['symbol']
            product_growth[key]['product']['currency'] = product['currency']
            product_growth[key]['product']['vwdId'] = product['vwdId']
            product_growth[key]['product']['vwdIdSecondary'] = product['vwdIdSecondary']

            # Calculate Quotation Range
            product_growth[key]['quotation'] = {}
            product_history_dates = list(product_growth[key]['history'].keys())
            start_date = product_history_dates[0]
            final_date = datetime.today().strftime(LocalizationUtility.DATE_FORMAT)
            tmp_last = product_history_dates[-1]
            if product_growth[key]['history'][tmp_last] == 0:
                final_date = tmp_last
            
            product_growth[key]['quotation']['from_date'] = start_date
            product_growth[key]['quotation']['to_date'] = final_date
            # Interval should be from start_date, since the QuoteCast query doesn't support more granularity
            product_growth[key]['quotation']['interval'] = self._calculate_interval(start_date)

        # Delete the non-tradable products
        for key in delete_keys:
            del product_growth[key]

        # We need to use the productIds to get the daily quote for each product
        for key in product_growth.keys():
            if product_growth[key]['product'].get('vwdIdSecondary') != None:
                issueId = product_growth[key]['product'].get('vwdIdSecondary') 
            else:
                issueId = product_growth[key]['product'].get('vwdId')
            
            interval = product_growth[key]['quotation']['interval']
            quotes_dict = self._get_product_quotations(key)

            product_growth[key]['quotation']['quotes'] = quotes_dict

        return product_growth
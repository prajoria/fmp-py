write a fmp_historical_chart_fetcher.py in /home/daaji/masterswork/git/FinRobot/external/fmp-py/src/fmp_py/StockAnalysis/cache
- This program fetches data for a stock or list of stocks using get_historical_price_full in /home/daaji/masterswork/git/FinRobot/external/fmp-py/src/fmp_py/fmp_historical_charts.py 
- saves data in mysql db in table named historical_price_full_daily
- it tries load data for last 5 year fetching data with considerations of API limits in place
- Maintain a watermark in separate table to make sure till what date data has been succesully fetched.
- When program crashes we resume from date data is not fecthed.
- stock symbol and date should be primary key for table.
- suggest a list of most popular stocks and put it in a popular_stocks list
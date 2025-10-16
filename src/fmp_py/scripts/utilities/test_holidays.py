#!/usr/bin/env python3
"""
Test holiday detection
"""

import os
import sys
from datetime import datetime, date, timedelta
from typing import Set

class HolidayTester:
    def get_us_market_holidays(self, year: int) -> Set[date]:
        """Get US stock market holidays for a given year"""
        holidays = set()
        
        # Fixed date holidays
        holidays.add(date(year, 1, 1))   # New Year's Day
        holidays.add(date(year, 7, 4))   # Independence Day
        holidays.add(date(year, 12, 25)) # Christmas Day
        
        # Martin Luther King Jr. Day (3rd Monday in January)
        jan_1 = date(year, 1, 1)
        days_to_first_monday = (7 - jan_1.weekday()) % 7
        first_monday = jan_1 + timedelta(days=days_to_first_monday)
        mlk_day = first_monday + timedelta(days=14)  # 3rd Monday
        holidays.add(mlk_day)
        
        # Presidents' Day (3rd Monday in February)
        feb_1 = date(year, 2, 1)
        days_to_first_monday = (7 - feb_1.weekday()) % 7
        first_monday = feb_1 + timedelta(days=days_to_first_monday)
        presidents_day = first_monday + timedelta(days=14)  # 3rd Monday
        holidays.add(presidents_day)
        
        # Good Friday (Friday before Easter) - approximate calculation
        easter = self.get_easter_date(year)
        good_friday = easter - timedelta(days=2)
        holidays.add(good_friday)
        
        # Memorial Day (last Monday in May)
        may_31 = date(year, 5, 31)
        days_back_to_monday = (may_31.weekday() - 0) % 7
        memorial_day = may_31 - timedelta(days=days_back_to_monday)
        holidays.add(memorial_day)
        
        # Juneteenth (June 19) - federal holiday since 2021
        if year >= 2021:
            holidays.add(date(year, 6, 19))
        
        # Labor Day (1st Monday in September)
        sep_1 = date(year, 9, 1)
        days_to_first_monday = (7 - sep_1.weekday()) % 7
        labor_day = sep_1 + timedelta(days=days_to_first_monday)
        holidays.add(labor_day)
        
        # Thanksgiving (4th Thursday in November)
        nov_1 = date(year, 11, 1)
        days_to_first_thursday = (3 - nov_1.weekday()) % 7
        first_thursday = nov_1 + timedelta(days=days_to_first_thursday)
        thanksgiving = first_thursday + timedelta(days=21)  # 4th Thursday
        holidays.add(thanksgiving)
        
        # Black Friday (day after Thanksgiving) - market closed
        black_friday = thanksgiving + timedelta(days=1)
        holidays.add(black_friday)
        
        return holidays
    
    def get_easter_date(self, year: int) -> date:
        """Calculate Easter date using algorithm"""
        # Simple Easter calculation algorithm
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        return date(year, month, day)

if __name__ == "__main__":
    tester = HolidayTester()
    
    # Test 2021 holidays
    holidays_2021 = sorted(tester.get_us_market_holidays(2021))
    print("2021 US Market Holidays:")
    for holiday in holidays_2021:
        day_name = holiday.strftime("%A")
        print(f"  {holiday} ({day_name})")
    
    # Check specific dates we know
    labor_day_2021 = date(2021, 9, 6)
    thanksgiving_2021 = date(2021, 11, 25)
    
    print(f"\nVerification:")
    print(f"Labor Day 2021 (Sep 6): {'✅ Detected' if labor_day_2021 in holidays_2021 else '❌ Missed'}")
    print(f"Thanksgiving 2021 (Nov 25): {'✅ Detected' if thanksgiving_2021 in holidays_2021 else '❌ Missed'}")
# MFtool

Tool to calclate MF returns and bechmark each fund wrt Nifty 50 performance from the date of investment

## How to use?
* Required columns in the input csv file:
	1. "symbol" - Name/Symbol of the MF
	2. "isin" - Security ID (ISIN) of the MF
	3. "trade_date" - Purchase date
	4. "price" - NAV on purchase date
	5. "quantity" - Units bought
* Paramters to be edited in `MF_Return.py`:

	`currDate = date(2023, 1, 6)


	file = "mf_2022_buy.csv"`

	
* Run the `MF_Return.py` script
	> Package requirements: `numpy, pandas, scipy, urllib`
* Output Summary Excel example [MF_Summary.xlsx](https://github.com/pa1tech/MFtool/blob/main/MF_Summary.xlsx?raw=true) for the input file [mf_transactions.csv](https://github.com/pa1tech/MFtool/blob/main/mf_transactions.csv)

### References
* [https://github.com/peliot/XIRR-and-XNPV](https://github.com/peliot/XIRR-and-XNPV)
* [https://github.com/swapniljariwala/nsepy](https://github.com/swapniljariwala/nsepy)
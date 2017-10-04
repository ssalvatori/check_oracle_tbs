# Check Oracle tablespace_name

Base on https://exchange.nagios.org/directory/Databases/Plugins/Oracle/check_oracle_tbs/details

## Requirements

* cx_Oracle (https://oracle.github.io/python-cx_Oracle/)
* oracle instantclient (http://www.oracle.com/technetwork/database/features/instant-client/index-097480.html)


## Setup

Install python dependencies

```bash
pip install -r requirements.txt
```

## Run

Add oracle instaclient libs to **LD_LIBRARY_PATH**

```bash
export LD_LIBRARY_PATH=/usr/lib/oracle/12.2/client64/lib:$LD_LIBRARY_PATH
```

Show usage

```bash
./check_oracle_tbs.py --help
```

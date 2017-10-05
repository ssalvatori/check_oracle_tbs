#!/usr/bin/env python
"""
Check Oracle Tablespace size
Base on https://exchange.nagios.org/directory/Databases/Plugins/Oracle/check_oracle_tbs/details
"""
import re
import argparse
import cx_Oracle
import sys

def main(dbhost, port, user, password, service_name, excluded_tables=None,
         warning_level=85, critical_level=95, check_autoextensible="false", min_space=0.0):
    """Check Oracle Tablespace size
    dbhost
    port
    user
    password
    service_name
    excluded_tables: regex for tablespace exclusion (example: -e='UNDOTBS[0-9]')
    warning_level: usage percent for warning alert
    critical_level: usage percent for critical alert
    check_autoextensible: check autoextensible tables also
    min_space: script will return exit 1 if the free space is less than this value
    """

    try:
        dsn_string = cx_Oracle.makedsn(host=dbhost, port=port, service_name=service_name)
        connection = cx_Oracle.connect(user=user, password=password, dsn=dsn_string)

        cursor = connection.cursor()
        cursor.execute("""
		SELECT
			NVL(b.tablespace_name,nvl(a.tablespace_name,'UNKOWN')) name,
			((kbytes_alloc-nvl(kbytes_free,0))/kbytes_alloc)*100 pct_used,
			NVL(kbytes_free/1024,0) free,
			autoextensible
		FROM
			(SELECT
				SUM(bytes)/1024 Kbytes_free,
				max(bytes)/1024 largest,
				tablespace_name
			FROM
				sys.dba_free_space
			GROUP BY
				tablespace_name
			) a,
			(SELECT SUM(bytes)/1024 Kbytes_alloc,
				tablespace_name
			FROM
				sys.dba_data_files
			GROUP BY
				tablespace_name
			) b,
			(SELECT
				tablespace_name,
				autoextensible
			FROM
				sys.dba_data_files
			GROUP BY
				tablespace_name,
				autoextensible
			HAVING
				autoextensible='YES'
			) c
			WHERE
				a.tablespace_name (+) =  b.tablespace_name
			AND
				c.tablespace_name (+) = b.tablespace_name
		""")

        regexp_exclude = None

        if excluded_tables:
            regexp_exclude = re.compile('(%s)'%excluded_tables)

        remaining = 0

        for result in cursor:

            if excluded_tables is not None and not regexp_exclude.match(result[0]):
                remaining += float(result[2])

                if check_autoextensible == 'false' and result[3] == 'YES':
                    print "skiping autoextensible table %s" % (result[0])
                    continue

                if float(result[1]) >= critical_level:
                    print "%s CRITICAL %.2f autoextensible(%s)" % (result[0], result[1], result[3])
                    continue

                if float(result[1]) >= warning_level:
                    print "%s WARNING %.2f autoextensible(%s)" % (result[0], result[1], result[3])
                    continue

        print "Remaining free space = (%.2fMb)" % remaining

        if min_space > 0 and remaining <= min_space:
            print "Space is less than %.2fMb" % min_space
            sys.exit(1)

    except Exception as exception:
        print "Error: %s" % format(exception)
        raise

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Check Oracle Tablespace size')

    parser.add_argument('--db_host', required=True, dest='db_host',
                        metavar='db_host', type=str, help="Oracle host")
    parser.add_argument('--db_port', required=True, dest='db_port',
                        metavar='db_port', type=str, help="Oracle port")
    parser.add_argument('--db_user', required=True, dest='db_user',
                        metavar='db_user', type=str, help="Oracle user")
    parser.add_argument('--db_password', required=True, dest='db_password',
                        metavar='db_password', type=str, help="Oracle password")
    parser.add_argument('--db_service_name', required=True, dest='db_service_name',
                        metavar='db_service_name', type=str, help="Oracle service_name")
    parser.add_argument('-e', metavar='exclusion', dest='exclusion', type=str,
                        help="regex for tablespace exclusion (example: -e='UNDOTBS[0-9]')")
    parser.add_argument('-w', metavar='warning', dest='warning_level',
                        default=85.0, type=float, help="usage percent for warning")
    parser.add_argument('-c', metavar='critical', dest='critical_level',
                        default=95.0, type=float, help="usage percent for critical alert")
    parser.add_argument('-wauto', metavar='wauto', dest='wauto', type=str,
                        help="usage percent for warning on autoextensible tablespaces (true|false)")
    parser.add_argument('-min_space', metavar='min_space', dest='min_space', type=float,
                        help="script will return exit 1 if the free space is less or equal thsn this value")

    args_obj = parser.parse_args()

    main(args_obj.db_host, args_obj.db_port, args_obj.db_user, args_obj.db_password,
         args_obj.db_service_name, args_obj.exclusion, args_obj.warning_level,
         args_obj.critical_level, args_obj.wauto, args_obj.min_space)
